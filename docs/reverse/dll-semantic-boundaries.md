# DLL Semantic Boundaries

The DLL inventory contains six modules, 515 recovered functions, and 1,866 call edges. Four resource modules (`Cmdicon.dll`, `Itemicon.dll`, `Mapatr.dll`, and `Mgcicon.dll`) have the identical `.text` SHA-256 `e48333d5c7e7e1fc3e420d4070c8b94f25f258cf14be84d46582b9ecc3c002ff`; their semantic difference is in resource sections, not executable code. Their current evidence therefore supports a shared resource-window loader, while per-icon business semantics are not separate code paths.

`Koeicda.dll` has 20 verified exports and a message protocol to MP3Serv for play, stop, pause, and resume. `AutoDLL.dll` has 108 recovered functions and exports `ASave`/`dummy`; `ASave` is a jump stub into `Ekd5.exe` (`0x44E1D3` or `0x44E6EE` depending on a global switch), not an independent save codec. The remaining DLL functions have complete inventory/call-edge evidence but require runtime call-site tracing before assigning business names.
