"""
SCR Script & Bytecode Engine for Ephemeral Fantasia (PS2)
Extracts strings, parses bytecode pointer references (0x082A / 0x082B),
and safely injects expanded translations with strict 1-to-1 index preservation.
"""

import struct
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set


SCR_MAGIC = b"SCR\x1a"


class TextExpansionLimitError(Exception):
    """Lançada quando a expansão de um script excede o limite estrito de 16 bits do operando."""
    pass


@dataclass
class SCRString:
    index: int
    orig_offset: int
    orig_text: str
    translated_text: str
    refs: List[Tuple[int, bool]] = field(default_factory=list)  # [(pc, is_32bit)]
    category: str = "dialogue"  # dialogue, speaker, system, asset


class SCRScript:
    def __init__(self, script_id: int, data: bytearray):
        self.script_id = script_id
        self.raw_data = bytearray(data)
        self.words: List[int] = []
        self.strings: List[SCRString] = []
        self.orig_text_end: int = 0
        self.binary_tail: bytes = b""
        self.struct_refs_16: List[int] = []  # pc of 16-bit struct refs
        self.struct_refs_32: List[int] = []  # pc of 32-bit struct refs
        self.is_valid_scr = False

        self._parse()

    def _parse(self) -> None:
        if len(self.raw_data) < 44 or self.raw_data[:4] != SCR_MAGIC:
            self.is_valid_scr = False
            return
        
        self.is_valid_scr = True
        self.words = list(struct.unpack("<11I", self.raw_data[:44]))
        
        code_start = self.words[5]
        code_end = self.words[7]  # words[7] is str_base (end of code section; words[6] was code relative size)
        str_base = self.words[7]
        str_len = self.words[8]
        
        if str_base >= len(self.raw_data) or str_len == 0:
            return
        
        # 1. Escanear Bytecode procurando referências de PUSH_STR (0x082A e 0x082B)
        referenced_text_offsets: Set[int] = set()
        p = code_start
        while p <= code_end - 4:
            instr = struct.unpack("<H", self.raw_data[p:p+2])[0]
            masked = instr & 0xF83F
            if masked == 0x082A:
                off16 = struct.unpack("<H", self.raw_data[p+2:p+4])[0]
                if off16 < 16000 and (str_base + off16) < len(self.raw_data):
                    abs_pos = str_base + off16
                    null_idx = self.raw_data.find(b"\x00", abs_pos, min(len(self.raw_data), abs_pos + 1024))
                    if null_idx != -1 and null_idx > abs_pos:
                        chunk = self.raw_data[abs_pos:null_idx]
                        if all(32 <= b <= 255 or b in (10, 13, 9, 26, 12, 1, 2, 3, 143) for b in chunk):
                            referenced_text_offsets.add(off16)
                p += 2
            elif masked == 0x082B and p <= code_end - 6:
                off32 = struct.unpack("<I", self.raw_data[p+2:p+6])[0]
                if off32 < 16000 and (str_base + off32) < len(self.raw_data):
                    abs_pos = str_base + off32
                    null_idx = self.raw_data.find(b"\x00", abs_pos, min(len(self.raw_data), abs_pos + 1024))
                    if null_idx != -1 and null_idx > abs_pos:
                        chunk = self.raw_data[abs_pos:null_idx]
                        if all(32 <= b <= 255 or b in (10, 13, 9, 26, 12, 1, 2, 3, 143) for b in chunk):
                            referenced_text_offsets.add(off32)
                p += 2
            else:
                p += 2

        # 2. Extrair strings da Seção 7 sequencialmente
        pos = str_base
        section_end = min(len(self.raw_data), str_base + str_len)
        extracted = []
        max_text_offset = max(referenced_text_offsets) if referenced_text_offsets else 0
        
        invalid_ctrls = set(range(0, 32)) - {9, 10, 13, 26, 12}
        
        while pos < section_end:
            rel_off = pos - str_base
            if self.raw_data[pos : pos + 4] == b"\x00\x00\x00\x00":
                break

            null_pos = self.raw_data.find(b"\x00", pos, section_end)
            if null_pos == -1:
                break
            chunk = self.raw_data[pos:null_pos]
            if len(chunk) > 0:
                if any(b in invalid_ctrls for b in chunk) or b"\xff\xff" in chunk:
                    break
                printable_cnt = sum(1 for b in chunk if 32 <= b <= 255 or b in (10, 13, 9, 26, 12, 1, 2, 3, 143))
                if printable_cnt / len(chunk) >= 0.75:
                    try:
                        text_str = chunk.decode("cp1252")
                    except UnicodeDecodeError:
                        text_str = chunk.decode("latin1", errors="replace")
                    
                    cat = "dialogue"
                    if text_str.startswith((".\\", "/", "data\\", "sys")) or text_str.endswith((".rhe", ".am", ".tm2")):
                        cat = "asset"
                    elif len(text_str) <= 16 and "\n" not in text_str and not text_str.endswith("."):
                        cat = "speaker"
                    
                    extracted.append((rel_off, chunk, text_str, cat))
                    pos = null_pos + 1
                else:
                    break
            else:
                pos += 1
        
        self.orig_text_end = pos - str_base
        self.binary_tail = bytes(self.raw_data[str_base + self.orig_text_end : section_end])
        
        for idx, (off, raw_b, text_s, cat) in enumerate(extracted):
            s_obj = SCRString(
                index=idx,
                orig_offset=off,
                orig_text=text_s,
                translated_text=text_s,
                category=cat
            )
            self.strings.append(s_obj)

        # 3. Vincular referências do bytecode
        offset_to_string = {s.orig_offset: s for s in self.strings}

        p = code_start
        while p <= code_end - 4:
            instr = struct.unpack("<H", self.raw_data[p:p+2])[0]
            masked = instr & 0xF83F
            if masked == 0x082A:
                off16 = struct.unpack("<H", self.raw_data[p+2:p+4])[0]
                if off16 in offset_to_string:
                    offset_to_string[off16].refs.append((p, False))
                elif off16 >= self.orig_text_end:
                    self.struct_refs_16.append(p)
                p += 2
            elif masked == 0x082B and p <= code_end - 6:
                off32 = struct.unpack("<I", self.raw_data[p+2:p+6])[0]
                if off32 in offset_to_string:
                    offset_to_string[off32].refs.append((p, True))
                elif off32 >= self.orig_text_end:
                    self.struct_refs_32.append(p)
                p += 2
            else:
                p += 2

    def get_max_safe_expansion(self) -> int:
        """
        Retorna quantos bytes extras este script pode expandir com segurança
        sem que nenhuma instrução de 16-bit exceda o limite de 65535.
        """
        if not self.struct_refs_16:
            return 65535 - self.orig_text_end
        
        max_16 = 0
        for pc in self.struct_refs_16:
            val = struct.unpack("<H", self.raw_data[pc+2 : pc+4])[0]
            if val > max_16:
                max_16 = val
        
        return max(0, 65535 - max_16)

    def rebuild(self, translations: Optional[Dict[int, str]] = None) -> bytearray:
        """
        Reconstrói o arquivo .SCR com as traduções aplicadas.
        Se nenhuma tradução foi fornecida ou se todas forem idênticas ao original,
        retorna uma cópia exata do raw_data original sem qualquer alteração.
        """
        if not self.is_valid_scr:
            return bytearray(self.raw_data)
        
        if not translations:
            return bytearray(self.raw_data)
        
        # Verificar se alguma string realmente difere do original
        has_changes = False
        for s in self.strings:
            t = translations.get(s.index)
            if t is not None and t != s.orig_text:
                has_changes = True
                break
        
        if not has_changes:
            return bytearray(self.raw_data)

        # 1. Montar novo bloco de texto mantendo a ordem exata de cada string
        new_text_bytes = bytearray()
        new_offsets: Dict[int, int] = {}

        for s in self.strings:
            text_to_encode = translations.get(s.index, s.orig_text)
            raw_text = text_to_encode.replace("[PAGE]", "\x1a").replace("\\n", "\n")
            try:
                enc_bytes = raw_text.encode("cp1252") + b"\x00"
            except UnicodeEncodeError:
                enc_bytes = raw_text.encode("latin1", errors="replace") + b"\x00"
            
            new_off = len(new_text_bytes)
            new_offsets[s.index] = new_off
            new_text_bytes += enc_bytes

        # Se o novo bloco couber dentro do espaço original, mantemos orig_text_end
        if len(new_text_bytes) <= self.orig_text_end:
            remaining = self.orig_text_end - len(new_text_bytes)
            if remaining > 0:
                new_text_bytes += b"\x00" * remaining
            delta = 0
            new_text_end = self.orig_text_end
        else:
            new_text_end = len(new_text_bytes)
            delta = new_text_end - self.orig_text_end

        # 2. Clonar dados e atualizar referências no bytecode
        rebuilt = bytearray(self.raw_data)

        # Atualizar ponteiros das strings
        for s in self.strings:
            new_off = new_offsets[s.index]
            for pc, is_32bit in s.refs:
                if is_32bit:
                    rebuilt[pc+2 : pc+6] = struct.pack("<I", new_off)
                else:
                    if new_off > 0xFFFF:
                        raise TextExpansionLimitError(
                            f"String {s.index} excedeu limite de 16 bits: offset {new_off} > 65535."
                        )
                    rebuilt[pc+2 : pc+4] = struct.pack("<H", new_off)

        # Atualizar operandos de structs se houve expansão positiva
        if delta > 0:
            for pc in self.struct_refs_16:
                old_val = struct.unpack("<H", rebuilt[pc+2 : pc+4])[0]
                new_val = old_val + delta
                if new_val > 0xFFFF:
                    raise TextExpansionLimitError(
                        f"Limite de Expansão Excedido no Script #{self.script_id}: "
                        f"o texto traduzido precisa ser reduzido em pelo menos {new_val - 0xFFFF} bytes "
                        f"para não quebrar a instrução 16-bit em pc 0x{pc:X}."
                    )
                rebuilt[pc+2 : pc+4] = struct.pack("<H", new_val)
            
            for pc in self.struct_refs_32:
                old_val = struct.unpack("<I", rebuilt[pc+2 : pc+6])[0]
                rebuilt[pc+2 : pc+6] = struct.pack("<I", old_val + delta)

        # 3. Reconstruir Seção 7 (Novo Bloco de Texto + Structs)
        str_base = self.words[7]
        rebuilt[str_base : str_base + self.orig_text_end] = new_text_bytes[:self.orig_text_end]
        if delta > 0:
            rebuilt[str_base + self.orig_text_end : str_base + new_text_end] = new_text_bytes[self.orig_text_end:]
            if self.binary_tail:
                rebuilt[str_base + new_text_end : str_base + new_text_end + len(self.binary_tail)] = self.binary_tail
            rebuilt[4:8] = struct.pack("<I", self.words[1] + delta)
            rebuilt[32:36] = struct.pack("<I", new_text_end + len(self.binary_tail))

        return rebuilt
