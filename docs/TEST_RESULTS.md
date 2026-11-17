# Public candidate checks — 2026-11-17

These are offline/host results, not a C5 hardware acceptance report.

| Check | Result |
| --- | --- |
| Public target build, without private Flash dumps | PASS; 917,504-byte package identical to the native v9.1 candidate |
| Clean Git-index export | PASS; all 694 public source files were tracked, and the exported source rebuilt the identical package without the working tree or private backups |
| Target package SHA-256 | `186bd3aea083dc85c3b7de2e115a6d6f1eb0d74c1c5a70ed11ed5e1ddbc127bb` |
| Cortex-M4 disassembly | Zero unknown instructions; `fpv4-sp-d16` |
| Tools unit tests | 18 passed, including target refusal and mismatched backup checks |
| Compressed/raw host engines | 512 matching frames/states; full pack, 3,000 random reads and 1,038 codec inputs passed |
| Frame composer | 138 engine/menu comparisons passed |
| PC/JPEG/controller | Input expiry/release, rotation, brightness, JPEG bounds/decoding and fake-HID scheduler/HTTP checks passed |
| Browser fixture | Keyboard combinations, pointer input, blur release, preview, enlarge, flip/brightness and mobile layout passed; zero browser errors |
| Freedoom converter | Reproduced the complete 1,056,192-byte reduced-art pack |
| Generated source inputs | Asset C/header/metadata, pack and adapted JPEG source reproduced byte-for-byte |
| Prepared Windows kit | Extracted under a path containing spaces and Japanese text; all per-file checksums and local documentation links passed |
| Windows entry points | `setup.cmd` with an explicit Python 3.14 executable created a fresh virtual environment and installed hidapi 0.15.0; `C5-Tools.cmd check` passed |

No controller, monitor, DFU probe, backup, updater or Flash writer was run against
a physical C5 during this workflow. Binary release publication remains on hold.
The screenshot in the READMEs is the browser fixture, with synthetic status/FPS.

## 日本語

公開用ソースだけで、個人のダンプを使わず元のv9.1と同一のパッケージを生成しました。
18件の単体テスト、512フレーム比較、素材・描画・PC操作・JPEGの検証、
ブラウザーの差し替え応答テストが合格しています。
空白と日本語を含む展開先でチェックサムと文書リンクを確認し、Pythonのパスを指定した
`setup.cmd` と `C5-Tools.cmd check` も実行しました。
実機にはアクセスせず、バイナリのリリース公開は保留しています。
