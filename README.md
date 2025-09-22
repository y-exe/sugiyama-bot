<div align="center">

# 杉山啓太Bot

多機能Bot（笑）<br>
杉山啓太がGM雑談ライフをサポートします。<br>
AIに修正もらってたら自分でもわけわかめなコードになってました。

<img src="https://count.yexe.xyz/@yexe.net?theme=rule34" alt="yexe.net 総合カウンター"/><br>
<sub>yexe.net 総合</sub>

[![Discord.py](https://img.shields.io/badge/discord.py-v2.x-blue?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/en/latest/)
[![Python](https://img.shields.io/badge/Python-3.10.x-yellow?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Support Server](https://img.shields.io/badge/Support%20Server-Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/FXamRgKSph)
[![License](https://img.shields.io/badge/LICENSE-MIT-green.svg?style=for-the-badge)](LICENSE) 

</div>

## 概要

杉山啓太Bot (`ymkw.py`) は、Discordサーバーでの遊びや情報取得をサポートするために開発された多機能Botです。<br>
AIによる会話要約、RVC技術を用いた音声変換（添付ファイルまたはテキストから）、様々なスタイルのテキスト画像生成、ウォーターマーク合成、そしてオセロやじゃんけんといったゲーム機能など、幅広い機能を提供します。

コマンドの実行は、多くの場合、許可されたチャンネルでコマンド名と引数を入力するだけで直感的に行えます (プレフィックス不要)。

## コマンドリスト (隠しコマンドも含む)

*   `watermark +[画像添付]`: 添付画像にウォーターマークを合成。アスペクト比が近いテンプレート候補からランダムに選択。
*   `/imakita`: 過去30分のチャットを3行で要約。(スラッシュコマンド・どこでも利用可、レート制限あり)
*   `5000 [上文字列] [下文字列] (hoshii) (rainbow)`: 「5000兆円欲しい！」画像を生成。
*   `gaming +[画像添付]`: 添付画像をゲーミング風GIFに変換。
*   `othello (@相手ユーザー)`:
    *   `othello`: オセロの対戦相手を募集します。
    *   `othello @メンション`: 指定したユーザーと即時対戦を開始します。
    *   `leave` (または `othello leave`): 進行中のオセロゲームから離脱します。
    *   `point` (または `othello points`): あなたの現在のゲームポイントとランキングを表示します。
*   `voice [テキスト]` または `voice +[音声ファイル添付]`:
    *   `voice こんにちは`: 入力テキストをVoiceVox API(玄野武宏)で音声生成後、RVCでやまかわてるきの声に変換。
    *   音声ファイル添付: 添付音声の声をRVCでやまかわてるきの声に変換。（45秒まで）
*   `janken`: じゃんけんゲームを開始します。ホスト・挑戦者共にボタンで手を選択。(ポイント変動あり)
*   `bet [金額]`: ポイントを賭けてシンプルなダイスゲームに挑戦。
*   `text [文字列] (,で改行) (squareで正方形化)`: 指定スタイル（黄文字、黒白二重縁取り）で文字画像を生成。
*   `text2 [文字列] (,で改行) (squareで正方形化)`: `text`コマンドの文字色を青色に変更したバージョン。
*   `text3 [文字列] (,で改行) (squareで正方形化)`: Noto Serif JP Boldフォント、濃赤文字、白縁取りで文字画像を生成。
*   `help`: このヘルプを表示。

**隠しコマンド (その他便利コマンド):**
*   `ping`: Botの現在の応答速度 (レイテンシ) をミリ秒単位で表示します。
*   `tenki [日本の都市名]` (または `weather [日本の都市名]`): 指定された日本の都市の天気予報を表示（つくもAPI使用、Geminiによる都市ID推測補助あり）。
*   `time (国コード)`: 世界時計です。国コードを入れなかった場合は日本時間を表示します (`time help`でコード一覧)。
*   `info (@ユーザーメンションまたはユーザーID)`: 指定されたユーザー (またはコマンド実行者) の詳細情報を表示します。
*   `rate [金額] [3文字通貨コード]`: 指定した外貨の金額を現在のレートで日本円に換算して表示します。
*   `shorturl [URL]` (または `short [URL]`): 指定したURLをx.gdサービスを利用して短縮します。
*   `amazon [Amazon URL]`: Amazonの商品ページのURLを短縮します。
*   `totusi [文字列]`: 入力した文字列を使って「＿人人人＿ ＞ 文字列 ＜ ￣Y^Y^Y￣」のようなAAを生成します。
*   `setchannel` (管理者のみ): Botのコマンド利用を現在のチャンネルで許可/禁止します。

## 動作に必要なファイル配置

Botを正しく動作させるためには、以下のフォルダ構成とファイル配置が必要です。
ルートフォルダは `C:\Bot` を想定しています。

```bash
C:\Bot
├── ymkw.py                 # Bot本体のPythonスクリプト
├── .env                    # APIキーなどを格納 (ユーザーが作成)
├── bot_settings.json       # チャンネル制限設定 (自動生成)
├── game_points.json        # ゲームのポイント記録 (自動生成)
├── weather_city_codes.json # 天気API用都市コードキャッシュ (自動生成/更新)
├── assets\                 # Bot用アセット
│   ├── fonts\              # フォントファイル
│   │   ├── MochiyPopOne-Regular.ttf  # text, text2用 (ユーザーが配置)
│   │   └── NotoSerifJP-Bold.otf      # text3用 (ユーザーが配置)
│   └── watermark_templates\  # ウォーターマーク用テンプレート
│       ├── POCO F3.png     # テンプレート画像例
│       └── ...             # 他のテンプレート画像
├── audio\                  # RVCの一時音声ファイル用 (自動生成)
│   ├── input\
│   └── output\
└── RVC_Project\            # RVC本体 (ユーザーが別途 git clone で取得)
    ├── tools\
    │   └── infer_cli.py    # RVC推論スクリプト
    ├── assets\
    │   ├── hubert\
    │   │   └── hubert_base.pt # HuBERTモデル (ユーザーが配置)
    │   └── weights\
    │       └── ymkw.pth      # RVC学習済みモデル (ユーザーが配置)
    ├── requirements.txt      # RVCのPython依存ライブラリリスト
    ├── venv\                 # Python共有仮想環境 (ユーザーが作成・設定)
    └── ...                   # RVCのその他ファイル群
```

## 導入手順 (Windows CPU環境向け)

### I. 事前準備: 必要なソフトウェアのインストール

1.  **Python (3.10.x推奨):** [python.org](https://www.python.org/) より入手し、インストール時に **「Add Python to PATH」に必ずチェック**。
2.  **Git:** [git-scm.com](https://git-scm.com/downloads) より入手し、インストール。
3.  **FFmpeg:** [ffmpeg.org](https://ffmpeg.org/download.html) 経由でWindowsビルドを入手。解凍後、`bin` フォルダにPATHを通し、**PC/ターミナルを再起動**。
    *   コマンドプロンプトで `winget install --id=Gyan.FFmpeg -e` でもインストール可能です。
    *   確認: `ffmpeg -version`
4.  **Microsoft C++ Build Tools:** [visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/) より入手。「ワークロード」で **「C++によるデスクトップ開発」** を選択。**インストール後、PCを再起動。**

### II. プロジェクトのセットアップ

1.  **このリポジトリのファイル配置:** `C:\Bot` フォルダに、このリポジトリの `ymkw.py` や `assets` フォルダなどを配置します。
2.  **RVCプロジェクトのダウンロード:** コマンドプロンプト/PowerShellで `C:\Bot` に移動し、`git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git RVC_Project` を実行。
3.  **必要なモデルファイル等の配置:**
    *   **HuBERTモデル (`hubert_base.pt`):** `C:\Bot\RVC_Project\assets\hubert\hubert_base.pt` に配置。 (ダウンロード: [Hugging Face](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt))
    *   **RVC学習済みモデル (`ymkw.pth`):** `C:\Bot\RVC_Project\assets\weights\` に配置。 (例: `ymkw.pth` を使用する場合)
    *   **ウォーターマーク用テンプレート画像:** `C:\Bot\assets\watermark_templates\` に配置。
    *   **フォントファイル:**
        *   `MochiyPopOne-Regular.ttf` を `C:\Bot\assets\fonts\` に配置。
        *   `NotoSerifJP-Bold.otf` (または他のNoto Serif JP Boldファイル) を `C:\Bot\assets\fonts\` に配置。
4.  **`.env` ファイルの作成:** `C:\Bot` に `.env` ファイルを作成し、以下を記述 (実際のキーに置換):
    ```env
    DISCORD_BOT_TOKEN="YOUR_DISCORD_BOT_TOKEN"
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    VOICEVOX_API_KEY="YOUR_VOICEVOX_API_KEY" # (textからのvoiceコマンドに必要)
    SHORTURL_API_KEY="YOUR_XGD_API_KEY"      # (任意)
    ```
5.  **設定JSONファイルの準備:** `bot_settings.json` と `game_points.json` は、Bot初回起動時に存在しなければ空の状態で自動生成されます。手動で空ファイル `{}` を作成しておくことも可能です。

### III. Pythonライブラリのインストール (共有仮想環境)

1.  **仮想環境の作成と有効化:**
    ```powershell
    cd C:\Bot\RVC_Project
    python -m venv venv
    Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
    .\venv\Scripts\Activate.ps1
    ```
    プロンプト先頭に `(venv)` が表示されることを確認。
2.  **ライブラリインストール:** 仮想環境が有効な状態で以下を実行:
    ```bash
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt  # RVC_Projectフォルダにあるもの
    python -m pip install discord.py python-dotenv google-generativeai pillow aiohttp numpy pytz pydub
    ```
    (もし `requirements.txt` に `torch` や `torchaudio` が含まれており、CPU環境で問題が出る場合は、CPU版を明示的にインストールする必要があるかもしれません。)

### IV. Botのコード (`ymkw.py`) 内の設定確認

*   `ymkw.py` を開き、`RVC_MODEL_NAME_WITH_EXT` (例: `"ymkw.pth"`) が実際に配置したモデルファイル名と一致しているか確認。
*   `TEXT_IMAGE_FONT_PATH_DEFAULT` と `TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD` が、実際に配置したフォントファイル名と一致しているか確認。

### V. Discord Developer Portalでの設定

*   Botアプリケーションページで、「Privileged Gateway Intents」の **「Server Members Intent」と「Message Content Intent」を有効化**。

### VI. Botの実行

1.  仮想環境を有効化 (まだ有効でない場合)。
    ```powershell
    cd C:\Bot\RVC_Project
    .\venv\Scripts\Activate.ps1
    ```
2.  `C:\Bot` に移動し、`py ymkw.py` を実行。
    ```powershell
    cd C:\Bot
    py ymkw.py
    ```
3.  コンソールログを確認し、Discordで動作テスト。

### VII. 再起動の手順
   ```powershell
    cd C:\Bot\RVC_Project
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
    .\venv\Scripts\Activate.ps1
    cd C:\Bot
    py ymkw.py
   ```

## トラブルシューティング

*   **`fairseq` ビルドエラー:** Microsoft C++ Build ToolsのインストールとPC再起動を確認。
*   **`ffmpeg` 見つからないエラー:** FFmpegのインストールとPATH設定、PC/ターミナル再起動を確認。
*   **HuBERTモデル (`hubert_base.pt`) 見つからないエラー:** `C:\Bot\RVC_Project\assets\hubert\` への配置を確認。
*   **APIキーエラー:** `C:\Bot\.env` ファイルのトークンとキー設定を確認。
*   **`ModuleNotFoundError`:** 正しい仮想環境が有効化されているか、必要なライブラリがその仮想環境にインストールされているか確認 (`pip list` コマンドで確認可能)。
*   **フォントエラー:** `text`系コマンドが動作しない場合、`assets/fonts/`に必要なフォントファイルが配置されているか確認。

## クレジット・参考プロジェクト

このBotは以下のプロジェクトやAPIを利用・参考にしています。

*   **RVC (Retrieval-based Voice Conversion):** [RVC-Project/Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)
*   **Google Gemini API:** [ai.google.dev](https://ai.google.dev/)
*   **VoiceVox (su-shiki API):** [voicevox.su-shiki.com/su-shikiapis/](https://voicevox.su-shiki.com/su-shikiapis/)
*   **5000兆円欲しい！ジェネレーターAPI:** [CyberRex0/5000choyen-api](https://github.com/CyberRex0/5000choyen-api)
*   **つくもAPI (天気予報):** [weather.tsukumijima.net](https://weather.tsukumijima.net/)
*   **KRNK Exchange Rate API:** [wiki.krnk.org/ja/services/api-service/exchange-rate-api](https://wiki.krnk.org/ja/services/api-service/exchange-rate-api)
*   **x.gd URL Shortener API:** [x.gd/view/developer](https://x.gd/view/developer)
*   **唐突の死ジェネレータースクリプト:** [fumiyas/home-commands/echo-sd](https://github.com/fumiyas/home-commands/blob/master/echo-sd)
*   **Discord.py:** [Rapptz/discord.py](https://github.com/Rapptz/discord.py)
*   **Pillow (PIL Fork):** [python-pillow/Pillow](https://github.com/python-pillow/Pillow)
*   **aiohttp:** [aio-libs/aiohttp](https://github.com/aio-libs/aiohttp)
*   **NumPy:** [numpy/numpy](https://github.com/numpy/numpy)
*   **Python-dotenv:** [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv)
*   **Pytz:** [stub42/pytz](https://github.com/stub42/pytz)
*   **Pydub:** [jiaaro/pydub](https://github.com/jiaaro/pydub)

---

© yexe.net
