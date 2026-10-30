#!/usr/bin/env python3
"""StoryArcade — play and test stories in an Agent, with local replayable state."""
import argparse
import json
from pathlib import Path
import sys

from engine import (act_file, audit, fork, load, new_session, npc_view, pretty,
                    project, relay_bundle, render, replay, validate_world, write_new)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ['catalog', 'new', 'show', 'act', 'npc', 'fork', 'relay', 'audit']:
        p = commands.add_parser(name); p.add_argument('--story', required=True, type=Path)
        if name == 'new':
            p.add_argument('--role', required=True); p.add_argument('--session', required=True, type=Path)
        elif name in {'show', 'act', 'npc', 'fork', 'relay'}:
            p.add_argument('--session', required=True, type=Path)
        if name == 'act':
            p.add_argument('--action', required=True); p.add_argument('--event', required=True)
            p.add_argument('--expect-sha256', required=True)
        if name == 'npc': p.add_argument('--character', required=True)
        if name == 'fork':
            p.add_argument('--at', required=True, type=int); p.add_argument('--out', required=True, type=Path)
        if name == 'relay': p.add_argument('--out', required=True, type=Path)
        if name in {'new', 'show', 'act'}: p.add_argument('--format', choices=['json', 'md'], default='json')
        if name == 'audit': p.add_argument('--max-states', type=int, default=10000)
    args = parser.parse_args()
    try:
        w, _ = load(args.story); validate_world(w)
        command = args.command
        if command == 'catalog':
            value = {'id': w['id'], 'title': w['title'], 'opening': w['opening'], 'goal': w['goal'],
                     'tone': w['tone'], 'content_notes': w.get('content_notes', []),
                     'roles': [{'id': r['id'], 'label': r['label']} for r in w['roles']]}
        elif command == 'audit':
            value = audit(w, args.max_states)
        elif command == 'new':
            if args.session.resolve() == args.story.resolve(): raise ValueError('Save cannot overwrite the story')
            session = new_session(w, args.role); write_new(args.session, session)
            value = project(w, session); value['save_sha256'] = load(args.session)[1]
        else:
            session, sha = load(args.session); replay(w, session)
            if command == 'show':
                value = project(w, session); value['save_sha256'] = sha
            elif command == 'act':
                if args.session.resolve() == args.story.resolve(): raise ValueError('Save cannot overwrite the story')
                session, state, sha, repeated = act_file(w, args.session, args.event, args.action, args.expect_sha256)
                value = project(w, session, state); value.update(save_sha256=sha, replayed_event=repeated)
            elif command == 'npc': value = npc_view(w, session, args.character)
            elif command == 'fork':
                if args.out.resolve() in {args.session.resolve(), args.story.resolve()}: raise ValueError('Fork needs a separate new file')
                value = fork(w, session, args.at); write_new(args.out, value)
                value = project(w, value); value['save_sha256'] = load(args.out)[1]
            else: value = relay_bundle(w, session, args.out)
        if getattr(args, 'format', None) == 'md': print(render(value), end='')
        else: print(pretty(value), end='')
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__': main()
