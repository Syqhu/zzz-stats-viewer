#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ゼンレスゾーンゼロ 理想ステータス一覧ツール
ZZZ Ideal Stats Viewer
=====================================================
データソース:
  - 内蔵データ（Prydwen.gg / game8.jp の公開ビルド情報を基に整理）
  - 起動後にprydwen.ggから最新キャラリスト & アイコンを取得
"""

import os
import io
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# 外部ライブラリ
try:
    import requests
    from PIL import Image, ImageTk, ImageDraw, ImageFont
except ImportError as e:
    print(f"必要なライブラリが不足: {e}")
    print("pip install requests Pillow を実行してください")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════
#  カラーテーマ
# ═══════════════════════════════════════════════════════════
BG_MAIN   = "#0B0B14"
BG_PANEL  = "#13131E"
BG_CARD   = "#1A1A28"
BG_CARD2  = "#1F1F30"
BG_HOVER  = "#252538"
BORDER    = "#2A2A40"
ACCENT    = "#FFC832"
ACCENT2   = "#FF6B35"
TEXT_PRI  = "#E8E8F0"
TEXT_SEC  = "#9595B0"
TEXT_TER  = "#5A5A75"

# 属性カラー(FG, BG)
ELEM_COLORS = {
    "氷":       ("#5DE0FF", "#0A2E3B"),
    "炎":       ("#FF6B3D", "#3B1108"),
    "雷":       ("#C896FF", "#1F0A55"),
    "物理":     ("#E0E0E0", "#2A2A2A"),
    "エーテル": ("#FFEE5D", "#3B3300"),
    "霜":       ("#7FF5FF", "#0C3540"),  # Frost (星見雅)
    "玄墨":     ("#A8A8A8", "#1A1A1A"),  # Auric Ink (儀玄)
    "凛刃":     ("#FF85B8", "#3A0A24"),  # Honed Edge (葉瞬光)
}

# 役割カラー
SPEC_COLORS = {
    "アタック":     "#FF4757",
    "スタン":       "#FFC832",
    "アノマリー":   "#5DE0FF",
    "サポート":     "#5BE584",
    "ディフェンス": "#FF8C42",
    "ラプチャー":   "#FF6B9D",
}

# レアリティカラー
RARE_COLORS = {"S": "#FFC832", "A": "#A075FF"}

# 優先度カラー
PRIO_COLORS = {"高": "#FF5566", "中": "#FFB840", "低": "#5BE584"}


# ═══════════════════════════════════════════════════════════
#  日本語フォント検索
# ═══════════════════════════════════════════════════════════
JP_FONT_CANDIDATES = [
    # Windows
    "C:/Windows/Fonts/YuGothB.ttc",
    "C:/Windows/Fonts/YuGothM.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
    # macOS
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
]


def get_jp_font(size: int):
    for path in JP_FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


# Tkinter用フォント
def tk_font(size: int, bold: bool = False):
    weight = "bold" if bold else "normal"
    # Windowsで日本語が確実に表示されるフォント優先
    return ("Yu Gothic UI", size, weight) if sys.platform == "win32" else \
           ("Noto Sans CJK JP", size, weight)


# ═══════════════════════════════════════════════════════════
#  キャラクター内蔵データ
#  Prydwen.gg / game8.jp の公開ビルドガイドを基に整理（2026年5月時点）
#  起動後にprydwen.ggから最新エージェント名簿を取得して補完
# ═══════════════════════════════════════════════════════════
CHARACTERS = [
    # ━━━━━━━━━━━ S ランク ━━━━━━━━━━━
    {
        "name": "星見雅", "slug": "miyabi", "rarity": "S",
        "element": "霜", "specialty": "アノマリー",
        "stats": [
            ("会心率",       "≥ 80%",      "高"),
            ("会心ダメージ", "≥ 150%",     "高"),
            ("攻撃力",       "≥ 2,500",    "中"),
            ("異常マスタリー","≥ 115",     "中"),
            ("貫通比率",     "≥ 20%",      "低"),
        ],
    },
    {
        "name": "エレン", "slug": "ellen", "rarity": "S",
        "element": "氷", "specialty": "アタック",
        "stats": [
            ("会心率",       "≥ 70%",      "高"),
            ("会心ダメージ", "≥ 200%",     "高"),
            ("攻撃力",       "≥ 2,600",    "中"),
            ("氷ダメージ強化","≥ 30%",     "中"),
            ("貫通比率",     "≥ 20%",      "低"),
        ],
    },
    {
        "name": "朱鳶", "slug": "zhu-yuan", "rarity": "S",
        "element": "エーテル", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 70%",   "高"),
            ("会心ダメージ",   "≥ 200%",  "高"),
            ("攻撃力",         "≥ 2,500", "中"),
            ("エーテル強化",   "≥ 30%",   "中"),
            ("貫通比率",       "≥ 30%",   "低"),
        ],
    },
    {
        "name": "リナ", "slug": "rina", "rarity": "S",
        "element": "雷", "specialty": "サポート",
        "stats": [
            ("エネルギー回復","≥ 130%",   "高"),
            ("攻撃力",       "≥ 2,000",  "高"),
            ("貫通値",       "≥ 80",     "中"),
            ("会心率",       "≥ 50%",    "低"),
        ],
    },
    {
        "name": "蒼角", "slug": "soukaku", "rarity": "S",
        "element": "氷", "specialty": "サポート",
        "stats": [
            ("攻撃力",         "≥ 2,400", "高"),
            ("エネルギー回復", "≥ 120%",  "高"),
            ("氷ダメージ強化", "≥ 15%",   "中"),
            ("HP",             "≥ 9,000", "低"),
        ],
    },
    {
        "name": "ライカン", "slug": "lycaon", "rarity": "S",
        "element": "氷", "specialty": "スタン",
        "stats": [
            ("衝撃力",       "≥ 190",    "高"),
            ("会心率",       "≥ 50%",    "高"),
            ("会心ダメージ", "≥ 100%",   "中"),
            ("攻撃力",       "≥ 2,000",  "中"),
            ("HP",           "≥ 10,500", "低"),
        ],
    },
    {
        "name": "ジェーン", "slug": "jane-doe", "rarity": "S",
        "element": "物理", "specialty": "アノマリー",
        "stats": [
            ("異常マスタリー", "≥ 350",    "高"),
            ("攻撃力",         "≥ 2,400",  "高"),
            ("会心率",         "≥ 60%",    "中"),
            ("会心ダメージ",   "≥ 120%",   "中"),
            ("貫通比率",       "≥ 20%",    "低"),
        ],
    },
    {
        "name": "バーニス", "slug": "burnice", "rarity": "S",
        "element": "炎", "specialty": "アノマリー",
        "stats": [
            ("異常マスタリー","≥ 600",    "高"),
            ("攻撃力",       "≥ 2,200",   "高"),
            ("炎ダメージ強化","≥ 25%",    "中"),
            ("エネルギー回復","≥ 130%",   "低"),
        ],
    },
    {
        "name": "シーザー", "slug": "caesar", "rarity": "S",
        "element": "物理", "specialty": "ディフェンス",
        "stats": [
            ("HP",         "≥ 12,000", "高"),
            ("衝撃力",     "≥ 130",    "高"),
            ("防御力",     "≥ 1,200",  "中"),
            ("会心率",     "≥ 45%",    "中"),
            ("エネルギー回復", "≥ 110%", "低"),
        ],
    },
    {
        "name": "ライト", "slug": "lighter", "rarity": "S",
        "element": "炎", "specialty": "スタン",
        "stats": [
            ("衝撃力",       "≥ 190",   "高"),
            ("会心率",       "≥ 50%",   "高"),
            ("攻撃力",       "≥ 1,900", "中"),
            ("会心ダメージ", "≥ 100%",  "中"),
            ("HP",           "≥ 10,500","低"),
        ],
    },
    {
        "name": "月城柳", "slug": "yanagi", "rarity": "S",
        "element": "雷", "specialty": "アノマリー",
        "stats": [
            ("異常マスタリー","≥ 350",   "高"),
            ("攻撃力",       "≥ 2,300", "高"),
            ("会心率",       "≥ 55%",   "中"),
            ("雷ダメージ強化","≥ 20%",  "中"),
            ("エネルギー回復","≥ 120%", "低"),
        ],
    },
    {
        "name": "悠真", "slug": "harumasa", "rarity": "S",
        "element": "雷", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 65%",  "高"),
            ("会心ダメージ",   "≥ 200%", "高"),
            ("攻撃力",         "≥ 2,400","中"),
            ("雷ダメージ強化", "≥ 25%",  "中"),
        ],
    },
    {
        "name": "イヴリン", "slug": "evelyn", "rarity": "S",
        "element": "炎", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 75%",  "高"),
            ("会心ダメージ",   "≥ 200%", "高"),
            ("攻撃力",         "≥ 2,600","中"),
            ("炎ダメージ強化", "≥ 30%",  "中"),
            ("貫通比率",       "≥ 20%",  "低"),
        ],
    },
    {
        "name": "「トリガー」", "slug": "trigger", "rarity": "S",
        "element": "雷", "specialty": "スタン",
        "stats": [
            ("衝撃力",       "≥ 180",   "高"),
            ("会心率",       "≥ 55%",   "高"),
            ("攻撃力",       "≥ 2,000", "中"),
            ("雷ダメージ強化","≥ 15%",  "中"),
            ("会心ダメージ", "≥ 100%",  "低"),
        ],
    },
    {
        "name": "青衣", "slug": "qingyi", "rarity": "S",
        "element": "雷", "specialty": "スタン",
        "stats": [
            ("衝撃力",       "≥ 200",   "高"),
            ("攻撃力",       "≥ 2,000", "高"),
            ("会心率",       "≥ 45%",   "中"),
            ("エネルギー回復","≥ 120%", "中"),
        ],
    },
    {
        "name": "アストラ", "slug": "astra-yao", "rarity": "S",
        "element": "エーテル", "specialty": "サポート",
        "stats": [
            ("攻撃力",         "≥ 2,800", "高"),
            ("エネルギー回復", "≥ 130%",  "高"),
            ("会心率",         "≥ 35%",   "中"),
            ("HP",             "≥ 10,000","低"),
        ],
    },
    {
        "name": "ビビアン", "slug": "vivian", "rarity": "S",
        "element": "エーテル", "specialty": "アノマリー",
        "stats": [
            ("異常マスタリー","≥ 350",   "高"),
            ("攻撃力",       "≥ 2,400", "高"),
            ("会心率",       "≥ 55%",   "中"),
            ("エーテル強化", "≥ 25%",   "中"),
        ],
    },
    {
        "name": "浮波柚葉", "slug": "yuzuha", "rarity": "S",
        "element": "氷", "specialty": "サポート",
        "stats": [
            ("攻撃力",         "≥ 2,400", "高"),
            ("エネルギー回復", "≥ 125%",  "高"),
            ("氷ダメージ強化", "≥ 15%",   "中"),
            ("会心率",         "≥ 40%",   "低"),
        ],
    },
    {
        "name": "儀玄 (イーシェン)", "slug": "yixuan", "rarity": "S",
        "element": "玄墨", "specialty": "ラプチャー",
        "stats": [
            ("会心率",         "≥ 70%",   "高"),
            ("会心ダメージ",   "≥ 180%",  "高"),
            ("HP",             "≥ 11,000","中"),
            ("玄墨強化",       "≥ 30%",   "中"),
        ],
    },
    {
        "name": "葉瞬光 (ヨウ・シュンコウ)", "slug": "ye-shunguang", "rarity": "S",
        "element": "凛刃", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 70%",   "高"),
            ("会心ダメージ",   "≥ 200%",  "高"),
            ("攻撃力",         "≥ 2,600", "中"),
            ("貫通比率",       "≥ 25%",   "中"),
        ],
    },
    {
        "name": "ヒューゴ", "slug": "hugo", "rarity": "S",
        "element": "氷", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 70%",   "高"),
            ("会心ダメージ",   "≥ 200%",  "高"),
            ("攻撃力",         "≥ 2,500", "中"),
            ("氷ダメージ強化", "≥ 30%",   "中"),
        ],
    },
    {
        "name": "アリス", "slug": "alice", "rarity": "S",
        "element": "エーテル", "specialty": "アノマリー",
        "stats": [
            ("異常マスタリー","≥ 350",   "高"),
            ("攻撃力",       "≥ 2,300", "高"),
            ("会心率",       "≥ 55%",   "中"),
            ("エーテル強化", "≥ 25%",   "中"),
        ],
    },
    {
        "name": "プルクラ", "slug": "pulchra", "rarity": "S",
        "element": "物理", "specialty": "アノマリー",
        "stats": [
            ("異常マスタリー","≥ 350",   "高"),
            ("攻撃力",       "≥ 2,200", "高"),
            ("会心率",       "≥ 55%",   "中"),
            ("物理ダメージ強化","≥ 25%","中"),
        ],
    },
    {
        "name": "オルペウス&「鬼火」", "slug": "orphie-magus", "rarity": "S",
        "element": "エーテル", "specialty": "サポート",
        "stats": [
            ("攻撃力",         "≥ 2,500", "高"),
            ("エネルギー回復", "≥ 130%",  "高"),
            ("会心率",         "≥ 40%",   "中"),
        ],
    },
    {
        "name": "リュシア", "slug": "lucia", "rarity": "S",
        "element": "炎", "specialty": "アノマリー",
        "stats": [
            ("異常マスタリー","≥ 350",   "高"),
            ("攻撃力",       "≥ 2,200", "高"),
            ("炎ダメージ強化","≥ 25%",  "中"),
            ("会心率",       "≥ 50%",   "低"),
        ],
    },
    {
        "name": "0号・アンビー", "slug": "anby-soldier-0", "rarity": "S",
        "element": "雷", "specialty": "スタン",
        "stats": [
            ("衝撃力",       "≥ 190",   "高"),
            ("会心率",       "≥ 55%",   "高"),
            ("攻撃力",       "≥ 2,000", "中"),
            ("雷ダメージ強化","≥ 20%",  "中"),
        ],
    },
    # ─── Ver 2.4: ダイアリン/盤岳 ───
    {
        "name": "ダイアリン", "slug": "dialyn", "rarity": "S",
        "element": "物理", "specialty": "スタン",
        "stats": [
            ("会心率",       "≥ 100%",  "高"),
            ("衝撃力",       "≥ 180",   "高"),
            ("攻撃力",       "≥ 2,000", "中"),
            ("エネルギー回復","≥ 120%", "中"),
        ],
    },
    {
        "name": "盤岳 (バンガク)", "slug": "bangaku", "rarity": "S",
        "element": "エーテル", "specialty": "ラプチャー",
        "stats": [
            ("会心率",         "≥ 65%",   "高"),
            ("会心ダメージ",   "≥ 180%",  "高"),
            ("HP",             "≥ 10,000","中"),
            ("貫通比率",       "≥ 20%",   "中"),
        ],
    },
    # ─── Ver 2.4 後半: 照(ザオ) ───
    {
        "name": "照 (ザオ)", "slug": "zhao", "rarity": "S",
        "element": "エーテル", "specialty": "ディフェンス",
        "stats": [
            ("HP",             "≥ 11,500","高"),
            ("攻撃力",         "≥ 2,400", "高"),
            ("エネルギー回復", "≥ 120%",  "中"),
            ("会心率",         "≥ 40%",   "低"),
        ],
    },
    # ─── Ver 2.5: イドリー ───
    {
        "name": "イドリー", "slug": "evrard", "rarity": "S",
        "element": "氷", "specialty": "ラプチャー",
        "stats": [
            ("会心率",         "≥ 70%",   "高"),
            ("会心ダメージ",   "≥ 200%",  "高"),
            ("HP",             "≥ 12,000","中"),
            ("氷ダメージ強化", "≥ 30%",   "中"),
        ],
    },
    # ─── Ver 2.6: 千夏/アリア ───
    {
        "name": "千夏 (チナツ)", "slug": "chinatsu", "rarity": "S",
        "element": "エーテル", "specialty": "ディフェンス",
        "stats": [
            ("HP",             "≥ 12,000","高"),
            ("攻撃力",         "≥ 2,200", "高"),
            ("エネルギー回復", "≥ 125%",  "中"),
            ("会心率",         "≥ 35%",   "低"),
        ],
    },
    {
        "name": "アリア", "slug": "aria", "rarity": "S",
        "element": "エーテル", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 70%",   "高"),
            ("会心ダメージ",   "≥ 200%",  "高"),
            ("攻撃力",         "≥ 2,500", "中"),
            ("エーテル強化",   "≥ 30%",   "中"),
        ],
    },
    # ─── Ver 2.7: 南宮羽/シーシィア ───
    {
        "name": "南宮羽 (なんぐうゆう)", "slug": "nanguyu", "rarity": "S",
        "element": "氷", "specialty": "スタン",
        "stats": [
            ("異常掌握",     "≥ 200",   "高"),
            ("衝撃力",       "≥ 170",   "高"),
            ("異常マスタリー","≥ 350",  "中"),
            ("攻撃力",       "≥ 2,000", "中"),
        ],
    },
    {
        "name": "シーシィア", "slug": "cytheia", "rarity": "S",
        "element": "雷", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 65%",   "高"),
            ("会心ダメージ",   "≥ 200%",  "高"),
            ("攻撃力",         "≥ 2,500", "中"),
            ("雷ダメージ強化", "≥ 25%",   "中"),
        ],
    },
    # ─── Ver 2.8: プロメイア ───
    {
        "name": "プロメイア", "slug": "promeia", "rarity": "S",
        "element": "氷", "specialty": "アノマリー",
        "stats": [
            ("異常掌握",     "≥ 250",   "高"),
            ("攻撃力",       "≥ 2,400", "高"),
            ("会心率",       "≥ 55%",   "中"),
            ("氷ダメージ強化","≥ 25%",  "中"),
            ("エネルギー回復","≥ 115%", "低"),
        ],
    },
    # ─── Ver 2.0: 橘福福 ───
    {
        "name": "橘福福 (チーフーフー)", "slug": "trochee", "rarity": "S",
        "element": "炎", "specialty": "スタン",
        "stats": [
            ("衝撃力",       "≥ 180",   "高"),
            ("攻撃力",       "≥ 2,000", "高"),
            ("会心率",       "≥ 50%",   "中"),
            ("エネルギー回復","≥ 120%", "中"),
        ],
    },
    # ─── Ver 2.3: 狛野真斗 ───
    {
        "name": "狛野真斗 (こまのまなと)", "slug": "komano-manato", "rarity": "S",
        "element": "炎", "specialty": "ラプチャー",
        "stats": [
            ("会心率",         "≥ 65%",   "高"),
            ("会心ダメージ",   "≥ 180%",  "高"),
            ("HP",             "≥ 11,000","中"),
            ("炎ダメージ強化", "≥ 25%",   "中"),
        ],
    },

    # ━━━━━━━━━━━ A ランク ━━━━━━━━━━━
    {
        "name": "アンビー", "slug": "anby", "rarity": "A",
        "element": "雷", "specialty": "スタン",
        "stats": [
            ("衝撃力",       "≥ 170",   "高"),
            ("会心率",       "≥ 50%",   "中"),
            ("攻撃力",       "≥ 1,800", "中"),
            ("雷ダメージ強化","≥ 15%",  "低"),
            ("エネルギー回復","≥ 110%", "低"),
        ],
    },
    {
        "name": "ビリー", "slug": "billy", "rarity": "A",
        "element": "物理", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 65%",  "高"),
            ("会心ダメージ",   "≥ 180%", "高"),
            ("攻撃力",         "≥ 2,200","中"),
            ("物理ダメージ強化","≥ 25%", "低"),
        ],
    },
    {
        "name": "コリン", "slug": "corin", "rarity": "A",
        "element": "物理", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 65%",   "高"),
            ("会心ダメージ",   "≥ 180%",  "高"),
            ("攻撃力",         "≥ 2,000", "中"),
            ("物理ダメージ強化","≥ 25%",  "低"),
        ],
    },
    {
        "name": "グレース", "slug": "grace", "rarity": "A",
        "element": "雷", "specialty": "アノマリー",
        "stats": [
            ("異常マスタリー","≥ 300",   "高"),
            ("攻撃力",       "≥ 1,800", "高"),
            ("雷ダメージ強化","≥ 20%",  "中"),
            ("エネルギー回復","≥ 120%", "低"),
        ],
    },
    {
        "name": "クレタ", "slug": "koleda", "rarity": "A",
        "element": "炎", "specialty": "スタン",
        "stats": [
            ("衝撃力",       "≥ 170",   "高"),
            ("攻撃力",       "≥ 1,800", "中"),
            ("会心率",       "≥ 45%",   "中"),
            ("炎ダメージ強化","≥ 15%",  "低"),
        ],
    },
    {
        "name": "猫又", "slug": "nekomata", "rarity": "A",
        "element": "物理", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 65%",  "高"),
            ("会心ダメージ",   "≥ 180%", "高"),
            ("攻撃力",         "≥ 2,000","中"),
            ("物理ダメージ強化","≥ 25%", "低"),
        ],
    },
    {
        "name": "パイパー", "slug": "piper", "rarity": "A",
        "element": "物理", "specialty": "アノマリー",
        "stats": [
            ("異常マスタリー","≥ 300",   "高"),
            ("攻撃力",       "≥ 1,900", "高"),
            ("物理ダメージ強化","≥ 20%","中"),
            ("エネルギー回復","≥ 120%", "低"),
        ],
    },
    {
        "name": "ルーシー", "slug": "lucy", "rarity": "A",
        "element": "炎", "specialty": "サポート",
        "stats": [
            ("攻撃力",         "≥ 2,000", "高"),
            ("エネルギー回復", "≥ 120%",  "高"),
            ("炎ダメージ強化", "≥ 15%",   "中"),
            ("HP",             "≥ 8,000", "低"),
        ],
    },
    {
        "name": "「11号」", "slug": "soldier-11", "rarity": "A",
        "element": "炎", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 65%",   "高"),
            ("会心ダメージ",   "≥ 180%",  "高"),
            ("攻撃力",         "≥ 2,000", "中"),
            ("炎ダメージ強化", "≥ 25%",   "中"),
        ],
    },
    {
        "name": "アンドー", "slug": "anton", "rarity": "A",
        "element": "雷", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 65%",   "高"),
            ("会心ダメージ",   "≥ 180%",  "高"),
            ("攻撃力",         "≥ 2,000", "中"),
            ("雷ダメージ強化", "≥ 20%",   "低"),
        ],
    },
    {
        "name": "ベン", "slug": "ben", "rarity": "A",
        "element": "炎", "specialty": "ディフェンス",
        "stats": [
            ("HP",         "≥ 10,000", "高"),
            ("防御力",     "≥ 1,000",  "高"),
            ("衝撃力",     "≥ 130",    "中"),
            ("炎ダメージ強化","≥ 15%", "低"),
        ],
    },
    {
        "name": "ニコ", "slug": "nicole", "rarity": "A",
        "element": "エーテル", "specialty": "サポート",
        "stats": [
            ("攻撃力",         "≥ 1,800", "高"),
            ("エネルギー回復", "≥ 120%",  "中"),
            ("エーテル強化",   "≥ 15%",   "中"),
            ("異常マスタリー", "≥ 250",   "低"),
        ],
    },
    {
        "name": "セス", "slug": "seth", "rarity": "A",
        "element": "雷", "specialty": "ディフェンス",
        "stats": [
            ("HP",       "≥ 9,500",  "高"),
            ("防御力",   "≥ 900",    "高"),
            ("攻撃力",   "≥ 1,800",  "中"),
            ("エネルギー回復","≥ 120%","中"),
        ],
    },
    {
        "name": "カリン", "slug": "caesar-killer-karin", "rarity": "A",
        "element": "物理", "specialty": "アタック",
        "stats": [
            ("会心率",         "≥ 65%",   "高"),
            ("会心ダメージ",   "≥ 180%",  "高"),
            ("攻撃力",         "≥ 2,000", "中"),
            ("物理ダメージ強化","≥ 25%",  "低"),
        ],
    },
    {
        "name": "潘引壺 (パン)", "slug": "pan-yinhu", "rarity": "A",
        "element": "物理", "specialty": "ラプチャー",
        "stats": [
            ("攻撃力",         "≥ 1,800", "高"),
            ("HP",             "≥ 9,000", "中"),
            ("エネルギー回復", "≥ 120%",  "中"),
            ("会心率",         "≥ 45%",   "低"),
        ],
    },
]


# ═══════════════════════════════════════════════════════════
#  アイコン処理
# ═══════════════════════════════════════════════════════════
CACHE_DIR = Path.home() / ".zzz_stats_cache"
CACHE_DIR.mkdir(exist_ok=True)


def make_circular(img: Image.Image, size: int, border_color: str) -> Image.Image:
    """画像を円形にして外枠を追加"""
    img = img.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([1, 1, size - 2, size - 2], fill=255)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, mask=mask)
    draw = ImageDraw.Draw(result)
    draw.ellipse([1, 1, size - 2, size - 2], outline=border_color, width=3)
    return result


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def generate_fallback_icon(char: dict, size: int = 72) -> Image.Image:
    """画像が取得できない場合の代替アイコン生成（オフラインモード用）"""
    fg, bg = ELEM_COLORS.get(char["element"], ("#888888", "#222222"))
    rarity_clr = RARE_COLORS.get(char["rarity"], "#888")

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 内側ラジアルグラデーション風(2層楕円)
    bg_rgb = _hex_to_rgb(bg)
    fg_rgb = _hex_to_rgb(fg)
    mid = tuple((b + f) // 4 + b // 2 for b, f in zip(bg_rgb, fg_rgb))

    # 大きい暗い円（背景）
    draw.ellipse([2, 2, size - 3, size - 3], fill=bg)
    # 中間色の小さな円(光彩風)
    inset = size // 5
    draw.ellipse([inset, inset, size - inset - 1, size - inset - 1],
                 fill=mid)

    # 外枠（レアリティ）
    draw.ellipse([1, 1, size - 2, size - 2], outline=rarity_clr, width=3)
    # 内枠(属性)
    draw.ellipse([4, 4, size - 5, size - 5], outline=fg, width=1)

    # イニシャル文字
    initial = char["name"][0]
    # 「ジェ」「シー」など複合英字始まりも考慮
    if char["name"].startswith(("[", "(")):
        initial = char["name"][1] if len(char["name"]) > 1 else "?"

    font_size = int(size * 0.42)
    font = get_jp_font(font_size)
    bbox = draw.textbbox((0, 0), initial, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1] - 2

    # 影付きテキスト
    draw.text((tx + 1, ty + 2), initial, fill="#000000A0", font=font)
    draw.text((tx, ty), initial, fill=fg, font=font)

    return img


def _build_browser_session() -> requests.Session:
    """画像取得用のセッション(複数ソース対応)"""
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    })
    return s


# ──────────────────────────────────────────
# キャラごとのFandom画像ファイル名マッピング
# 公式英名 → ファイル名(Agent_XXX_Icon.png)パターン
# ──────────────────────────────────────────
FANDOM_NAMES = {
    "miyabi":         "Hoshimi_Miyabi",
    "ellen":          "Ellen_Joe",
    "zhu-yuan":       "Zhu_Yuan",
    "rina":           "Alexandrina_Sebastiane",
    "soukaku":        "Soukaku",
    "lycaon":         "Von_Lycaon",
    "jane-doe":       "Jane_Doe",
    "burnice":        "Burnice_White",
    "caesar":         "Caesar_King",
    "lighter":        "Lighter",
    "yanagi":         "Tsukishiro_Yanagi",
    "harumasa":       "Asaba_Harumasa",
    "evelyn":         "Evelyn_Chevalier",
    "trigger":        "Trigger",
    "qingyi":         "Qingyi",
    "astra-yao":      "Astra_Yao",
    "vivian":         "Vivian_Banshee",
    "yuzuha":         "Ukinami_Yuzuha",
    "yixuan":         "Yixuan",
    "ye-shunguang":   "Ye_Shunguang",
    "hugo":           "Hugo_Vlad",
    "alice":          "Alice_Thymefield",
    "pulchra":        "Pulchra_Fellini",
    "orphie-magus":   "Orphie",
    "lucia":          "Lucia_de_Montefio",
    "anby-soldier-0": "Soldier_0_-_Anby",
    # ─── 新規追加 ───
    "dialyn":          "Dialyn",
    "bangaku":         "Pan_Yinhu",  # 暫定; 後で正確な名前に
    "zhao":            "Zhao",
    "evrard":          "Evrard",
    "chinatsu":        "Chinatsu",
    "aria":            "Aria",
    "nanguyu":         "Nangong_Yu",
    "cytheia":         "Cytheia",
    "promeia":         "Promeia",
    "trochee":         "Trochee",
    "komano-manato":   "Komano_Manato",
    # ─── Aランク ───
    "anby":           "Anby_Demara",
    "billy":          "Billy_Kid",
    "corin":          "Corin_Wickes",
    "grace":          "Grace_Howard",
    "koleda":         "Koleda_Belobog",
    "nekomata":       "Nekomata",
    "piper":          "Piper_Wheel",
    "lucy":           "Lucy",
    "soldier-11":     "Soldier_11",
    "anton":          "Anton_Ivanov",
    "ben":            "Ben_Bigger",
    "nicole":         "Nicole_Demara",
    "seth":           "Seth_Lowell",
    "caesar-killer-karin": "Karin",
    "pan-yinhu":       "Pan_Yinhu",
}


def _try_fandom_api(session: requests.Session, fandom_name: str) -> str:
    """Fandom MediaWiki APIで画像の直接URLを取得"""
    # Agent_<Name>_Icon.png を試す
    candidates = [
        f"Agent_{fandom_name}_Icon.png",
        f"Agent_{fandom_name}_Profile.png",
        f"Agent_{fandom_name}_Card.png",
        f"Agent_{fandom_name}_Avatar.png",
    ]
    api_url = "https://zenless-zone-zero.fandom.com/api.php"

    for filename in candidates:
        try:
            params = {
                "action": "query",
                "titles": f"File:{filename}",
                "prop": "imageinfo",
                "iiprop": "url",
                "format": "json",
            }
            r = session.get(api_url, params=params, timeout=8)
            if r.status_code != 200:
                continue
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            for _, page in pages.items():
                if "imageinfo" in page:
                    url = page["imageinfo"][0].get("url")
                    if url:
                        return url
        except Exception:
            continue
    return ""


def _try_hoyolab_api(session: requests.Session, slug: str) -> str:
    """HoYoLABのAPIから画像URLを取得 (バックアップ)"""
    # HoYoLAB wiki has a public agent list endpoint
    # 一覧APIから取得 (ライセンス上, 公開情報のみアクセス)
    try:
        r = session.get(
            "https://sg-wiki-api-static.hoyolab.com/hoyowiki/zzz/wapi/get_entry_page_list",
            params={"app_sn": "zzz_global", "filters": "", "menu_id": "8", "page_num": "1", "page_size": "50"},
            headers={"x-rpc-language": "en-us", "x-rpc-wiki_app": "zzz"},
            timeout=8,
        )
        if r.status_code == 200:
            data = r.json()
            for entry in data.get("data", {}).get("list", []):
                name = (entry.get("name") or "").lower().replace(" ", "-")
                if slug in name or name.replace("-", "") in slug.replace("-", ""):
                    icon = entry.get("icon_url")
                    if icon:
                        return icon
    except Exception:
        pass
    return ""


def fetch_character_icon(char: dict, size: int = 72) -> Image.Image:
    """複数ソースからアイコン取得 / 失敗時はフォールバック生成"""
    slug = char["slug"]
    cache_file = CACHE_DIR / f"{slug}_{size}.png"

    # ── 1. キャッシュ確認 ──
    if cache_file.exists():
        try:
            return Image.open(cache_file).convert("RGBA")
        except Exception:
            pass

    rarity_clr = RARE_COLORS.get(char["rarity"], "#888")
    session = _build_browser_session()
    log_file = CACHE_DIR / "fetch_log.txt"
    errors = []

    # ── 2. 取得を試行する画像URLのリスト ──
    candidate_urls = []

    # Fandom API経由(最も信頼性が高い)
    fandom_name = FANDOM_NAMES.get(slug)
    if fandom_name:
        url = _try_fandom_api(session, fandom_name)
        if url:
            candidate_urls.append(("fandom", url))

    # HoYoLAB
    url = _try_hoyolab_api(session, slug)
    if url:
        candidate_urls.append(("hoyolab", url))

    # フォールバック: 直接Prydwen
    candidate_urls.extend([
        ("prydwen", f"https://www.prydwen.gg/static/img/zzz/characters/{slug}.webp"),
        ("prydwen-card", f"https://www.prydwen.gg/static/img/zzz/characters/{slug}_card.webp"),
    ])

    for source, url in candidate_urls:
        try:
            r = session.get(url, timeout=10)
            if r.status_code == 200 and len(r.content) > 800:
                try:
                    img = Image.open(io.BytesIO(r.content)).convert("RGBA")
                    result = make_circular(img, size, rarity_clr)
                    try:
                        result.save(cache_file, "PNG")
                    except Exception:
                        pass
                    return result
                except Exception as ex:
                    errors.append(f"{source}: image parse error: {ex}")
            else:
                errors.append(f"{source}: HTTP {r.status_code}")
        except Exception as ex:
            errors.append(f"{source}: {type(ex).__name__}: {ex}")

    # ── 3. ログ書き込み(全失敗時のみ) ──
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{slug}] {char['name']}\n")
            for err in errors:
                f.write(f"  - {err}\n")
    except Exception:
        pass

    # ── 4. 全失敗 → 生成フォールバック ──
    return generate_fallback_icon(char, size)


# ═══════════════════════════════════════════════════════════
#  メインアプリ
# ═══════════════════════════════════════════════════════════
class ZZZStatsApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("⬡  ゼンレスゾーンゼロ  理想ステータス一覧")
        self.root.geometry("1480x920")
        self.root.minsize(1000, 600)
        self.root.configure(bg=BG_MAIN)

        # アプリ状態
        self.all_chars = list(CHARACTERS)
        self.filtered = list(self.all_chars)
        self.icon_cache: dict = {}        # name -> ImageTk.PhotoImage
        self.icon_labels: dict = {}       # name -> tk.Label

        self.filter_elem = tk.StringVar(value="全て")
        self.filter_spec = tk.StringVar(value="全て")
        self.filter_rare = tk.StringVar(value="全て")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *_: self._apply_filters())

        # スクロール状態管理(ホバーチラつき防止)
        self._is_scrolling = False
        self._scroll_after_id = None
        self._hovered_row = None

        self._build_ui()
        self._render_rows()
        self._start_background_tasks()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UI 構築
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_ui(self):
        # ── ヘッダー ──
        header = tk.Frame(self.root, bg=BG_PANEL, height=66)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg=BG_PANEL)
        title_frame.pack(side="left", padx=24, pady=12)
        tk.Label(title_frame, text="⬡", bg=BG_PANEL, fg=ACCENT,
                 font=tk_font(20, True)).pack(side="left", padx=(0, 8))
        tk.Label(title_frame, text="ゼンレスゾーンゼロ  理想ステータス",
                 bg=BG_PANEL, fg=TEXT_PRI,
                 font=tk_font(15, True)).pack(side="left")
        tk.Label(title_frame, text="  ZZZ Ideal Stats",
                 bg=BG_PANEL, fg=TEXT_TER,
                 font=tk_font(10)).pack(side="left", padx=(8, 0))

        # 右側ステータス
        right = tk.Frame(header, bg=BG_PANEL)
        right.pack(side="right", padx=24)
        tk.Label(right, text="優先度:", bg=BG_PANEL, fg=TEXT_SEC,
                 font=tk_font(9)).pack(side="left", padx=(0, 8))
        for prio, clr in PRIO_COLORS.items():
            f = tk.Frame(right, bg=BG_PANEL); f.pack(side="left", padx=4)
            tk.Frame(f, bg=clr, width=10, height=10).pack(side="left", padx=(0, 3), pady=4)
            tk.Label(f, text=prio, bg=BG_PANEL, fg=TEXT_PRI,
                     font=tk_font(9)).pack(side="left")

        self.status_indicator = tk.Label(
            right, text="  🔄 起動中...", bg=BG_PANEL, fg=ACCENT2,
            font=tk_font(9))
        self.status_indicator.pack(side="left", padx=(16, 0))

        # ── フィルターバー ──
        fbar = tk.Frame(self.root, bg=BG_MAIN, pady=12)
        fbar.pack(fill="x", padx=16)

        # 検索ボックス
        sframe = tk.Frame(fbar, bg=BG_CARD, highlightthickness=1,
                          highlightbackground=BORDER)
        sframe.pack(side="left", padx=(0, 12))
        tk.Label(sframe, text="🔍", bg=BG_CARD, fg=TEXT_SEC,
                 font=tk_font(11)).pack(side="left", padx=(8, 4))
        sentry = tk.Entry(sframe, textvariable=self.search_var,
                          bg=BG_CARD, fg=TEXT_PRI,
                          insertbackground=TEXT_PRI,
                          relief="flat", width=14,
                          font=tk_font(10))
        sentry.pack(side="left", pady=6, padx=(0, 8))

        # 属性フィルター
        tk.Label(fbar, text="属性:", bg=BG_MAIN, fg=TEXT_SEC,
                 font=tk_font(10)).pack(side="left", padx=(4, 6))
        self.elem_buttons = {}
        for elem in ["全て", "氷", "霜", "炎", "雷", "物理", "エーテル", "玄墨", "凛刃"]:
            btn = tk.Button(
                fbar, text=elem,
                bg=ACCENT if elem == "全て" else BG_CARD,
                fg=BG_MAIN if elem == "全て" else TEXT_PRI,
                relief="flat", cursor="hand2",
                padx=10, pady=4, bd=0,
                font=tk_font(9, bold=(elem == "全て")),
                activebackground=BG_HOVER,
                command=lambda e=elem: self._set_filter("elem", e),
            )
            btn.pack(side="left", padx=2)
            self.elem_buttons[elem] = btn

        # 役割フィルター
        tk.Label(fbar, text="  役割:", bg=BG_MAIN, fg=TEXT_SEC,
                 font=tk_font(10)).pack(side="left", padx=(8, 6))
        self.spec_buttons = {}
        for spec in ["全て", "アタック", "スタン", "アノマリー", "サポート", "ディフェンス", "ラプチャー"]:
            btn = tk.Button(
                fbar, text=spec,
                bg=ACCENT if spec == "全て" else BG_CARD,
                fg=BG_MAIN if spec == "全て" else TEXT_PRI,
                relief="flat", cursor="hand2",
                padx=8, pady=4, bd=0,
                font=tk_font(9, bold=(spec == "全て")),
                activebackground=BG_HOVER,
                command=lambda s=spec: self._set_filter("spec", s),
            )
            btn.pack(side="left", padx=2)
            self.spec_buttons[spec] = btn

        # レアリティフィルター
        tk.Label(fbar, text="  ★:", bg=BG_MAIN, fg=TEXT_SEC,
                 font=tk_font(10)).pack(side="left", padx=(8, 4))
        self.rare_buttons = {}
        for rare in ["全て", "S", "A"]:
            clr = RARE_COLORS.get(rare, ACCENT)
            btn = tk.Button(
                fbar, text=rare,
                bg=ACCENT if rare == "全て" else BG_CARD,
                fg=BG_MAIN if rare == "全て" else clr,
                relief="flat", cursor="hand2",
                padx=10, pady=4, bd=0,
                font=tk_font(9, True),
                activebackground=BG_HOVER,
                command=lambda r=rare: self._set_filter("rare", r),
            )
            btn.pack(side="left", padx=2)
            self.rare_buttons[rare] = btn

        # ── テーブルヘッダー ──
        thead = tk.Frame(self.root, bg=BG_PANEL, height=36)
        thead.pack(fill="x", padx=16)
        thead.pack_propagate(False)

        # 各列幅
        col_widths = [(298, "キャラクター"), (218, "ステータス ①"),
                      (218, "ステータス ②"), (218, "ステータス ③"),
                      (218, "ステータス ④"), (200, "ステータス ⑤")]
        for w, label in col_widths:
            f = tk.Frame(thead, bg=BG_PANEL, width=w)
            f.pack(side="left", fill="y")
            f.pack_propagate(False)
            tk.Label(f, text=label, bg=BG_PANEL, fg=ACCENT,
                     font=tk_font(9, True), anchor="w"
                     ).pack(side="left", padx=12, pady=8, fill="y")

        # ── スクロール可能リスト ──
        listwrap = tk.Frame(self.root, bg=BG_MAIN)
        listwrap.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        self.canvas = tk.Canvas(listwrap, bg=BG_MAIN, bd=0,
                                highlightthickness=0)
        sb = tk.Scrollbar(listwrap, orient="vertical",
                          command=self.canvas.yview,
                          bg=BG_PANEL, troughcolor=BG_MAIN,
                          activebackground=ACCENT, bd=0,
                          width=12)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.row_container = tk.Frame(self.canvas, bg=BG_MAIN)
        self._cwin_id = self.canvas.create_window(
            (0, 0), window=self.row_container, anchor="nw")

        self.row_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")))
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(
                self._cwin_id, width=e.width))

        # マウスホイール
        self.canvas.bind_all("<MouseWheel>", self._on_scroll)
        self.canvas.bind_all("<Button-4>", self._on_scroll)
        self.canvas.bind_all("<Button-5>", self._on_scroll)

        # ── ステータスバー ──
        self.statusbar = tk.Label(
            self.root, text="", bg=BG_PANEL, fg=TEXT_SEC,
            font=tk_font(9), anchor="w", padx=16, pady=4)
        self.statusbar.pack(fill="x")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 行レンダリング
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _render_rows(self):
        for child in self.row_container.winfo_children():
            child.destroy()
        self.icon_labels.clear()
        self._hovered_row = None  # 古い行への参照をクリア

        for idx, char in enumerate(self.filtered):
            self._build_row(idx, char)

        total = len(self.all_chars)
        shown = len(self.filtered)
        self.statusbar.config(
            text=f"  表示: {shown} / {total} 体   "
                 f"データ: 内蔵 + Prydwen.gg 連携   "
                 f"アイコンキャッシュ: {CACHE_DIR}")

    def _build_row(self, idx: int, char: dict):
        bg = BG_CARD if idx % 2 == 0 else BG_CARD2
        row = tk.Frame(self.row_container, bg=bg, height=88)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        row._base_bg = bg  # 元の背景色を覚えておく

        # ホバー(スクロール中はスキップしてチラつきを防止)
        def on_enter(_):
            if self._is_scrolling:
                return
            if self._hovered_row is row:
                return
            # 直前にホバーされていた行をリセット
            if self._hovered_row is not None and self._hovered_row.winfo_exists():
                prev_bg = getattr(self._hovered_row, "_base_bg", BG_CARD)
                _set_bg_recursive(self._hovered_row, prev_bg)
            self._hovered_row = row
            _set_bg_recursive(row, BG_HOVER)

        def on_leave(_):
            if self._is_scrolling:
                return
            if self._hovered_row is row:
                _set_bg_recursive(row, bg)
                self._hovered_row = None

        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)

        elem_fg, _ = ELEM_COLORS.get(char["element"], ("#888", "#222"))

        # 属性ラインインジケーター
        tk.Frame(row, bg=elem_fg, width=4).pack(side="left", fill="y")

        # ── キャラクター列 (合計294px) ──
        char_col = tk.Frame(row, bg=bg, width=294)
        char_col.pack(side="left", fill="y")
        char_col.pack_propagate(False)

        # アイコンエリア
        icon_frame = tk.Frame(char_col, bg=bg, width=82, height=82)
        icon_frame.pack(side="left", padx=(10, 8), pady=4)
        icon_frame.pack_propagate(False)

        # プレースホルダー（後で画像差し替え）
        placeholder = generate_fallback_icon(char, 72)
        ph_img = ImageTk.PhotoImage(placeholder)
        self.icon_cache[f"_ph_{char['slug']}"] = ph_img  # GCを防ぐ
        ilbl = tk.Label(icon_frame, image=ph_img, bg=bg, bd=0)
        ilbl.place(relx=0.5, rely=0.5, anchor="center")
        self.icon_labels[char["slug"]] = ilbl

        # 名前&バッジ
        info_col = tk.Frame(char_col, bg=bg)
        info_col.pack(side="left", fill="both", expand=True, pady=12)

        name_row = tk.Frame(info_col, bg=bg)
        name_row.pack(anchor="w", fill="x")
        rare_clr = RARE_COLORS.get(char["rarity"], TEXT_SEC)
        tk.Label(name_row, text=f"[{char['rarity']}]",
                 bg=bg, fg=rare_clr,
                 font=tk_font(9, True)).pack(side="left")
        tk.Label(name_row, text=f" {char['name']}",
                 bg=bg, fg=TEXT_PRI,
                 font=tk_font(11, True)).pack(side="left")

        # 属性 + 役割バッジ
        badge_row = tk.Frame(info_col, bg=bg)
        badge_row.pack(anchor="w", pady=(4, 0))
        spec_clr = SPEC_COLORS.get(char["specialty"], TEXT_SEC)
        _make_badge(badge_row, char["element"], elem_fg)
        _make_badge(badge_row, char["specialty"], spec_clr)

        # ── ステータス列 (各218 / 最後の1つは200) ──
        col_widths = [218, 218, 218, 218, 200]
        for i, w in enumerate(col_widths):
            scol = tk.Frame(row, bg=bg, width=w)
            scol.pack(side="left", fill="y")
            scol.pack_propagate(False)

            if i < len(char["stats"]):
                sname, sval, prio = char["stats"][i]
                self._build_stat_cell(scol, sname, sval, prio, bg)

    def _build_stat_cell(self, parent, sname, sval, prio, bg):
        inner = tk.Frame(parent, bg=bg)
        inner.place(relx=0, rely=0.5, anchor="w", x=12)

        # 優先度ドット
        prio_clr = PRIO_COLORS.get(prio, TEXT_SEC)
        dotframe = tk.Frame(inner, bg=bg)
        dotframe.pack(side="left", padx=(0, 8))
        tk.Frame(dotframe, bg=prio_clr, width=10, height=10).pack(pady=14)

        # ステータス名 + 値
        vf = tk.Frame(inner, bg=bg)
        vf.pack(side="left")
        tk.Label(vf, text=sname, bg=bg, fg=TEXT_SEC,
                 font=tk_font(8)).pack(anchor="w")
        tk.Label(vf, text=sval, bg=bg, fg=prio_clr,
                 font=tk_font(13, True)).pack(anchor="w")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # フィルター
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _set_filter(self, kind: str, value: str):
        if kind == "elem":
            self.filter_elem.set(value)
            _update_button_states(self.elem_buttons, value)
        elif kind == "spec":
            self.filter_spec.set(value)
            _update_button_states(self.spec_buttons, value)
        elif kind == "rare":
            self.filter_rare.set(value)
            _update_button_states(self.rare_buttons, value)
        self._apply_filters()

    def _apply_filters(self):
        q = self.search_var.get().strip().lower()
        e = self.filter_elem.get()
        s = self.filter_spec.get()
        r = self.filter_rare.get()
        self.filtered = [
            c for c in self.all_chars
            if (e == "全て" or c["element"] == e)
            and (s == "全て" or c["specialty"] == s)
            and (r == "全て" or c["rarity"] == r)
            and (not q or q in c["name"].lower() or q in c["slug"].lower())
        ]
        self._render_rows()
        self.canvas.yview_moveto(0)
        # フィルター変更後もアイコン読込再開
        threading.Thread(target=self._load_all_icons, daemon=True).start()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # スクロール
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _on_scroll(self, event):
        # スクロール中はホバーエフェクトを抑制(チラつき防止)
        self._is_scrolling = True
        if self._scroll_after_id:
            self.root.after_cancel(self._scroll_after_id)
        self._scroll_after_id = self.root.after(150, self._scroll_done)

        # スクロール量を正規化(Windows/Linux/Macで挙動を統一)
        if event.num == 4:
            delta = -2
        elif event.num == 5:
            delta = 2
        else:
            # Windowsでは event.delta は ±120の倍数
            delta = int(-1 * (event.delta / 120) * 2)
            if delta == 0:
                delta = -1 if event.delta > 0 else 1

        self.canvas.yview_scroll(delta, "units")

    def _scroll_done(self):
        self._is_scrolling = False
        self._scroll_after_id = None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # バックグラウンド処理
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _start_background_tasks(self):
        # 起動時に古いログをクリア
        try:
            log_file = CACHE_DIR / "fetch_log.txt"
            with open(log_file, "w", encoding="utf-8") as f:
                from datetime import datetime
                f.write(f"=== ZZZ Stats Viewer 起動 {datetime.now()} ===\n")
        except Exception:
            pass
        threading.Thread(target=self._load_all_icons, daemon=True).start()

    def _load_all_icons(self):
        total = len(self.filtered)
        success = 0
        failed = 0
        failed_names = []

        for i, char in enumerate(self.filtered):
            slug = char["slug"]
            if slug not in self.icon_labels:
                continue

            # 進捗表示
            progress_text = f"  🔄 アイコン取得中... ({i+1}/{total})"
            self.root.after(0, lambda t=progress_text: self.status_indicator.config(
                text=t, fg=ACCENT2))

            try:
                img = fetch_character_icon(char, 72)
                # 取得した画像が「生成フォールバック」かどうかを判定
                # キャッシュファイルが存在する場合は成功
                cache_file = CACHE_DIR / f"{slug}_72.png"
                if cache_file.exists():
                    success += 1
                else:
                    failed += 1
                    failed_names.append(char["name"])

                tk_img = ImageTk.PhotoImage(img)
                self.icon_cache[slug] = tk_img
                self.root.after(0, self._apply_icon, slug, tk_img)
            except Exception as ex:
                failed += 1
                failed_names.append(char["name"])
                print(f"アイコン取得失敗 {slug}: {ex}")

        # 完了通知
        if failed == 0:
            msg = f"  ✅ アイコン取得完了 ({success}/{total})"
            color = "#5BE584"
        elif success == 0:
            msg = f"  ⚠️ アイコン取得失敗 - ネット未接続? (0/{total})"
            color = "#FF6B3D"
        else:
            msg = f"  ⚠️ 一部失敗 ({success}/{total} 取得)"
            color = "#FFB840"

        self.root.after(0, lambda: self.status_indicator.config(
            text=msg, fg=color))

        # ステータスバーに詳細
        if failed > 0 and failed_names:
            sample = ", ".join(failed_names[:3])
            if len(failed_names) > 3:
                sample += f" 他{len(failed_names)-3}件"
            self.root.after(0, lambda: self.statusbar.config(
                text=f"  ⚠️ アイコン未取得: {sample}   "
                     f"キャッシュ: {CACHE_DIR}"))

    def _apply_icon(self, slug: str, tk_img):
        lbl = self.icon_labels.get(slug)
        if lbl and lbl.winfo_exists():
            lbl.config(image=tk_img)

    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════
#  ユーティリティ
# ═══════════════════════════════════════════════════════════
def _set_bg_recursive(widget, color):
    """ホバー時の背景変更。badgeタグ付き要素はスキップして色を保持"""
    try:
        # _badge属性を持つ要素はバッジなのでスキップ
        if getattr(widget, "_is_badge", False):
            return
        widget.config(bg=color)
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        cls = child.winfo_class()
        if cls in ("Frame", "Label"):
            if getattr(child, "_is_badge", False):
                continue  # バッジ要素はスキップ
            try:
                child.config(bg=color)
            except tk.TclError:
                pass
            _set_bg_recursive(child, color)


def _make_badge(parent, text, color):
    """属性/役割バッジ。border付きで全色で視認性確保、hover時も色を保持"""
    frame = tk.Frame(parent, bg=color, highlightthickness=0, bd=0)
    frame._is_badge = True  # hover時にスキップさせるためのマーク
    frame.pack(side="left", padx=(0, 5))
    lbl = tk.Label(frame, text=f" {text} ", bg=color, fg=BG_MAIN,
                   font=tk_font(8, True),
                   padx=3, pady=1)
    lbl._is_badge = True
    lbl.pack()


def _update_button_states(buttons: dict, selected: str):
    for key, btn in buttons.items():
        if key == selected:
            btn.config(bg=ACCENT, fg=BG_MAIN, font=tk_font(9, True))
        else:
            # レアリティはキー文字色を維持
            if key in RARE_COLORS:
                btn.config(bg=BG_CARD, fg=RARE_COLORS[key],
                           font=tk_font(9, True))
            else:
                btn.config(bg=BG_CARD, fg=TEXT_PRI,
                           font=tk_font(9))


# ═══════════════════════════════════════════════════════════
#  エントリーポイント
# ═══════════════════════════════════════════════════════════
def main():
    try:
        app = ZZZStatsApp()
        app.run()
    except Exception as ex:
        try:
            messagebox.showerror("エラー", f"起動に失敗しました:\n{ex}")
        except Exception:
            print(f"FATAL: {ex}")
        raise


if __name__ == "__main__":
    main()
