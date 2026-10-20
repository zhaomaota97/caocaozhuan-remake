# Native ordinary AI attack score

`src/rules/aiAttackScore.ts` ports the explicitly documented ordinary branch
of native `0x438A20`. It covers lethal prediction (80), nonzero damage ratio
(16), low current-HP ratio (16), attacker mode 1 (10), default score (2),
target flag bit 3 (+8), identity below 174 adjustment (+8 for leader match
or target slot 35, otherwise +4), and the candidate risk decrement boundary.
Identity 174 itself receives no identity bonus. Same-side input skips the
base score but can still receive flag and identity bonuses in this leaf;
the caller must filter allied candidates before invoking it.

The class-filter input (historically named `covered` in the Web interface)
rejects only scores below 75. Candidate attack coverage subtracts one only
when the score exceeds one. These branches were corrected after direct
comparison with all 2,880 native return records; every record now matches.

The leader-match bit and candidate coverage are explicit inputs. They are not
hardcoded from a saved slot because the native probe controlled those fields.
Special-range multi-target scoring, full terrain/coverage map scoring and the
complete AI turn remain separate paths. This helper therefore does not claim
to replace the current turn selector until those inputs are wired from native
scenario state.

The enemy turn now uses this ordinary score for candidate ordering with the
currently known inputs: predicted damage, current/max HP and target flags.
Identity/leader and coverage values remain explicit at their controlled
defaults until those fields are recovered from each scenario controller.
Those defaults are incomplete integration placeholders, not evidence of
the native values in actual campaign state. The current turn selector is
therefore still not a faithful complete native AI implementation.
