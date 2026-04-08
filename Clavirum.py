"""
Clavirum — Auto Key Presser  (v4)
==================================
  • icon.ico logo (falls back to programmatic) — pencere + görev çubuğu ikonu
  • Basılı Tutma Modu: tuşu belirli ms boyunca basılı tutar
  • Makro Modu: birden fazla tuş/metin sırası
  • INI tabanlı çok dil sistemi (TR / EN + ./lang/ klasörü)
  • Tüm metinler beyaz (başlık degradesi hariç)
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time
import json
import os
import sys
import io
import configparser
import webbrowser
import ctypes
from urllib.request import Request, urlopen
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
#  Dependency guard
# ─────────────────────────────────────────────────────────────────────────────

def _missing(pkg: str, cmd: str) -> None:
    root = tk.Tk(); root.withdraw()
    messagebox.showerror(
        "Missing Dependency — Clavirum",
        f"Package '{pkg}' is not installed.\n\nRun:  {cmd}\n\nThen restart Clavirum."
    )
    root.destroy(); sys.exit(1)

try:
    import keyboard
except ImportError:
    _missing("keyboard", "pip install keyboard")

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
except ImportError:
    _missing("Pillow", "pip install pillow")


# ─────────────────────────────────────────────────────────────────────────────
#  Theme
# ─────────────────────────────────────────────────────────────────────────────

CONFIG_FILE = "clavirum_config.json"

THEME_DARK = {
    "BG":        "#0A0B0F",
    "CARD":      "#13141A",
    "CARD2":     "#1A1B23",
    "BORDER":    "#FFFFFF",
    "INPUT_BG":  "#08090D",
    "WHITE":     "#FFFFFF",
    "MUTED":     "#4A4B60",
    "DIM":       "#1E1F2C",
    "ACCENT":    "#7C6FFF",
    "ACCENT2":   "#5548CC",
    "TEAL":      "#00D4AA",
    "AMBER":     "#FFB347",
    "RED":       "#FF4D6A",
    "GREEN":     "#39FF9A",
}

THEME_LIGHT = {
    "BG":        "#F3F4F6",
    "CARD":      "#FFFFFF",
    "CARD2":     "#E5E7EB",
    "BORDER":    "#000000",
    "INPUT_BG":  "#F9FAFB",
    "WHITE":     "#000000",
    "MUTED":     "#6B7280",
    "DIM":       "#D1D5DB",
    "ACCENT":    "#7C6FFF",
    "ACCENT2":   "#5548CC",
    "TEAL":      "#0D9488",
    "AMBER":     "#D97706",
    "RED":       "#E11D48",
    "GREEN":     "#059669",
}

THEME = THEME_DARK.copy()

PRESETS = [
    ("50 ms",  0.050),
    ("100 ms", 0.100),
    ("250 ms", 0.250),
    ("500 ms", 0.500),
    ("1 s",    1.000),
    ("5 s",    5.000),
]

FONT_LABEL = ("Segoe UI", 9,  "bold")
FONT_BIG   = ("Consolas", 22, "bold")


# ─────────────────────────────────────────────────────────────────────────────
#  Language system  (INI files in ./lang/)
# ─────────────────────────────────────────────────────────────────────────────

LANG_DIR = "lang"

DEFAULT_LANGS: dict = {
    "tr": {
        "presses":        "BASIMLAR",
        "elapsed":        "SURE",
        "status":         "DURUM",
        "idle":           "BEKLE",
        "active":         "AKTIF",
        "loop_interval":  "DONGU ARALIGI",
        "skip_zero":      "0 = atla",
        "hour":           "Saat",
        "min":            "Dak",
        "sec":            "San",
        "ms":             "Ms",
        "presets":        "HAZIR:",
        "repeat_limit":   "TEKRAR LIMITI",
        "tooltip_repeat": "0 = sonsuz dongu",
        "assigned_key":   "ATANAN TUS",
        "none":           "[ YOK ]",
        "scan_key":       "YENi TUS TARA",
        "clear_key":      "Temizle",
        "tooltip_clear":  "Atanan tusu sifirla",
        "start":          "BASLAT",
        "stop":           "DURDUR",
        "settings_icon":  "Ayarlar",
        "settings_title": "Ayarlar",
        "hotkey_active":  "Kısayol Aktif",
        "hotkey_label":   "Kısayol Tuşu:",
        "language":       "Dil / Language",
        "save_close":     "Kaydet ve Kapat",
        "more_soon":      "Daha fazla ayar yakin zamanda.",
        "listening":      "DINLENIYOR...",
        "press_key":      "[ TUSA BAS ]",
        "no_key_title":   "Tus Yok",
        "no_key_msg":     "Lutfen once bir tus atayin.",
        "bad_inp_title":  "Hatali Giris",
        "bad_inp_msg":    "Interval alanlari yalnizca sayi icermeli.",
        "open_github":    "  GitHub'da Ac",
        "developer":      "Yapimci",
        "about_desc":     "sectigi tusu belirledigin araliklarla otomatik basar.",
        "tooltip_dev":    "Yapimci",
        "tooltip_sets":   "Ayarlar",
        "made_by":        "Axtarres tarafından yapıldı",
        "target_app":     "SADECE BU UYGULAMADA",
        "tooltip_target": "Boş bırakılırsa her yerde çalışır.",
        "anywhere":       "[ Her Yerde (Boş) ]",
        # ── Yeni özellikler ──
        "mode_single":    "TEK TUŞ",
        "mode_macro":     "MAKRO",
        "hold_mode":      "Basılı Tut Modu",
        "hold_dur":       "Tutma Süresi",
        "macro_title":    "MAKRO SIRA",
        "add_key_btn":    "+ Tuş",
        "add_text_btn":   "+ Metin",
        "clear_macro":    "Temizle",
        "no_macro_title": "Makro Boş",
        "no_macro_msg":   "Makroya en az bir öğe ekleyin.",
        "macro_move_up":  "▲",
        "macro_move_dn":  "▼",
        "macro_remove":   "✕",
        "delay_label":    "ms sonra",
        "text_prompt":    "Yazılacak metni girin:",
        "text_title":     "Metin Ekle",
        "delay_prompt":   "Bu adım sonrası bekleme (ms):",
        "delay_title":    "Gecikme",
        "macro_hint":     "↑↓ sırala  ✕ sil  Tuş veya metin ekle",
        "theme":          "Tema",
        "dark":           "Koyu",
        "light":          "Beyaz",
    },
    "en": {
        "presses":        "PRESSES",
        "elapsed":        "ELAPSED",
        "status":         "STATUS",
        "idle":           "IDLE",
        "active":         "ACTIVE",
        "loop_interval":  "LOOP INTERVAL",
        "skip_zero":      "0 = skip",
        "hour":           "Hour",
        "min":            "Min",
        "sec":            "Sec",
        "ms":             "Ms",
        "presets":        "QUICK:",
        "repeat_limit":   "REPEAT LIMIT",
        "tooltip_repeat": "0 = infinite loop",
        "assigned_key":   "ASSIGNED KEY",
        "none":           "[ NONE ]",
        "scan_key":       "SCAN NEW KEY",
        "clear_key":      "Clear",
        "tooltip_clear":  "Clear assigned key",
        "start":          "START",
        "stop":           "STOP",
        "settings_icon":  "Settings",
        "settings_title": "Settings",
        "hotkey_active":  "Hotkey enabled",
        "hotkey_label":   "Hotkey:",
        "language":       "Dil / Language",
        "save_close":     "Save & Close",
        "more_soon":      "More settings coming soon.",
        "listening":      "LISTENING...",
        "press_key":      "[ PRESS A KEY ]",
        "no_key_title":   "No Key",
        "no_key_msg":     "Please assign a key first.",
        "bad_inp_title":  "Bad Input",
        "bad_inp_msg":    "Interval fields must contain numbers only.",
        "open_github":    "  Open on GitHub",
        "developer":      "Developer",
        "about_desc":     "automatically presses your chosen key at the set interval.",
        "tooltip_dev":    "Developer",
        "tooltip_sets":   "Settings",
        "made_by":        "Made by Axtarres",
        "target_app":     "TARGET APP ONLY",
        "tooltip_target": "Leave empty to work anywhere.",
        "anywhere":       "[ Anywhere (Empty) ]",
        # ── New features ──
        "mode_single":    "SINGLE KEY",
        "mode_macro":     "MACRO",
        "hold_mode":      "Hold Key Mode",
        "hold_dur":       "Hold Duration",
        "macro_title":    "MACRO SEQUENCE",
        "add_key_btn":    "+ Key",
        "add_text_btn":   "+ Text",
        "clear_macro":    "Clear",
        "no_macro_title": "Macro Empty",
        "no_macro_msg":   "Please add at least one item to the macro.",
        "macro_move_up":  "▲",
        "macro_move_dn":  "▼",
        "macro_remove":   "✕",
        "delay_label":    "ms after",
        "text_prompt":    "Enter text to type:",
        "text_title":     "Add Text",
        "delay_prompt":   "Delay after this step (ms):",
        "delay_title":    "Delay",
        "macro_hint":     "↑↓ reorder  ✕ delete  Add keys or text",
        "theme":          "Theme",
        "dark":           "Dark",
        "light":          "Light",
    },
    "de": {
        "presses":        "KLICKS",
        "elapsed":        "VERLAUFEN",
        "status":         "STATUS",
        "idle":           "INAKTIV",
        "active":         "AKTIV",
        "loop_interval":  "INTERVALL",
        "skip_zero":      "0 = überspringen",
        "hour":           "Std",
        "min":            "Min",
        "sec":            "Sek",
        "ms":             "Ms",
        "presets":        "SCHNELL:",
        "repeat_limit":   "WIEDERHOLUNGEN",
        "tooltip_repeat": "0 = Endlosschleife",
        "assigned_key":   "ZUG. TASTE",
        "none":           "[ KEINE ]",
        "scan_key":       "TASTE SCANNEN",
        "clear_key":      "Löschen",
        "tooltip_clear":  "Zugewiesene Taste löschen",
        "start":          "START",
        "stop":           "STOPP",
        "settings_icon":  "Einstell.",
        "settings_title": "Einstellungen",
        "hotkey_active":  "Hotkey aktiv",
        "hotkey_label":   "Hotkey:",
        "language":       "Sprache / Language",
        "save_close":     "Speichern & Schließen",
        "more_soon":      "Weitere Einstellungen folgen.",
        "listening":      "WARTEN...",
        "press_key":      "[ TASTE DRÜCKEN ]",
        "no_key_title":   "Keine Taste",
        "no_key_msg":     "Bitte weisen Sie zuerst eine Taste zu.",
        "bad_inp_title":  "Falsche Eingabe",
        "bad_inp_msg":    "Intervallfelder dürfen nur Zahlen enthalten.",
        "open_github":    "  Auf GitHub öffnen",
        "developer":      "Entwickler",
        "about_desc":     "drückt automatisch in dem festgelegten Intervall Ihre Taste.",
        "tooltip_dev":    "Entwickler",
        "tooltip_sets":   "Einstellungen",
        "made_by":        "Von Axtarres gemacht",
        "target_app":     "NUR ZIEL-APP",
        "tooltip_target": "Leer lassen, um überall zu funktionieren.",
        "anywhere":       "[ Überall (Leer) ]",
        "mode_single":    "EINZELTASTE",
        "mode_macro":     "MAKRO",
        "hold_mode":      "Taste Halten",
        "hold_dur":       "Haltezeit",
        "macro_title":    "MAKRO-SEQUENZ",
        "add_key_btn":    "+ Taste",
        "add_text_btn":   "+ Text",
        "clear_macro":    "Löschen",
        "no_macro_title": "Makro leer",
        "no_macro_msg":   "Bitte mindestens ein Element hinzufügen.",
        "macro_move_up":  "▲",
        "macro_move_dn":  "▼",
        "macro_remove":   "✕",
        "delay_label":    "ms danach",
        "text_prompt":    "Zu tippenden Text eingeben:",
        "text_title":     "Text hinzufügen",
        "delay_prompt":   "Verzögerung nach diesem Schritt (ms):",
        "delay_title":    "Verzögerung",
        "macro_hint":     "↑↓ sortieren  ✕ löschen",
    },
    "fr": {
        "presses":        "PRESSIONS",
        "elapsed":        "ÉCOULÉ",
        "status":         "STATUT",
        "idle":           "INACTIF",
        "active":         "ACTIF",
        "loop_interval":  "INTERVALLE",
        "skip_zero":      "0 = ignorer",
        "hour":           "Heure",
        "min":            "Min",
        "sec":            "Sec",
        "ms":             "Ms",
        "presets":        "RAPIDE :",
        "repeat_limit":   "LIMITE DE RÉP",
        "tooltip_repeat": "0 = boucle infinie",
        "assigned_key":   "TOUCHE ASSIGNÉE",
        "none":           "[ AUCUN ]",
        "scan_key":       "LIRE UNE TOUCHE",
        "clear_key":      "Effacer",
        "tooltip_clear":  "Effacer la touche assignée",
        "start":          "DÉBUT",
        "stop":           "ARRÊT",
        "settings_icon":  "Paramètres",
        "settings_title": "Paramètres",
        "hotkey_active":  "Raccourci défini",
        "hotkey_label":   "Raccourci :",
        "language":       "Langue / Language",
        "save_close":     "Enreg. & Fermer",
        "more_soon":      "D'autres paramètres bientôt.",
        "listening":      "ÉCOUTE...",
        "press_key":      "[ APPUYEZ SUR LA TOUCHE ]",
        "no_key_title":   "Pas de touche",
        "no_key_msg":     "Veuillez d'abord assigner une touche.",
        "bad_inp_title":  "Entrée Invalide",
        "bad_inp_msg":    "Les champs doivent contenir uniquement des chiffres.",
        "open_github":    "  Ouvrir sur GitHub",
        "developer":      "Développeur",
        "about_desc":     "appuie automatiquement sur la touche choisie.",
        "tooltip_dev":    "Développeur",
        "tooltip_sets":   "Paramètres",
        "made_by":        "Fait par Axtarres",
        "target_app":     "APPLICATION CIBLE",
        "tooltip_target": "Laissez vide pour fonctionner partout.",
        "anywhere":       "[ Partout (Vide) ]",
        "mode_single":    "TOUCHE UNIQUE",
        "mode_macro":     "MACRO",
        "hold_mode":      "Maintenir Touche",
        "hold_dur":       "Durée maintien",
        "macro_title":    "SÉQUENCE MACRO",
        "add_key_btn":    "+ Touche",
        "add_text_btn":   "+ Texte",
        "clear_macro":    "Effacer",
        "no_macro_title": "Macro vide",
        "no_macro_msg":   "Ajoutez au moins un élément.",
        "macro_move_up":  "▲",
        "macro_move_dn":  "▼",
        "macro_remove":   "✕",
        "delay_label":    "ms après",
        "text_prompt":    "Entrez le texte à taper :",
        "text_title":     "Ajouter Texte",
        "delay_prompt":   "Délai après cette étape (ms) :",
        "delay_title":    "Délai",
        "macro_hint":     "↑↓ réordonner  ✕ supprimer",
    },
    "es": {
        "presses":        "PULSACIONES",
        "elapsed":        "TIEMPO",
        "status":         "ESTADO",
        "idle":           "INACTIVO",
        "active":         "ACTIVO",
        "loop_interval":  "INTERVALO",
        "skip_zero":      "0 = saltar",
        "hour":           "Hora",
        "min":            "Min",
        "sec":            "Seg",
        "ms":             "Ms",
        "presets":        "RÁPIDO:",
        "repeat_limit":   "LÍMITE DE REP.",
        "tooltip_repeat": "0 = bucle infinito",
        "assigned_key":   "TECLA ASIGNADA",
        "none":           "[ NINGUNO ]",
        "scan_key":       "ESCANEAR TECLA",
        "clear_key":      "Borrar",
        "tooltip_clear":  "Borrar tecla asignada",
        "start":          "INICIO",
        "stop":           "DETENER",
        "settings_icon":  "Ajustes",
        "settings_title": "Ajustes",
        "hotkey_active":  "Atajo activado",
        "hotkey_label":   "Atajo:",
        "language":       "Idioma / Language",
        "save_close":     "Guardar y Cerrar",
        "more_soon":      "Más ajustes próximamente.",
        "listening":      "ESCUCHANDO...",
        "press_key":      "[ PRESIONE UNA TECLA ]",
        "no_key_title":   "Sin Tecla",
        "no_key_msg":     "Por favor asigne una tecla primero.",
        "bad_inp_title":  "Entrada incorrecta",
        "bad_inp_msg":    "Los campos deben contener solo números.",
        "open_github":    "  Abrir en GitHub",
        "developer":      "Desarrollador",
        "about_desc":     "presiona automáticamente la tecla elegida.",
        "tooltip_dev":    "Desarrollador",
        "tooltip_sets":   "Ajustes",
        "made_by":        "Hecho por Axtarres",
        "target_app":     "SOLO APLICACIÓN OBJETIVO",
        "tooltip_target": "Deje vacío para funcionar en cualquier lugar.",
        "anywhere":       "[ Cualquier lugar (Vacío) ]",
        "mode_single":    "TECLA ÚNICA",
        "mode_macro":     "MACRO",
        "hold_mode":      "Mantener Tecla",
        "hold_dur":       "Duración mantener",
        "macro_title":    "SECUENCIA MACRO",
        "add_key_btn":    "+ Tecla",
        "add_text_btn":   "+ Texto",
        "clear_macro":    "Limpiar",
        "no_macro_title": "Macro Vacío",
        "no_macro_msg":   "Agregue al menos un elemento.",
        "macro_move_up":  "▲",
        "macro_move_dn":  "▼",
        "macro_remove":   "✕",
        "delay_label":    "ms después",
        "text_prompt":    "Ingrese el texto a escribir:",
        "text_title":     "Agregar Texto",
        "delay_prompt":   "Retraso tras este paso (ms):",
        "delay_title":    "Retraso",
        "macro_hint":     "↑↓ reordenar  ✕ eliminar",
    },
    "it": {
        "presses":        "PRESSIONI",
        "elapsed":        "TRASCORSO",
        "status":         "STATO",
        "idle":           "INATTIVO",
        "active":         "ATTIVO",
        "loop_interval":  "INTERVALLO",
        "skip_zero":      "0 = ignora",
        "hour":           "Ora",
        "min":            "Min",
        "sec":            "Sec",
        "ms":             "Ms",
        "presets":        "RAPIDO:",
        "repeat_limit":   "LIMITE RIPET.",
        "tooltip_repeat": "0 = ciclo infinito",
        "assigned_key":   "TASTO ASSEGNATO",
        "none":           "[ NESSUNO ]",
        "scan_key":       "SCANSIONA TASTO",
        "clear_key":      "Cancella",
        "tooltip_clear":  "Cancella tasto assegnato",
        "start":          "AVVIA",
        "stop":           "FERMA",
        "settings_icon":  "Imp.",
        "settings_title": "Impostazioni",
        "hotkey_active":  "Hotkey attiva",
        "hotkey_label":   "Hotkey:",
        "language":       "Lingua / Language",
        "save_close":     "Salva e Chiudi",
        "more_soon":      "Altre impostazioni in arrivo.",
        "listening":      "IN ASCOLTO...",
        "press_key":      "[ PREMI UN TASTO ]",
        "no_key_title":   "Nessun Tasto",
        "no_key_msg":     "Assegna prima un tasto.",
        "bad_inp_title":  "Input Errato",
        "bad_inp_msg":    "I campi devono contenere solo numeri.",
        "open_github":    "  Apri su GitHub",
        "developer":      "Sviluppatore",
        "about_desc":     "preme automaticamente il tasto scelto.",
        "tooltip_dev":    "Sviluppatore",
        "tooltip_sets":   "Impostazioni",
        "made_by":        "Creato da Axtarres",
        "target_app":     "SOLO APP DESTINAZIONE",
        "tooltip_target": "Lascia vuoto per funzionare ovunque.",
        "anywhere":       "[ Ovunque (Vuoto) ]",
        "mode_single":    "TASTO SINGOLO",
        "mode_macro":     "MACRO",
        "hold_mode":      "Tieni Premuto",
        "hold_dur":       "Durata pressione",
        "macro_title":    "SEQUENZA MACRO",
        "add_key_btn":    "+ Tasto",
        "add_text_btn":   "+ Testo",
        "clear_macro":    "Cancella",
        "no_macro_title": "Macro Vuoto",
        "no_macro_msg":   "Aggiungi almeno un elemento.",
        "macro_move_up":  "▲",
        "macro_move_dn":  "▼",
        "macro_remove":   "✕",
        "delay_label":    "ms dopo",
        "text_prompt":    "Inserisci il testo da digitare:",
        "text_title":     "Aggiungi Testo",
        "delay_prompt":   "Ritardo dopo questo passo (ms):",
        "delay_title":    "Ritardo",
        "macro_hint":     "↑↓ riordina  ✕ elimina",
    },
    "ru": {
        "presses":        "НАЖАТИЙ",
        "elapsed":        "ВРЕМЯ",
        "status":         "СТАТУС",
        "idle":           "ОЖИДАНИЕ",
        "active":         "АКТИВНО",
        "loop_interval":  "ИНТЕРВАЛ",
        "skip_zero":      "0 = пропуск",
        "hour":           "Час",
        "min":            "Мин",
        "sec":            "Сек",
        "ms":             "Мс",
        "presets":        "БЫСТРО:",
        "repeat_limit":   "ЛИМИТ",
        "tooltip_repeat": "0 = бесконечно",
        "assigned_key":   "КЛАВИША",
        "none":           "[ НЕТ ]",
        "scan_key":       "СКАН КЛАВИШИ",
        "clear_key":      "Очистить",
        "tooltip_clear":  "Очистить клавишу",
        "start":          "СТАРТ",
        "stop":           "СТОП",
        "settings_icon":  "Настройки",
        "settings_title": "Настройки",
        "hotkey_active":  "Хоткей включен",
        "hotkey_label":   "Хоткей:",
        "language":       "Язык / Language",
        "save_close":     "Сохранить и Выйти",
        "more_soon":      "Скоро будет больше настроек.",
        "listening":      "СЛУШАЮ...",
        "press_key":      "[ НАЖМИТЕ ]",
        "no_key_title":   "Нет клавиши",
        "no_key_msg":     "Сначала назначьте клавишу.",
        "bad_inp_title":  "Ошибка ввода",
        "bad_inp_msg":    "Поля интервала только цифры.",
        "open_github":    "  Открыть GitHub",
        "developer":      "Разработчик",
        "about_desc":     "автонажатие клавиши с заданным интервалом.",
        "tooltip_dev":    "Разработчик",
        "tooltip_sets":   "Настройки",
        "made_by":        "Сделано Axtarres",
        "target_app":     "ТОЛЬКО В ПРИЛОЖЕНИИ",
        "tooltip_target": "Оставьте пустым для работы везде.",
        "anywhere":       "[ Везде (Пусто) ]",
        "mode_single":    "ОДНА КЛАВИША",
        "mode_macro":     "МАКРОС",
        "hold_mode":      "Удерживать клавишу",
        "hold_dur":       "Время удержания",
        "macro_title":    "ПОСЛЕДОВАТЕЛЬНОСТЬ",
        "add_key_btn":    "+ Клавиша",
        "add_text_btn":   "+ Текст",
        "clear_macro":    "Очистить",
        "no_macro_title": "Макрос пуст",
        "no_macro_msg":   "Добавьте хотя бы один элемент.",
        "macro_move_up":  "▲",
        "macro_move_dn":  "▼",
        "macro_remove":   "✕",
        "delay_label":    "мс после",
        "text_prompt":    "Введите текст для набора:",
        "text_title":     "Добавить текст",
        "delay_prompt":   "Задержка после шага (мс):",
        "delay_title":    "Задержка",
        "macro_hint":     "↑↓ порядок  ✕ удалить",
    },
}


def ensure_lang_files() -> None:
    os.makedirs(LANG_DIR, exist_ok=True)
    for code, strings in DEFAULT_LANGS.items():
        path = os.path.join(LANG_DIR, f"{code}.ini")
        cfg = configparser.ConfigParser()
        if os.path.exists(path):
            cfg.read(path, encoding="utf-8")
        if "strings" not in cfg:
            cfg["strings"] = {}
        for k, v in strings.items():
            cfg["strings"][k] = v
        with open(path, "w", encoding="utf-8") as f:
            cfg.write(f)


def load_lang(code: str) -> dict:
    base = dict(DEFAULT_LANGS.get(code, DEFAULT_LANGS["en"]))
    path = os.path.join(LANG_DIR, f"{code}.ini")
    if os.path.exists(path):
        cfg = configparser.ConfigParser()
        cfg.read(path, encoding="utf-8")
        if "strings" in cfg:
            default_keys = set(DEFAULT_LANGS.get(code, {}).keys())
            for k, v in cfg["strings"].items():
                if k not in default_keys:
                    base[k] = v
    return base


def available_langs() -> list:
    if not os.path.exists(LANG_DIR):
        return list(DEFAULT_LANGS.keys())
    codes = [f[:-4] for f in os.listdir(LANG_DIR) if f.endswith(".ini")]
    return codes or list(DEFAULT_LANGS.keys())


# ─────────────────────────────────────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    defaults = {
        "hotkey_enabled": True,
        "start_hotkey":   "f9",
        "hour":           "0",
        "min":            "0",
        "sec":            "0",
        "ms":             "100",
        "repeat_limit":   "0",
        "last_key":       "",
        "language":       "en",
        "theme":          "dark",
        "mode":           "single",
        "hold_mode":      False,
        "hold_ms":        "50",
        "macro_sequence": [],
    }
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            defaults.update(json.load(f))
    except Exception:
        pass
    defaults["last_key"] = ""
    return defaults


def save_config(cfg: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  Tooltip
# ─────────────────────────────────────────────────────────────────────────────

class Tooltip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self._win: Optional[tk.Toplevel] = None
        self._text = text
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None) -> None:
        if self._win:
            return
        x = event.widget.winfo_rootx() + 20
        y = event.widget.winfo_rooty() + 24
        self._win = tk.Toplevel()
        self._win.wm_overrideredirect(True)
        self._win.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self._win, text=self._text,
            font=("Segoe UI", 8), bg=THEME["CARD2"], fg=THEME["WHITE"],
            padx=8, pady=4, relief="flat",
            highlightbackground=THEME["BORDER"], highlightthickness=1
        ).pack()

    def _hide(self, event=None) -> None:
        if self._win:
            self._win.destroy()
            self._win = None


# ─────────────────────────────────────────────────────────────────────────────
#  Application
# ─────────────────────────────────────────────────────────────────────────────

class Clavirum:

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.cfg  = load_config()

        ensure_lang_files()
        self.lang_code = self.cfg.get("language", "en")
        self.S         = load_lang(self.lang_code)

        self.current_theme = self.cfg.get("theme", "dark")
        self._apply_theme_colors(self.current_theme)

        self.root.title("Clavirum")
        self.root.resizable(False, False)
        self.root.configure(bg=THEME["BG"])
        self._center_window(560, 760)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Temel durum ──
        self.var_hotkey_enabled = tk.BooleanVar(value=bool(self.cfg["hotkey_enabled"]))
        self.start_hotkey  = self.cfg.get("start_hotkey", "f9")
        self.hotkey_id:    Optional[object] = None
        self.target_key:   Optional[str]    = None
        self.is_running    = False
        self.is_capturing  = False
        self.press_count   = 0
        self.start_time:   Optional[float]  = None

        # ── Yeni: Mod, Basılı Tut, Makro ──
        self.mode_var      = tk.StringVar(value=self.cfg.get("mode", "single"))
        self.var_hold_mode = tk.BooleanVar(value=bool(self.cfg.get("hold_mode", False)))
        self.var_hold_ms   = tk.StringVar(value=str(self.cfg.get("hold_ms", "50")))
        self.macro_sequence: list = list(self.cfg.get("macro_sequence", []))
        # macro_sequence öğe formatı: {"type": "key"/"text", "value": "...", "delay_ms": 50}

        # ── Görsel referanslar ──
        self._logo_photo:  Optional[ImageTk.PhotoImage] = None
        self._title_photo: Optional[ImageTk.PhotoImage] = None
        self._dev_photo:   Optional[ImageTk.PhotoImage] = None
        self._icon_photos: list = []

        self.github_user = "Axtarres"
        self._gh_profile: dict = {}

        self._build()
        self._set_app_icon()
        self._bind_hotkey()
        self._tick()
        self._fetch_gh_async()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _apply_theme_colors(self, code: str) -> None:
        if code == "light":
            THEME.update(THEME_LIGHT)
        else:
            THEME.update(THEME_DARK)

    def _center_window(self, w: int, h: int) -> None:
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _center_child(self, win: tk.Toplevel, w: int, h: int) -> None:
        px = self.root.winfo_x() + (self.root.winfo_width()  - w) // 2
        py = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        win.geometry(f"{w}x{h}+{px}+{py}")
        self._apply_icon_to(win)

    def _apply_icon_to(self, win) -> None:
        """Ana pencere ikonunu verilen pencereye de uygular."""
        # .ico dosyası varsa iconbitmap en güvenilirdir
        for name in ("icon.ico", "imageico.ico"):
            if os.path.exists(name):
                try:
                    win.iconbitmap(name)
                    return
                except Exception:
                    pass
        # Pillow ile üretilen PhotoImage'ları kullan (zaten _icon_photos'ta saklı)
        if hasattr(self, "_icon_photos") and self._icon_photos:
            try:
                win.iconphoto(False, *self._icon_photos)
            except Exception:
                pass

    def _ask_string(self, title: str, prompt: str, initialvalue: str = "") -> Optional[str]:
        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=THEME["BG"])
        win.resizable(False, False)
        self._center_child(win, 340, 160)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text=prompt, font=("Segoe UI", 10, "bold"),
                 fg=THEME["WHITE"], bg=THEME["BG"]).pack(pady=(20, 8))

        var = tk.StringVar(value=initialvalue)
        ent = tk.Entry(win, textvariable=var, font=("Consolas", 12, "bold"),
                       bg=THEME["INPUT_BG"], fg=THEME["WHITE"],
                       insertbackground=THEME["ACCENT"], relief="flat", justify="center",
                       highlightbackground=THEME["BORDER"], highlightthickness=1)
        ent.pack(padx=24, fill="x", ipady=4)
        ent.focus_set()
        if initialvalue:
            ent.select_range(0, tk.END)

        ent.bind("<FocusIn>", lambda e: ent.config(highlightbackground=THEME["ACCENT"]))
        ent.bind("<FocusOut>", lambda e: ent.config(highlightbackground=THEME["BORDER"]))

        res = [None]
        def _ok(*_):
            res[0] = var.get()
            win.destroy()
        def _cancel(*_):
            win.destroy()

        ent.bind("<Return>", _ok)
        ent.bind("<Escape>", _cancel)
        win.protocol("WM_DELETE_WINDOW", _cancel)

        fr = tk.Frame(win, bg=THEME["BG"])
        fr.pack(pady=(15, 0))
        self._btn(fr, "\u2713", _ok, font=("Segoe UI", 9, "bold"), fg=THEME["TEAL"], accent=THEME["TEAL"], padx=16, pady=4).pack(side="left", padx=6)
        self._btn(fr, "\u2715", _cancel, font=("Segoe UI", 9, "bold"), fg=THEME["RED"], accent=THEME["RED"], padx=16, pady=4).pack(side="left", padx=6)

        self.root.wait_window(win)
        return res[0]

    def _on_close(self) -> None:
        self.is_running = False
        try:
            if self.hotkey_id is not None:
                keyboard.remove_hotkey(self.hotkey_id)
        except Exception:
            pass
        self._save_config()
        self.root.destroy()

    def _save_config(self) -> None:
        save_config({
            "hotkey_enabled": self.var_hotkey_enabled.get(),
            "start_hotkey":   self.start_hotkey,
            "hour":           self.entries["hour"].get(),
            "min":            self.entries["min"].get(),
            "sec":            self.entries["sec"].get(),
            "ms":             self.entries["ms"].get(),
            "repeat_limit":   self.entry_repeat.get(),
            "last_key":       self.target_key or "",
            "language":       self.lang_code,
            "theme":          self.current_theme,
            "mode":           self.mode_var.get(),
            "hold_mode":      self.var_hold_mode.get(),
            "hold_ms":        self.var_hold_ms.get(),
            "macro_sequence": self.macro_sequence,
        })

    # ── İkon ayarla (pencere + görev çubuğu) ─────────────────────────────────

    def _set_app_icon(self) -> None:
        # Önce .ico dosyası ara
        for name in ("icon.ico", "imageico.ico"):
            if os.path.exists(name):
                try:
                    self.root.iconbitmap(name)
                    return
                except Exception:
                    pass

        # .ico yoksa Pillow ile oluştur ve iconphoto kullan
        try:
            img32  = self._make_icon_image(32)
            img64  = self._make_icon_image(64)
            ph32   = ImageTk.PhotoImage(img32)
            ph64   = ImageTk.PhotoImage(img64)
            self._icon_photos = [ph32, ph64]   # GC koruması
            self.root.iconphoto(True, ph64, ph32)
        except Exception:
            pass

    def _make_icon_image(self, size: int = 64) -> Image.Image:
        """Programatik klavye ikonu — PIL Image döndürür (PhotoImage değil)."""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d   = ImageDraw.Draw(img)
        # Yuvarlak köşeli arka plan
        d.rounded_rectangle([0, 0, size-1, size-1],
                             radius=int(size*0.18),
                             fill="#13141A", outline="#7C6FFF", width=max(1, size//32))
        accent = (124, 111, 255)
        muted  = (42,  43,  56)

        # Mini tuş satırları
        sc = size / 80.0
        rows = [
            [(6,14,18,22),(22,14,34,22),(38,14,50,22),(54,14,66,22)],
            [(6,28,18,36),(22,28,34,36),(38,28,50,36),(54,28,66,36)],
            [(6,42,60,50)],
        ]
        for ri, row in enumerate(rows):
            for ki, (x0,y0,x1,y1) in enumerate(row):
                c = accent if (ri == 1 and ki == 1) else muted
                d.rounded_rectangle(
                    [int(x0*sc)+1, int(y0*sc)+1,
                     int(x1*sc)+1, int(y1*sc)+1],
                    radius=max(2, int(3*sc)), fill=c
                )
        # "C" harfi
        try:
            fnt = ImageFont.truetype(r"C:\Windows\Fonts\seguibl.ttf", int(size*0.32))
        except Exception:
            try:
                fnt = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", int(size*0.32))
            except Exception:
                fnt = ImageFont.load_default()
        white = (240, 240, 248)
        bb = d.textbbox((0, 0), "C", font=fnt)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]
        d.text(((size-tw)//2, (size-th)//2), "C", font=fnt, fill=white)
        return img

    # ── Hotkey ────────────────────────────────────────────────────────────────

    def _bind_hotkey(self) -> None:
        try:
            if self.hotkey_id is not None:
                keyboard.remove_hotkey(self.hotkey_id)
                self.hotkey_id = None
        except Exception:
            pass
        if self.var_hotkey_enabled.get():
            try:
                self.hotkey_id = keyboard.add_hotkey(
                    self.start_hotkey, lambda: self.root.after(0, self.toggle_process)
                )
            except Exception:
                self.hotkey_id = None

    # ── GitHub async ──────────────────────────────────────────────────────────

    def _fetch_gh_async(self) -> None:
        def worker():
            try:
                url = f"https://github.com/{self.github_user}.png?size=256"
                req = Request(url, headers={"User-Agent": "Clavirum/tkinter"})
                with urlopen(req, timeout=10) as r:
                    raw = r.read()
                size = 64
                img  = Image.open(io.BytesIO(raw)).convert("RGBA")
                img  = img.resize((size, size), Image.LANCZOS)
                mask = Image.new("L", (size, size), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
                img.putalpha(mask)
                photo = ImageTk.PhotoImage(img)
                self.root.after(0, lambda: setattr(self, "_dev_photo", photo))
            except Exception:
                pass
            try:
                api  = f"https://api.github.com/users/{self.github_user}"
                req2 = Request(api, headers={"User-Agent": "Clavirum/tkinter"})
                with urlopen(req2, timeout=10) as r2:
                    self._gh_profile = json.loads(r2.read().decode())
            except Exception:
                self._gh_profile = {}
        threading.Thread(target=worker, daemon=True).start()

    # ── Görsel yardımcılar ────────────────────────────────────────────────────

    def _make_logo(self, size: int = 82) -> Optional[ImageTk.PhotoImage]:
        for name in ("icon.ico", "imageico.ico"):
            if os.path.exists(name):
                try:
                    img = Image.open(name).convert("RGBA")
                    img = img.resize((size, size), Image.LANCZOS)
                    return ImageTk.PhotoImage(img)
                except Exception:
                    pass
        return ImageTk.PhotoImage(self._make_icon_image(size))

    def _make_gradient_title(self, text: str, size: int = 42) -> Optional[ImageTk.PhotoImage]:
        if THEME["BG"] == THEME_LIGHT["BG"]:
            top, bot = (0,0,0), (60,50,200)
        else:
            top, bot = (255,255,255), (124,111,255)
        font = None
        for p in [r"C:\Windows\Fonts\seguibl.ttf",
                  r"C:\Windows\Fonts\arialbd.ttf",
                  r"C:\Windows\Fonts\seguiui.ttf"]:
            try:
                if os.path.exists(p):
                    font = ImageFont.truetype(p, size); break
            except Exception:
                pass
        if font is None:
            try:   font = ImageFont.truetype("seguiui.ttf", size)
            except Exception: font = ImageFont.load_default()

        tmp = Image.new("RGBA",(10,10),(0,0,0,0))
        d2  = ImageDraw.Draw(tmp)
        bb  = d2.textbbox((0,0),text,font=font)
        w,h = max(1,bb[2]-bb[0]), max(1,bb[3]-bb[1])

        mask = Image.new("L",(w,h),0)
        ImageDraw.Draw(mask).text((-bb[0],-bb[1]),text,font=font,fill=255)

        grad = Image.new("RGB",(1,h))
        for y in range(h):
            t = y/(h-1) if h>1 else 0
            grad.putpixel((0,y),(
                int(top[0]*(1-t)+bot[0]*t),
                int(top[1]*(1-t)+bot[1]*t),
                int(top[2]*(1-t)+bot[2]*t),
            ))
        out = grad.resize((w,h)).convert("RGBA")
        out.putalpha(mask)
        return ImageTk.PhotoImage(out)

    # ── Widget yardımcıları ───────────────────────────────────────────────────

    def _frame(self, parent, bg=None, **kw) -> tk.Frame:
        return tk.Frame(parent, bg=bg or THEME["BG"], **kw)

    def _card(self, parent, **pack_kw) -> tk.Frame:
        f = tk.Frame(parent, bg=THEME["CARD"],
                     highlightbackground=THEME["BORDER"],
                     highlightthickness=1)
        f.pack(**pack_kw)
        return f

    def _sep(self, parent, vertical=False) -> None:
        if vertical:
            tk.Frame(parent, bg=THEME["BORDER"], width=1
                     ).pack(side="left", fill="y", pady=8, padx=6)
        else:
            tk.Frame(parent, bg=THEME["BORDER"], height=1
                     ).pack(fill="x", padx=16, pady=4)

    def _btn(self, parent, text, cmd, fg=None, bg=None,
             font=None, accent=None, **kw) -> tk.Button:
        _fg  = fg     or THEME["WHITE"]
        _bg  = bg     or THEME["CARD2"]
        _acc = accent or THEME["BORDER"]
        rel = kw.pop("relief", "flat")
        bw  = kw.pop("borderwidth", 0)
        b = tk.Button(
            parent, text=text, command=cmd,
            font=font or FONT_LABEL,
            fg=_fg, bg=_bg,
            activebackground=THEME["ACCENT"],
            activeforeground=THEME["WHITE"],
            cursor="hand2", relief=rel,
            borderwidth=bw, highlightthickness=1,
            highlightbackground=_acc, **kw
        )
        b.bind("<Enter>", lambda e: b.config(highlightbackground=THEME["ACCENT"]))
        b.bind("<Leave>", lambda e: b.config(highlightbackground=_acc))
        return b

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_header()
        self._build_stats()
        self._build_timing()
        self._build_key_panel()
        self._build_toggle()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        h = tk.Frame(self.root, bg=THEME["BG"], height=140)
        h.pack(fill="x", padx=22, pady=(16,6))
        h.pack_propagate(False)

        right = self._frame(h)
        right.place(relx=1.0, rely=0.0, anchor="ne")
        bc = self._frame(right)
        bc.pack(anchor="ne")

        person_btn = tk.Button(
            bc, text="\U0001f464",
            font=("Segoe UI", 13),
            bg=THEME["CARD"], fg=THEME["WHITE"],
            activebackground=THEME["ACCENT"],
            activeforeground=THEME["WHITE"],
            cursor="hand2", relief="flat",
            borderwidth=0, highlightthickness=1,
            highlightbackground=THEME["BORDER"],
            padx=6, pady=4,
            command=self._show_developer
        )
        person_btn.pack(pady=(0,5))
        person_btn.bind("<Enter>", lambda e: person_btn.config(highlightbackground=THEME["ACCENT"]))
        person_btn.bind("<Leave>", lambda e: person_btn.config(highlightbackground=THEME["BORDER"]))
        Tooltip(person_btn, self.S["tooltip_dev"])

        sb = self._btn(bc, "\u2699", self._show_settings, padx=8, pady=4)
        sb.pack()
        Tooltip(sb, self.S["tooltip_sets"])

        left = self._frame(h)
        left.place(relx=0.0, rely=0.0, anchor="nw")
        try:
            self._title_photo = self._make_gradient_title("CLAVIRUM", 20)
            if self._title_photo:
                tk.Label(left, image=self._title_photo,
                         bg=THEME["BG"], borderwidth=0).pack(anchor="nw")
            else:
                raise ValueError
        except Exception:
            tk.Label(left, text="CLAVIRUM",
                     font=("Segoe UI Black", 14),
                     fg=THEME["WHITE"], bg=THEME["BG"]).pack(anchor="nw")
        tk.Frame(left, bg=THEME["ACCENT"], height=2).pack(fill="x", pady=(2,0))

        center = self._frame(h)
        center.place(relx=0.5, rely=0.5, anchor="center")
        try:
            self._logo_photo = self._make_logo(120)
            if self._logo_photo:
                tk.Label(center, image=self._logo_photo,
                         bg=THEME["BG"], borderwidth=0).pack()
            else:
                raise ValueError
        except Exception:
            tk.Label(center, text="\u2328", font=("Segoe UI", 60),
                     bg=THEME["BG"], fg=THEME["WHITE"]).pack()

    # ── Stats ─────────────────────────────────────────────────────────────────

    def _build_stats(self) -> None:
        panel = self._card(self.root, fill="x", padx=22, pady=6)
        inner = self._frame(panel, bg=THEME["CARD"])
        inner.pack(fill="x")

        def stat(key: str, color: str):
            col = self._frame(inner, bg=THEME["CARD"])
            col.pack(side="left", expand=True, pady=12)
            tk.Label(col, text=self.S[key], font=FONT_LABEL,
                     fg=THEME["WHITE"], bg=THEME["CARD"]).pack()
            lbl = tk.Label(col, text="\u2014", font=FONT_BIG,
                           bg=THEME["CARD"], fg=color)
            lbl.pack(pady=(1,0))
            return lbl

        self.lbl_count   = stat("presses", THEME["AMBER"])
        self._sep(inner, vertical=True)
        self.lbl_elapsed = stat("elapsed",  THEME["WHITE"])
        self._sep(inner, vertical=True)
        self.lbl_status  = stat("status",   THEME["WHITE"])

        self.lbl_count.config(text="0")
        self.lbl_elapsed.config(text="00:00:00")
        self.lbl_status.config(
            text="\u25cf " + self.S["idle"],
            font=("Segoe UI",11,"bold"),
            fg=THEME["WHITE"]
        )

    # ── Timing ────────────────────────────────────────────────────────────────

    def _build_timing(self) -> None:
        panel = self._card(self.root, fill="x", padx=22, pady=6)

        head = self._frame(panel, bg=THEME["CARD"])
        head.pack(fill="x", padx=14, pady=(12,6))
        tk.Label(head, text=self.S["loop_interval"], font=FONT_LABEL,
                 fg=THEME["WHITE"], bg=THEME["CARD"]).pack(side="left")
        tk.Label(head, text=self.S["skip_zero"], font=("Segoe UI",8),
                 fg=THEME["WHITE"], bg=THEME["CARD"]).pack(side="right")

        grid = self._frame(panel, bg=THEME["CARD"])
        grid.pack(pady=(0,6), padx=14)

        self.entries: dict = {}
        unit_keys = ["hour","min","sec","ms"]
        defaults  = [self.cfg.get(k,"0") for k in unit_keys]
        defaults[3] = self.cfg.get("ms","100")

        vcmd = (self.root.register(
            lambda txt: txt=="" or (txt.isdigit() and len(txt)<=6)
        ), "%P")

        for i, (uk, dv) in enumerate(zip(unit_keys, defaults)):
            col = self._frame(grid, bg=THEME["CARD"])
            col.grid(row=0, column=i, padx=8)
            e = tk.Entry(
                col, width=6, justify="center",
                bg=THEME["INPUT_BG"], fg=THEME["WHITE"],
                insertbackground=THEME["ACCENT"],
                relief="flat", font=("Consolas",14,"bold"),
                highlightbackground=THEME["BORDER"],
                highlightthickness=1, borderwidth=0,
                validate="key", validatecommand=vcmd
            )
            e.insert(0, dv)
            e.pack()
            e.bind("<FocusIn>",  lambda ev, w=e: w.config(highlightbackground=THEME["ACCENT"]))
            e.bind("<FocusOut>", lambda ev, w=e, d=dv: (
                w.config(highlightbackground=THEME["BORDER"]),
                (w.insert(0,d) if not w.get().strip() else None)
            ))
            tk.Label(col, text=self.S[uk], font=FONT_LABEL,
                     fg=THEME["WHITE"], bg=THEME["CARD"]).pack(pady=(3,0))
            self.entries[uk] = e

        self._sep(panel)
        pf = self._frame(panel, bg=THEME["CARD"])
        pf.pack(pady=(0,8), padx=14)
        tk.Label(pf, text=self.S["presets"], font=("Segoe UI",8,"bold"),
                 fg=THEME["WHITE"], bg=THEME["CARD"]).pack(side="left", padx=(0,6))
        for label, ds in PRESETS:
            b = tk.Button(
                pf, text=label,
                font=("Segoe UI",8,"bold"),
                bg=THEME["DIM"], fg=THEME["WHITE"],
                activebackground=THEME["ACCENT"],
                activeforeground=THEME["WHITE"],
                relief="flat", cursor="hand2",
                borderwidth=0, highlightthickness=0,
                padx=6, pady=2,
                command=lambda d=ds: self._apply_preset(d)
            )
            b.pack(side="left", padx=2)
            b.bind("<Enter>", lambda e,w=b: w.config(bg=THEME["ACCENT"]))
            b.bind("<Leave>", lambda e,w=b: w.config(bg=THEME["DIM"]))

        self._sep(panel)
        rr = self._frame(panel, bg=THEME["CARD"])
        rr.pack(fill="x", padx=14, pady=(0,12))
        rl = tk.Label(rr, text=self.S["repeat_limit"], font=FONT_LABEL,
                      fg=THEME["WHITE"], bg=THEME["CARD"])
        rl.pack(side="left")
        Tooltip(rl, self.S["tooltip_repeat"])

        self.entry_repeat = tk.Entry(
            rr, width=7, justify="center",
            bg=THEME["INPUT_BG"], fg=THEME["WHITE"],
            insertbackground=THEME["ACCENT"],
            relief="flat", font=("Consolas",12,"bold"),
            highlightbackground=THEME["BORDER"],
            highlightthickness=1, borderwidth=0,
            validate="key", validatecommand=vcmd
        )
        self.entry_repeat.insert(0, self.cfg.get("repeat_limit","0"))
        self.entry_repeat.pack(side="right")
        self.entry_repeat.bind("<FocusIn>",
            lambda e: self.entry_repeat.config(highlightbackground=THEME["ACCENT"]))
        self.entry_repeat.bind("<FocusOut>",
            lambda e: self.entry_repeat.config(highlightbackground=THEME["BORDER"]))

    def _apply_preset(self, ds: float) -> None:
        ms_total = int(ds * 1000)
        h, rem = divmod(ms_total // 1000, 3600)
        m, s   = divmod(rem, 60)
        ms     = ms_total % 1000
        for uk, val in zip(["hour","min","sec","ms"], [h,m,s,ms]):
            e = self.entries[uk]; e.delete(0,tk.END); e.insert(0,str(val))

    # ── Tuş Paneli (Mod seçici + Tek Tuş + Makro) ─────────────────────────────

    def _build_key_panel(self) -> None:
        panel = self._card(self.root, fill="x", padx=22, pady=6)

        # ── Mod seçici ──────────────────────────────────────────────────────
        mode_row = self._frame(panel, bg=THEME["CARD"])
        mode_row.pack(fill="x", padx=14, pady=(10,6))

        self._mode_btns: dict = {}

        def _set_mode(m: str) -> None:
            self.mode_var.set(m)
            for k, b in self._mode_btns.items():
                if k == m:
                    b.config(bg=THEME["ACCENT"], highlightbackground=THEME["ACCENT"])
                else:
                    b.config(bg=THEME["DIM"], highlightbackground=THEME["MUTED"])
            if m == "single":
                self._macro_frame.pack_forget()
                self._single_frame.pack(fill="x")
            else:
                self._single_frame.pack_forget()
                self._macro_frame.pack(fill="x")

        for label_key, mode_id in [("mode_single","single"), ("mode_macro","macro")]:
            is_sel = self.mode_var.get() == mode_id
            b = tk.Button(
                mode_row, text=self.S[label_key],
                font=("Segoe UI",9,"bold"),
                bg=THEME["ACCENT"] if is_sel else THEME["DIM"],
                fg=THEME["WHITE"],
                activebackground=THEME["ACCENT2"],
                activeforeground=THEME["WHITE"],
                relief="flat", cursor="hand2",
                borderwidth=0, highlightthickness=1,
                highlightbackground=THEME["ACCENT"] if is_sel else THEME["MUTED"],
                padx=16, pady=5,
                command=lambda m=mode_id: _set_mode(m)
            )
            b.pack(side="left", padx=(0,6))
            self._mode_btns[mode_id] = b

        self._sep(panel)

        # ── Tek Tuş paneli ────────────────────────────────────────────────────
        self._single_frame = self._frame(panel, bg=THEME["CARD"])

        kr = self._frame(self._single_frame, bg=THEME["CARD"])
        kr.pack(fill="x", padx=14, pady=(8,4))
        tk.Label(kr, text=self.S["assigned_key"], font=FONT_LABEL,
                 fg=THEME["WHITE"], bg=THEME["CARD"]).pack(side="left")
        self.lbl_key = tk.Label(kr, text=self.S["none"],
                                font=("Consolas",14,"bold"),
                                bg=THEME["CARD"], fg=THEME["WHITE"])
        self.lbl_key.pack(side="right")

        self._sep(self._single_frame)

        br = self._frame(self._single_frame, bg=THEME["CARD"])
        br.pack(fill="x", padx=14, pady=(0,6))

        self.btn_capture = self._btn(
            br, text="\u2b21   " + self.S["scan_key"],
            cmd=self.start_capture,
            fg=THEME["WHITE"], accent=THEME["BORDER"],
            font=("Segoe UI",10,"bold"), padx=20, pady=9
        )
        self.btn_capture.pack(side="left")

        clr = self._btn(br, text="\u2715  " + self.S["clear_key"],
                        cmd=self._clear_key,
                        font=("Segoe UI",8,"bold"), padx=8, pady=9)
        clr.pack(side="right")
        Tooltip(clr, self.S["tooltip_clear"])

        # ── Basılı Tut satırı ─────────────────────────────────────────────────
        self._sep(self._single_frame)
        hold_row = self._frame(self._single_frame, bg=THEME["CARD"])
        hold_row.pack(fill="x", padx=14, pady=(0,10))

        hold_chk = tk.Checkbutton(
            hold_row, text=self.S["hold_mode"],
            variable=self.var_hold_mode,
            onvalue=True, offvalue=False,
            bg=THEME["CARD"], fg=THEME["WHITE"],
            selectcolor=THEME["ACCENT"],
            activebackground=THEME["CARD"],
            activeforeground=THEME["WHITE"],
            font=("Segoe UI",9,"bold"),
        )
        hold_chk.pack(side="left")

        tk.Label(hold_row, text=self.S["hold_dur"],
                 font=("Segoe UI",8), fg=THEME["WHITE"],
                 bg=THEME["CARD"]).pack(side="left", padx=(14,4))

        vcmd2 = (self.root.register(
            lambda t: t=="" or (t.isdigit() and len(t)<=5)
        ), "%P")
        hold_entry = tk.Entry(
            hold_row, textvariable=self.var_hold_ms,
            width=5, justify="center",
            bg=THEME["INPUT_BG"], fg=THEME["WHITE"],
            insertbackground=THEME["ACCENT"],
            relief="flat", font=("Consolas",11,"bold"),
            highlightbackground=THEME["BORDER"],
            highlightthickness=1, borderwidth=0,
            validate="key", validatecommand=vcmd2
        )
        hold_entry.pack(side="left")
        tk.Label(hold_row, text="ms",
                 font=("Segoe UI",8), fg=THEME["WHITE"],
                 bg=THEME["CARD"]).pack(side="left", padx=(4,0))

        # ── Makro paneli ──────────────────────────────────────────────────────
        self._macro_frame = self._frame(panel, bg=THEME["CARD"])
        self._build_macro_panel(self._macro_frame)

        # Başlangıç modunu uygula
        if self.mode_var.get() == "macro":
            self._single_frame.pack_forget()
            self._macro_frame.pack(fill="x")
        else:
            self._macro_frame.pack_forget()
            self._single_frame.pack(fill="x")

    def _build_macro_panel(self, parent: tk.Frame) -> None:
        """Makro sıra editörü."""
        # Başlık + butonlar
        top = self._frame(parent, bg=THEME["CARD"])
        top.pack(fill="x", padx=14, pady=(8,4))

        tk.Label(top, text=self.S["macro_title"], font=FONT_LABEL,
                 fg=THEME["WHITE"], bg=THEME["CARD"]).pack(side="left")

        btn_clear = self._btn(top, self.S["clear_macro"],
                              cmd=self._macro_clear,
                              fg=THEME["RED"], accent=THEME["RED"],
                              font=("Segoe UI",8,"bold"), padx=8, pady=4)
        btn_clear.pack(side="right")

        btn_addtxt = self._btn(top, self.S["add_text_btn"],
                               cmd=self._macro_add_text,
                               fg=THEME["TEAL"], accent=THEME["TEAL"],
                               font=("Segoe UI",8,"bold"), padx=8, pady=4)
        btn_addtxt.pack(side="right", padx=(0,6))

        btn_addkey = self._btn(top, self.S["add_key_btn"],
                               cmd=self._macro_add_key,
                               fg=THEME["AMBER"], accent=THEME["AMBER"],
                               font=("Segoe UI",8,"bold"), padx=8, pady=4)
        btn_addkey.pack(side="right", padx=(0,4))

        self._sep(parent)

        # Liste kutusu
        lf = self._frame(parent, bg=THEME["CARD"])
        lf.pack(fill="x", padx=14, pady=(0,4))

        sb = tk.Scrollbar(lf, orient="vertical",
                          bg=THEME["DIM"], troughcolor=THEME["CARD"],
                          width=8, relief="flat", borderwidth=0)
        sb.pack(side="right", fill="y")

        self.macro_listbox = tk.Listbox(
            lf, height=5,
            bg=THEME["INPUT_BG"], fg=THEME["WHITE"],
            selectbackground=THEME["ACCENT"],
            selectforeground=THEME["WHITE"],
            font=("Consolas",10),
            relief="flat", borderwidth=0,
            highlightthickness=0,
            activestyle="none",
            exportselection=False,
            yscrollcommand=sb.set
        )
        self.macro_listbox.pack(fill="x", expand=True)
        sb.config(command=self.macro_listbox.yview)

        # Kontrol butonları
        ctrl = self._frame(parent, bg=THEME["CARD"])
        ctrl.pack(fill="x", padx=14, pady=(2,10))

        for txt, cmd in [
            (self.S["macro_move_up"], self._macro_move_up),
            (self.S["macro_move_dn"], self._macro_move_dn),
            (self.S["macro_remove"],  self._macro_remove),
        ]:
            b = self._btn(ctrl, txt, cmd,
                          font=("Segoe UI",10,"bold"), padx=10, pady=4)
            b.pack(side="left", padx=(0,4))

        tk.Label(ctrl, text=self.S.get("macro_hint",""),
                 font=("Segoe UI",7), fg=THEME["MUTED"],
                 bg=THEME["CARD"]).pack(side="right")

        # Mevcut sekansı doldur
        self._macro_refresh_list()

    # ── Makro işlemleri ───────────────────────────────────────────────────────

    def _macro_refresh_list(self) -> None:
        if not hasattr(self, "macro_listbox"):
            return
        self.macro_listbox.delete(0, tk.END)
        for item in self.macro_sequence:
            icon = "🔑" if item["type"] == "key" else "📝"
            delay = item.get("delay_ms", 50)
            self.macro_listbox.insert(tk.END,
                f"  {icon}  {item['value']}   ({delay} ms)")

    def _macro_add_key(self) -> None:
        """Tuş yakalamak icin yeni bir Toplevel pencere acar."""
        if self.is_capturing:
            return

        win = tk.Toplevel(self.root)
        win.title(self.S["scan_key"])
        win.configure(bg=THEME["BG"])
        win.resizable(False, False)
        self._center_child(win, 300, 140)

        lbl = tk.Label(win, text=self.S["press_key"],
                       font=("Consolas", 14, "bold"),
                       fg=THEME["AMBER"], bg=THEME["BG"])
        lbl.pack(expand=True, pady=30)

        cancel_var = [False]

        def _release():
            """is_capturing'i serbest birak — her durumda cagrilir."""
            cancel_var[0] = True
            self.is_capturing = False

        def _cancel():
            _release()
            try:
                win.destroy()
            except Exception:
                pass

        # Pencere X ile kapatildiginda da bayrak sifirlansin
        win.protocol("WM_DELETE_WINDOW", _cancel)

        self._btn(win, "x  " + self.S["clear_key"], _cancel,
                  fg=THEME["RED"], accent=THEME["RED"],
                  font=("Segoe UI", 8, "bold"), padx=10, pady=4
                  ).pack(pady=(0, 10))

        captured = [None]
        self.is_capturing = True

        def _capture():
            # KEY_UP / KEY_DOWN karisikligini onlemek icin
            # ilk KEY_DOWN gelene kadar dongude bekle
            while not cancel_var[0]:
                try:
                    ev = keyboard.read_event(suppress=False)
                except Exception:
                    break
                if ev.event_type == keyboard.KEY_DOWN:
                    captured[0] = ev.name
                    break
            self.root.after(0, _done)

        def _done():
            was_cancelled = cancel_var[0]
            _release()
            key = captured[0]
            try:
                win.destroy()
            except Exception:
                pass
            if not key or was_cancelled:
                return
            delay_str = self._ask_string(
                self.S["delay_title"],
                self.S["delay_prompt"],
                "50"
            )
            try:
                delay_ms = max(0, int(delay_str or 50))
            except Exception:
                delay_ms = 50
            self.macro_sequence.append({
                "type":     "key",
                "value":    key,
                "delay_ms": delay_ms
            })
            self._macro_refresh_list()

        threading.Thread(target=_capture, daemon=True).start()

    def _macro_add_text(self) -> None:
        txt = self._ask_string(
            self.S["text_title"],
            self.S["text_prompt"]
        )
        if not txt:
            return
        delay_str = self._ask_string(
            self.S["delay_title"],
            self.S["delay_prompt"],
            "100"
        )
        try:
            delay_ms = max(0, int(delay_str or 100))
        except Exception:
            delay_ms = 100
        self.macro_sequence.append({
            "type":     "text",
            "value":    txt,
            "delay_ms": delay_ms
        })
        self._macro_refresh_list()

    def _macro_remove(self) -> None:
        sel = self.macro_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        del self.macro_sequence[idx]
        self._macro_refresh_list()
        if self.macro_sequence:
            self.macro_listbox.selection_set(min(idx, len(self.macro_sequence)-1))

    def _macro_move_up(self) -> None:
        sel = self.macro_listbox.curselection()
        if not sel or sel[0] == 0:
            return
        i = sel[0]
        self.macro_sequence[i-1], self.macro_sequence[i] = \
            self.macro_sequence[i], self.macro_sequence[i-1]
        self._macro_refresh_list()
        self.macro_listbox.selection_set(i-1)

    def _macro_move_dn(self) -> None:
        sel = self.macro_listbox.curselection()
        if not sel or sel[0] >= len(self.macro_sequence)-1:
            return
        i = sel[0]
        self.macro_sequence[i+1], self.macro_sequence[i] = \
            self.macro_sequence[i], self.macro_sequence[i+1]
        self._macro_refresh_list()
        self.macro_listbox.selection_set(i+1)

    def _macro_clear(self) -> None:
        self.macro_sequence.clear()
        self._macro_refresh_list()

    def _clear_key(self) -> None:
        self.target_key = None
        self.lbl_key.config(text=self.S["none"], fg=THEME["WHITE"])

    # ── Toggle butonu ─────────────────────────────────────────────────────────

    def _build_toggle(self) -> None:
        self.toggle_frame = tk.Frame(self.root, bg=THEME["WHITE"])
        self.toggle_frame.pack(fill="x", padx=22, pady=(12, 16))

        self.btn_toggle = tk.Button(
            self.toggle_frame,
            text=f"\u25b6   {self.S['start']}   ({self.start_hotkey.upper()})",
            font=("Segoe UI Black", 20),
            bg=THEME["CARD"], fg=THEME["WHITE"],
            activebackground=THEME["ACCENT"],
            activeforeground=THEME["WHITE"],
            relief="flat", cursor="hand2",
            borderwidth=0,
            command=self.toggle_process
        )
        self.btn_toggle.pack(fill="x", padx=2, pady=2, ipady=44)

    # ── Tick ──────────────────────────────────────────────────────────────────

    def _tick(self) -> None:
        if self.is_running and self.start_time:
            elapsed = int(time.time() - self.start_time)
            h, rem  = divmod(elapsed, 3600)
            m, s    = divmod(rem, 60)
            self.lbl_elapsed.config(text=f"{h:02d}:{m:02d}:{s:02d}")
            self.lbl_count.config(text=f"{self.press_count:,}")
        self.root.after(200, self._tick)

    # ── Yakalama (tek tuş) ────────────────────────────────────────────────────

    def start_capture(self) -> None:
        self.root.focus_set()
        if self.is_capturing:
            return
        threading.Thread(target=self._capture_logic, daemon=True).start()

    def _capture_logic(self) -> None:
        self.is_capturing = True
        self.root.after(0, lambda: (
            self.btn_capture.config(
                state="disabled",
                text=self.S["listening"],
                fg=THEME["RED"],
                highlightbackground=THEME["RED"]
            ),
            self.lbl_key.config(text=self.S["press_key"], fg=THEME["AMBER"])
        ))

        event = keyboard.read_event()
        key   = event.name if event.event_type == keyboard.KEY_DOWN else None

        def _done():
            if key:
                self.target_key = key
                self.lbl_key.config(text=f"[ {key.upper()} ]", fg=THEME["TEAL"])
            self.is_capturing = False
            self.btn_capture.config(
                state="normal",
                text="\u2b21   " + self.S["scan_key"],
                fg=THEME["WHITE"],
                highlightbackground=THEME["BORDER"]
            )

        self.root.after(0, _done)

    # ── Toggle process ────────────────────────────────────────────────────────

    def toggle_process(self) -> None:
        self.root.focus_set()
        if self.is_running:
            self._stop()
        else:
            self._start()

    def _stop(self) -> None:
        self.is_running = False
        self.btn_toggle.config(
            text=f"\u25b6   {self.S['start']}   ({self.start_hotkey.upper()})",
            fg=THEME["WHITE"], bg=THEME["CARD"]
        )
        self.toggle_frame.config(bg=THEME["WHITE"])
        self.lbl_status.config(text="\u25cf " + self.S["idle"], fg=THEME["WHITE"])

    def _start(self) -> None:
        mode = self.mode_var.get()

        # Doğrulama
        if mode == "single" and not self.target_key:
            messagebox.showwarning(self.S["no_key_title"], self.S["no_key_msg"])
            return
        if mode == "macro" and not self.macro_sequence:
            messagebox.showwarning(self.S["no_macro_title"], self.S["no_macro_msg"])
            return

        try:
            h  = float(self.entries["hour"].get().strip() or 0) * 3600
            m  = float(self.entries["min"].get().strip()  or 0) * 60
            s  = float(self.entries["sec"].get().strip()  or 0)
            ms = float(self.entries["ms"].get().strip()   or 0) / 1000.0
            delay = h + m + s + ms
            if delay <= 0:
                delay = 0.01
        except ValueError:
            messagebox.showerror(self.S["bad_inp_title"], self.S["bad_inp_msg"])
            return

        try:
            repeat_val = int(self.entry_repeat.get().strip() or 0)
        except ValueError:
            repeat_val = 0

        try:
            hold_ms = max(0, int(self.var_hold_ms.get().strip() or 50))
        except ValueError:
            hold_ms = 50

        self.press_count = 0
        self.start_time  = time.time()
        self.is_running  = True

        self.lbl_elapsed.config(text="00:00:00")
        self.lbl_count.config(text="0")
        self.btn_toggle.config(
            text=f"\u25a0   {self.S['stop']}   ({self.start_hotkey.upper()})",
            fg=THEME["RED"], bg="#130008"
        )
        self.toggle_frame.config(bg=THEME["RED"])
        self.lbl_status.config(text="\u25cf " + self.S["active"], fg=THEME["TEAL"])

        if mode == "macro":
            threading.Thread(
                target=self._loop_macro,
                args=(delay, repeat_val),
                daemon=True
            ).start()
        else:
            threading.Thread(
                target=self._loop_single,
                args=(delay, repeat_val, hold_ms),
                daemon=True
            ).start()

    # ── Döngüler ──────────────────────────────────────────────────────────────

    def _loop_single(self, delay: float, limit: int, hold_ms: int) -> None:
        """Tek tuş modu — isteğe bağlı basılı tutma ile."""
        hold = self.var_hold_mode.get()
        count = 0
        while self.is_running:
            key = self.target_key
            if not key:
                break
            if hold:
                total_hold = hold_ms / 1000.0
                
                # Başlangıçta tuşu fiziksel olarak basılı duruma getiriyoruz
                keyboard.press(key)
                
                if total_hold == 0:
                    # 0 = Sonsuz basılı tutma (Dur diyene kadar basılı kalır)
                    while self.is_running:
                        time.sleep(0.05)
                else:
                    # Süreli basılı tutma (ms bazında)
                    slept = 0.0
                    while slept < total_hold and self.is_running:
                        time.sleep(0.01)
                        slept += 0.01
                
                # Süre bitince veya program durdurulunca tuşu bırakıyoruz
                keyboard.release(key)
            else:
                keyboard.press_and_release(key)
            
            self.press_count += 1
            count += 1
            if limit > 0 and count >= limit:
                self.root.after(0, self._stop)
                break
            
            # Program/Makro o an durdurulduysa delay beklemeye gerek yok
            if not self.is_running:
                break
            
            if delay > 0:
                slept_delay = 0.0
                while slept_delay < delay and self.is_running:
                    time.sleep(0.01)
                    slept_delay += 0.01

    def _loop_macro(self, delay: float, limit: int) -> None:
        """Makro modu — sırayla tuş/metin basar."""
        count = 0
        while self.is_running:
            for item in list(self.macro_sequence):
                if not self.is_running:
                    break
                try:
                    if item["type"] == "key":
                        keyboard.press_and_release(item["value"])
                    elif item["type"] == "text":
                        keyboard.write(item["value"], delay=0.02)
                except Exception:
                    pass
                item_delay = item.get("delay_ms", 50) / 1000.0
                if item_delay > 0:
                    time.sleep(item_delay)
            self.press_count += 1
            count += 1
            if limit > 0 and count >= limit:
                self.root.after(0, self._stop)
                break
            time.sleep(delay)

    # ── Yapımcı penceresi ─────────────────────────────────────────────────────

    def _show_developer(self) -> None:
        if hasattr(self, "_dev_win") and self._dev_win.winfo_exists():
            self._dev_win.lift(); self._dev_win.focus_force(); return

        win = tk.Toplevel(self.root)
        self._dev_win = win
        win.title(f"Clavirum \u2014 {self.S['developer']}")
        win.configure(bg=THEME["BG"])
        win.resizable(False, False)
        self._center_child(win, 370, 310)

        c = tk.Frame(win, bg=THEME["BG"])
        c.pack(fill="both", expand=True, padx=22, pady=20)

        top = tk.Frame(c, bg=THEME["BG"])
        top.pack(fill="x", pady=(0,14))
        nf = tk.Frame(top, bg=THEME["BG"])
        nf.pack(side="left", anchor="w")

        name_lbl = tk.Label(nf, text=self.S["made_by"],
                            font=("Segoe UI", 13, "bold"),
                            fg=THEME["WHITE"], bg=THEME["BG"])
        name_lbl.pack(anchor="w")

        tk.Label(nf, text=f"@{self.github_user}",
                 font=("Segoe UI", 9),
                 fg=THEME["MUTED"], bg=THEME["BG"]).pack(anchor="w")

        def _poll_avatar(n=0):
            if self._dev_photo:
                try:
                    av = tk.Label(top, image=self._dev_photo,
                                  bg=THEME["BG"], borderwidth=0)
                    av.pack(side="right")
                except Exception:
                    pass
            elif n < 20:
                win.after(500, lambda: _poll_avatar(n+1))
        _poll_avatar()

        bio_text = (self._gh_profile.get("bio") or
                    f"Clavirum \u2014 {self.S['about_desc']}")
        bio_lbl = tk.Label(c, text=bio_text,
                           font=("Segoe UI",9),
                           fg=THEME["WHITE"], bg=THEME["BG"],
                           justify="left", wraplength=310)
        bio_lbl.pack(anchor="w", pady=(0,16))

        def _poll_bio(n=0):
            bio = self._gh_profile.get("bio","")
            if bio:
                try: bio_lbl.config(text=bio)
                except Exception: pass
            elif n < 20:
                win.after(500, lambda: _poll_bio(n+1))
        _poll_bio()

        tk.Frame(c, bg=THEME["BORDER"], height=1).pack(fill="x", pady=(0,12))
        if self.current_theme == "light":
            gh_bg = "#FFFFFF"
            gh_fg = "#000000"
            gh_acc = "#000000"
            gh_rel = "solid"
            gh_bw = 1
        else:
            gh_bg = "#161B22"
            gh_fg = THEME["WHITE"]
            gh_acc = THEME["BORDER"]
            gh_rel = "flat"
            gh_bw = 0

        gh = self._btn(c, self.S["open_github"], self._open_github,
                       bg=gh_bg, fg=gh_fg,
                       accent=gh_acc,
                       relief=gh_rel, borderwidth=gh_bw,
                       font=("Segoe UI",9,"bold"), padx=14, pady=7)
        gh.pack(anchor="w")

    # ── Ayarlar ───────────────────────────────────────────────────────────────

    def _show_settings(self) -> None:
        if hasattr(self, "_sets_win") and self._sets_win.winfo_exists():
            self._sets_win.lift(); self._sets_win.focus_force(); return

        win = tk.Toplevel(self.root)
        self._sets_win = win
        win.title(f"Clavirum \u2014 {self.S['settings_title']}")
        win.configure(bg=THEME["BG"])
        win.resizable(False, False)
        self._center_child(win, 480, 360)

        c = tk.Frame(win, bg=THEME["BG"])
        c.pack(fill="both", expand=True, padx=22, pady=18)

        tk.Label(c, text=self.S["settings_title"],
                 font=("Segoe UI",13,"bold"),
                 fg=THEME["WHITE"], bg=THEME["BG"]).pack(anchor="w", pady=(0,14))

        def chk(text, var, cmd):
            return tk.Checkbutton(
                c, text=text, variable=var,
                onvalue=True, offvalue=False,
                bg=THEME["BG"], fg=THEME["WHITE"],
                selectcolor=THEME["ACCENT"],
                activebackground=THEME["BG"],
                activeforeground=THEME["WHITE"],
                font=("Segoe UI",10), command=cmd
            )

        chk(self.S["hotkey_active"], self.var_hotkey_enabled,
            self._bind_hotkey).pack(anchor="w", pady=(0,8))

        f_hotkey = tk.Frame(c, bg=THEME["BG"])
        f_hotkey.pack(fill="x", pady=(0,14))
        tk.Label(f_hotkey, text=self.S["hotkey_label"], font=("Segoe UI",10),
                 fg=THEME["WHITE"], bg=THEME["BG"]).pack(side="left")

        self.var_hotkey = tk.StringVar(value=self.start_hotkey.upper())
        opts = [f"F{i}" for i in range(1, 13)]
        hotkey_menu = tk.OptionMenu(f_hotkey, self.var_hotkey, *opts)
        hotkey_menu.config(bg=THEME["DIM"], fg=THEME["WHITE"],
                           activebackground=THEME["ACCENT"],
                           activeforeground=THEME["WHITE"],
                           highlightthickness=0, borderwidth=0, relief="flat", cursor="hand2")
        hotkey_menu["menu"].config(bg=THEME["DIM"], fg=THEME["WHITE"],
                                   activebackground=THEME["ACCENT"],
                                   activeforeground=THEME["WHITE"], borderwidth=0)
        hotkey_menu.pack(side="right")

        lr = tk.Frame(c, bg=THEME["BG"])
        lr.pack(fill="x", pady=(0,14))
        tk.Label(lr, text=self.S["language"], font=FONT_LABEL,
                 fg=THEME["WHITE"], bg=THEME["BG"]).pack(side="left")

        self._lang_var = tk.StringVar(value=self.lang_code)
        lf = tk.Frame(lr, bg=THEME["BG"])
        lf.pack(side="right")
        self._lang_btns: dict = {}

        def _select_lang(code):
            self._lang_var.set(code)
            for c2, btn in self._lang_btns.items():
                if c2 == code:
                    btn.config(bg=THEME["ACCENT"], highlightbackground=THEME["ACCENT"])
                else:
                    btn.config(bg=THEME["DIM"], highlightbackground=THEME["MUTED"])

        for code in available_langs():
            is_selected = (code == self.lang_code)
            btn = tk.Button(
                lf, text=code.upper(),
                font=("Segoe UI", 9, "bold"),
                bg=THEME["ACCENT"] if is_selected else THEME["DIM"],
                fg=THEME["WHITE"],
                activebackground=THEME["ACCENT2"],
                activeforeground=THEME["WHITE"],
                relief="flat", cursor="hand2",
                borderwidth=0, highlightthickness=1,
                highlightbackground=THEME["ACCENT"] if is_selected else THEME["MUTED"],
                padx=12, pady=4,
                command=lambda c2=code: _select_lang(c2)
            )
            btn.pack(side="left", padx=3)
            btn.bind("<Enter>", lambda e, w=btn, c2=code: w.config(
                bg=THEME["ACCENT"], highlightbackground=THEME["ACCENT"]))
            btn.bind("<Leave>", lambda e, w=btn, c2=code: w.config(
                bg=THEME["ACCENT"] if self._lang_var.get()==c2 else THEME["DIM"],
                highlightbackground=THEME["ACCENT"] if self._lang_var.get()==c2 else THEME["MUTED"]
            ))
            self._lang_btns[code] = btn

        # Theme frame
        tr_frame = tk.Frame(c, bg=THEME["BG"])
        tr_frame.pack(fill="x", pady=(0,14))
        tk.Label(tr_frame, text=self.S.get("theme", "Tema / Theme"), font=FONT_LABEL,
                 fg=THEME["WHITE"], bg=THEME["BG"]).pack(side="left")

        self._theme_var = tk.StringVar(value=self.current_theme)
        tf = tk.Frame(tr_frame, bg=THEME["BG"])
        tf.pack(side="right")
        self._theme_btns: dict = {}

        def _select_theme(code):
            self._theme_var.set(code)
            for c2, btn in self._theme_btns.items():
                if c2 == code:
                    btn.config(bg=THEME["ACCENT"], highlightbackground=THEME["ACCENT"])
                else:
                    btn.config(bg=THEME["DIM"], highlightbackground=THEME["MUTED"])

        for code, label in [("dark", self.S.get("dark", "Koyu")), ("light", self.S.get("light", "Beyaz"))]:
            is_selected = (code == self.current_theme)
            btn = tk.Button(
                tf, text=label.upper(),
                font=("Segoe UI", 9, "bold"),
                bg=THEME["ACCENT"] if is_selected else THEME["DIM"],
                fg=THEME["WHITE"],
                activebackground=THEME["ACCENT2"],
                activeforeground=THEME["WHITE"],
                relief="flat", cursor="hand2",
                borderwidth=0, highlightthickness=1,
                highlightbackground=THEME["ACCENT"] if is_selected else THEME["MUTED"],
                padx=12, pady=4,
                command=lambda c2=code: _select_theme(c2)
            )
            btn.pack(side="left", padx=3)
            btn.bind("<Enter>", lambda e, w=btn: w.config(
                bg=THEME["ACCENT"], highlightbackground=THEME["ACCENT"]))
            btn.bind("<Leave>", lambda e, w=btn, c2=code: w.config(
                bg=THEME["ACCENT"] if self._theme_var.get()==c2 else THEME["DIM"],
                highlightbackground=THEME["ACCENT"] if self._theme_var.get()==c2 else THEME["MUTED"]
            ))
            self._theme_btns[code] = btn

        tk.Label(c, text=self.S.get("more_soon", "Daha fazla ayar yakin zamanda."),
                 font=("Segoe UI",8), fg=THEME["WHITE"], bg=THEME["BG"]
                 ).pack(anchor="w", pady=(0,10))

        def _save():
            new_lang    = self._lang_var.get()
            new_theme   = self._theme_var.get()
            new_hotkey  = self.var_hotkey.get().lower()

            changed_lang   = new_lang   != self.lang_code
            changed_theme  = new_theme  != self.current_theme
            changed_hotkey = new_hotkey != self.start_hotkey

            self.start_hotkey = new_hotkey
            self.current_theme = new_theme
            self._save_config()
            win.destroy()

            if changed_hotkey:
                self._bind_hotkey()
                if not self.is_running:
                    self.btn_toggle.config(
                        text=f"\u25b6   {self.S['start']}   ({self.start_hotkey.upper()})")
                else:
                    self.btn_toggle.config(
                        text=f"\u25a0   {self.S['stop']}   ({self.start_hotkey.upper()})")

            if changed_lang or changed_theme:
                self._apply_language(new_lang)

        self._btn(c, self.S["save_close"], _save,
                  fg=THEME["TEAL"], accent=THEME["TEAL"],
                  font=("Segoe UI",9,"bold"), padx=12, pady=5
                  ).pack(anchor="e", pady=(4,0))

    # ── Dil yenile ────────────────────────────────────────────────────────────

    def _apply_language(self, code: str) -> None:
        self.lang_code = code
        self.S = load_lang(code)
        self._apply_theme_colors(self.current_theme)
        self.root.configure(bg=THEME["BG"])
        for w in self.root.winfo_children():
            w.destroy()
        self._logo_photo  = None
        self._title_photo = None
        self._build()
        self._set_app_icon()
        if self.target_key:
            self.lbl_key.config(
                text=f"[ {self.target_key.upper()} ]",
                fg=THEME["TEAL"]
            )
        self._macro_refresh_list()
        if self.is_running:
            self.btn_toggle.config(
                text=f"\u25a0   {self.S['stop']}   ({self.start_hotkey.upper()})",
                fg=THEME["RED"], bg="#130008"
            )
            self.lbl_status.config(text="\u25cf " + self.S["active"], fg=THEME["TEAL"])
            if self.start_time:
                elapsed = int(time.time() - self.start_time)
                h, rem = divmod(elapsed, 3600)
                m, s   = divmod(rem, 60)
                self.lbl_elapsed.config(text=f"{h:02d}:{m:02d}:{s:02d}")
            self.lbl_count.config(text=f"{self.press_count:,}")
        else:
            self.lbl_status.config(text="\u25cf " + self.S["idle"], fg=THEME["WHITE"])

    # ── Yardımcılar ───────────────────────────────────────────────────────────

    def _open_github(self) -> None:
        try:
            webbrowser.open(f"https://github.com/{self.github_user}")
        except Exception:
            messagebox.showerror(
                "Hata",
                f"Tarayici acilamadi.\nhttps://github.com/{self.github_user}"
            )


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    Clavirum(root)
    root.mainloop()
