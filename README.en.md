<p align="center"><img src="media/storyarcade-cover.png" alt="StoryArcade: don't just read the ending. Step inside and make a choice." width="100%"></p>

# StoryArcade 🎟️ Step inside the story

**Your Agent hosts. You investigate. Tools keep the clues, consequences and save files.**

Play an original short mystery, try another perspective, turn story notes into a playable case, or let a friend continue from your checkpoint.

[中文](README.md) · [Actual tool outputs](examples/README.md) · [Skill entrypoint](SKILL.md) · [Design evidence](references/design-evidence.md)

![Story checks](https://github.com/l422145205-source/story-arcade/actions/workflows/ci.yml/badge.svg)

## 23:17. The display says seven. You can only see six.

A last train pauses at a fictional unnamed station. The announcement repeats: **“Don't take this sentence outside the carriage.”**

Read the small print? Listen to the loop? Ask the attendant? You have a limited investigation budget, and public or private handling of a clue can lead to different consequences.

<img src="media/first-scene.png" alt="Three-panel original opening: a count of seven, six visible figures, and actual choices to inspect the screen, compare the audio or ask the attendant." width="100%">

The bundled original case is **Last Train: The Seventh Passenger**. A gentler alternative, **Rainy Convenience Store: The Thirteenth Coffee**, starts with a twelve-cup order and thirteen cups on the counter. The authored packs and images are currently Chinese; the host can narrate in your language while keeping IDs and state unchanged.

## Install and say one sentence

```sh
npx skills add l422145205-source/story-arcade
```

> Use `$story-arcade` to host Last Train from the passenger perspective. Wait for my actions, save locally in this workspace, and don't reveal the ending yet.

Use a compatible Agent with local file access and Python execution. Runtime helpers require **Python 3.10+ standard library only**. No additional model service, database or API key is needed. The host Agent handles interpretation and prose.

## What does the Skill package?

| Want to… | Reusable behavior |
| --- | --- |
| Continue next time | A version-bound event save reconstructs the same established state |
| Keep characters from being all-knowing | Active player and NPC contexts are projected separately |
| Make choices matter | Declared prerequisites, resource costs, flags, bounded variables and ending gates execute in tools |
| Try a different decision | Fork a checkpoint into a new save while preserving the original path |
| Test a plot | Author-only state exploration provides reachable ending routes and explicit coverage limits |

Ordinary chat can do this with equivalent instructions, files and tools. Installation packages the workflow and executable operations for reuse; it does not add a new model or guarantee spoiler-free language generation.

<img src="media/play-save.gif" alt="Illustrated sequence of actual scripted CLI outputs: opening, two choices, save/retry and relay restoration." width="100%">

The GIF illustrates actual tool results on fictional content. It is not an Agent screen recording or human playtest.

## Six ways to use it

1. **A short mystery break.** Speak naturally; the Agent maps your action to a currently authored choice. Decisive evidence enters the save after a successful transition.
2. **A different point of view.** A passenger starts from visible events; an audio volunteer has one additional observation. Separate saves preserve their different starting knowledge.
3. **A relay with a friend.** Export the current perspective's recap and event save. The recipient uses the same case version to continue; no automatic sending or cloud sync.
4. **“What if I had…?”** Fork a saved prefix, choose another route and keep both consequences.
5. **Turn an original idea into a case.** The Agent helps author observations, testimony, inferences, canon and conditions using a small JSON format. [Authoring guide](references/authoring.md).
6. **Find plot blockers.** Check references, prerequisites, resources and reachable endings. A bounded search reports incomplete coverage instead of claiming an unobserved route impossible.

<img src="media/perspective-cards.png" alt="Actual initial context counts: two for the passenger, three for the volunteer and two for the attendant. Each view is supplied separately." width="100%">

These are authored short cases, not an unrestricted simulation. Unsupported decisive actions require an explicit extension, rather than a claim that an imaginary transition was saved. The full open-source pack contains the author solution; projections are a narrative convention, not encryption or filesystem isolation.

<img src="media/branch-relay.png" alt="A two-choice checkpoint can be relayed, continued on the original route or forked into an alternate path. The recorded original remains intact." width="100%">

## What has actually been checked?

- Repeating the same event does not spend again and leaves file bytes unchanged.
- A relay restores the same progress and known clues.
- An alternate path reaches a different ending while preserving the original save.
- Complete small-state exploration finds authored ending routes for all three starting perspectives across the two packs.
- Locked actions, conflicting event IDs and stale updates are rejected without overwriting the current save.

[Inspect the outputs, with spoiler warnings](examples/README.md). These checks concern tools and authored rules, not model quality, literary coherence, enjoyment or adoption.

## Run the examples without a model

Clone the repository, then use a new output directory:

```sh
python -m unittest discover -s tests -v
python tools/reproduce.py --out work/my-demo
```

The reproduction makes real CLI calls, including retry, relay, branching and author audits. It needs no model or network. [Hosting](references/hosting.md) · [Format](references/story-format.md) · [Media reproduction](tools/README.md).

## Why this shape?

[AI Dungeon's official documentation](https://help.aidungeon.com/faq/plot-components) describes persistent plot/context components; [ink](https://www.inklestudios.com/ink/) makes testable branches part of writing. Recent research discusses [author/player design roles](https://arxiv.org/abs/2601.18785) and [long-horizon narrative consistency](https://arxiv.org/abs/2608.08160).

This Skill uses explicit state transitions for decisive facts while leaving language to the host. It uses its own small format, doesn't import those products' projects, and hasn't reproduced the papers' experiments. [Evidence and limitations](references/design-evidence.md).

## Leave a ticket for the next player

Try one case and [report a redacted action-matching or storytelling problem](https://github.com/l422145205-source/story-arcade/issues): what you wanted to do, which choices were visible and what broke the experience. Original small cases are welcome.

If the idea is worth continuing, a **Star** or a shared opening card helps another player or writer find it. MIT licensed. Keep personal information, private conversations and unauthorized source material out of public examples.
