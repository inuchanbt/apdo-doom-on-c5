# Install and run — one-unit-tested v9.1 Pre-release

[日本語](INSTALL.ja.md) · [Recovery](RECOVERY.md)

The owner checked the major functions on one C5. This remains a Pre-release;
read the limits in [validation](VALIDATION.md) and do not skip device qualification.

1. Extract the whole kit to a writable folder. Install Python 3.11+ for Windows
   if needed. Run `setup.cmd`; it creates a local `.venv` and installs pinned
   `hidapi`. This setup step needs Internet access. Python 3.14 was used locally.
   If Python is not on PATH, run `setup.cmd "C:\path\to\python.exe"` from a terminal.
2. Run `C5-Tools.cmd`, choose **1**, and verify all supplied checksums. This does
   not open USB. For a source checkout, build the firmware first.
3. Obtain the official updater and the correct stock firmware from
   [WITRN's download page](https://www.witrn.com/?p=90), using its C4/C4L/C5 updater
   link. They are not bundled. Keep the stock package and recovery instructions.
4. Close WITRNUP and other HID tools. Connect the C5's HID port with a data-capable
   cable while holding **OK**; confirm the C5 shows **DFU**, then release OK.
5. Choose **4** in `C5-Tools.cmd`, then type `DFU`. The helper reads information
   and the complete 1 MiB Flash twice, checks equality and checks the target boot
   hash. Keep the complete `backups` folder private and copy it somewhere safe.
   A mismatch means stop: this candidate is not qualified for that bootloader.
   Successful reads are not a demonstrated recovery procedure.
6. Close the helper. Open the official updater and install
   `firmware/build/C5-native-doom-v9.1.c4ser`. This replaces the stock measurement
   app. The kit provides no C5-specific erase/program/restore helper.
7. Close the updater. Disconnect all cables to remove every power feed, then
   reconnect the PC to HID **without holding OK**. Check the banner, game,
   physical buttons, movement, firing and menus before starting the PC helper.
8. Choose **2** in `C5-Tools.cmd` for PC control. The helper opens
   `http://127.0.0.1:8768/`. Enable keyboard control on the page. Test preview on
   and off, enlarge/save, 180° physical flip and brightness. Settings reset on
   power cycling. Ctrl+C stops PC control; the game continues.

Choose **3** for telemetry after stopping the controller. Captures go under
`captures/`; keep reports and unit-specific data out of public commits.

## Optional post-install preservation audit

In DFU, take a second read-only backup into a new folder using menu 4. Then:

```powershell
.\.venv\Scripts\python.exe tools\verify_install.py --before backups\YOUR-STOCK-BACKUP --after backups\YOUR-DOOM-BACKUP
```

This compares two verified dumps from **your same unit**. The candidate uses a
896 KiB package; expected erase is `0x08004000..0x080E3FFF`, including the updater's
48-byte header-length tail. The audit checks activation, payload, erased tail,
boot/factory areas and everything after that range. It does not measure SRAM
stack use, gameplay stability or prove restoration. Never use someone else's
complete Flash backup as your baseline or stock restore image.

## If something fails

- No HID device: check the HID port, data cable, DFU/normal mode and competing tools.
- CPU FAULT: stop, photograph the entire CFSR/PC/LR display, and record which action
  triggered it. Re-enter DFU for recovery; do not try a different model's image.
- A slow preview is not proof of slow native rendering. Compare with preview off.
- Keep charging/PD equipment disconnected during these development tests. The
  application is a game and does not expose the stock meter's operational UI.
