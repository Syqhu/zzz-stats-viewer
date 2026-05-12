# ⬡ ZZZ Stats Viewer — ゼンレスゾーンゼロ 理想ステータス一覧

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

ゼンレスゾーンゼロ (Zenless Zone Zero) のエージェント理想ステータスを一覧表示する**シンプルなデスクトップGUIツール**です。

![スクリーンショット](docs/screenshots/main.png)

## 特徴

**52体のエージェント収録** (Ver2.8時点)
**属性カラーリング** — 氷/炎/雷/物理/エーテル/霜/玄墨/凛刃を視覚化
**3軸フィルター** — 属性 × 役割 × レアリティ で絞り込み + 名前検索
**優先度マーカー** — 各ステータスに高/中/低の色付きドット
**オフライン動作** — ネットなしでもフォールバックアイコンで動作

##  ダウンロード & 使い方

### 方法A: Pythonランチャー版(ビルド不要)

1. [Python 3.10+](https://www.python.org/downloads/) をインストール (Add to PATH 必須)
2. このリポジトリを Code → Download ZIP でダウンロード
3. ZIPを展開し、`launcher` フォルダ内の **`setup.bat`** をダブルクリック (初回のみ)
4. **`start.bat`** をダブルクリックで起動

### 方法B: Pythonコマンドで実行

```bash
git clone https://github.com/YOURNAME/zzz-stats-viewer.git
cd zzz-stats-viewer
pip install -r requirements.txt
python zzz_stats_viewer.py
```

### 方法C: 自分でEXE化する

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "ZZZ_Stats" zzz_stats_viewer.py
# dist/ZZZ_Stats.exe が生成される
```

##  機能

### フィルタリング
- **属性**: 全て / 氷 / 霜 / 炎 / 雷 / 物理 / エーテル / 玄墨 / 凛刃
- **役割**: 全て / アタック / スタン / アノマリー / サポート / ディフェンス / ラプチャー
- **レアリティ**: 全て / S / A
- **名前検索**: 日本語名 / 英名(slug)でリアルタイム絞り込み

### 表示内容
- レアリティ + 名前 + 属性 + 役割 + 理想ステータス×5
- 優先度ドット(🔴高 🟡中 🟢低) で各ステータスの重要度を可視化

## 📊 データソース

- **ステータス値**: [Prydwen.gg](https://www.prydwen.gg/zenless/) / [game8.jp](https://game8.jp/zenless) / [wikiwiki.jp/zenless](https://wikiwiki.jp/zenless/) の公開ビルドガイドを基に整理
- **キャラアイコン**: [Fandom ZZZ Wiki](https://zenless-zone-zero.fandom.com/) MediaWiki API経由 (起動時自動取得)

最新パッチでデータが古くなった場合、`zzz_stats_viewer.py` 内の `CHARACTERS` リストを直接編集してください。Pull Request も歓迎します!

##  開発

### 必要環境
- Python 3.10 以降
- Tkinter (標準搭載、Ubuntuは `apt install python3-tk`)
- 依存ライブラリ: `requests`, `Pillow`, `beautifulsoup4`

### キャラ追加方法

`zzz_stats_viewer.py` 内の `CHARACTERS` リストに辞書を追加するだけ:

```python
{
    "name": "新キャラ名",
    "slug": "new-char-slug",
    "rarity": "S",           # "S" or "A"
    "element": "氷",          # 氷/炎/雷/物理/エーテル/霜/玄墨/凛刃
    "specialty": "アタック",   # アタック/スタン/アノマリー/サポート/ディフェンス/ラプチャー
    "stats": [
        ("会心率",       "≥ 70%",   "高"),  # (名前, 値, 優先度) のタプル
        ("会心ダメージ", "≥ 140%",  "高"),
        ("攻撃力",       "≥ 2,500", "中"),
    ],
},
```

`FANDOM_NAMES` 辞書にも英語名を追加するとアイコン取得対象になります。

##  既知の問題

| 症状 | 対処 |
|---|---|
| アイコンが取得できない | ネット接続を確認、`%USERPROFILE%\.zzz_stats_cache\fetch_log.txt` のエラー内容を確認 |
| `pip is not recognized` | `python -m pip install ...` を使う (詳細は `launcher/setup_必要なら実行.bat`) |
| 日本語が文字化け | Yu Gothic UI フォントを利用、Linuxは `fonts-noto-cjk` をインストール |



##  コントリビュート

Pull Request 歓迎です! 特にこんな貢献を求めています:
- 新キャラ実装時のステータスデータ追加
- 既存データの誤りの修正
- 多言語対応
- バグ修正・UI改善

## ライセンス

[MIT License](LICENSE)

##  免責事項

このツールはファンメイドであり、**miHoYo / HoYoverse / COGNOSPHERE による公式なものではありません**。
「ゼンレスゾーンゼロ」および関連する全ての名称・画像・キャラクターは各権利者に帰属します。

---

