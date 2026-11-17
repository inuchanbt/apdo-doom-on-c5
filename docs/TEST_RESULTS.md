# Public candidate checks — 2026-11-17

The first table records the offline/host checks. The subsequent owner-unit check
is listed separately below; it does not establish long-duration or other-unit compatibility.

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

The initial build/package checks did not access a physical device. Afterwards the
owner installed the exact v9.1 package and confirmed normal standalone gameplay,
PC keyboard controls, preview/enlarge/save, physical flip and brightness. Live
HID/JPEG reception was recorded, with 220 connected/error-free status samples over
about 90 seconds. See [the sanitized summary](validation/owner-unit-v9.1-20261117.json).
The owner then reported restoring stock V8.5 on the same C5 and trying its functions
without observing problems. The assistant did not flash the unit. A new full DFU
readback/preservation audit and long-duration stability remain unverified; the
functional restoration report does not establish calibration accuracy or all stock functions.
The large controller screenshot is a fixture; the separate small JPEG is an
actual frame received from the owner's C5.

## 日本語

公開用ソースだけで、個人のダンプを使わず元のv9.1と同一のパッケージを生成しました。
18件の単体テスト、512フレーム比較、素材・描画・PC操作・JPEGの検証、
ブラウザーの差し替え応答テストが合格しています。
空白と日本語を含む展開先でチェックサムと文書リンクを確認し、Pythonのパスを指定した
`setup.cmd` と `C5-Tools.cmd check` も実行しました。
初期のビルド・配布確認では実機へアクセスしていません。その後、所有者が正確なv9.1を導入し、
本体プレイ、PCキー操作、プレビュー拡大・保存、反転・明るさを確認しました。
実機のHID／JPEG受信も記録し、約90秒・220件の状態応答はすべて接続継続・エラー0でした。
その後、所有者から同じ個体で純正V8.5への復帰・各種操作が正常との報告がありました。
アシスタントは実機へ書き込んでいません。新たな全Flash保持監査と長時間安定性は未確認で、
機能上の復帰報告は校正精度や純正の全機能の実証とは区別します。
