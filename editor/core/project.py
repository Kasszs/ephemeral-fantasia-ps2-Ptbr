"""
Project Manager for Ephemeral Fantasia ROM Translation
Coordinates loading scripts, persisting translation entries, and compiling DATA6_US.BIN.
"""

import os
import json
import shutil
from typing import Dict, List, Optional, Tuple
from .rhz import RHZArchive, RHZEntry
from .scr import SCRScript, SCRString, TextExpansionLimitError
from .font_engine import FontEngine


class TranslationProject:
    def __init__(self, data6_path: str, project_dir: Optional[str] = None):
        self.data6_path = data6_path
        if project_dir is None:
            self.project_dir = os.path.dirname(os.path.abspath(data6_path))
        else:
            self.project_dir = project_dir

        self.trans_file = os.path.join(self.project_dir, "translation_database.json")
        self.archive: Optional[RHZArchive] = None
        self.scripts: Dict[int, SCRScript] = {}
        self.translations: Dict[str, str] = {}  # key: "script_id:string_index" -> translated_text

        self._load_translations()
        self._load_archive()

    def _load_translations(self) -> None:
        if os.path.exists(self.trans_file):
            try:
                with open(self.trans_file, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
            except Exception:
                self.translations = {}
        else:
            self.translations = {}

    def save_translations(self) -> None:
        with open(self.trans_file, "w", encoding="utf-8") as f:
            json.dump(self.translations, f, indent=2, ensure_ascii=False)

    def _load_archive(self) -> None:
        self.archive = RHZArchive.load(self.data6_path)
        for idx, entry in enumerate(self.archive.entries):
            # Parse only valid SCR scripts
            if len(entry.data) >= 44 and entry.data[:4] == b"SCR\x1a":
                scr = SCRScript(idx, entry.data)
                if scr.strings:
                    self.scripts[idx] = scr

    def get_script_list(self) -> List[dict]:
        """Retorna a lista de scripts que possuem textos com estatísticas de progresso."""
        results = []
        for s_id, scr in sorted(self.scripts.items()):
            total = len(scr.strings)
            translated = sum(1 for s in scr.strings if f"{s_id}:{s.index}" in self.translations)
            pct = int((translated / total) * 100) if total > 0 else 0
            
            # Identificar cena pelo primeiro asset ou nome
            scene_name = f"Script #{s_id:03d}"
            for s in scr.strings:
                if s.category == "asset":
                    scene_name += f" ({s.orig_text})"
                    break
            
            results.append({
                "script_id": s_id,
                "label": scene_name,
                "total": total,
                "translated": translated,
                "percent": pct
            })
        return results

    def get_script_strings(self, script_id: int) -> List[dict]:
        """Retorna todas as strings de um determinado script com suas traduções atuais."""
        scr = self.scripts.get(script_id)
        if not scr:
            return []
        
        fe = FontEngine.get_instance()
        items = []
        for s in scr.strings:
            key = f"{script_id}:{s.index}"
            current_trans = self.translations.get(key, s.orig_text)
            is_translated = key in self.translations
            
            # Análise de métricas
            metrics = fe.analyze_text(current_trans)
            has_error = any(p.line_overflow or p.width_overflow for p in metrics)

            items.append({
                "index": s.index,
                "category": s.category,
                "orig_text": s.orig_text,
                "trans_text": current_trans,
                "is_translated": is_translated,
                "pages_count": len(metrics),
                "has_overflow": has_error,
                "status": "Aviso de Estouro" if has_error else ("Traduzido" if is_translated else "Original")
            })
        return items

    def update_translation(self, script_id: int, string_idx: int, text: str) -> None:
        key = f"{script_id}:{string_idx}"
        self.translations[key] = text

    def get_script_budget(self, script_id: int) -> dict:
        scr = self.scripts.get(script_id)
        if not scr:
            return {"orig": 0, "current": 0, "max_safe": 0, "headroom": 0, "overflow": False}
        
        orig_len = scr.orig_text_end
        headroom = scr.get_max_safe_expansion()
        max_safe_len = orig_len + headroom
        
        # Calcular tamanho atual com traduções
        cur_len = 0
        for s in scr.strings:
            key = f"{script_id}:{s.index}"
            text = self.translations.get(key, s.orig_text)
            raw = text.replace("[PAGE]", "\x1a").replace("\\n", "\n")
            try:
                b = raw.encode("cp1252")
            except Exception:
                b = raw.encode("latin1", errors="replace")
            cur_len += len(b) + 1
        
        # Alinhamento 4 bytes
        cur_len = (cur_len + 3) & ~3
        overflow = cur_len > max_safe_len
        excess = max(0, cur_len - max_safe_len)
        remaining = max(0, max_safe_len - cur_len)

        return {
            "orig": orig_len,
            "current": cur_len,
            "max_safe": max_safe_len,
            "headroom": headroom,
            "remaining": remaining,
            "overflow": overflow,
            "excess": excess
        }

    def build_script(self, script_id: int) -> bytearray:
        """Reconstrói um script específico aplicando as traduções do banco de dados."""
        scr = self.scripts.get(script_id)
        if not scr:
            raise KeyError(f"Script {script_id} não encontrado.")
        
        script_trans = {}
        for s in scr.strings:
            key = f"{script_id}:{s.index}"
            if key in self.translations:
                script_trans[s.index] = self.translations[key]
        
        return scr.rebuild(script_trans)

    def compile_all(self, output_bin_path: Optional[str] = None) -> Tuple[int, int]:
        """
        Recompila todos os scripts com as traduções e gera um novo DATA6_US.BIN.
        Cria backup automático do original antes de sobrescrever.
        Retorna (scripts_atualizados, total_scripts).
        """
        if output_bin_path is None:
            output_bin_path = self.data6_path

        # Fazer backup do original caso não exista backup
        backup_path = self.data6_path + ".bak"
        if not os.path.exists(backup_path):
            shutil.copy2(self.data6_path, backup_path)

        updated_count = 0
        for s_id, scr in self.scripts.items():
            # Verificar se tem alguma tradução
            has_trans = any(f"{s_id}:{s.index}" in self.translations for s in scr.strings)
            if has_trans:
                new_data = self.build_script(s_id)
                self.archive.entries[s_id].data = new_data
                self.archive.entries[s_id].exact_size = len(new_data)
                updated_count += 1

        self.archive.save(output_bin_path)
        return updated_count, len(self.scripts)

    def export_json(self, export_path: str) -> int:
        """Exporta todas as strings do jogo para um único JSON facilitando tradução externa."""
        data = {}
        total = 0
        for s_id, scr in self.scripts.items():
            script_data = []
            for s in scr.strings:
                key = f"{s_id}:{s.index}"
                script_data.append({
                    "index": s.index,
                    "category": s.category,
                    "original": s.orig_text,
                    "translation": self.translations.get(key, "")
                })
                total += 1
            data[str(s_id)] = script_data
        
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return total

    def import_json(self, import_path: str) -> int:
        """Importa traduções de um arquivo JSON externo."""
        with open(import_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        imported = 0
        for s_id_str, list_items in data.items():
            s_id = int(s_id_str)
            for item in list_items:
                idx = item["index"]
                trans = item.get("translation", "").strip()
                if trans:
                    key = f"{s_id}:{idx}"
                    self.translations[key] = trans
                    imported += 1
        
        self.save_translations()
        return imported
