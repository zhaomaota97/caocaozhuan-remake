# Reverse tool source archive

All 277 regular source files from the reverse workspace tools directory are
archived verbatim under `tool-sources/`. Their filenames, lengths and SHA-256
hashes are in `TOOL-SOURCES-MANIFEST.json`. No interpreter caches or nested
runtime directories are copied. The archive includes extraction, EEX decoding,
native probes, save codecs, reporting and validation scripts and their sibling
source dependencies. It is source preservation, not a standalone native lab.

The original scripts retain root-relative paths to `analysis/`, original
binaries and fixtures. To reproduce a native report, run the corresponding
script in the original reverse workspace layout with its required Python
dependencies (for example Frida, pefile or Pillow). Some scripts write results
into that workspace or the sibling remake. Do not run archived scripts in
place assuming their root resolves correctly. Web runtime never imports them.
Native probes may intentionally replace presentation leaves; consult each
script and report for evidence scope before treating results as a playthrough.

Refresh the exact archive with:

```powershell
node tools/sync-reverse-tools.mjs <reverse-workspace-tools-directory>
```

`npm run test:items` now includes archive integrity and all newly migrated
consumable/resource rules. This command is included in `verify:all`. Hash
checks prove preservation only; they do not prove every archived tool can
currently execute or that all reverse-engineering work is complete.
