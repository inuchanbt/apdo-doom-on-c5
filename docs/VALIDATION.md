# Evidence and remaining checks

[日本語](VALIDATION.ja.md)

The [2026-11-17 public-source check record](TEST_RESULTS.md) lists the executed host checks.

| Version | Device evidence | Limit |
| --- | --- | --- |
| Native v7 | Owner accepted standalone gameplay, four buttons, gap-free HUD and improved scanout on one C5 | Does not qualify other units or long-duration stability |
| Native v8 | Owner confirmed PC controls on that C5 | Its 80×43 preview was too coarse for play |
| Native v9 | Owner saw banner/first game image, then CPU FAULT with CFSR `00010000` | Exact stacked fault PC was not captured |
| Native v9.1 / proposed 0.1.0-rc.1 | Offline checks pass; package remains SHA-256 `186bd3aea083dc85c3b7de2e115a6d6f1eb0d74c1c5a70ed11ed5e1ddbc127bb` | Hardware check and binary publication are pending |

v9 accidentally used `fpv5-sp-d16` with Cortex-M4 and emitted eight VRINTZ
instructions unsupported by that target. v9.1 uses `fpv4-sp-d16`, rejects unknown
M4 instructions and displays stacked PC/LR if another fault occurs. This fixes
a concrete defect consistent with the symptom; it is not a proven hardware
root cause without the missing fault PC or a successful v9.1 device run.

The relocated private development builds reproduced all 10 historical packages
byte-for-byte. The public source removes the private baseline-file dependency;
its candidate is required to reproduce the same v9.1 package.

## Reproducible offline coverage

`tools/run_checks.py` exercises target/host/raw-reference builds, package pins,
synthetic installation plus seven corruptions, full resource reconstruction,
3,000 random reads, 1,038 codec vectors, 512 engine frames/state comparisons,
138 compositor comparisons, PC-input leases/releases, JPEG decoding/bounds,
full-panel rotation, brightness acknowledgments and a fake-HID controller.
The separate browser fixture test checks its interaction flow without hardware.
The official pure package validator also accepted the unchanged candidate locally;
that proprietary validator is not redistributed or required by the public build.

Synthetic tests do not measure LCD transfer behavior, physical buttons, HID
throughput, JPEG-induced stalls, stack high-water use or charging behavior.
Static data+BSS is 80,364 bytes, plus four alignment bytes; the linker leaves
a 1,552-byte guard and an 8 KiB reserved stack. These are link-time figures.

## Hardware gate before release

On the qualified owner's unit: standalone boot; all physical controls; PC input
and release on blur/disconnect; preview on/off responsiveness and JPEG save;
180° flip and brightness; repeated power cycles; a longer play session;
post-install dual readback/preservation audit; and stock restoration.
Record observations and limitations before promoting or publishing the candidate.
No firmware was written to a device by the documentation/packaging workflow.
