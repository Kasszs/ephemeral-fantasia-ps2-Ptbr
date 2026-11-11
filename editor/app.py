"""
Main Entry Point for Ephemeral Fantasia ROM Text Editor & Expander
"""

import os
import sys
import tkinter as tk

# Adicionar pasta raiz do editor ao path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from ui.main_window import MainWindow


def main():
    root = tk.Tk()
    
    # Tentar definir ícone da janela
    try:
        # Se houver um ícone ou usar o padrão do sistema
        pass
    except Exception:
        pass

    # Caminho padrão do arquivo de textos no workspace
    workspace_root = os.path.dirname(CURRENT_DIR)
    default_bin = os.path.join(workspace_root, "Ephemeral Fantasia (USA)", "DATA", "DATA6_US.BIN")
    
    if not os.path.exists(default_bin):
        default_bin = None

    app = MainWindow(root, default_data6_path=default_bin)
    root.mainloop()


if __name__ == "__main__":
    main()
