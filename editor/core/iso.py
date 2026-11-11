"""
ISO-9660 Patcher and Injector for Ephemeral Fantasia (PS2)
Allows direct injection of DATA6_US.BIN into the game ISO image,
with support for in-place sector replacement, relocation, and backup creation.
"""

import os
import shutil
import struct
import math
from typing import Optional, Tuple, Dict, Callable


SECTOR_SIZE = 2048
KONAMI_PAD = b"\x01\x23\x45\x67\x89\xab\xcd\xef"


def make_padding(num_bytes: int) -> bytes:
    if num_bytes <= 0:
        return b""
    reps = (num_bytes // 8) + 1
    return (KONAMI_PAD * reps)[:num_bytes]


class ISOManager:
    @staticmethod
    def get_iso_info(iso_path: str) -> Dict:
        """Lê informações básicas do sistema de arquivos ISO-9660."""
        if not os.path.exists(iso_path):
            raise FileNotFoundError(f"Arquivo ISO não encontrado: {iso_path}")

        iso_size = os.path.getsize(iso_path)
        with open(iso_path, "rb") as f:
            # Setor 16: PVD
            f.seek(16 * SECTOR_SIZE)
            pvd = f.read(SECTOR_SIZE)
            if pvd[1:6] != b"CD001":
                raise ValueError("A imagem selecionada não é uma ISO-9660 válida (Magic CD001 ausente).")
            
            vol_id = pvd[40:72].decode("latin1").strip()
            total_sectors = struct.unpack("<I", pvd[80:84])[0]
            
            # Localizar diretório DATA no Setor 263
            f.seek(263 * SECTOR_SIZE)
            data_dir = f.read(SECTOR_SIZE)
            target = b"DATA6_US.BIN;1"
            idx = data_dir.find(target)
            if idx == -1:
                raise ValueError("DATA6_US.BIN;1 não encontrado no diretório DATA da ISO.")
            
            rec_start = idx - 33
            rec = data_dir[rec_start : rec_start + data_dir[rec_start]]
            lba = struct.unpack("<I", rec[2:6])[0]
            size = struct.unpack("<I", rec[10:14])[0]
            
            # Setor do próximo arquivo (DATA0.BIN;1) para calcular o espaço alocado
            orig_data6_lba = 386669
            idx_data0 = data_dir.find(b"DATA0.BIN;1")
            if idx_data0 != -1:
                rec0_start = idx_data0 - 33
                rec0 = data_dir[rec0_start : rec0_start + data_dir[rec0_start]]
                next_lba = struct.unpack("<I", rec0[2:6])[0]
                orig_allocated_sectors = next_lba - orig_data6_lba
            else:
                next_lba = 414547
                orig_allocated_sectors = next_lba - orig_data6_lba

            # Se o LBA atual estiver dentro do slot original, calcula normal;
            # se já tiver sido movido para o final da ISO, mantém o slot original disponível
            if lba <= orig_data6_lba:
                allocated_sectors = orig_allocated_sectors
            else:
                allocated_sectors = orig_allocated_sectors

        return {
            "iso_path": iso_path,
            "iso_size": iso_size,
            "vol_id": vol_id,
            "total_sectors": total_sectors,
            "orig_data6_lba": orig_data6_lba,
            "data6_lba": lba,
            "data6_size": size,
            "data6_allocated_sectors": allocated_sectors,
            "data6_allocated_bytes": allocated_sectors * SECTOR_SIZE,
            "rec_sector": 263,
            "rec_offset_in_sector": rec_start
        }

    @classmethod
    def inject_data6(
        cls,
        iso_path: str,
        data6_bin_path: str,
        output_iso_path: Optional[str] = None,
        create_backup: bool = True,
        progress_cb: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict:
        """
        Injeta o arquivo DATA6_US.BIN compilado diretamente na imagem ISO do PS2.
        Se output_iso_path for fornecido e diferente de iso_path, gera uma nova ISO.
        Caso contrário, injeta diretamente (criando backup se create_backup=True).
        """
        info = cls.get_iso_info(iso_path)
        data6_size = os.path.getsize(data6_bin_path)
        needed_sectors = math.ceil(data6_size / SECTOR_SIZE)
        allocated_sectors = info["data6_allocated_sectors"]

        target_iso = output_iso_path if output_iso_path else iso_path

        # Se for criar uma nova ISO de saída, clona a original primeiro
        if output_iso_path and os.path.abspath(output_iso_path) != os.path.abspath(iso_path):
            if progress_cb:
                progress_cb(0, 100, "Copiando imagem ISO base para a saída...")
            shutil.copy2(iso_path, output_iso_path)
        elif create_backup:
            bak_path = iso_path + ".bak"
            if not os.path.exists(bak_path):
                if progress_cb:
                    progress_cb(0, 100, "Criando cópia de segurança da ISO original (.iso.bak)...")
                shutil.copy2(iso_path, bak_path)

        orig_slot_lba = info["orig_data6_lba"]

        # Se couber no slot original (LBA 386669, 27878 setores)
        if needed_sectors <= allocated_sectors:
            mode = "in_place"
            target_lba = orig_slot_lba
        else:
            mode = "appended"
            target_lba = info["total_sectors"]

        if progress_cb:
            progress_cb(20, 100, f"Gravando dados no LBA {target_lba} ({mode})...")

        with open(target_iso, "r+b") as f_iso, open(data6_bin_path, "rb") as f_bin:
            # 1. Gravar dados do arquivo BIN na ISO
            f_iso.seek(target_lba * SECTOR_SIZE)
            
            chunk_size = 1024 * 1024  # 1 MB por bloco
            bytes_copied = 0
            while True:
                chunk = f_bin.read(chunk_size)
                if not chunk:
                    break
                f_iso.write(chunk)
                bytes_copied += len(chunk)
                if progress_cb and data6_size > 0:
                    pct = 20 + int((bytes_copied / data6_size) * 60)
                    progress_cb(pct, 100, f"Gravando {bytes_copied // (1024*1024)} MB de {data6_size // (1024*1024)} MB...")

            # Preenchimento até o limite de setores necessários
            padding_needed = (needed_sectors * SECTOR_SIZE) - data6_size
            if padding_needed > 0:
                f_iso.write(make_padding(padding_needed))

            # Se foi in_place e sobrou espaço alocado original não utilizado
            if mode == "in_place" and needed_sectors < allocated_sectors:
                extra_pad = (allocated_sectors - needed_sectors) * SECTOR_SIZE
                f_iso.write(make_padding(extra_pad))

            if progress_cb:
                progress_cb(85, 100, "Atualizando descritores de diretório e TOC ISO-9660...")

            # 2. Atualizar o Directory Record de DATA6_US.BIN;1 no Setor 263
            rec_pos = (info["rec_sector"] * SECTOR_SIZE) + info["rec_offset_in_sector"]
            
            # Bytes 2..10: LBA (Little Endian + Big Endian)
            # Bytes 10..18: Tamanho em bytes (Little Endian + Big Endian)
            lba_both = struct.pack("<I", target_lba) + struct.pack(">I", target_lba)
            size_both = struct.pack("<I", data6_size) + struct.pack(">I", data6_size)

            f_iso.seek(rec_pos + 2)
            f_iso.write(lba_both)
            f_iso.write(size_both)

            # 3. Se foi modo in_place, restaurar tamanho original no PVD (Setor 16) e truncar ISO limpa
            if mode == "in_place":
                orig_total_sectors = 728144
                f_iso.seek(16 * SECTOR_SIZE + 80)
                vol_size_both = struct.pack("<I", orig_total_sectors) + struct.pack(">I", orig_total_sectors)
                f_iso.write(vol_size_both)
                f_iso.flush()

                # Truncar tamanho de arquivo da ISO se ela tiver sido estendida antes
                clean_iso_bytes = orig_total_sectors * SECTOR_SIZE
                if os.path.getsize(target_iso) > clean_iso_bytes:
                    f_iso.truncate(clean_iso_bytes)

            elif mode == "appended":
                new_total_sectors = target_lba + needed_sectors
                f_iso.seek(16 * SECTOR_SIZE + 80)
                vol_size_both = struct.pack("<I", new_total_sectors) + struct.pack(">I", new_total_sectors)
                f_iso.write(vol_size_both)

            f_iso.flush()

            f_iso.flush()

        if progress_cb:
            progress_cb(100, 100, "Injeção concluída com sucesso!")

        return {
            "target_iso": target_iso,
            "mode": mode,
            "lba": target_lba,
            "size_bytes": data6_size,
            "sectors": needed_sectors
        }
