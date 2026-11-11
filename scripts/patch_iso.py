import os
import sys
import json
import math

# Adicionar pasta raiz ao path para importar editor
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)

from editor.core.project import TranslationProject
from editor.core.iso import ISOManager

def main():
    print("=== Patch de Tradução de Ephemeral Fantasia PT-BR ===")
    if len(sys.argv) < 2:
        print("Uso: python patch_iso.py <caminho_da_iso>")
        print("Exemplo: python patch_iso.py \"D:\\PS2 ROM\\Ephemeral Fantasia (USA).iso\"")
        return

    iso_path = sys.argv[1]
    if not os.path.exists(iso_path):
        print(f"Erro: Arquivo ISO não encontrado em: {iso_path}")
        return

    db_path = os.path.join(repo_root, "database", "translation_database.json")
    if not os.path.exists(db_path):
        print(f"Erro: Banco de tradução não encontrado em: {db_path}")
        return

    print(f"Carregando banco de dados: {db_path}")
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)
    print(f"Total de strings no banco: {len(db):,}")

    # Extrair DATA6 da ISO
    print(f"Lendo DATA6_US.BIN da ISO em LBA 386669...")
    temp_data6 = os.path.join(repo_root, "temp_DATA6_US.BIN")
    with open(iso_path, "rb") as f_iso:
        f_iso.seek(386669 * 2048)
        data6_bytes = f_iso.read(57094144)
    with open(temp_data6, "wb") as f_out:
        f_out.write(data6_bytes)

    print("Carregando projeto e aplicando traduções...")
    proj = TranslationProject(temp_data6)
    proj.translations = db

    print("Recompilando scripts modificados...")
    updated, total = proj.compile_all(temp_data6)
    print(f"Scripts atualizados: {updated}/{total}")

    print("Injetando DATA6_US.BIN traduzido na ISO...")
    ISOManager.inject_data6(iso_path, temp_data6, create_backup=True)

    if os.path.exists(temp_data6):
        os.remove(temp_data6)

    print("=== PROCESSO CONCLUÍDO COM SUCESSO! ===")

if __name__ == '__main__':
    main()
