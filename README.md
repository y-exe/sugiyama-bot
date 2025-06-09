<div align="center">

# 杉山啓太Bot

多機能Bot（笑）
杉山啓太がGM雑談ライフをサポートします

<img src="https://count.getloli.com/@yexe.net" /><br>
yexe.net 総合

[![Discord.py](https://img.shields.io/badge/discord.py-v2.x-blue?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/en/latest/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/LICENSE-MIT-green.svg?style=for-the-badge)](LICENSE) 
<!-- ライセンスファイルを別途作成する場合 -->

</div>

杉山啓太Botは `#Botと遊ぶ場所` で使えるコンテンツを提供します
RVCを用いたリアルタイム風の音声変換、様々な画像処理機能、そしてオセロゲームなどの機能を実装しています。

## 主な機能

*   **AI機能 (Google Gemini API):**
    *   **チャット要約:** 指定時間内のチャット履歴を要約します (`/imakita` スラッシュコマンド)。
*   **RVC 音声変換:**
    *   ユーザーが添付した音声ファイルを、事前に学習させたRVCモデルを使用して声質変換します。
    *   CPUベースでの処理に対応しています。
*   **画像処理:**
    *   **ウォーターマーク合成:** ユーザーがアップロードした画像に、複数のテンプレートから最適なものを選択してウォーターマークを合成します。
    *   **「5000兆円欲しい！」画像生成:** 指定した文字列で人気のジェネレーター画像を生成します。
    *   **ゲーミング風GIF変換:** 画像を虹色に変化するゲーミング風のGIFアニメーションに変換します。
*   **ゲーム機能:**
    *   **オセロ:** サーバー内で他のユーザーとオセロゲームをプレイできます。対戦相手の募集も可能です。
*   **その他:**
    *   **コマンド実行チャンネル制限:** 管理者はBotのコマンドを利用できるチャンネルを指定できます。
    *   **ヘルプコマンド:** 利用可能なコマンドの一覧と説明を表示します。

## 導入手順 (Windows CPU環境向け)

このBotを動作させるためには、いくつかのソフトウェアのインストールと設定が必要です。

### I. 事前準備: 必要なソフトウェアのインストール

1.  **Python 3.10.x:**
    *   **ダウンロード:** [python.org](https://www.python.org/downloads/) より Windows installer (64-bit推奨) を入手。
    *   **インストール時:** インストーラーの最初の画面で **「Add Python 3.10 to PATH」に必ずチェックを入れてください。**

2.  **Git:**
    *   **ダウンロード:** [git-scm.com](https://git-scm.com/downloads) より Windows版を入手。
    *   **インストール時:** 基本的にデフォルト設定で進めてください。

3.  **FFmpeg:**
    *   **ダウンロード:** [ffmpeg.org/download.html](https://ffmpeg.org/download.html) 経由で、Windowsビルド (例: [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) の `ffmpeg-release-full.7z`) を入手。
    *   **展開・配置:** 解凍後、フォルダ (例: `ffmpeg-7.x.x-release-full`) を `C:\ffmpeg` などに配置。
    *   **PATH設定:** `C:\ffmpeg\bin` (ffmpeg.exeがあるフォルダ) をシステムの環境変数 `Path` に追加し、**PCを再起動** (またはターミナルを再起動)。
    *   **確認:** コマンドプロンプトで `ffmpeg -version` と入力し、バージョン情報が表示されることを確認。

4.  **Microsoft C++ Build Tools:**
    *   **ダウンロード:** [visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/) より「Build Tools for Visual Studio」を入手。
    *   **インストール時:** 「ワークロード」タブで **「C++によるデスクトップ開発」** を選択しインストール。
    *   **インストール後、PCを再起動。**

### II. プロジェクトのセットアップ

1.  **プロジェクトリポジトリのクローン:**
    *   このGitHubリポジトリをクローンするか、ZIPファイルをダウンロードして展開します。
    *   展開先を `C:\Bot` (Cドライブ直下の `Bot` フォルダ) とします。

2.  **RVCプロジェクトのダウンロード:**
    *   コマンドプロンプトまたはPowerShellを開き、`C:\Bot` フォルダに移動します。
        ```bash
        cd C:\Bot
        ```
    *   RVCプロジェクトを `RVC_Project` という名前でクローンします。
        ```bash
        git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git RVC_Project
        ```

3.  **必要なモデルファイルとアセットの配置:**

    *   **HuBERTモデル (`hubert_base.pt`):**
        *   **ダウンロード:** [例: Hugging Face](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt) (RVCプロジェクトの公式情報を確認推奨)
        *   **配置:** `C:\Bot\RVC_Project\assets\` フォルダ内に `hubert` フォルダを作成し、その中に `hubert_base.pt` を配置します。
            (最終パス: `C:\Bot\RVC_Project\assets\hubert\hubert_base.pt`)

    *   **RVC用学習済みモデル (例: `RVC.pth`):**
        *   使用したい `.pth` モデルファイル (および対応する `.index` ファイルがあれば) を用意します。
        *   **配置:** `C:\Bot\RVC_Project\assets\weights\` フォルダ (なければ作成) に配置します。
        *   `C:\Bot\ymkw.py` 内の `RVC_MODEL_NAME_WITH_EXT` の値を、ここで配置したモデルのファイル名 (例: `"MyModel.pth"`) に合わせてください。

    *   **ウォーターマーク用テンプレート画像:**
        *   Botリポジトリ内の `assets/watermark_templates/` フォルダにあるテンプレート画像 (例: `POCO F3.png` など) が `C:\Bot\assets\watermark_templates\` に正しく配置されていることを確認します。(`ymkw.py` の `TEMPLATES_DATA` リスト参照)

4.  **ファイル作成**

```bash
C:Bot\
├── ymkw.py
├── .env
├── bot_settings.json (空でもOK、またはsetchannel後に生成)
├── assets\
│   └── watermark_templates\
│       ├── POCO F3.png
│       └── ... (他のテンプレート)
├── audio\
│   ├── input\
│   └── output\
└── RVC_Project\
    ├── tools\
    │   └── infer_cli.py
    ├── assets\
    │   ├── hubert\
    │   │   └── hubert_base.pt
    │   └── weights\
    │       └── RVC.pth  (例)
    │       └── RVC.index (例、あれば)
    ├── requirements.txt
    └── ... (RVCの他のファイル)
```

こんな感じに最終的になります。
RVC_Projectの中身は後で勝手に追加されますので作らなくていいです

### III. Pythonライブラリのインストール (仮想環境)

1.  **仮想環境の作成:**
    *   コマンドプロンプト/PowerShellで `C:\Bot\RVC_Project` フォルダに移動します。
        ```bash
        cd C:\Bot\RVC_Project
        ```
    *   仮想環境 (`venv`という名前で) を作成します。
        ```bash
        python -m venv venv
        ```

2.  **仮想環境の有効化:**
    *   コマンドプロンプト: `venv\Scripts\activate.bat`
    *   PowerShell: `.\venv\Scripts\Activate.ps1`
        (PowerShellでエラーが出る場合は `Set-ExecutionPolicy RemoteSigned -Scope Process` を先に実行)
    *   プロンプトの先頭に `(venv)` と表示されることを確認します。

3.  **必要なPythonライブラリのインストール:**
    仮想環境が有効な状態で、以下のコマンドを実行します。

    *   **`pip` のアップグレードと一時的なダウングレード:**
        ```bash
        python -m pip install --upgrade pip
        python -m pip install "pip<24.1" 
        ```
        (`pip<24.1` は `omegaconf` のメタデータエラー対策です。)

    *   **RVCの依存ライブラリ:**
        ```bash
        pip install -r requirements.txt
        ```
        (この際、特に `fairseq` のビルドに成功するか確認してください。)

    *   **Bot本体の追加ライブラリ:**
        ```bash
        pip install discord.py python-dotenv google-generativeai pillow aiohttp numpy
        ```

    *   **(PyTorch `weights_only` エラー対策 - 推奨):**
        `hubert_base.pt` 読み込み時のエラーを防ぐため、`fairseq` のファイルを修正します。
        1.  テキストエディタで `C:\Bot\RVC_Project\venv\lib\site-packages\fairseq\checkpoint_utils.py` を開きます。
        2.  `state = torch.load(f, map_location=torch.device("cpu"))` という行を探します。
        3.  この行を `state = torch.load(f, map_location=torch.device("cpu"), weights_only=False)` に変更します。
        4.  ファイルを保存します。

### IV. Botの起動

1.  コマンドプロンプト/PowerShellで `C:\Bot\RVC_Project` に移動し、仮想環境を有効化します (上記III-2参照)。
2.  `C:\Bot` フォルダに移動し、Botを実行します。
    ```bash
    cd C:\Bot
    python ymkw.py
    ```
3.  コンソールにBotの起動ログが表示され、エラーがないことを確認します。
4.  DiscordでBotがオンラインになり、コマンドが利用できるかテストします。

## 主なコマンド

*   `!help`: このヘルプメッセージを表示します。
*   `!voice`: (音声ファイルを添付) 添付された音声の声をRVCモデルで変換します。
*   `!watermark`: (画像ファイルを添付) 画像にウォーターマークを合成します。
*   `!image [プロンプト]`: (画像ファイルを添付) 添付画像とプロンプトでAIが画像を編集・生成します。
*   `!5000 [上の文字] [下の文字] (hoshii) (rainbow)`: 「5000兆円欲しい！」画像を生成します。
*   `!gaming`: (画像ファイルを添付) 画像をゲーミング風GIFに変換します。
*   `!othello (@相手ユーザー)`: オセロの対戦相手を募集、または指定ユーザーと即時対戦を開始します。
*   `/imakita`: (スラッシュコマンド) 直近30分のチャンネルの会話を3行で要約します。
*   `!setchannel`: (管理者のみ) Botの通常コマンドの利用を現在のチャンネルで許可/禁止します。

## トラブルシューティング

*   **`fairseq` のビルドエラー:** Microsoft C++ Build Toolsが正しくインストールされ、PCが再起動されているか確認してください。
*   **`ffmpeg` が見つからないエラー:** FFmpegがインストールされ、PATHが正しく設定されているか、PC/ターミナルが再起動されているか確認してください。
*   **HuBERTモデルが見つからないエラー:** `C:\Bot\RVC_Project\assets\hubert\hubert_base.pt` にファイルが正しく配置されているか確認してください。
*   **`_pickle.UnpicklingError: Weights only load failed...`:** 上記「III. Pythonライブラリのインストール」のPyTorchエラー対策が適用されているか確認してください。
*   **APIキーエラー:** `.env` ファイルに正しいDiscord BotトークンとGemini APIキーが設定されているか確認してください。

## クレジット・参考プロジェクト

仕様APIなど

*   **RVC (Retrieval-based Voice Conversion):** [RVC-Project/Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)
*   **Google Gemini API:** [ai.google.dev](https://ai.google.dev/)
*   **5000兆円欲しい！ジェネレーターAPI:** [github.com/CyberRex0](https://github.com/CyberRex0/5000choyen-api) 
*   **Discord.py:** [Rapptz/discord.py](https://github.com/Rapptz/discord.py)
*   **Pillow (PIL Fork):** [python-pillow/Pillow](https://github.com/python-pillow/Pillow)
*   **aiohttp:** [aio-libs/aiohttp](https://github.com/aio-libs/aiohttp)
*   **NumPy:** [numpy/numpy](https://github.com/numpy/numpy)
*   **Python-dotenv:** [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv)

---
こっちみんなカス
