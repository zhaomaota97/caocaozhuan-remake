$ErrorActionPreference = 'Stop'

python tools/inventory_game_formats.py
python tools/verify_yuxi_critical_static.py
python tools/verify_hit_static.py
python tools/verify_ui_save_chain.py
python tools/verify_save_objects_native.py
python tools/verify_battle_turn_chain.py
python tools/verify_completion_audit.py
python tools/verify_dll_boundaries.py
python tools/export_eex_handler_semantics.py
python tools/verify_eex_side_effect_candidates.py
python tools/verify_eex_side_effect_native.py
python tools/verify_combat_magnitude_native.py
python tools/verify_battle_save_native.py
python tools/verify_eex_branch_selection_native.py
python tools/verify_eex_numeric_predicates_native.py
python tools/scan_data_entry_references.py
python tools/build_eex_coverage_matrix.py
python tools/verify_native_target_shapes.py
python tools/summarize_target_shape_matrix.py
python tools/verify_open_work_items.py
python tools/verify_progress_snapshot.py
python -m compileall -q tools
python tools/build_verification_manifest.py

Write-Host 'Reverse-engineering regression checks completed.'
Write-Host 'Open semantic scope: EEX full playthrough, DLL business semantics, AI/battle state machine, DATA.E5 entries, and unmodified UI save/load round trips.'
