"""Deterministic story state and scoped projections. No models, network or eval()."""
from __future__ import annotations

from collections import deque
import copy
import hashlib
import html
import json
import os
from pathlib import Path
import re
import tempfile

FORMAT = 'story-arcade/1'
LIMIT = 2_000_000


def ident(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9_.-]{1,80}', value):
        raise ValueError('IDs must use 1–80 letters, digits, _, . or -')
    return value


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Expected non-empty text')
    return value


def integer(value, low=0, high=1000):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f'Expected integer from {low} to {high}')
    return value


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def pretty(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


def load(path):
    raw = Path(path).read_bytes()
    if len(raw) > LIMIT:
        raise ValueError('File exceeds 2 MB')
    def invalid_constant(value):
        raise ValueError(f'Non-finite number is not allowed: {value}')
    value = json.loads(raw.decode('utf-8-sig'), parse_constant=invalid_constant)
    if not isinstance(value, dict):
        raise ValueError('Expected a JSON object')
    return value, hashlib.sha256(raw).hexdigest()


def indexed(rows, kind):
    if not isinstance(rows, list):
        raise ValueError(f'{kind} must be a list')
    result = {}
    for row in rows:
        key = ident(row['id'])
        if key in result:
            raise ValueError(f'Duplicate {kind} ID: {key}')
        result[key] = row
    return result


def refs(values, known, kind):
    if not isinstance(values, list) or any(v not in known for v in values):
        raise ValueError(f'Unknown or malformed {kind} references')
    if len(set(values)) != len(values):
        raise ValueError(f'Duplicate {kind} reference')


def validate_world(w):
    if w.get('format') != FORMAT:
        raise ValueError('Unsupported story format')
    ident(w['id'])
    for k in ('title', 'opening', 'goal', 'tone'):
        text(w[k])
    integer(w['budget'], 1, 90)
    facts = indexed(w['facts'], 'fact')
    roles = indexed(w['roles'], 'role')
    npcs = indexed(w.get('npcs', []), 'npc')
    actions = indexed(w['actions'], 'action')
    endings = indexed(w['endings'], 'ending')
    if not roles or not actions or not endings:
        raise ValueError('A story needs roles, actions and endings')
    variables = indexed(w.get('variables', []), 'variable')
    flags = w.get('flags', {})
    if not isinstance(flags, dict):
        raise ValueError('flags must be an object')
    for key, value in flags.items():
        ident(key)
        if not isinstance(value, bool):
            raise ValueError('Flag values must be boolean')
    for f in facts.values():
        text(f['text']); text(f['source'])
        if f['kind'] not in {'observation', 'testimony', 'inference', 'canon'}:
            raise ValueError('Fact kind must be observation, testimony, inference or canon')
    for role in roles.values():
        text(role['label']); text(role['opening'])
        refs(role['initial_facts'], facts, 'initial fact')
    for npc in npcs.values():
        text(npc['name']); text(npc['persona'])
        refs(npc['initial_facts'], facts, 'npc fact')
    for v in variables.values():
        text(v['label']); integer(v['min'], -1000); integer(v['max'], v['min'])
        integer(v['initial'], v['min'], v['max'])
    def condition(c):
        if not isinstance(c, dict) or set(c) - {'all', 'any', 'flags', 'variables'}:
            raise ValueError('Unknown condition; use all, any, flags or variables')
        for key in ('all', 'any'):
            refs(c.get(key, []), facts, 'condition fact')
        for key, value in c.get('flags', {}).items():
            if key not in flags or not isinstance(value, bool):
                raise ValueError('Unknown flag or non-boolean condition')
        for key, bound in c.get('variables', {}).items():
            if key not in variables or not isinstance(bound, dict) or not bound or set(bound) - {'min', 'max'}:
                raise ValueError('Invalid variable condition')
            for value in bound.values(): integer(value, -1000)
            if bound.get('min', -1000) > bound.get('max', 1000):
                raise ValueError('Variable condition min exceeds max')
    for ending in endings.values():
        text(ending['title']); text(ending['text'])
        condition(ending.get('requires', {}))
        refs(ending.get('reveal', []), facts, 'ending reveal')
        if ending.get('classification') not in {'resolved', 'open'}:
            raise ValueError('Ending classification must be resolved or open')
    for action in actions.values():
        text(action['label']); text(action['outcome']); integer(action['cost'], 0, 90)
        refs(action.get('roles', []), roles, 'action role')
        condition(action.get('requires', {}))
        effect = action.get('effects', {})
        if not isinstance(effect, dict) or set(effect) - {'reveal', 'flags', 'variables', 'npc_reveal'}:
            raise ValueError('Unknown effect')
        refs(effect.get('reveal', []), facts, 'effect fact')
        for key, value in effect.get('flags', {}).items():
            if key not in flags or not isinstance(value, bool):
                raise ValueError('Unknown flag or non-boolean effect')
        for key, value in effect.get('variables', {}).items():
            if key not in variables: raise ValueError('Unknown variable effect')
            integer(value, -1000)
        for key, values in effect.get('npc_reveal', {}).items():
            if key not in npcs: raise ValueError('Unknown NPC in effect')
            refs(values, facts, 'NPC reveal')
        if action.get('ending') and action['ending'] not in endings:
            raise ValueError('Unknown ending')
    return w


def initial(w, role):
    roles = indexed(w['roles'], 'role')
    if role not in roles: raise ValueError('Unknown perspective')
    return {'role': role, 'known': set(roles[role]['initial_facts']), 'used': set(),
            'budget': w['budget'], 'flags': dict(w.get('flags', {})),
            'variables': {v['id']: v['initial'] for v in w.get('variables', [])},
            'npc_known': {n['id']: set(n['initial_facts']) for n in w.get('npcs', [])},
            'ending': None, 'journal': []}


def satisfied(c, s):
    if not set(c.get('all', [])).issubset(s['known']): return False
    if c.get('any') and not set(c['any']).intersection(s['known']): return False
    if any(s['flags'][key] != value for key, value in c.get('flags', {}).items()): return False
    for key, bound in c.get('variables', {}).items():
        value = s['variables'][key]
        if value < bound.get('min', -1000) or value > bound.get('max', 1000): return False
    return True


def available(w, s):
    if s['ending']: return []
    endings = indexed(w['endings'], 'ending')
    variables = indexed(w.get('variables', []), 'variable')
    result = []
    for a in w['actions']:
        if a['id'] in s['used'] or a['cost'] > s['budget']: continue
        if a.get('roles') and s['role'] not in a['roles']: continue
        if not satisfied(a.get('requires', {}), s): continue
        # Closing evidence must be known BEFORE the ending action, not supplied by its own effects.
        if a.get('ending') and not satisfied(endings[a['ending']].get('requires', {}), s): continue
        if any(not variables[key]['min'] <= s['variables'][key] + delta <= variables[key]['max']
               for key, delta in a.get('effects', {}).get('variables', {}).items()): continue
        result.append(a)
    return result


def step(w, s, action_id):
    action = next((a for a in available(w, s) if a['id'] == action_id), None)
    if action is None:
        # Don't print locked action labels, conditions, IDs or unrevealed facts.
        raise ValueError('This action is unavailable in the current view; inspect the visible choices')
    result = copy.deepcopy(s)
    result['used'].add(action_id); result['budget'] -= action['cost']
    effect = action.get('effects', {})
    added = set(effect.get('reveal', [])) - result['known']
    result['known'].update(added)
    result['flags'].update(effect.get('flags', {}))
    for key, value in effect.get('variables', {}).items(): result['variables'][key] += value
    for key, values in effect.get('npc_reveal', {}).items(): result['npc_known'][key].update(values)
    if action.get('ending'):
        ending = next(e for e in w['endings'] if e['id'] == action['ending'])
        result['ending'] = ending['id']
        added.update(set(ending.get('reveal', [])) - result['known'])
        result['known'].update(ending.get('reveal', []))
    result['journal'].append({'action_id': action_id, 'label': action['label'], 'outcome': action['outcome'],
                              'revealed': sorted(added), 'remaining': result['budget']})
    return result


def new_session(w, role):
    validate_world(w); initial(w, role)
    return {'format': FORMAT, 'story_id': w['id'], 'story_sha256': digest(w), 'role': role, 'events': []}


def replay(w, session):
    validate_world(w)
    if set(session) != {'format', 'story_id', 'story_sha256', 'role', 'events'}:
        raise ValueError('Unexpected save fields; use an unmodified event save')
    if session.get('format') != FORMAT or session.get('story_id') != w['id'] or session.get('story_sha256') != digest(w):
        raise ValueError('Save belongs to another story/version; use its matching story file')
    events = session['events']
    if not isinstance(events, list) or len(events) > len(w['actions']):
        raise ValueError('Invalid event list')
    s = initial(w, session['role']); seen = set()
    for event in events:
        if set(event) != {'id', 'action_id'}: raise ValueError('Unexpected event fields')
        key = ident(event['id']); ident(event['action_id'])
        if key in seen: raise ValueError('Duplicate event IDs in save')
        seen.add(key); s = step(w, s, event['action_id'])
    return s


def append_event(w, session, event_id, action_id):
    ident(event_id); ident(action_id)
    s = replay(w, session)
    previous = next((e for e in session['events'] if e['id'] == event_id), None)
    if previous:
        if previous['action_id'] != action_id: raise ValueError('Event ID already refers to another action')
        return copy.deepcopy(session), s, True
    result = copy.deepcopy(session)
    s = step(w, s, action_id)
    result['events'].append({'id': event_id, 'action_id': action_id})
    return result, s, False


def project(w, session, s=None):
    s = s or replay(w, session)
    role = next(r for r in w['roles'] if r['id'] == s['role'])
    ending = next((e for e in w['endings'] if e['id'] == s['ending']), None)
    return {'story': {'id': w['id'], 'title': w['title'], 'tone': w['tone'], 'goal': w['goal']},
            'role': {'id': role['id'], 'label': role['label']},
            'opening': role['opening'] or w['opening'], 'revision': len(session['events']),
            'status': 'ended' if ending else 'playing', 'remaining': s['budget'], 'initial_budget': w['budget'],
            'variables': [{'id': v['id'], 'label': v['label'], 'value': s['variables'][v['id']], 'min': v['min'], 'max': v['max']}
                          for v in w.get('variables', [])],
            'known_facts': [copy.deepcopy(f) for f in w['facts'] if f['id'] in s['known']],
            'journal': copy.deepcopy(s['journal']),
            'last_outcome': s['journal'][-1]['outcome'] if s['journal'] else role['opening'],
            'choices': [{'id': a['id'], 'label': a['label'], 'cost': a['cost']} for a in available(w, s)],
            'ending': {k: ending[k] for k in ('id', 'title', 'text', 'classification')} if ending else None}


def npc_view(w, session, npc_id):
    s = replay(w, session)
    npc = next((n for n in w.get('npcs', []) if n['id'] == npc_id), None)
    if npc is None: raise ValueError('Unknown NPC')
    return {'name': npc['name'], 'persona': npc['persona'],
            'known_facts': [copy.deepcopy(f) for f in w['facts'] if f['id'] in s['npc_known'][npc_id]],
            'basis': 'Available character context, not permission to disclose every fact in dialogue. Follow the current visible action outcome; do not infer hidden canon.'}


def md(value):
    return html.escape(str(value)).replace('|', '\\|').replace('\r', '').replace('\n', ' ')


def render(view):
    r = view
    lines = [f'# {md(r["story"]["title"])}', '', f'视角：{md(r["role"]["label"])} · 第 {r["revision"]} 次选择 · 剩余 {r["remaining"]}/{r["initial_budget"]} 格调查时间', '',
             r['last_outcome'], '', '## 已知线索', '']
    for f in r['known_facts']:
        lines.append(f'- [{md(f["id"])} / {md(f["kind"])}] {md(f["text"])}（{md(f["source"])}）')
    if not r['known_facts']: lines.append('- 暂无已记录线索。')
    if r['variables']:
        lines += ['', '## 已发生的影响', '']
        lines += [f'- {md(v["label"])}：{v["value"]}（范围 {v["min"]}—{v["max"]}）' for v in r['variables']]
    if r['ending']:
        lines += ['', '## '+md(r['ending']['title']), '', r['ending']['text']]
    else:
        lines += ['', '## 你可以继续', '']
        lines += [f'- `{a["id"]}` · {md(a["label"])}（消耗 {a["cost"]} 格）' for a in r['choices']]
        lines += ['', '也可以用自己的话行动；主持 Agent 会匹配可用行动，歧义时先确认。']
    return '\n'.join(lines) + '\n'


def write_new(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f: f.write(pretty(value))


def act_file(w, path, event_id, action_id, expected):
    path = Path(path); lock = path.with_name(path.name+'.arcade.lock'); temp = None
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.close(fd)
        old, sha = load(path)
        value, s, repeated = append_event(w, old, event_id, action_id)
        if repeated:
            return value, s, sha, True
        if sha != expected: raise ValueError('Save changed; inspect the current view before choosing again')
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.arcade-', suffix='.tmp', delete=False) as f:
            temp = Path(f.name); f.write(pretty(value)); f.flush(); os.fsync(f.fileno())
        if load(path)[1] != sha: raise ValueError('Save changed during update; original file retained')
        os.replace(temp, path); temp = None
        return value, s, load(path)[1], False
    finally:
        if temp is not None: temp.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)


def fork(w, session, at):
    replay(w, session); integer(at, 0, len(session['events']))
    result = copy.deepcopy(session); result['events'] = result['events'][:at]
    replay(w, result)
    return result


def relay_bundle(w, session, out):
    view = project(w, session)
    out = Path(out)
    # Explicit new folder: don't overwrite an earlier handoff or a user's files.
    out.mkdir(parents=True, exist_ok=False)
    write_new(out/'relay.save.json', session)
    prefix = '# 接力存档 / 玩家视图\n\n原创虚构故事。只含此视角已发生的选择与已知线索。\n\n'
    suffix = '\n## 继续方法\n\n使用相同版本的故事文件和 `relay.save.json` 调用 `show`，再选择行动。此包未附作者真相；它不是加密或对抗读文件的安全边界。\n'
    (out/'relay.md').write_text(prefix+render(view)+suffix, encoding='utf-8')
    return {'files': ['relay.md', 'relay.save.json'], 'revision': view['revision'], 'story_sha256': session['story_sha256']}


def state_key(s):
    return (s['role'], tuple(sorted(s['known'])), tuple(sorted(s['used'])), s['budget'],
            tuple(sorted(s['flags'].items())), tuple(sorted(s['variables'].items())), s['ending'],
            tuple((n, tuple(sorted(v))) for n, v in sorted(s['npc_known'].items())))


def audit(w, max_states=10000):
    validate_world(w); integer(max_states, 1, 100000)
    results = []
    for role in w['roles']:
        start = initial(w, role['id']); queue = deque([(start, [])]); seen = {state_key(start)}
        endings, actions, closing_only, examined = {}, set(), 0, 0
        while queue and examined < max_states:
            s, path = queue.popleft(); examined += 1
            options = available(w, s)
            if not s['ending'] and not any(not a.get('ending') for a in options): closing_only += 1
            for a in options:
                actions.add(a['id']); nxt = step(w, s, a['id']); route = path+[a['id']]
                if nxt['ending']:
                    endings.setdefault(nxt['ending'], route)
                    continue
                key = state_key(nxt)
                if key not in seen:
                    seen.add(key); queue.append((nxt, route))
        complete = not queue
        results.append({'role': role['id'], 'complete': complete, 'states_examined': examined,
                        'states_pending': len(queue), 'ending_routes': endings,
                        'endings_not_observed': [e['id'] for e in w['endings'] if e['id'] not in endings],
                        'actions_not_observed': [a['id'] for a in w['actions'] if a['id'] not in actions and (not a.get('roles') or role['id'] in a['roles'])],
                        'closing_only_states': closing_only})
    return {'author_only': True, 'story_id': w['id'], 'complete': all(r['complete'] for r in results),
            'roles': results, 'basis': 'Exhaustive only when complete=true. Checks authored state transitions, not prose quality, real user enjoyment or LLM leakage resistance.'}
