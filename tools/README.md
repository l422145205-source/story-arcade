# Reproduce the story tools

```sh
python -m unittest discover -s tests -v
python tools/reproduce.py --out work/my-demo
```

Use a new output folder. Runtime helpers need only Python 3.10+ standard library. The script makes real CLI calls using fixed choices through original fictional packs, then checks idempotent retry, relay restoration and preservation of the original path after forking. These are tool reproductions, not a recording of an Agent or a human playtest.

Tracked examples are copied from the matching run in `examples/demo`. Don't replace them with private user saves. They contain spoilers beyond the opening/checkpoint views.

## Optional visual regeneration

Only the contributor renderer needs Pillow (`pip install Pillow`) and a locally available CJK font:

```sh
python tools/render_showcase.py --font /path/to/cjk-font.ttf --bold-font /path/to/cjk-bold.ttf
```

It draws original subway/ticket artwork and reads the tracked tool views for the clue counts, resource displays and retry/relay results. The GIF is an illustration of actual scripted tool outputs, not an Agent screen recording. No fonts, real photos, third-party characters or personal information are bundled. Graphics are not needed to run the Skill.
