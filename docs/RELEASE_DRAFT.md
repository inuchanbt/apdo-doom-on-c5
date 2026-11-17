# APDO DOOM on C5 0.1.0-rc.1 — preparation notes

The final bilingual release text is [v0.1.0-rc.1](releases/v0.1.0-rc.1.md).

Native DOOM/Freedoom E1M1 on the WITRN C5, with standalone play, physical buttons
and optional browser PC controls. This candidate includes a full-panel 320×172
JPEG preview, physical 180° rotation and brightness adjustment.

The owner has now confirmed v9.1 standalone play, PC controls, preview/enlarge/save,
physical flip and brightness on one C5. Live HID/JPEG reception was recorded.
The owner subsequently restored stock V8.5 and reported normal operation on that
unit. This remains a Pre-release; a new full preservation audit and long-duration
stability are unverified. See the final release text above.

Planned assets: install ZIP with firmware, complete matching source, Windows
setup/menu, read-only backup/qualification/audit tools, English/Japanese docs,
licenses and per-file checksums; separate source ZIP; archive SHA256SUMS.
The official updater, stock firmware, compiler and personal backups are excluded.

Firmware: `C5-native-doom-v9.1.c4ser`, 917,504 bytes, SHA-256
`186bd3aea083dc85c3b7de2e115a6d6f1eb0d74c1c5a70ed11ed5e1ddbc127bb`.
Qualify your own C5 bootloader and retain your own stock backup first.
Read [installation](INSTALL.md), [recovery](RECOVERY.md) and [validation](VALIDATION.md).

---

## 日本語

WITRN C5でFreedoom E1M1を本体単独プレイできる、APDO DOOMの公開候補です。
本体ボタンとPC操作、320×172 JPEGプレビュー、本体の180度反転・明るさ調整を備えます。

v9.1の本体プレイ、PC操作、プレビュー拡大・保存、反転・明るさは所有者の1台で確認しました。
実機HID／JPEG受信も記録しています。その後、同じ個体で純正V8.5復帰・操作正常との報告がありました。
長時間安定性と新たな全Flash保持監査は未確認で、Pre-releaseとして扱います。
最終の英日リリース文は上記リンクを参照してください。

配布予定ZIPにはファーム、対応ソース、Windows用セットアップ・メニュー、読み取り専用のバックアップ・
適合確認・導入監査、英日手順、ライセンス、チェックサムを含みます。
メーカー更新ツール・純正ファーム・コンパイラー・個体バックアップは含みません。
最初に[導入](INSTALL.ja.md)・[復帰](RECOVERY.ja.md)・[検証状況](VALIDATION.ja.md)を確認してください。
