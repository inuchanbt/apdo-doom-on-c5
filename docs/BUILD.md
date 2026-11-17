# Build and reproduce

[日本語](BUILD.ja.md)

Tested on Windows x64 with Python 3.14, llvm-mingw
`20261020-ucrt-x86_64` (Clang 23.1.4), hidapi 0.15.0 and Pillow 12.2.0.
The compiler is not redistributed. Use a local llvm-mingw installation and set
`APDO_LLVM_BIN` to its `bin` directory. Other toolchains have not been qualified.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:APDO_LLVM_BIN = 'C:\your\llvm-mingw\bin'
.\.venv\Scripts\python.exe firmware\build.py
.\.venv\Scripts\python.exe firmware\test_package.py
```

The target is Cortex-M4F, `fpv4-sp-d16`, hard-float, with the checked linker map.
Build output is `firmware/build/`. The original candidate package is 917,504
bytes; its pinned SHA-256 is in `SOURCE_LOCK.json`. The build rejects unknown
Cortex-M4 instructions; the package test checks the expected package, all hashed
source inputs, activation/erase simulation and seven corruption cases.
No private Flash image, WITRN updater assembly, device or network is needed for
the build itself. Historical baseline hashes are identification metadata only.

## Offline tests

```powershell
.\.venv\Scripts\python.exe tools\run_checks.py
```

This builds target/host/raw-reference versions and runs the existing source,
asset, engine, compositor, PC-input, JPEG, controller and read-only-protocol
checks. Logs go to ignored `verification/`. No real HID device is opened.
For the existing browser fixture test, run `node firmware/test_ui.mjs` with
Chrome installed at its configured Windows path; it uses CDP pipes and
intercepted responses, without a device. No browser hardware claim follows.

## Resource regeneration

The checked-in generated data is sufficient to compile. To reproduce it, obtain
the [Freedoom 0.13.0 ZIP](https://github.com/freedoom/freedoom/releases/download/v0.13.0/freedoom-0.13.0.zip).
The converter checks SHA-256
`3f9b264f3e3ce503b4fb7f6bdcb1f419d93c7b546f4df3e874dd878db9688f59`.

```powershell
.\.venv\Scripts\python.exe tools\regenerate_pack.py --freedoom-zip C:\downloads\freedoom-0.13.0.zip
.\.venv\Scripts\python.exe firmware\prepare.py
.\.venv\Scripts\python.exe firmware\adapt_jpeg.py
```

The complete reduced-art pack must reproduce SHA-256
`8e020d3822edf873b0209c92dfbb6518bb8a92c6fe9fdb64be17d66699ae2664`.
Freedoom source notices and the pinned doomgeneric input tree are included.
The startup banner's conversion details and hash are in
`firmware/freedoom-banner.json`; its converted bytes are checked in and tested.

## Prepare a local kit

After the checks pass:

```powershell
.\.venv\Scripts\python.exe tools\package.py
```

The resulting `dist/` archives are local review artifacts. This command does
not create a GitHub release, tag, commit or network upload. The install ZIP
contains the matching source, required notices and per-file checksums. It
does not contain the compiler, official updater, stock firmware, private
backups, `.git`, virtual environments or other meter projects.

Vendored DMC100-Doom sources include their upstream development tools. Those
target different hardware; use only this project's documented C5 helpers on a C5.
