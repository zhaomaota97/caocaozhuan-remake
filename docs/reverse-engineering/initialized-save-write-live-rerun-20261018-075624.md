# Initialized save write rerun

The corrected observer waited for initialization and retried direct commands
after collecting the actual game window. In this run:

- the save initializer completed with a nonzero buffer;
- direct `WM_COMMAND 101` was finally posted to the game window with
  `queued=true`;
- the save serializer entered with buffer `0xA0B978` and serialized data;
- after pressing `是`, the original process attempted both D/S save-partition
  file creation paths and remained alive through the bounded observation.

Raw evidence:
`analysis/live-startup-20261018-075624/events.jsonl`.

The observer's ANSI path display renders the slot-0 path with replacement
characters because the native slot selector is `0xFFFFFFFF` and the path
construction uses the original dialog's internal slot convention. This run is
therefore strong evidence of the initialized write chain, but file replacement
is not claimed until raw path bytes and a successful file handle are captured.
