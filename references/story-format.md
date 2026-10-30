# StoryArcade JSON v1

Runtime uses Python standard library only. JSON objects are data, never code. Files are limited to 2 MB; IDs use 1–80 letters/digits/`_.-`. See [rain-shop.json](../assets/rain-shop.json) for a complete small case and [last-train.json](../assets/last-train.json) for role/flag/variable examples. Both contain spoilers.

| Root field | Meaning |
| --- | --- |
| `format` | `story-arcade/1` |
| `id`, `title`, `opening`, `goal`, `tone` | Stable case ID and public setup; non-empty strings |
| `budget` | Initial integer resource, 1–90; narrative “time units”, not measured real minutes |
| `content_notes[]` | Public genre/content notes |
| `roles[]` | Unique `id`, `label`, `opening`, `initial_facts[]` |
| `facts[]` | Unique `id`, `text`, `kind`, `source` |
| `npcs[]` | Unique `id`, `name`, `persona`, `initial_facts[]`; optional list |
| `flags` | Object of declared boolean defaults; optional |
| `variables[]` | Unique `id`, `label`, integer `min`, `max`, `initial`; bounds within -1000…1000 |
| `actions[]` | Unique IDs and transitions below |
| `endings[]` | Unique IDs, closing requirements and text |
| `author` | Optional private design notes/canonical answer; never included in normal projections |

Fact kinds: `observation` (seen/heard material), `testimony` (someone's claim), `inference` (a stated interpretation), `canon` (authored underlying truth). A fact is visible only if the current perspective knows its ID; visibility does not turn testimony into proof.

## Conditions

Allowed condition keys are `all`, `any`, `flags`, `variables`. All supplied clauses are combined with AND. `all` means all listed fact IDs are known. A non-empty `any` means at least one listed fact is known. Empty/missing `any` adds no condition. Flags must exactly match booleans. Variable conditions use inclusive `min` and/or `max`.

```json
{
  "all":["evidence-a","evidence-b"],
  "flags":{"shared":false},
  "variables":{"trust":{"min":2}}
}
```

References must exist in the same pack. No Python expressions, scripts, external URLs or arbitrary condition evaluators are executed.

## Actions

Required: `id`, `label`, `cost` (integer 0–90), `outcome` (fixed, player-visible result). Optional `roles[]` restricts perspectives; missing/empty means any role. Optional `requires` uses the condition structure. Optional `ending` names one ending.

Optional `effects` supports:

- `reveal[]`: fact IDs added to the active player's known set.
- `flags`: declared booleans to set.
- `variables`: integer deltas to declared variables. A choice that would exceed a bound is unavailable; deltas aren't silently clamped.
- `npc_reveal`: NPC ID → list of fact IDs to add to that character's context.

An action is available only if it is unused, affordable, allowed for the role, satisfies its conditions, keeps variable bounds valid, and—when closing—satisfies the ending's requirements **before** effects. Its own effects cannot manufacture the evidence needed to unlock that ending. Each action is once-only. A successful act subtracts cost, applies effects and appends its fixed outcome. The host may voice that outcome but not rewrite its facts.

## Endings

Required: `id`, `title`, `text`, `classification` (`resolved` or `open`). Optional `requires` and `reveal[]`. Upon an eligible closing action the ending becomes fixed, listed facts are released to the current player, and no further actions are available. An open ending can deliberately keep canon undisclosed.

## Saves, replay and concurrency

A save has exactly `format`, `story_id`, `story_sha256`, `role`, `events`. Every event has exactly `id` and `action_id`. No freeform user messages or cached “known facts” are trusted. State is reconstructed from the matching pack and every legal event in order. This catches inconsistent edits, not malicious users who legitimately replay another allowed path; saves are not signed.

The story digest is SHA-256 of canonical sorted JSON (UTF-8, finite numbers only). Every content edit changes the version binding; whitespace changes do not. The update token is SHA-256 of the actual save bytes. `act` requires that token for a new event. Replaying the same prior event/action is a no-op even with its old token; an event ID used for a different action is rejected.

`act` uses an exclusive sidecar lock, rechecks the file and atomically replaces a fully written temporary file. Busy locks and conflicting/stale writes leave the save unchanged; it doesn't break someone else's lock. Locks coordinate these tools and don't constrain unrelated editors. `new`, `fork` and relay exports require new destinations. No network or external state is involved.

## Scope of the guarantees

The helper validates structure, references, transitions, resources and generated projection fields. It does not semantically inspect authored text for hidden spoilers or prove host-generated prose consistent. All canon remains in the original case file; filtering is a narrative/view convention, not filesystem isolation, encryption, authentication or adversarial protection.
