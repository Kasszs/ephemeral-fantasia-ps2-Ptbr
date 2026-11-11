"""
Interactive PS2 Text Box Preview Canvas for Ephemeral Fantasia
Renders the exact 588x88 dialogue box with proportional font emulation,
guidelines, margin boundaries, and real-time overflow detection.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List
from core.font_engine import FontEngine, PageMetric, LineMetric


class DialogueBoxPreview(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.font_engine = FontEngine.get_instance()
        self.current_text: str = ""
        self.current_page_idx: int = 0
        self.pages: List[PageMetric] = []
        
        # Dimensões da janela original do PS2
        self.orig_box_w = 588
        self.orig_box_h = 88
        self.usable_w = 540
        self.max_lines = 3
        
        # Fator de escala visual para nitidez em monitores modernos
        self.scale = 1.25
        self.canvas_w = int(self.orig_box_w * self.scale)
        self.canvas_h = int(self.orig_box_h * self.scale)

        self._create_widgets()

    def _create_widgets(self):
        # 1. Barra de ferramentas e controle de páginas
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.pack(fill=tk.X, pady=(0, 4))
        
        self.page_label = ttk.Label(ctrl_frame, text="Página: 1 / 1", font=("Segoe UI", 9, "bold"))
        self.page_label.pack(side=tk.LEFT, padx=4)
        
        self.btn_prev = ttk.Button(ctrl_frame, text="◀ Anterior", width=10, command=self.prev_page)
        self.btn_prev.pack(side=tk.LEFT, padx=2)
        
        self.btn_next = ttk.Button(ctrl_frame, text="Próxima ▶", width=10, command=self.next_page)
        self.btn_next.pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(ctrl_frame, text="✔ Sem erros", font=("Segoe UI", 9), foreground="#2ecc71")
        self.status_label.pack(side=tk.RIGHT, padx=6)

        # 2. Canvas da Caixa de Diálogo
        canvas_container = tk.Frame(self, bg="#1a1c23", bd=2, relief=tk.SOLID)
        canvas_container.pack(fill=tk.NONE, expand=False)

        self.canvas = tk.Canvas(
            canvas_container,
            width=self.canvas_w,
            height=self.canvas_h,
            bg="#0c111d",
            highlightthickness=0
        )
        self.canvas.pack(padx=2, pady=2)

        # 3. Legenda e Métricas Rápidas
        metrics_frame = ttk.Frame(self)
        metrics_frame.pack(fill=tk.X, pady=(4, 0))
        
        self.metric_info = ttk.Label(
            metrics_frame,
            text="Limite Seguro: 540px de largura | Máximo: 3 linhas por caixa",
            font=("Segoe UI", 8),
            foreground="#888888"
        )
        self.metric_info.pack(side=tk.LEFT)

    def set_text(self, text: str):
        """Atualiza o texto exibido e redesenha a caixa em tempo real."""
        self.current_text = text
        self.pages = self.font_engine.analyze_text(text, max_w=self.usable_w, max_lines=self.max_lines)
        if self.current_page_idx >= len(self.pages):
            self.current_page_idx = max(0, len(self.pages) - 1)
        self.redraw()

    def prev_page(self):
        if self.current_page_idx > 0:
            self.current_page_idx -= 1
            self.redraw()

    def next_page(self):
        if self.current_page_idx < len(self.pages) - 1:
            self.current_page_idx += 1
            self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        s = self.scale

        if not self.pages:
            self.page_label.config(text="Página: 1 / 1")
            self.status_label.config(text="✔ Vazio", foreground="#888888")
            self._draw_frame()
            return

        total_pages = len(self.pages)
        self.page_label.config(text=f"Página: {self.current_page_idx + 1} / {total_pages}")
        self.btn_prev.config(state=tk.NORMAL if self.current_page_idx > 0 else tk.DISABLED)
        self.btn_next.config(state=tk.NORMAL if self.current_page_idx < total_pages - 1 else tk.DISABLED)

        page = self.pages[self.current_page_idx]

        # 1. Desenhar a moldura do PS2
        self._draw_frame()

        # 2. Desenhar Linha Guia de Limite Seguro (X = 24 + 540 = 564px)
        limit_x = (24 + self.usable_w) * s
        self.canvas.create_line(
            limit_x, 4 * s, limit_x, (self.orig_box_h - 4) * s,
            fill="#e74c3c", dash=(3, 3), width=1
        )
        self.canvas.create_text(
            limit_x - 4, 10 * s,
            text="LIMITE 540px", fill="#e74c3c", font=("Consolas", int(7 * s), "bold"), anchor="ne"
        )

        # 3. Desenhar Texto Proporcional (VWF) Linha por Linha
        start_x = 24 * s
        start_y = 14 * s
        line_pitch = 20 * s
        has_width_overflow = False
        has_line_overflow = len(page.lines) > self.max_lines

        max_measured_w = 0

        for line_idx, line in enumerate(page.lines):
            cur_y = start_y + line_idx * line_pitch
            cur_x = start_x
            prev_char = None
            line_w = line.width
            if line_w > max_measured_w:
                max_measured_w = line_w

            is_line_overflow = line.overflow
            if is_line_overflow:
                has_width_overflow = True

            # Destaque de fundo se ultrapassou a 3ª linha
            if line_idx >= self.max_lines:
                self.canvas.create_rectangle(
                    start_x - 4, cur_y - 2, (self.orig_box_w - 20) * s, cur_y + 18 * s,
                    fill="#3d1414", outline="#e74c3c", dash=(2, 2)
                )

            # Desenhar cada caractere
            line_text = line.text
            active_color = "#f1c40f"  # Amarelo clássico padrão
            i = 0
            n = len(line_text)
            while i < n:
                c = line_text[i]
                # Suporte ao código de cor nativo do PS2 \x8fc0xRRGGBBAA
                if c == "\x8f" and i + 13 <= n and line_text[i:i+5] == "\x8fc0x":
                    hex_rgb = line_text[i+5 : i+11]
                    active_color = f"#{hex_rgb}"
                    i += 13
                    continue

                # Pular marcações de controle antigas
                if c == "\x0c" and i + 1 < n:
                    i += 2
                    continue
                if line_text[i:i+7].startswith("[COLOR:"):
                    end_b = line_text.find("]", i)
                    if end_b != -1:
                        i = end_b + 1
                        continue

                cw, _ = self.font_engine.get_char_width(c, prev_char)
                scaled_cw = cw * s

                # Cor do texto: cor ativa do diálogo ou vermelho vivo se ultrapassar
                is_char_overflow = (cur_x + scaled_cw) > limit_x
                char_color = "#ff3333" if is_char_overflow else (active_color if line_idx < self.max_lines else "#e74c3c")

                # Sombra para legibilidade estilo PS2
                self.canvas.create_text(
                    cur_x + 1, cur_y + 1,
                    text=c, fill="#050810", font=("Consolas", int(11 * s), "bold"), anchor="nw"
                )
                self.canvas.create_text(
                    cur_x, cur_y,
                    text=c, fill=char_color, font=("Consolas", int(11 * s), "bold"), anchor="nw"
                )

                cur_x += scaled_cw
                prev_char = c
                i += 1

            # Tag de largura ao lado da linha
            width_color = "#e74c3c" if is_line_overflow else "#7f8c8d"
            self.canvas.create_text(
                (self.orig_box_w - 18) * s, cur_y + 2,
                text=f"{line_w}px", fill=width_color, font=("Consolas", int(7 * s)), anchor="ne"
            )

        # 4. Atualizar Mensagem de Status
        if has_width_overflow and has_line_overflow:
            self.status_label.config(
                text="⛔ ESTOURO DUPLO: Texto excede 540px E mais de 3 linhas!",
                foreground="#e74c3c"
            )
        elif has_width_overflow:
            excess = max_measured_w - self.usable_w
            self.status_label.config(
                text=f"⚠ ESTOURO HORIZONTAL: +{excess}px acima de 540px!",
                foreground="#e67e22"
            )
        elif has_line_overflow:
            self.status_label.config(
                text=f"⛔ ESTOURO VERTICAL: {len(page.lines)}/3 linhas! Insira [PAGE] para quebrar.",
                foreground="#e74c3c"
            )
        else:
            self.status_label.config(
                text=f"✔ DENTRO DOS LIMITES (Largura: {max_measured_w}/540px | Linhas: {len(page.lines)}/3)",
                foreground="#2ecc71"
            )

    def _draw_frame(self):
        """Desenha a moldura clássica de diálogo do PS2 com bordas ornamentadas."""
        s = self.scale
        w = self.orig_box_w * s
        h = self.orig_box_h * s

        # Fundo degradê/camadas
        self.canvas.create_rectangle(2, 2, w - 2, h - 2, fill="#0d1424", outline="#202b42", width=1)
        self.canvas.create_rectangle(6, 6, w - 6, h - 6, fill="#111a2e", outline="#34495e", width=1)

        # Borda externa dourada/bronze
        self.canvas.create_rectangle(8, 8, w - 8, h - 8, outline="#b89758", width=2)
        # Cantoneiras ornamentadas
        corner_len = 10 * s
        for cx, cy in [(8, 8), (w - 8, 8), (8, h - 8), (w - 8, h - 8)]:
            self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="#f1c40f", outline="#d4ac0d")
