# Native ordinary AI attack score

`src/rules/aiAttackScore.ts` ports the explicitly documented ordinary branch
of native `0x438A20`. It covers lethal prediction (80), nonzero damage ratio
(16), low current-HP ratio (16), attacker mode 1 (10), default score (2),
target flag bit 3 (+8), identity 174 leader-match adjustment (+8 or +4),
same-side/dead/covered rejection, and the candidate risk decrement boundary.

The leader-match bit and candidate coverage are explicit inputs. They are not
hardcoded from a saved slot because the native probe controlled those fields.
Special-range multi-target scoring, full terrain/coverage map scoring and the
complete AI turn remain separate paths. This helper therefore does not claim
to replace the current turn selector until those inputs are wired from native
scenario state.
