# Evidence and remaining checks

[日本語](VALIDATION.ja.md)

The [2026-11-17 public-source check record](TEST_RESULTS.md) lists the executed host checks.

| Version | Device evidence | Limit |
| --- | --- | --- |
| Native v7 | Owner accepted standalone gameplay, four buttons, gap-free HUD and improved scanout on one C5 | Does not qualify other units or long-duration stability |
| Native v8 | Owner confirmed PC controls on that C5 | Its 80×43 preview was too coarse for play |
| Native v9 | Owner saw banner/first game image, then CPU FAULT with CFSR `00010000` | Exact stacked fault PC was not captured |
| Native v9.1 / 0.1.0-rc.1 | Owner confirmed standalone play, PC controls, preview/enlarge/save, physical flip/brightness, then normal operation after restoring stock V8.5; live HID/JPEG reception recorded | One C5 only; long-duration stability and new full Flash preservation audit remain unverified |

v9 accidentally used `fpv5-sp-d16` with Cortex-M4 and emitted eight VRINTZ
instructions unsupported by that target. v9.1 uses `fpv4-sp-d16`, rejects unknown
M4 instructions and displays stacked PC/LR if another fault occurs. This fixes
a concrete defect consistent with the symptom. The successful v9.1 gameplay and
preview run supports the correction, but the original v9 fault PC was not captured.

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

## Owner check and remaining work

On 2026-11-17 the owner confirmed the exact v9.1 package path and provided an
official-updater screenshot showing successful erase/install/verify and restart.
The owner reported normal gameplay, PC keyboard control, preview enlargement/save,
physical 180° rotation and brightness adjustment. Read-only observation collected
220 status samples over about 90 seconds, all connected with application error 0.
Key masks, key releases, applied brightness 10/30/65/100 and both rotation states
were observed; actual 320×172 JPEGs were decoded. See the
[sanitized hardware-check summary](validation/owner-unit-v9.1-20261117.json).

Initially Windows did not enumerate the C5. After a power/reconnection cycle,
HID and live preview appeared. The exact cause was not established; this is not
a demonstrated USB firmware defect. Fully remove other power feeds when restarting.

This supports a **one-unit functional Pre-release**, not stable or broad hardware
qualification. Long-duration stability, a new post-install dual-read preservation
audit remain unverified. The owner subsequently reported restoring stock V8.5
on the same unit and trying its functions without observing problems. This
functional check does not prove byte-for-byte Flash preservation or calibration
accuracy. Disconnect/blur
release timing and repeated power-cycle behavior have offline coverage but no
separate physical acceptance record here. The assistant did not flash the unit.
