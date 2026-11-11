"""
Modern Dark Theme Styles for Ephemeral Fantasia ROM Editor
"""

import tkinter as tk
from tkinter import ttk


DARK_BG = "#161922"
DARK_PANEL = "#1f2330"
DARK_INPUT = "#272c3d"
DARK_BORDER = "#32384e"
TEXT_COLOR = "#ecf0f1"
TEXT_MUTED = "#8a93a5"
ACCENT_BLUE = "#3498db"
ACCENT_GREEN = "#2ecc71"
ACCENT_ORANGE = "#e67e22"
ACCENT_RED = "#e74c3c"
GOLD_COLOR = "#f1c40f"


def apply_theme(root: tk.Tk):
    root.configure(bg=DARK_BG)
    style = ttk.Style(root)
    
    # Try clam or default
    available = style.theme_names()
    if "clam" in available:
        style.theme_use("clam")

    # Frames
    style.configure("TFrame", background=DARK_BG)
    style.configure("Panel.TFrame", background=DARK_PANEL)

    # Labels
    style.configure("TLabel", background=DARK_BG, foreground=TEXT_COLOR, font=("Segoe UI", 9))
    style.configure("Muted.TLabel", background=DARK_BG, foreground=TEXT_MUTED, font=("Segoe UI", 8))
    style.configure("Title.TLabel", background=DARK_BG, foreground=GOLD_COLOR, font=("Segoe UI", 12, "bold"))
    style.configure("Header.TLabel", background=DARK_PANEL, foreground=TEXT_COLOR, font=("Segoe UI", 10, "bold"))

    # Buttons
    style.configure(
        "TButton",
        background="#2c3345",
        foreground=TEXT_COLOR,
        bordercolor=DARK_BORDER,
        darkcolor="#232938",
        lightcolor="#384157",
        font=("Segoe UI", 9)
    )
    style.map(
        "TButton",
        background=[("active", "#3d475f"), ("disabled", "#1c202b")],
        foreground=[("disabled", "#555555")]
    )

    style.configure("Accent.TButton", background=ACCENT_BLUE, foreground="#ffffff", font=("Segoe UI", 9, "bold"))
    style.map("Accent.TButton", background=[("active", "#2980b9")])

    style.configure("Green.TButton", background=ACCENT_GREEN, foreground="#000000", font=("Segoe UI", 9, "bold"))
    style.map("Green.TButton", background=[("active", "#27ae60")])

    # Treeview
    style.configure(
        "Treeview",
        background=DARK_PANEL,
        foreground=TEXT_COLOR,
        fieldbackground=DARK_PANEL,
        bordercolor=DARK_BORDER,
        font=("Segoe UI", 9)
    )
    style.map("Treeview", background=[("selected", "#2980b9")], foreground=[("selected", "#ffffff")])

    style.configure(
        "Treeview.Heading",
        background="#252a3a",
        foreground=GOLD_COLOR,
        font=("Segoe UI", 9, "bold"),
        bordercolor=DARK_BORDER
    )
    style.map("Treeview.Heading", background=[("active", "#31384d")])

    # Entry
    style.configure("TEntry", fieldbackground=DARK_INPUT, foreground=TEXT_COLOR, bordercolor=DARK_BORDER)
