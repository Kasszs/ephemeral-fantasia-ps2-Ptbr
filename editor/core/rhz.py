"""
RHZ Container Manager for Ephemeral Fantasia (PS2)
Handles parsing, unpacking, sector alignment, and rebuilding of DATA*.BIN archives.
"""

import struct
import math
from dataclasses import dataclass
from typing import List, Optional


SECTOR_SIZE = 2048
RHZ_MAGIC = b"RHZ\x00"
PAD_PATTERN = b"\x01\x23\x45\x67\x89\xab\xcd\xef"


def make_padding(num_bytes: int) -> bytes:
    if num_bytes <= 0:
        return b""
    reps = (num_bytes // 8) + 1
    return (PAD_PATTERN * reps)[:num_bytes]


@dataclass
class RHZEntry:
    file_id: int
    start_sector: int
    sector_count: int
    exact_size: int
    data: bytearray


class RHZArchive:
    def __init__(self):
        self.entries: List[RHZEntry] = []
        self.header_reserved: bytes = b""
        self.extra_dword: int = 0

    @classmethod
    def load(cls, file_path: str) -> "RHZArchive":
        archive = cls()
        with open(file_path, "rb") as f:
            header = f.read(32)
            if len(header) < 32:
                raise ValueError("Arquivo inválido: cabeçalho menor que 32 bytes.")
            
            magic = header[:4]
            if magic != RHZ_MAGIC:
                raise ValueError(f"Magic inválido: esperado {RHZ_MAGIC!r}, encontrado {magic!r}")
            
            archive.header_reserved = header[4:16]
            num_files, sector_size, first_sec, extra = struct.unpack("<IIII", header[16:32])
            archive.extra_dword = extra
            
            # Read TOC (16 bytes per entry)
            toc_raw = f.read(num_files * 16)
            toc_entries = []
            for i in range(num_files):
                fid, sec, cnt, sz = struct.unpack("<IIII", toc_raw[i * 16 : (i + 1) * 16])
                toc_entries.append((fid, sec, cnt, sz))
            
            # Read file payloads
            for fid, sec, cnt, sz in toc_entries:
                f.seek(sec * SECTOR_SIZE)
                data = bytearray(f.read(sz))
                archive.entries.append(RHZEntry(
                    file_id=fid,
                    start_sector=sec,
                    sector_count=cnt,
                    exact_size=sz,
                    data=data
                ))
        
        return archive

    def save(self, output_path: str) -> None:
        """
        Recompila o arquivo RHZ com alinhamento correto de setores de 2048 bytes
        e recálculo automático de setores para todos os arquivos modificados/expandidos.
        """
        num_files = len(self.entries)
        toc_bytes_len = 32 + num_files * 16
        first_file_sector = math.ceil(toc_bytes_len / SECTOR_SIZE)
        
        cur_sector = first_file_sector
        recalculated_toc = []
        for entry in self.entries:
            exact_sz = len(entry.data)
            sector_cnt = math.ceil(exact_sz / SECTOR_SIZE) if exact_sz > 0 else 1
            recalculated_toc.append((entry.file_id, cur_sector, sector_cnt, exact_sz))
            cur_sector += sector_cnt
        
        with open(output_path, "wb") as f:
            # Write 32-byte header
            f.write(RHZ_MAGIC)
            f.write(self.header_reserved.ljust(12, b"\x00"))
            f.write(struct.pack("<IIII", num_files, SECTOR_SIZE, first_file_sector, self.extra_dword))
            
            # Write TOC entries
            for fid, sec, cnt, sz in recalculated_toc:
                f.write(struct.pack("<IIII", fid, sec, cnt, sz))
            
            # Pad TOC up to first_file_sector
            toc_padding_len = (first_file_sector * SECTOR_SIZE) - f.tell()
            if toc_padding_len > 0:
                f.write(make_padding(toc_padding_len))
            
            # Write file data aligned to sectors
            for idx, entry in enumerate(self.entries):
                expected_sec = recalculated_toc[idx][1]
                cur_pos = f.tell()
                expected_pos = expected_sec * SECTOR_SIZE
                if cur_pos != expected_pos:
                    raise RuntimeError(f"Desalinhamento no arquivo {idx}: pos {cur_pos} != {expected_pos}")
                
                f.write(entry.data)
                exact_sz = len(entry.data)
                sec_cnt = recalculated_toc[idx][2]
                file_padding = (sec_cnt * SECTOR_SIZE) - exact_sz
                if file_padding > 0:
                    f.write(make_padding(file_padding))
