import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from engine import (act_file, append_event, audit, available, digest, fork, initial,
                    load, new_session, npc_view, pretty, project, relay_bundle,
                    render, replay, step, validate_world, write_new)


class StoryTests(unittest.TestCase):
    def setUp(self):
        self.w=json.loads((ROOT/'assets/last-train.json').read_text(encoding='utf-8'))
        self.save=new_session(self.w,'passenger')

    def play(self,path,session=None,world=None):
        w=world or self.w; result=copy.deepcopy(self.save if session is None else session)
        for i,action in enumerate(path,len(result['events'])+1):
            result,_,_=append_event(w,result,f'e{i}',action)
        return result

    def test_initial_view_does_not_disclose_author_or_future_endings(self):
        p=project(self.w,self.save)
        self.assertEqual({f['id'] for f in p['known_facts']},{'f-screen','f-loop'})
        self.assertIsNone(p['ending'])
        raw=pretty(p)
        self.assertNotIn(self.w['author']['truth'],raw)
        self.assertNotIn('quiet-return',raw)
        self.assertNotIn('f-confirmed',raw)

    def test_locked_action_and_error_do_not_reveal_gate(self):
        choices=project(self.w,self.save)['choices']
        self.assertNotIn('finish-private',{a['id'] for a in choices})
        with self.assertRaises(ValueError) as ctx:
            append_event(self.w,self.save,'e1','finish-private')
        self.assertNotIn('f-card-label',str(ctx.exception))
        self.assertEqual(self.save['events'],[])

    def test_npc_has_separate_knowledge(self):
        p=npc_view(self.w,self.save,'attendant')
        self.assertEqual({f['id'] for f in p['known_facts']},{'f-roster','f-room'})
        self.assertNotIn('f-cut',{f['id'] for f in p['known_facts']})
        played=self.play(['compare-audio','private-check'])
        self.assertIn('f-cut',{f['id'] for f in npc_view(self.w,played,'attendant')['known_facts']})

    def test_perspectives_start_with_different_information(self):
        other=new_session(self.w,'volunteer')
        a={f['id'] for f in project(self.w,self.save)['known_facts']}
        b={f['id'] for f in project(self.w,other)['known_facts']}
        self.assertEqual(b-a,{'f-cut'})
        self.assertEqual(project(self.w,other)['last_outcome'],self.w['roles'][1]['opening'])
        self.assertEqual(self.save['role'],'passenger')

    def test_direct_location_question_can_follow_personnel_question(self):
        asked=self.play(['ask-attendant'])
        self.assertIn('check-location',{a['id'] for a in project(self.w,asked)['choices']})
        checked=self.play(['check-location'],asked)
        self.assertIn('f-confirmed',{f['id'] for f in project(self.w,checked)['known_facts']})
        self.assertNotIn('f-cut',{f['id'] for f in npc_view(self.w,checked,'attendant')['known_facts']})
        self.assertNotIn('private-check',{a['id'] for a in project(self.w,checked)['choices']})

    def test_replay_is_idempotent_and_conflicting_event_id_fails(self):
        first,s,repeated=append_event(self.w,self.save,'turn-1','read-screen')
        second,t,repeated=append_event(self.w,first,'turn-1','read-screen')
        self.assertTrue(repeated); self.assertEqual(first,second)
        self.assertEqual(s,t); self.assertEqual(t['budget'],7)
        with self.assertRaises(ValueError): append_event(self.w,first,'turn-1','compare-audio')

    def test_new_event_cannot_repeat_a_once_only_choice(self):
        first=self.play(['read-screen'])
        with self.assertRaises(ValueError): append_event(self.w,first,'e2','read-screen')

    def test_private_ending_requires_prior_evidence_and_consequence(self):
        path=['read-screen','compare-audio','check-label','private-check']
        played=self.play(path)
        view=project(self.w,played)
        self.assertIn('finish-private',{a['id'] for a in view['choices']})
        self.assertEqual(view['variables'][0]['value'],2)
        done=self.play(['finish-private'],played)
        v=project(self.w,done)
        self.assertEqual(v['ending']['id'],'quiet-return')
        self.assertIn('f-truth',{f['id'] for f in v['known_facts']})
        self.assertEqual(v['choices'],[])

    def test_ending_cannot_grant_itself_missing_evidence(self):
        a=next(a for a in self.w['actions'] if a['id']=='finish-private')
        a['effects']['reveal']=['f-count-label','f-card-label','f-confirmed']
        s=initial(self.w,'passenger'); s['variables']['trust']=2
        self.assertNotIn('finish-private',{a['id'] for a in available(self.w,s)})

    def test_public_choice_has_persistent_cost(self):
        played=self.play(['read-screen','compare-audio','check-label','private-check','broadcast'])
        choices={a['id'] for a in project(self.w,played)['choices']}
        self.assertNotIn('finish-private',choices); self.assertIn('finish-public',choices)
        self.assertTrue(replay(self.w,played)['flags']['public-audio'])
        self.assertEqual(project(self.w,played)['variables'][0]['value'],1)

    def test_open_ending_does_not_supply_canonical_truth(self):
        played=self.play(['archive'])
        v=project(self.w,played)
        self.assertEqual(v['ending']['classification'],'open')
        self.assertNotIn('f-truth',{f['id'] for f in v['known_facts']})
        with self.assertRaises(ValueError): self.play(['read-screen'],played)

    def test_insufficient_budget_blocks_action_without_spending(self):
        s=initial(self.w,'passenger'); s['budget']=1
        with self.assertRaises(ValueError): step(self.w,s,'compare-audio')
        self.assertEqual(s['budget'],1)
        self.assertIn('archive',{a['id'] for a in available(self.w,s)})

    def test_variable_bounds_are_enforced(self):
        s=initial(self.w,'volunteer'); s['variables']['trust']=3
        self.assertNotIn('private-check',{a['id'] for a in available(self.w,s)})

    def test_changed_story_rejected_but_whitespace_is_not_a_version_change(self):
        loaded=json.loads(json.dumps(self.w,indent=8,ensure_ascii=False))
        self.assertEqual(digest(self.w),digest(loaded))
        changed=copy.deepcopy(self.w); changed['budget']=9
        with self.assertRaises(ValueError): replay(changed,self.save)

    def test_tampered_save_cannot_introduce_facts_or_duplicate_events(self):
        bad=copy.deepcopy(self.save); bad['known_facts']=['f-truth']
        with self.assertRaises(ValueError): replay(self.w,bad)
        bad=self.play(['read-screen']); bad['events'].append(copy.deepcopy(bad['events'][0]))
        with self.assertRaises(ValueError): replay(self.w,bad)

    def test_fork_reconstructs_prefix_and_preserves_original(self):
        played=self.play(['read-screen','compare-audio','private-check'])
        before=copy.deepcopy(played)
        branch=fork(self.w,played,2)
        self.assertEqual(played,before)
        self.assertEqual(project(self.w,branch)['revision'],2)
        self.assertNotIn('f-confirmed',{f['id'] for f in project(self.w,branch)['known_facts']})
        alt=self.play(['broadcast'],branch)
        self.assertTrue(replay(self.w,alt)['flags']['public-audio'])
        self.assertFalse(replay(self.w,played)['flags']['public-audio'])

    def test_fork_rejects_invalid_checkpoint(self):
        for checkpoint in (-1,1,True):
            with self.assertRaises(ValueError): fork(self.w,self.save,checkpoint)

    def test_export_round_trip_contains_only_current_player_projection(self):
        played=self.play(['read-screen'])
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'relay'
            relay_bundle(self.w,played,out)
            restored,_=load(out/'relay.save.json')
            self.assertEqual(project(self.w,restored),project(self.w,played))
            raw=(out/'relay.md').read_text(encoding='utf-8')
            self.assertNotIn(self.w['author']['truth'],raw)
            self.assertNotIn('f-confirmed',raw)
            self.assertNotIn('f-cut',raw)
            with self.assertRaises(FileExistsError): relay_bundle(self.w,played,out)

    def test_audit_finds_all_authored_endings_in_both_roles(self):
        r=audit(self.w)
        self.assertTrue(r['complete']); self.assertEqual(len(r['roles']),2)
        for role in r['roles']:
            self.assertEqual(role['endings_not_observed'],[])
            self.assertEqual(role['actions_not_observed'],[])
            for ending,path in role['ending_routes'].items():
                save=new_session(self.w,role['role'])
                done=self.play(path,save)
                self.assertEqual(project(self.w,done)['ending']['id'],ending)

    def test_bounded_audit_reports_incomplete_instead_of_proving_absence(self):
        r=audit(self.w,1)
        self.assertFalse(r['complete'])
        self.assertTrue(all(not role['complete'] and role['states_pending']>0 for role in r['roles']))

    def test_audit_detects_unreachable_ending(self):
        self.w['facts'].append({'id':'never-found','text':'unavailable evidence','kind':'observation','source':'test'})
        self.w['endings'][0]['requires']['all'].append('never-found')
        r=audit(self.w)
        self.assertTrue(r['complete'])
        self.assertTrue(all('quiet-return' in x['endings_not_observed'] for x in r['roles']))

    def test_invalid_ids_references_cost_and_condition_rejected(self):
        changes=[lambda w:w['facts'].append(copy.deepcopy(w['facts'][0])),
                 lambda w:w['actions'][0].update(cost=-1),
                 lambda w:w['actions'][0].update(requires={'python':'print(1)'}),
                 lambda w:w['actions'][0]['effects'].update(reveal=['missing'])]
        for mutation in changes:
            w=copy.deepcopy(self.w); mutation(w)
            with self.assertRaises(ValueError): validate_world(w)

    def test_stale_write_and_conflict_preserve_original_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'save.json'; write_new(file,self.save); before=file.read_bytes()
            with self.assertRaises(ValueError): act_file(self.w,file,'e1','read-screen','0'*64)
            self.assertEqual(file.read_bytes(),before)
            _,_,sha,_=act_file(self.w,file,'e1','read-screen',load(file)[1])
            after=file.read_bytes()
            with self.assertRaises(ValueError): act_file(self.w,file,'e1','compare-audio',sha)
            self.assertEqual(file.read_bytes(),after)
            self.assertFalse(file.with_name(file.name+'.arcade.lock').exists())

    def test_successful_retry_preserves_bytes_even_with_old_hash(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'save.json'; write_new(file,self.save); old=load(file)[1]
            first,_,sha,again=act_file(self.w,file,'e1','read-screen',old)
            second,_,next_sha,again=act_file(self.w,file,'e1','read-screen',old)
            self.assertTrue(again); self.assertEqual(first,second); self.assertEqual(sha,next_sha)

    def test_busy_lock_remains_owned_by_other_writer(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'save.json'; write_new(file,self.save)
            lock=file.with_name(file.name+'.arcade.lock'); lock.write_text('busy')
            with self.assertRaises(FileExistsError): act_file(self.w,file,'e1','read-screen',load(file)[1])
            self.assertEqual(lock.read_text(),'busy')

    def test_new_file_never_overwrites_existing_save(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'save.json'; write_new(file,self.save)
            with self.assertRaises(FileExistsError): write_new(file,self.save)

    def test_small_case_supports_two_distinct_valid_choices(self):
        w=json.loads((ROOT/'assets/rain-shop.json').read_text(encoding='utf-8'))
        start=new_session(w,'customer')
        prepared=self.play(['read-receipt','read-sleeve'],start,w)
        a=self.play(['leave-coffee'],prepared,w); b=self.play(['take-coffee'],prepared,w)
        self.assertNotEqual(project(w,a)['ending']['id'],project(w,b)['ending']['id'])
        self.assertEqual(audit(w)['roles'][0]['endings_not_observed'],[])

    def test_cli_new_show_act_are_real_and_show_is_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'save.json'
            prefix=[sys.executable,'-X','utf8','-B',str(ROOT/'scripts/storyarcade.py')]
            def run(*args):
                return subprocess.run(prefix+list(map(str,args)),capture_output=True,encoding='utf-8')
            args=['--story',ROOT/'assets/last-train.json','--session',file]
            made=run('new',*args,'--role','passenger'); self.assertEqual(made.returncode,0,made.stderr)
            before=file.read_bytes(); shown=run('show',*args)
            self.assertEqual(shown.returncode,0,shown.stderr); self.assertEqual(file.read_bytes(),before)
            v=json.loads(shown.stdout)
            acted=run('act',*args,'--action','read-screen','--event','e1','--expect-sha256',v['save_sha256'])
            self.assertEqual(acted.returncode,0,acted.stderr)
            self.assertEqual(json.loads(acted.stdout)['revision'],1)
            self.assertNotEqual(run('new',*args,'--role','passenger').returncode,0)


if __name__=='__main__': unittest.main()
