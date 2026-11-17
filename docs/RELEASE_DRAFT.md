# APDO DOOM on C5 0.1.0-rc.1 — draft, publication on hold

Native DOOM/Freedoom E1M1 on the WITRN C5, with standalone play, physical buttons
and optional browser PC controls. This candidate includes a full-panel 320×172
JPEG preview, physical 180° rotation and brightness adjustment.

**Hardware-unverified candidate. Do not publish this draft until the owner's
device check is recorded.** Native v7 gameplay and v8 PC controls worked on one
owner unit; v9 faulted. This v9.1 image corrects the Cortex-M4 FPU instruction
setting and includes PC/LR fault diagnostics, but its device behavior is pending.

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

**実機未確認の候補版です。所有者の実機確認を記録するまで公開を保留しています。**
v7のゲームとv8のPC操作は1台で確認済みですが、v9ではCPU FAULTが発生しました。
今回のv9.1はCortex-M4のFPU命令設定を修正し、異常時PC／LR表示を追加した候補で、実機確認待ちです。

配布予定ZIPにはファーム、対応ソース、Windows用セットアップ・メニュー、読み取り専用のバックアップ・
適合確認・導入監査、英日手順、ライセンス、チェックサムを含みます。
メーカー更新ツール・純正ファーム・コンパイラー・個体バックアップは含みません。
最初に[導入](INSTALL.ja.md)・[復帰](RECOVERY.ja.md)・[検証状況](VALIDATION.ja.md)を確認してください。
