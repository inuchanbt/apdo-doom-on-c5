# Third-party notices

The combined firmware and corresponding source are GPL-2.0-or-later. See
`LICENSE` / `COPYING` and the notices in each source file. The initial empty
repository's MIT text is retained in `notices/initial-repository-MIT.txt`; it
does not replace the GPL notices of the engine and C5 firmware.

| Component | Location / provenance | Terms |
| --- | --- | --- |
| DOOM / Chocolate Doom / DMC100-Doom | `vendor/dmc100-doom`; engine and doomgeneric revisions in `SOURCE_LOCK.json` | GPL-2.0-or-later; detailed copyrights in `vendor/dmc100-doom/CREDITS.md` and source headers |
| KWS-X1 / KM003C-derived bridge | `native/doom_bridge.c`, engine patch in `patches/` | GPL-2.0-or-later, original source notices retained |
| Freedoom 0.13.0 | Converted E1M1 data, generated asset tables and startup banner | Modified BSD; both `notices/freedoom-0.13.0/COPYING.txt` and `CREDITS.txt` are included |
| TinyJPEG | `firmware/tiny_jpeg.original.h`, adapted by `adapt_jpeg.py` | Upstream public domain / irrevocable fallback license, full text retained in the original header |
| Font and upstream panel code | DMC100-Doom source tree | Original notices and `vendor/dmc100-doom/LICENSES/` retained; see upstream credits |
| C5 enclosure picture | `firmware/web/WITRN_C5.png`, supplied for the owner's C5 controller | Device/product artwork is separate from the software license; WITRN marks remain their owner's |

The vendor tree includes the pinned doomgeneric input source used for generation.
The engine is a local modified snapshot, not an unmodified upstream checkout;
the KWS-X1 patch is retained alongside it. C5 platform code and the source/build
rules are shipped with the candidate kit. Generated data includes only Freedoom,
not a commercial DOOM WAD. Preserve the applicable license and attribution files
when redistributing the binary or source.

Python, hidapi, Pillow, LLVM and the official WITRN updater are tools installed
separately, not bundled in this source or candidate kit.
