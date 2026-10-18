# Scenario to Map/Artwork Resource Links

`tools/export_scenario_resource_links.py` decodes EEX opcode 39 scene commands, resolves their map IDs through `analysis/battle-maps/resource-links.json`, and invokes the original dispatcher with the re-encoded instruction.

The current run resolves 58 scene commands from the EEX corpus to 58 unique maps. Native dispatch validation is `58/58`: status `2`, consumed instruction length, mode `3`, common-index `255`, map ID, and global change marker all match the expected native result. Each record includes the corresponding `HmNN.e5` artwork, `Spalet.e5` palette entry, and map tile dimensions in `analysis/scenario-resource-links.json` and `.csv`.
