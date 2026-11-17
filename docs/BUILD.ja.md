# ビルドと再現手順

[English](BUILD.md)

確認環境はWindows x64、Python 3.14、llvm-mingw `20261020-ucrt-x86_64`
（Clang 23.1.4）、hidapi 0.15.0、Pillow 12.2.0です。
コンパイラーは同梱していません。`APDO_LLVM_BIN` に手元のllvm-mingwの `bin` を指定します。
他のツールチェーンでの同一性は確認していません。

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:APDO_LLVM_BIN = 'C:\your\llvm-mingw\bin'
.\.venv\Scripts\python.exe firmware\build.py
.\.venv\Scripts\python.exe firmware\test_package.py
```

対象はCortex-M4F、`fpv4-sp-d16`、hard-floatです。出力は `firmware/build/` に保存します。
元の候補パッケージは917,504バイトで、SHA-256は `SOURCE_LOCK.json` に固定しています。
M4で不明な命令があればビルドを停止します。パッケージテストではソースのハッシュ、
パッケージの一致、起動・消去のシミュレーション、7種類の破損検出を確認します。
ビルド自体に個人のFlashダンプ、公式更新ツール、実機、通信は不要です。
過去の基準ダンプのハッシュは識別用メタデータだけを収録しています。

## オフラインテスト

```powershell
.\.venv\Scripts\python.exe tools\run_checks.py
```

ターゲット・PC用・無圧縮参照用をビルドし、素材、エンジン、描画、PC入力、JPEG、
コントローラー、読み取り専用プロトコルを確認します。ログは非公開扱いの `verification/` へ保存します。
実際のHID機器は開きません。
既存のブラウザーテストは、設定されたWindowsパスにChromeがある環境で
`node firmware/test_ui.mjs` を実行します。CDPパイプと差し替え応答を使い、実機には接続しません。

## 素材の再生成

通常ビルドには同梱の生成済み素材を使います。再生成する場合は
[Freedoom 0.13.0のZIP](https://github.com/freedoom/freedoom/releases/download/v0.13.0/freedoom-0.13.0.zip)
を入手してください。変換処理が元ZIPのSHA-256を照合します。

```powershell
.\.venv\Scripts\python.exe tools\regenerate_pack.py --freedoom-zip C:\downloads\freedoom-0.13.0.zip
.\.venv\Scripts\python.exe firmware\prepare.py
.\.venv\Scripts\python.exe firmware\adapt_jpeg.py
```

生成する軽量化パックのSHA-256は
`8e020d3822edf873b0209c92dfbb6518bb8a92c6fe9fdb64be17d66699ae2664` です。
Freedoomのライセンス・クレジットと、固定版doomgenericの入力ソースも同梱しています。
起動バナーの変換情報は `firmware/freedoom-banner.json` に記録しています。

## ローカル配布キットの準備

テスト合格後に実行します。

```powershell
.\.venv\Scripts\python.exe tools\package.py
```

`dist/` に確認用ZIPを作成します。この処理はGitHub Release・タグ・コミット・アップロードを行いません。
インストールZIPには対応ソース、ライセンス、ファイルごとのチェックサムも含みます。
コンパイラー、メーカー更新ツール、純正ファーム、個体バックアップ、`.git`、仮想環境、他機種プロジェクトは除外します。

同梱DMC100-Doomソース内の上流開発ツールは別機種用です。
C5には、このプロジェクトの手順に明記したC5用ヘルパーだけを使用してください。
