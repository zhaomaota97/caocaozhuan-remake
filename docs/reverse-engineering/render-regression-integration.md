# Integrated rendering regression run

The full gate now includes `test:render-rules` (18 tests): native indexed
darkening, full actor renderer gates, status colors/icons, idle phase,
browser texture pixels, terrain masks, palette sharing and all 302 combat
sheet frames. The tool source archive now contains 297 original files;
every Git index blob matches its recorded original byte hash.

Current run passed build, independent runtime scan (491 files), asset
integrity (11,185 files), source resource migration (329 originals), battle
rules (31), attribute/EEX rules (17), item rules (23), item presentation
rules (10), render rules (18), and scenario browser checks (2). That is
101 passing tests across the named commands.

The initial full run failed five render-page startup waits with eight
concurrent browsers decoding the full resource bank. The render group now
uses two workers, with unchanged assertions/timeouts. All 18 then passed,
followed by the two scenario checks. Earlier successful groups were not
repeated because no runtime source changed during this adjustment. This
record does not assert that a single subsequent `verify:all` invocation
was executed after the worker-count edit.

These checks prove only their stated resource/rule/browser boundaries, not
campaign completion, full EEX/AI logic, all effects or pixel-perfect UI.
