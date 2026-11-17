# Recovery and scope

[日本語](RECOVERY.ja.md)

Before installing, retain your own qualified two-pass Flash backup and an
official stock package appropriate to your C5. A readback backup is evidence
of saved bytes, not a tested full-Flash recovery mechanism. This project
does not supply a raw-Flash restore writer.

To return to the stock app, close PC tools, disconnect, hold OK while connecting
to enter the stock DFU screen, and use the official WITRN updater with the correct
official C5 package. Close the updater and reconnect normally afterwards.
Do not substitute C4/C4L images or another unit's full dump.

On 2026-11-17, after the v9.1 game and PC checks, the owner reported returning
the same C5 to **stock V8.5** and trying its functions without observing problems.
This is a one-unit functional restoration report. It does not establish
byte-for-byte Flash preservation, calibration accuracy or every stock function;
a new full readback/preservation audit remains unverified.
The native game relies on a pinned stock bootloader and private functions;
replacing the bootloader is outside this project's installation procedure.

If the bootloader no longer shows DFU, stop and retain the original backups and
failure evidence. These host helpers do not establish an invasive recovery path.

The proposed v9.1 package occupies the same bounded update envelope as the
earlier large C5 DOOM versions. The offline audit models preservation of boot,
factory and upper Flash areas; it cannot substitute for a physical readback
or a successful restoration test.
