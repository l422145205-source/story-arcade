# Hosting, resuming and passing a story on

Read this for play, continuation and alternate paths. It is enough to run a supplied case; do not load the full author JSON unless the user asks for creation, testing or spoilers.

## A useful first turn

`catalog --story <path>` returns title, opening, goal, content notes and perspective names. For a broad “play a short mystery” request, default to `last-train.json` / `passenger`. For a lighter tone use `rain-shop.json` / `customer`. If the user chooses another supplied role, start a separate save; changing the role field in an existing save would rewrite what that character knew from the beginning.

`new --story <path> --role <role> --session <new-save>` creates a local event save and returns JSON. The `opening`/`last_outcome` and visible facts provide the first scene. Use a few sentences and invite a choice. “格调查时间” is an authored resource, not measured elapsed minutes. Trust values are story mechanics, not psychological assessments.

## Choose, apply, narrate

`show --story <path> --session <save>` is read-only. The view has:

- Current role and remaining resource.
- Known facts, each with kind and source.
- Journal of committed actions and their fixed outcomes.
- Available actions only, with IDs, player-facing labels and costs.
- A full-file `save_sha256` for guarded updates.

For example, “我想先看屏幕下面写了什么” maps to a visible action `read-screen`. Call `act` with a stable event ID such as `t1`; record the successful result before describing a new clue. A request like “去问问” might fit several choices, so clarify which person/topic if the consequences differ. Do not ask the user to type JSON or hashes.

If a request is atmospheric (look around, repeat an already obtained statement), respond from current facts without inventing a state-changing event. If it needs a new mechanic or decisive clue, explain the available scope briefly and offer a matching choice or an explicit authoring extension. Don't claim the runtime supports unrestricted simulation.

An unavailable action fails with a generic message, without printing hidden conditions. Don't brute-force hidden action IDs. If a tool fails, use the last confirmed view and state that the attempted action was not saved. A matching prior event/action retry returns the current state without spending again, even if its old expected hash is stale. A new action requires the current hash. Conflicting event IDs, a busy lock or a changed file require reconciliation; do not delete another writer's lock.

## Dialogue without all-knowing characters

`npc --story <path> --session <save> --character attendant` returns only that NPC's declared current knowledge and persona. The player finding a clue does not automatically tell every NPC about it. Explicit action effects can pass information to a character.

Use this context to voice a character consistently while honoring the active action's outcome and release conditions. Do not expose information just because the character context contains it. The host still interprets and generates language; this projection cannot guarantee semantic consistency or stop a determined user/Agent from reading the author file.

## Stop and resume

An action already persists its event. When the user says “save here”, summarize only this view's last developments and location of the chosen save. Don't close the case by selecting an ending. Later:

```sh
python <skill-dir>/scripts/storyarcade.py show --story <story.json> --session <save.json>
```

The story hash is calculated from canonical JSON, so whitespace changes are harmless, while changed story content is rejected. Preserve the matching pack for an existing run. Don't silently migrate outcomes to a rewritten case.

## What if I had chosen differently?

```sh
python <skill-dir>/scripts/storyarcade.py fork --story <story.json> --session <save.json> --at 2 --out <new-branch.save.json>
```

This replays the first two committed events into a new save. It does not modify the original path. Run `show` on the new file, let the user choose an available alternate action, then continue there. The original branch remains available. Checkpoint zero starts from the same perspective; beyond the saved event count is invalid.

## Let a friend continue

```sh
python <skill-dir>/scripts/storyarcade.py relay --story <story.json> --session <save.json> --out <new-relay-folder>
```

It writes `relay.md` (current player recap, facts and choices) plus `relay.save.json` (version-bound events). The recipient needs the same case version and a compatible Agent/Python environment. They resume the same perspective, not a new all-knowing role. The local export is not automatically sent, posted, synced or encrypted. A source pack openly contains spoilers; only the handoff projection omits unrevealed information.

The folder must be new; previous handoffs are not overwritten. A user request to export locally is enough to create the files; request a destination only when necessary for actual sending.
