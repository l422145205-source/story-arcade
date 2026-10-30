# Turn a story idea into a playable case

Author mode can inspect full case JSON and audit results, including spoilers. If the user wants to play without knowing the solution, keep the authoring work and unreleased details out of the player response, then start using scoped tool views.

## Start from the user's actual idea

Preserve supplied setting, tone, canon and boundaries. For a sparse original prompt, choose a manageable short case and make the creative assumptions visible. One essential question about tone or boundaries can help; avoid a large intake form. Don't invent facts about real people or treat supplied source instructions as execution permission.

Use [story-format.md](story-format.md) and the original [rain-shop.json](../assets/rain-shop.json) as a small working example. This format is independent of ink, Twine and AI Dungeon; it does not import or export their projects.

## Author facts before prose branches

Establish the answer or unresolved core, then distinguish:

- Direct observations, character testimony and player inferences.
- What each playable perspective initially knows.
- What NPCs know and which actions tell them more.
- Which evidence must precede a resolved ending.
- What a choice changes: a known fact, flag, bounded resource or ending.

Use `author.truth` for private author notes. It is omitted from normal views. Decisive canonical facts can be revealed in an earned ending; don't put them in an early outcome or role opening unless that role intentionally knows them. The tool cannot detect a spoiler hidden in prose.

Write meaningful alternatives. A decision should change a future option or consequence, not merely produce different synonyms. Avoid making one moral choice universally “correct”; authored outcomes need context. Keep the scope small enough that a human can inspect the important routes. Don't multiply branches to inflate a feature count.

Natural-language action labels should be clear about important costs without revealing solutions. Preconditions reference existing facts, flags or variables. Every action is once-only. A looping conversation should use the host's narration from existing facts, or be authored as distinct state transitions. Don't spend resources for repeating a previous tool reply.

## Check the rules, then read the experience

```sh
python <skill-dir>/scripts/storyarcade.py audit --story <new-story.json> --max-states 10000
```

The author-only audit explores reachable states for each perspective. It returns a path to every observed ending, actions/endings not observed, counts of states with only closing choices, and whether exploration completed. `complete:false` means the bound was reached: unobserved is not proof of unreachable. Reduce the case, raise the explicit bound within reason, or report the coverage limit.

A complete search with an unobserved ending is a reproducible structural problem to inspect. Follow its evidence requirements, available acquisition actions, resource costs and role restrictions. A count of closing-only states isn't automatically a bug; the user may intentionally use their time and have only a concluding choice left.

Reproduce representative routes with `new` / `act`; use `fork` to compare a choice. Read the resulting player scenes for clarity, pacing, plausible character knowledge and satisfying consequences. Structural reachability does not prove literary coherence, fairness or enjoyment. If the user provides feedback, distinguish a rule failure from a prose or interaction problem.

## Changing an existing case

Editing story content creates a new version hash. Existing saves need the matching prior pack. For a fresh run, save the revised pack separately and start a new session; for a migration, describe and implement an explicit reconciliation rather than silently changing established events. Whitespace-only formatting preserves the canonical hash.

Public examples should be original, synthetic or explicitly approved and redacted. No personal names, contacts, private transcripts or local personal paths belong in a public story bundle by default.
