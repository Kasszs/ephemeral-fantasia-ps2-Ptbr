"""
Font & VWF (Variable Width Font) Metrics Engine for Ephemeral Fantasia (PS2)
Accurately emulates the LetLib text rendering subsystem, using the game's native
FontCode glyph table and kerning matrix dumped from SLUS_201.69.
"""

import os
import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


DEFAULT_MAX_WIDTH = 540  # Largura máxima útil em pixels na TV
DEFAULT_MAX_LINES = 3    # Capacidade máxima padrão por caixa


@dataclass
class LineMetric:
    text: str
    width: int
    max_width: int
    overflow: bool
    excess_px: int


@dataclass
class PageMetric:
    page_idx: int
    raw_text: str
    lines: List[LineMetric] = field(default_factory=list)
    total_lines: int = 0
    max_lines: int = DEFAULT_MAX_LINES
    line_overflow: bool = False
    width_overflow: bool = False


class FontEngine:
    _instance: Optional["FontEngine"] = None

    def __init__(self, json_path: Optional[str] = None):
        if json_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            json_path = os.path.join(base_dir, "data", "font_data.json")
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.glyphs: Dict[int, dict] = {g["char_code"]: g for g in data["glyphs"]}
        self.kerning: Dict[str, int] = data["kerning"]

    @classmethod
    def get_instance(cls) -> "FontEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_char_width(self, char: str, prev_char: Optional[str] = None) -> Tuple[int, Optional[int]]:
        """
        Calcula a largura de um caractere em pixels seguindo LetLib_GetStrCodeWidth:
        largura = glifo_width + 3 + kerning(prev_idx, cur_idx)
        """
        code = ord(char)
        glyph = self.glyphs.get(code)
        if glyph:
            w = glyph["width"] + 3
            cur_idx = glyph["index"]
            if prev_char is not None:
                prev_glyph = self.glyphs.get(ord(prev_char))
                if prev_glyph:
                    k_key = f"{prev_glyph['index']},{cur_idx}"
                    if k_key in self.kerning:
                        w += self.kerning[k_key]
            return w, cur_idx
        else:
            return 14, None

    def measure_line(self, line: str) -> int:
        """Calcula a largura exata de uma linha em pixels, ignorando tags de cor e controle."""
        # Remover tags de cor do jogo: \x8fc0xRRGGBBAA (12 chars)
        line = re.sub(r"\x8fc0x[0-9a-fA-F]{8}", "", line)
        # Remover tags amigáveis [COLOR:...]
        line = re.sub(r"\[COLOR:[^\]]*\]", "", line)
        # Remover tags de controle de 1 byte \x0c.
        line = re.sub(r"\x0c.", "", line)

        total_w = 0
        prev_char = None
        for c in line:
            w, _ = self.get_char_width(c, prev_char)
            total_w += w
            prev_char = c
        return total_w

    def analyze_text(self, text: str, max_w: int = DEFAULT_MAX_WIDTH, max_lines: int = DEFAULT_MAX_LINES) -> List[PageMetric]:
        """
        Analisa todo o texto de uma entrada de diálogo.
        Separa por páginas (\x1A ou [PAGE]) e por linhas (\n).
        Retorna métricas completas de cada linha e página com alertas de estouro.
        """
        normalized = text.replace("[PAGE]", "\x1a").replace("\\n", "\n")
        pages_raw = normalized.split("\x1a")
        results = []

        for p_idx, page_str in enumerate(pages_raw):
            lines_raw = page_str.split("\n")
            lines_metric = []
            has_width_overflow = False

            for l_str in lines_raw:
                w = self.measure_line(l_str)
                is_over = w > max_w
                if is_over:
                    has_width_overflow = True
                lines_metric.append(LineMetric(
                    text=l_str,
                    width=w,
                    max_width=max_w,
                    overflow=is_over,
                    excess_px=max(0, w - max_w)
                ))

            line_cnt_over = len(lines_metric) > max_lines
            results.append(PageMetric(
                page_idx=p_idx,
                raw_text=page_str,
                lines=lines_metric,
                total_lines=len(lines_metric),
                max_lines=max_lines,
                line_overflow=line_cnt_over,
                width_overflow=has_width_overflow
            ))

        return results

    def auto_wrap(self, text: str, max_w: int = DEFAULT_MAX_WIDTH, max_lines: int = DEFAULT_MAX_LINES) -> str:
        """
        Quebra automática inteligente: quebra palavras com \n quando atingem max_w px,
        e insere [PAGE] quando atinge max_lines linhas.
        Preserva marcações de cor e quebras manuais.
        """
        normalized = text.replace("[PAGE]", "\x1a").replace("\\n", "\n")
        raw_pages = normalized.split("\x1a")
        wrapped_pages = []

        for page in raw_pages:
            words = page.split(" ")
            page_lines = []
            cur_line = ""

            for word in words:
                if "\n" in word:
                    sub_words = word.split("\n")
                    for s_idx, sw in enumerate(sub_words):
                        if s_idx > 0:
                            page_lines.append(cur_line)
                            cur_line = ""
                        test_line = (cur_line + " " + sw).strip() if cur_line else sw
                        if self.measure_line(test_line) > max_w:
                            if cur_line:
                                page_lines.append(cur_line)
                            cur_line = sw
                        else:
                            cur_line = test_line
                    continue

                test_line = (cur_line + " " + word).strip() if cur_line else word
                if self.measure_line(test_line) > max_w:
                    if cur_line:
                        page_lines.append(cur_line)
                    cur_line = word
                else:
                    cur_line = test_line

            if cur_line:
                page_lines.append(cur_line)

            # Paginar caso tenha mais de max_lines
            paged_blocks = []
            for i in range(0, len(page_lines), max_lines):
                chunk = page_lines[i : i + max_lines]
                paged_blocks.append("\n".join(chunk))
            
            wrapped_pages.append("[PAGE]".join(paged_blocks))

        return "[PAGE]".join(wrapped_pages)
