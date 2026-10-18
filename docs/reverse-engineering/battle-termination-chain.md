# Battle Termination Chain Index

`tools/index_battle_termination_chain.py` indexes the 11 native routines that participate in target scoring, faction predicates, turn refresh, and the observed termination branch. All 11 have recovered pseudocode. The JSON records their direct `FUN_` calls and referenced `DAT_` globals so later dynamic probes can target exact state transitions.

This is an index of evidence, not a victory-condition claim. The final victory/defeat integration still requires a live battle trace that reaches the end-state dispatcher.
