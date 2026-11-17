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

The development unit demonstrated DFU access, an earlier stock update/readback
and earlier custom applications. **Stock restoration after the current v9.1
candidate and its post-install full readback are not yet verified.**
The native game relies on a pinned stock bootloader and private functions;
replacing the bootloader is outside this project's installation procedure.

If the bootloader no longer shows DFU, stop and retain the original backups and
failure evidence. These host helpers do not establish an invasive recovery path.

The proposed v9.1 package occupies the same bounded update envelope as the
earlier large C5 DOOM versions. The offline audit models preservation of boot,
factory and upper Flash areas; it cannot substitute for a physical readback
or a successful restoration test.
