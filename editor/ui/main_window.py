"""
Main Application Window for Ephemeral Fantasia ROM Text Editor
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List
from core.project import TranslationProject
from core.iso import ISOManager
from ui.preview_canvas import DialogueBoxPreview
from ui.styles import apply_theme, DARK_BG, DARK_PANEL, DARK_INPUT, TEXT_COLOR, GOLD_COLOR, ACCENT_GREEN, ACCENT_RED


class MainWindow:
    def __init__(self, root: tk.Tk, default_data6_path: Optional[str] = None):
        self.root = root
        self.root.title("Ephemeral Fantasia - ROM Text Editor & Expander (PS2)")
        self.root.geometry("1280x850")
        self.root.minsize(1024, 720)

        apply_theme(self.root)

        self.project: Optional[TranslationProject] = None
        self.current_script_id: Optional[int] = None
        self.current_string_index: Optional[int] = None
        self.strings_cache: List[dict] = []

        self._build_ui()

        # Carregar jogo automaticamente se o caminho padrão for válido
        if default_data6_path and os.path.exists(default_data6_path):
            self.load_project(default_data6_path)

    def _build_ui(self):
        # 1. Barra de Ações Superior
        top_bar = ttk.Frame(self.root, padding=6)
        top_bar.pack(fill=tk.X, side=tk.TOP)

        ttk.Button(top_bar, text="📁 Abrir Jogo / BIN", command=self.on_open_project).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_bar, text="💾 Salvar Traduções (Ctrl+S)", command=self.on_save_translations).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_bar, text="⚡ Recompilar DATA6_US.BIN", style="Green.TButton", command=self.on_compile_bin).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_bar, text="💿 Injetar na ISO", style="Accent.TButton", command=self.on_inject_iso).pack(side=tk.LEFT, padx=6)

        ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Button(top_bar, text="📤 Exportar JSON", command=self.on_export_json).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_bar, text="📥 Importar JSON", command=self.on_import_json).pack(side=tk.LEFT, padx=3)

        self.lbl_proj_info = ttk.Label(top_bar, text="Nenhum arquivo aberto", font=("Segoe UI", 9, "italic"))
        self.lbl_proj_info.pack(side=tk.RIGHT, padx=8)

        # 2. Painel Dividido Principal (Esquerda: Scripts, Direita: Editor + Diálogos + Prévia)
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        # === Painel Esquerdo: Lista de Scripts ===
        left_frame = ttk.Frame(paned, width=320, padding=4)
        paned.add(left_frame, weight=1)

        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(filter_frame, text="🔍", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=2)
        self.entry_filter = ttk.Entry(filter_frame)
        self.entry_filter.pack(fill=tk.X, side=tk.LEFT, expand=True)
        self.entry_filter.bind("<KeyRelease>", self.on_filter_scripts)

        # Tabela de Scripts
        script_cols = ("id", "cena", "textos", "pct")
        self.tree_scripts = ttk.Treeview(left_frame, columns=script_cols, show="headings", selectmode="browse")
        self.tree_scripts.heading("id", text="ID")
        self.tree_scripts.heading("cena", text="Cena / Arquivo")
        self.tree_scripts.heading("textos", text="Textos")
        self.tree_scripts.heading("pct", text="%")

        self.tree_scripts.column("id", width=50, anchor="center")
        self.tree_scripts.column("cena", width=160, anchor="w")
        self.tree_scripts.column("textos", width=55, anchor="center")
        self.tree_scripts.column("pct", width=45, anchor="center")

        scroll_s = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree_scripts.yview)
        self.tree_scripts.configure(yscrollcommand=scroll_s.set)
        scroll_s.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_scripts.pack(fill=tk.BOTH, expand=True)
        self.tree_scripts.bind("<<TreeviewSelect>>", self.on_script_selected)

        # === Painel Direito: Grid de Diálogos + Editor + Prévia ===
        right_frame = ttk.Frame(paned, padding=4)
        paned.add(right_frame, weight=3)

        # Sub-paned vertical: Cima = Grid de Diálogos, Baixo = Edição + Prévia
        sub_paned = ttk.PanedWindow(right_frame, orient=tk.VERTICAL)
        sub_paned.pack(fill=tk.BOTH, expand=True)

        # 2.1 Grid de Diálogos
        top_grid_frame = ttk.Frame(sub_paned)
        sub_paned.add(top_grid_frame, weight=2)

        diag_cols = ("idx", "tipo", "orig", "trans", "status")
        self.tree_dialogues = ttk.Treeview(top_grid_frame, columns=diag_cols, show="headings", selectmode="browse")
        self.tree_dialogues.heading("idx", text="#")
        self.tree_dialogues.heading("tipo", text="Tipo")
        self.tree_dialogues.heading("orig", text="Texto Original (EN)")
        self.tree_dialogues.heading("trans", text="Texto Traduzido (PT-BR)")
        self.tree_dialogues.heading("status", text="Status")

        self.tree_dialogues.column("idx", width=40, anchor="center")
        self.tree_dialogues.column("tipo", width=70, anchor="center")
        self.tree_dialogues.column("orig", width=280, anchor="w")
        self.tree_dialogues.column("trans", width=280, anchor="w")
        self.tree_dialogues.column("status", width=90, anchor="center")

        scroll_d = ttk.Scrollbar(top_grid_frame, orient=tk.VERTICAL, command=self.tree_dialogues.yview)
        self.tree_dialogues.configure(yscrollcommand=scroll_d.set)
        scroll_d.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_dialogues.pack(fill=tk.BOTH, expand=True)
        self.tree_dialogues.bind("<<TreeviewSelect>>", self.on_dialogue_selected)

        # 2.2 Painel de Edição e Prévia
        bottom_edit_frame = ttk.Frame(sub_paned, padding=4)
        sub_paned.add(bottom_edit_frame, weight=3)

        # Divide lado a lado: Esquerda = Caixas de Texto, Direita = Canvas do PS2
        edit_split = ttk.Frame(bottom_edit_frame)
        edit_split.pack(fill=tk.BOTH, expand=True)

        left_text_frame = ttk.Frame(edit_split, width=460)
        left_text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        # Barra de status do orçamento do script
        self.lbl_script_budget = ttk.Label(
            left_text_frame,
            text="Orçamento do Script: Carregando...",
            font=("Segoe UI", 8)
        )
        self.lbl_script_budget.pack(anchor="w", pady=(0, 4))

        # Texto Original (Leitura)
        ttk.Label(left_text_frame, text="Texto Original:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.txt_original = tk.Text(
            left_text_frame, height=3, bg=DARK_INPUT, fg="#bdc3c7",
            insertbackground="white", relief=tk.SOLID, bd=1, font=("Consolas", 10)
        )
        self.txt_original.pack(fill=tk.X, pady=(2, 6))
        self.txt_original.config(state=tk.DISABLED)

        # Texto Traduzido (Edição)
        ttk.Label(left_text_frame, text="Tradução (PT-BR):", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.txt_translated = tk.Text(
            left_text_frame, height=4, bg="#1a1e29", fg="#f1c40f",
            insertbackground="white", relief=tk.SOLID, bd=1, font=("Consolas", 10, "bold")
        )
        self.txt_translated.pack(fill=tk.X, pady=(2, 6))
        self.txt_translated.bind("<KeyRelease>", self.on_text_modified)

        # Botões de Ação Rápida
        btn_box = ttk.Frame(left_text_frame)
        btn_box.pack(fill=tk.X, pady=2)

        ttk.Button(btn_box, text="+ \\n (Quebra)", width=12, command=lambda: self.insert_tag("\\n")).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_box, text="+ [PAGE]", width=12, command=lambda: self.insert_tag("[PAGE]")).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_box, text="⚡ Auto-Quebra", width=14, command=self.on_auto_wrap).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_box, text="↺ Restaurar", width=12, command=self.on_reset_string).pack(side=tk.LEFT, padx=2)

        # Lado Direito: Caixa de Prévia do PS2
        right_preview_frame = ttk.Frame(edit_split)
        right_preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)

        ttk.Label(right_preview_frame, text="Prévia da Caixa de Diálogo (PS2):", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 2))
        self.preview_canvas = DialogueBoxPreview(right_preview_frame)
        self.preview_canvas.pack(anchor="nw")

        # Atalhos de Teclado
        self.root.bind("<Control-s>", lambda e: self.on_save_translations())
        self.root.bind("<Alt-Down>", lambda e: self.select_next_dialogue())
        self.root.bind("<Alt-Up>", lambda e: self.select_prev_dialogue())
        self.txt_translated.bind("<Control-a>", self.select_all_text)
        self.txt_translated.bind("<Control-A>", self.select_all_text)

    def select_all_text(self, event=None):
        self.txt_translated.tag_add("sel", "1.0", "end")
        return "break"

    def select_next_dialogue(self):
        cur = self.tree_dialogues.selection()
        if not cur:
            return
        nxt = self.tree_dialogues.next(cur[0])
        if nxt:
            self.tree_dialogues.selection_set(nxt)
            self.tree_dialogues.see(nxt)
            self.on_dialogue_selected()

    def select_prev_dialogue(self):
        cur = self.tree_dialogues.selection()
        if not cur:
            return
        prv = self.tree_dialogues.prev(cur[0])
        if prv:
            self.tree_dialogues.selection_set(prv)
            self.tree_dialogues.see(prv)
            self.on_dialogue_selected()

    def load_project(self, data6_path: str):
        try:
            self.project = TranslationProject(data6_path)
            scripts = self.project.get_script_list()
            total_strings = sum(s["total"] for s in scripts)
            self.lbl_proj_info.config(
                text=f"{len(scripts)} scripts com texto ({total_strings} diálogos) | {os.path.basename(data6_path)}"
            )
            self.populate_script_tree(scripts)
            # Selecionar o script 556 (Prólogo) por padrão se existir
            found = False
            for item in self.tree_scripts.get_children():
                val = self.tree_scripts.item(item, "values")
                if val and int(val[0]) == 556:
                    self.tree_scripts.selection_set(item)
                    self.tree_scripts.see(item)
                    found = True
                    break
            if not found and self.tree_scripts.get_children():
                first = self.tree_scripts.get_children()[0]
                self.tree_scripts.selection_set(first)
            self.on_script_selected()
        except Exception as e:
            messagebox.showerror("Erro ao Abrir Jogo", f"Falha ao carregar arquivo RHZ:\n{str(e)}")

    def populate_script_tree(self, scripts: List[dict]):
        self.tree_scripts.delete(*self.tree_scripts.get_children())
        for s in scripts:
            self.tree_scripts.insert(
                "", tk.END,
                values=(s["script_id"], s["label"], s["total"], f"{s['percent']}%")
            )

    def on_filter_scripts(self, event=None):
        if not self.project:
            return
        query = self.entry_filter.get().strip().lower()
        scripts = self.project.get_script_list()
        if query:
            scripts = [s for s in scripts if query in s["label"].lower() or query in str(s["script_id"])]
        self.populate_script_tree(scripts)

    def on_script_selected(self, event=None):
        selected = self.tree_scripts.selection()
        if not selected or not self.project:
            return
        vals = self.tree_scripts.item(selected[0], "values")
        script_id = int(vals[0])
        self.current_script_id = script_id

        self.tree_dialogues.delete(*self.tree_dialogues.get_children())
        self.strings_cache = self.project.get_script_strings(script_id)

        for s in self.strings_cache:
            orig_preview = s["orig_text"].replace("\n", " \\n ").replace("\x1a", " [PAGE] ")[:60]
            trans_preview = s["trans_text"].replace("\n", " \\n ").replace("\x1a", " [PAGE] ")[:60]
            self.tree_dialogues.insert(
                "", tk.END,
                values=(s["index"], s["category"], orig_preview, trans_preview, s["status"])
            )

        if self.tree_dialogues.get_children():
            first_diag = self.tree_dialogues.get_children()[0]
            self.tree_dialogues.selection_set(first_diag)
            self.on_dialogue_selected()

        self.update_budget_display()

    def update_budget_display(self):
        if not self.project or self.current_script_id is None:
            self.lbl_script_budget.config(text="")
            return
        
        info = self.project.get_script_budget(self.current_script_id)
        if info["overflow"]:
            self.lbl_script_budget.config(
                text=f"⛔ Orçamento do Script: {info['current']} / {info['max_safe']} bytes (+{info['excess']}b ACIMA DO LIMITE)",
                foreground=ACCENT_RED
            )
        else:
            self.lbl_script_budget.config(
                text=f"✔ Orçamento do Script: {info['current']} / {info['max_safe']} bytes (Margem: +{info['remaining']} bytes livres)",
                foreground=ACCENT_GREEN
            )

    def on_dialogue_selected(self, event=None):
        selected = self.tree_dialogues.selection()
        if not selected:
            return
        vals = self.tree_dialogues.item(selected[0], "values")
        str_idx = int(vals[0])
        self.current_string_index = str_idx

        s_data = next((s for s in self.strings_cache if s["index"] == str_idx), None)
        if not s_data:
            return

        # Carregar texto original
        self.txt_original.config(state=tk.NORMAL)
        self.txt_original.delete("1.0", tk.END)
        self.txt_original.insert("1.0", s_data["orig_text"])
        self.txt_original.config(state=tk.DISABLED)

        # Carregar texto traduzido
        self.txt_translated.delete("1.0", tk.END)
        self.txt_translated.insert("1.0", s_data["trans_text"])

        # Atualizar prévia
        self.preview_canvas.set_text(s_data["trans_text"])

    def on_text_modified(self, event=None):
        if self.current_script_id is None or self.current_string_index is None:
            return
        new_text = self.txt_translated.get("1.0", tk.END).rstrip("\r\n")
        self.preview_canvas.set_text(new_text)

        # Atualizar no projeto em memória
        self.project.update_translation(self.current_script_id, self.current_string_index, new_text)

        # Atualizar item na Treeview
        selected = self.tree_dialogues.selection()
        if selected:
            preview_str = new_text.replace("\n", " \\n ").replace("\x1a", " [PAGE] ")[:60]
            cur_vals = list(self.tree_dialogues.item(selected[0], "values"))
            cur_vals[3] = preview_str
            cur_vals[4] = "Traduzido" if new_text != cur_vals[2] else "Original"
            self.tree_dialogues.item(selected[0], values=cur_vals)

        self.update_budget_display()

    def insert_tag(self, tag: str):
        self.txt_translated.insert(tk.INSERT, tag)
        self.on_text_modified()

    def on_auto_wrap(self):
        text = self.txt_translated.get("1.0", tk.END).rstrip("\r\n")
        wrapped = self.preview_canvas.font_engine.auto_wrap(text)
        self.txt_translated.delete("1.0", tk.END)
        self.txt_translated.insert("1.0", wrapped)
        self.on_text_modified()

    def on_reset_string(self):
        if self.current_string_index is None:
            return
        s_data = next((s for s in self.strings_cache if s["index"] == self.current_string_index), None)
        if s_data:
            self.txt_translated.delete("1.0", tk.END)
            self.txt_translated.insert("1.0", s_data["orig_text"])
            self.on_text_modified()

    def on_open_project(self):
        file_path = filedialog.askopenfilename(
            title="Selecione DATA6_US.BIN",
            filetypes=[("Arquivos RHZ DATA*.BIN", "*.BIN"), ("Todos os Arquivos", "*.*")]
        )
        if file_path:
            self.load_project(file_path)

    def on_save_translations(self):
        if not self.project:
            return
        try:
            self.project.save_translations()
            messagebox.showinfo("Sucesso", "Banco de traduções salvo com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", str(e))

    def on_compile_bin(self):
        if not self.project:
            messagebox.showwarning("Aviso", "Abra um arquivo DATA6_US.BIN primeiro.")
            return
        
        ans = messagebox.askyesno(
            "Confirmar Recompilação",
            "Deseja recompilar o arquivo DATA6_US.BIN com todas as traduções salvas?\n\n"
            "Um backup (.bak) será criado automaticamente."
        )
        if not ans:
            return
        
        try:
            updated, total = self.project.compile_all()
            messagebox.showinfo(
                "Recompilação Concluída",
                f"Sucesso! {updated} de {total} scripts foram atualizados e injetados no arquivo BIN com setores alinhados!"
            )
        except Exception as e:
            messagebox.showerror("Erro na Recompilação", f"Falha na compilação:\n{str(e)}")

    def on_inject_iso(self):
        if not self.project:
            messagebox.showwarning("Aviso", "Abra um arquivo DATA6_US.BIN primeiro.")
            return

        # Localizar automaticamente a ISO no diretório do projeto
        workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(self.project.data6_path)))
        default_iso = os.path.join(workspace_dir, "Ephemeral Fantasia (USA).iso")
        if not os.path.exists(default_iso):
            default_iso = filedialog.askopenfilename(
                title="Selecione a imagem ISO do jogo",
                filetypes=[("Imagens ISO do PS2", "*.iso"), ("Todos os Arquivos", "*.*")]
            )
            if not default_iso:
                return

        ans = messagebox.askyesno(
            "Confirmar Injeção na ISO",
            f"Deseja injetar as traduções diretamente na imagem ISO?\n\n"
            f"Arquivo ISO: {os.path.basename(default_iso)}\n\n"
            "Uma cópia de segurança (.iso.bak) será gerada automaticamente caso ainda não exista."
        )
        if not ans:
            return

        try:
            # 1. Recompilar DATA6_US.BIN
            self.lbl_proj_info.config(text="Recompilando DATA6_US.BIN...")
            self.root.update()
            updated, total = self.project.compile_all()

            # 2. Injetar na ISO
            self.lbl_proj_info.config(text="Gravando dados na imagem ISO...")
            self.root.update()

            res = ISOManager.inject_data6(
                iso_path=default_iso,
                data6_bin_path=self.project.data6_path,
                create_backup=True
            )

            mb_written = res["size_bytes"] // (1024 * 1024)
            self.lbl_proj_info.config(text=f"✔ Injeção concluída na ISO ({mb_written} MB gravados no LBA {res['lba']})")
            messagebox.showinfo(
                "Injeção Concluída com Sucesso",
                f"As traduções foram injetadas com sucesso na ISO!\n\n"
                f"Arquivo: {os.path.basename(res['target_iso'])}\n"
                f"LBA Alocado: {res['lba']}\n"
                f"Tamanho Gravado: {res['size_bytes']} bytes ({res['sectors']} setores)\n"
                f"Modo: {res['mode']}\n\n"
                "A imagem ISO já está pronta para rodar diretamente no emulador PCSX2 ou console PS2!"
            )
        except Exception as e:
            self.lbl_proj_info.config(text="Erro ao injetar na ISO")
            messagebox.showerror("Erro na Injeção da ISO", f"Falha na injeção:\n{str(e)}")

    def on_export_json(self):
        if not self.project:
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Arquivos JSON", "*.json")],
            initialfile="ephemeral_fantasia_texts.json"
        )
        if save_path:
            cnt = self.project.export_json(save_path)
            messagebox.showinfo("Exportação Concluída", f"{cnt} textos exportados para:\n{save_path}")

    def on_import_json(self):
        if not self.project:
            return
        load_path = filedialog.askopenfilename(
            filetypes=[("Arquivos JSON", "*.json")]
        )
        if load_path:
            try:
                cnt = self.project.import_json(load_path)
                messagebox.showinfo("Importação Concluída", f"{cnt} traduções foram importadas com sucesso!")
                if self.current_script_id:
                    self.on_script_selected()
            except Exception as e:
                messagebox.showerror("Erro ao Importar", str(e))
