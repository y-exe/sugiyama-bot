<div align="center">

# 杉山啓太Bot (ymkw.py)

多機能Bot（笑）<br>
杉山啓太がGM雑談ライフをサポートします。<br>
AIに修正もらってたら自分でもわけわかめなコードになってました。

<img src="https://count.getloli.com/@yexe.net" alt="yexe.net 総合カウンター"/><br>
<sub>yexe.net 総合</sub>

[![Discord.py](https://img.shields.io/badge/discord.py-v2.x-blue?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/en/latest/)
[![Python](https://img.shields.io/badge/Python-3.10.11-yellow?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/release/python-31011/)
[![Support Server](https://img.shields.io/badge/Support%20Server-Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/FXamRgKSph)
[![License](https://img.shields.io/badge/LICENSE-MIT-green.svg?style=for-the-badge)](LICENSE) 

</div>

## 概要

杉山啓太Bot (`ymkw.py`) は、Discordサーバーでの活動を多角的にサポートするために開発されたBotです。
GoogleのGemini AIによるテキスト生成や会話要約、RVC (Retrieval-based Voice Conversion) 技術を用いた音声変換、多彩な画像処理ユーティリティ、そしてインタラクティブなオセロゲームなど、幅広い機能を提供します。

コマンドの実行は、許可されたチャンネルでコマンド名（例: `totusi`）と引数を入力するだけで直感的に行えます (プレフィックス不要)。

## コマンドリスト(隠しコマンドも)

*   `watermark +[画像添付]`: 添付画像にウォーターマークを合成。
*   `/imakita`: 過去30分のチャットを3行で要約。(どこでも利用可)
*   `5000 [上文字列] [下文字列] (hoshii) (rainbow)`: 「5000兆円欲しい！」画像を生成。
*   `gaming +[画像添付]`: 添付画像をゲーミング風GIFに変換。
*   `othello (@相手ユーザー)`:
    *   `othello`: オセロの対戦相手を募集します。
    *   `othello @メンション`: 指定したユーザーと即時対戦を開始します。
    *   `leave` (または `othello leave`): 進行中のオセロゲームから離脱します。
    *   `point` (または `othello points`): あなたの現在のオセロポイントとランキングを表示します。
*   `voice +[音声ファイル添付]`: 添付音声の声をRVCでやまかわてるきの声に変換。（30秒まで）
*   `help`: このヘルプを表示。

**隠しコマンドについて:**
*   `ping`: Botの現在の応答速度 (レイテンシ) をミリ秒単位で表示します。
*   `tenki [都市名]` (または `weather [都市名]`): 指定された日本の都市の3日間の天気予報を表示します。
*   `info (@ユーザーメンションまたはユーザーID)`: 指定されたユーザー (またはコマンド実行者) の詳細情報を表示します。
*   `rate [金額] [3文字通貨コード]`: 指定した外貨の金額を現在のレートで日本円に換算して表示します。
*   `shorturl [URL]` (または `short [URL]`): 指定したURLをx.gdサービスを利用して短縮します。 (別途APIキーの設定が必要です)
*   `totusi [文字列]`: 入力した文字列を使って「＿人人人＿ ＞ 文字列 ＜ ￣Y^Y^Y￣」のようなAAを生成します。
*   `amazon [Amazon商品URL]`: Amazonの商品ページのURLを短縮URL (amzn.to) に変換します。

## 動作に必要なファイル配置

Botを正しく動作させるためには、以下のフォルダ構成とファイル配置が必要です。
ルートフォルダは `C:\Bot` を想定しています。

```bash
C:\Bot
├── ymkw.py # Bot本体のPythonスクリプト (このリポジトリから)
├── .env # APIキーなどを格納 (ユーザーが作成)
├── bot_settings.json # チャンネル制限設定 (空で作成 or 初回setchannelで自動生成)
├── othello_points.json # オセロのポイント記録 (空で作成 or 初回ポイント変動で自動生成)
├── assets\ # Bot用アセット (このリポジトリから、またはユーザーが用意)
│ └── watermark_templates
│ ├── POCO F3.png # ウォーターマーク用テンプレート画像 (例)
│ └── ... # 他のテンプレート画像
├── audio\ # RVCの一時音声ファイル用 (Botが自動生成)
│ ├── input
│ └── output
└── RVC_Project\ # RVC本体 (ユーザーが別途 git clone で取得)
├── tools
│ └── infer_cli.py # RVC推論スクリプト
├── assets
│ ├── hubert
│ │ └── hubert_base.pt # HuBERTモデル (ユーザーが別途ダウンロード・配置)
│ └── weights
│ └── ymkw.pth # RVC学習済みモデル (ユーザーが用意・配置)
│ └── ymkw.index # RVC学習済みモデルのインデックス (例, あれば)
├── requirements.txt # RVCのPython依存ライブラリリスト
├── venv\ # Python共有仮想環境 (ユーザーが作成・設定)
└── ... # RVCのその他ファイル群
```

(各ファイル/フォルダの詳細は以前の回答を参照してください)

## 導入手順 (Windows CPU環境向け)

### I. 事前準備: 必要なソフトウェアのインストール

1.  **Python 3.10.11 (または3.10.x):** [python.org](https://www.python.org/downloads/release/python-31011/) より入手し、インストール時に **「Add Python to PATH」に必ずチェック**。
2.  **Git:** [git-scm.com](https://git-scm.com/downloads) より入手し、インストール。
3.  **FFmpeg:** [ffmpeg.org](https://ffmpeg.org/download.html) 経由でWindowsビルドを入手。解凍後、`bin` フォルダにPATHを通し、**PC/ターミナルを再起動**。確認: `ffmpeg -version`。
4.  **Microsoft C++ Build Tools:** [visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/) より入手。「ワークロード」で **「C++によるデスクトップ開発」** を選択。**インストール後、PCを再起動。**

### II. プロジェクトのセットアップ

1.  **このリポジトリのファイル配置:** `C:\Bot` フォルダに、このリポジトリの `ymkw.py` や `assets` フォルダなどを配置します。
2.  **RVCプロジェクトのダウンロード:** コマンドプロンプト/PowerShellで `C:\Bot` に移動し、`git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git RVC_Project` を実行。
3.  **必要なモデルファイル等の配置:**
    *   **HuBERTモデル (`hubert_base.pt`):** `C:\Bot\RVC_Project\assets\hubert\hubert_base.pt` に配置。 (ダウンロードリンク例: [Hugging Face](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt))
    *   **RVC学習済みモデル (`ymkw.pth`):** `C:\Bot\RVC_Project\assets\weights\` に配置。
    *   **ウォーターマーク用テンプレート画像:** `C:\Bot\assets\watermark_templates\` に配置。
4.  **`.env` ファイルの作成:** `C:\Bot` に `.env` ファイルを作成し、以下を記述 (実際のキーに置換):
    ```env
    DISCORD_BOT_TOKEN="YOUR_DISCORD_BOT_TOKEN"
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    SHORTURL_API_KEY="YOUR_XGD_API_KEY" 
    ```
5.  **設定JSONファイルの作成 (空ファイル):** `C:\Bot` に `bot_settings.json` と `othello_points.json` を `{}` という内容で作成。

### III. Pythonライブラリのインストール (共有仮想環境)

1.  **仮想環境の作成と有効化
    ```bash
    cd C:\Bot\RVC_Project
    python -m venv venvAdd commentMore actions
    Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
    .\venv\Scripts\Activate.ps1
    ```
　  プロンプト先頭に `(venv)` が表示されることを確認。
2.  **ライブラリインストール:** 仮想環境が有効な状態で以下を実行:
    
   ```bash
   python -m pip install --upgrade pip
   python -m pip install "pip<24.1" 
   python -m pip install -r requirements.txt  # RVC_Projectフォルダにあるもの
   python -m pip install discord.py python-dotenv google-generativeai pillow aiohttp numpy
   ```
    *   **PyTorch `weights_only` エラー対策:** `C:\Bot\RVC_Project\venv\lib\site-packages\fairseq\checkpoint_utils.py` の `torch.load(...)` に `weights_only=False` を追加。

### IV. Botのコード (`ymkw.py`) 内の設定確認

*   `ymkw.py` を開き、`RVC_MODEL_NAME_WITH_EXT` (例: `"ymkw.pth"`) が正しいか確認。
*   `infer_cli.py` のコマンドラインオプションが `ymkw.py` 内の呼び出しと一致しているか、`python tools\infer_cli.py --help` で確認し、必要なら `ymkw.py` を修正。

### V. Discord Developer Portalでの設定

*   Botアプリケーションページで、「Privileged Gateway Intents」の **「Server Members Intent」を有効化**。

### VI. Botの実行

1.  仮想環境を有効化。
    ```bash
    cd C:\Bot\RVC_Project
    python -m venv venvAdd commentMore actions
    Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
    .\venv\Scripts\Activate.ps1
    ```
2.  `C:\Bot` に移動し、`py ymkw.py` を実行。
3.  コンソールログを確認し、Discordで動作テスト。

## トラブルシューティング

*   **`fairseq` ビルドエラー:** Microsoft C++ Build ToolsのインストールとPC再起動を確認。
*   **`ffmpeg` 見つからないエラー:** FFmpegのインストールとPATH設定、PC/ターミナル再起動を確認。
*   **HuBERTモデル (`hubert_base.pt`) 見つからないエラー:** `C:\Bot\RVC_Project\assets\hubert\` への配置を確認。
*   **`_pickle.UnpicklingError: Weights only load failed...`:** III-2のPyTorchエラー対策を確認。
*   **APIキーエラー:** `C:\Bot\.env` ファイルのトークンとキー設定を確認。
*   **`ModuleNotFoundError`:** 正しい仮想環境が有効化されているか、必要なライブラリがその仮想環境にインストールされているか確認。

## クレジット・参考プロジェクト

このBotは以下の素晴らしいプロジェクトやAPIを利用しています。

*   **RVC (Retrieval-based Voice Conversion):** [RVC-Project/Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)
*   **Google Gemini API:** [ai.google.dev](https://ai.google.dev/)
*   **5000兆円欲しい！ジェネレーターAPI:** [gsapi.cbrx.io/image](https://gsapi.cbrx.io/image)
*   **つくもたんAPI (天気予報):** [weather.tsukumijima.net](https://weather.tsukumijima.net/)
*   **KRNK Exchange Rate API:** [wiki.krnk.org/ja/services/api-service/exchange-rate-api](https://wiki.krnk.org/ja/services/api-service/exchange-rate-api)
*   **x.gd URL Shortener API:** [x.gd/view/developer](https://x.gd/view/developer)
*   **唐突の死ジェネレータースクリプト (参考):** [fumiyas/home-commands/echo-sd](https://github.com/fumiyas/home-commands/blob/master/echo-sd)
*   **Discord.py:** [Rapptz/discord.py](https://github.com/Rapptz/discord.py)
*   **Pillow (PIL Fork):** [python-pillow/Pillow](https://github.com/python-pillow/Pillow)
*   **aiohttp:** [aio-libs/aiohttp](https://github.com/aio-libs/aiohttp)
*   **NumPy:** [numpy/numpy](https://github.com/numpy/numpy)
*   **Python-dotenv:** [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv)

---

© yexe.net
