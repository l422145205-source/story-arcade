#!/usr/bin/env python3
"""Reproduce fictional story paths through real CLI calls. No model or network."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from engine import pretty, render


def run(command,story,**options):
    args=[sys.executable,'-X','utf8','-B',str(ROOT/'scripts/storyarcade.py'),command,'--story',str(story)]
    for key,value in options.items(): args+=['--'+key.replace('_','-'),str(value)]
    r=subprocess.run(args,capture_output=True,encoding='utf-8',check=True)
    return json.loads(r.stdout)


def save_view(out,name,value):
    (out/(name+'.json')).write_text(pretty(value),encoding='utf-8')
    (out/(name+'.md')).write_text(render(value),encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=ROOT/'work/demo')
    args=p.parse_args(); out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    train=ROOT/'assets/last-train.json'; shop=ROOT/'assets/rain-shop.json'
    session=out/'passenger.save.json'
    opening=run('new',train,session=session,role='passenger'); save_view(out,'opening',opening)
    volunteer=run('new',train,session=out/'volunteer.save.json',role='volunteer'); save_view(out,'volunteer-opening',volunteer)
    view=opening; frames=[opening]
    for n,action in enumerate(['read-screen','compare-audio'],1):
        view=run('act',train,session=session,action=action,event=f'e{n}',expect_sha256=view['save_sha256'])
        frames.append(view)
    checkpoint=view; save_view(out,'checkpoint',checkpoint)
    # A repeat after a lost reply must not spend time twice, even with the original pre-action hash.
    before=session.read_bytes()
    retried=run('act',train,session=session,action='compare-audio',event='e2',expect_sha256=opening['save_sha256'])
    repeat_unchanged=before==session.read_bytes()
    run('relay',train,session=session,out=out/'relay')
    branch=out/'public.save.json'
    run('fork',train,session=session,at=2,out=branch)
    for n,action in enumerate(['check-label','private-check','finish-private'],3):
        view=run('act',train,session=session,action=action,event=f'e{n}',expect_sha256=view['save_sha256'])
        frames.append(view)
    save_view(out,'quiet-ending',view)
    other=run('show',train,session=branch)
    for n,action in enumerate(['broadcast','ask-attendant','follow-up','finish-public'],3):
        other=run('act',train,session=branch,action=action,event=f'b{n}',expect_sha256=other['save_sha256'])
    save_view(out,'public-ending',other)
    restored=run('show',train,session=out/'relay/relay.save.json')
    shop_session=out/'shop.save.json'
    cup=run('new',shop,session=shop_session,role='customer')
    for n,action in enumerate(['read-receipt','read-sleeve','leave-coffee'],1):
        cup=run('act',shop,session=shop_session,action=action,event=f'c{n}',expect_sha256=cup['save_sha256'])
    save_view(out,'shop-ending',cup)
    audits={name:run('audit',story) for name,story in [('last-train',train),('rain-shop',shop)]}
    (out/'author-audit.json').write_text(pretty(audits),encoding='utf-8')
    (out/'frames.json').write_text(pretty({'notice':'Scripted CLI reproduction, not an Agent recording. Original fictional story.','frames':frames}),encoding='utf-8')
    result={'basis':'Original fictional packs; actual scripted CLI calls, not an LLM benchmark or human playtest.',
            'retry':{'same_event_replayed':retried['replayed_event'],'bytes_unchanged':repeat_unchanged,'revision':retried['revision'],'remaining':retried['remaining']},
            'relay':{'same_revision':restored['revision']==checkpoint['revision'],'same_known_facts':restored['known_facts']==checkpoint['known_facts']},
            'fork':{'quiet_ending':view['ending']['id'],'alternate_ending':other['ending']['id'],'original_ending_preserved':run('show',train,session=session)['ending']['id']==view['ending']['id']},
            'audit':{name:{'complete':a['complete'],'role_states':{r['role']:r['states_examined'] for r in a['roles']},'all_endings_observed':all(not r['endings_not_observed'] for r in a['roles'])} for name,a in audits.items()}}
    assert repeat_unchanged and result['relay']['same_known_facts'] and result['fork']['original_ending_preserved']
    (out/'verification.json').write_text(pretty(result),encoding='utf-8')
    print(pretty(result),end='')


if __name__=='__main__': main()
