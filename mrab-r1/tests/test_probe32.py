from copy import deepcopy as cp
import unittest
from mrab_r1.controller import Controller
from mrab_r1.b4 import KEY_FIELDS
from mrab_r1.canonical import loads
from mrab_r1.schemas import DESIGN,Schemas
from tests.test_runtime_contracts import initial_profile,observation,b3_record


class Probe32Tests(unittest.TestCase):
    def setup_controller(self):
        self.sequence=0;self.events=[]
        def seq():self.sequence+=1;return self.sequence
        c=Controller(seq,lambda k,p:self.events.append((k,cp(p))))
        claim=initial_profile()["claims"][0]
        f=observation(claim);key={k:f[k] for k in (*KEY_FIELDS,"scope_id")}
        key["execution_mode"]="PREP_EXECUTED"
        return c,claim,key

    def test_PROBE21_labels_never_causal_discrimination(self):
        for case in loads((DESIGN/"design_checks/goldens.json").read_bytes())["probe_scope_cases"]:
            with self.subTest(case=case["id"]):
                c,claim,key=self.setup_controller();record=b3_record(True,"VERIFY_CURRENT")
                record["candidate_loci"]=case["loci"]
                record["probe_predictions"]=[dict(locus=l,observable_pattern="SOLO_"+p,if_not_observed="KEEP_UNKNOWN") for l,p in zip(case["loci"],case["labels"])]
                s=Schemas();s.validate(record,s.ref("reflexive_record","b3"))
                c.begin(1,key);c.accept_prep(record,1,key,[])
                self.assertTrue(c.action(1,key,"VERIFY"))
                c.feedback(1,key,observation(claim,1,True,"VERIFY",mode="PREP_EXECUTED"),claim,True)
                self.assertIsNone(c.pending)
                self.assertTrue(any(p.get("reason")=="OBSERVED_NOT_CAUSALLY_IDENTIFIED" for k,p in self.events))
                self.assertFalse(case["expected_causal"])

    def test_32_next_matched_stop_pending_expiry_and_end_pending(self):
        c,claim,key=self.setup_controller();evidence=[];snapshots=[]
        for episode in range(1,33):
            allowed=c.begin(episode,key)
            # Hand-authored declarations at 3, 12 and 31; not provider output.
            if episode in {3,12,31}:
                record=b3_record(True,"VERIFY_NEXT_MATCHED")
                prior=observation(claim,episode-1,True,"VERIFY",mode="PREP_SKIPPED")
                evidence.append(prior)
                c.accept_prep(record,episode,key,evidence)
                self.assertTrue(c._state(key["scope_id"])["latched"])
            current={**key,"execution_mode":"PREP_SKIPPED" if c._state(key["scope_id"])["latched"] else "PREP_EXECUTED"}
            action="VERIFY" if episode==4 else "DELEGATE"
            executed=c.action(episode,current,action)
            f=observation(claim,episode,True,action,mode=current["execution_mode"])
            c.feedback(episode,current,f,claim,executed)
            evidence.append(f);snapshots.append(cp(c.public_state()))
        self.assertEqual(len(snapshots),32)
        self.assertTrue(any(p.get("event_kind")=="EXPIRED" for k,p in self.events))
        self.assertTrue(any(p.get("resolution")=="EVIDENCE_RETURNED" for k,p in self.events))
        self.assertEqual(c.finish(),"END_PENDING")
        self.assertEqual(c.pending["declared_episode"],31)

    def test_cancel_then_declare_order_and_CURRENT_failed_action(self):
        c,claim,key=self.setup_controller();c.begin(1,key)
        c.accept_prep(b3_record(False,"VERIFY_CURRENT"),1,key,[])
        replacement=b3_record(True,"SOLO_CURRENT");replacement["cancel_pending_probe"]=True
        c.accept_prep(replacement,1,key,[])
        self.assertEqual([p["event_kind"] for p in c.probe_events],["DECLARED","CANCELLED","DECLARED"])
        c.feedback(1,key,observation(claim,1,True,"DELEGATE"),claim,False)
        self.assertIsNone(c.pending)
        self.assertEqual(c.probe_events[-1]["event_kind"],"CANCELLED")

    def test_32_C0_restarts_without_numeric_map(self):
        c,claim,key=self.setup_controller();prep_count=0
        for episode in range(1,33):
            if c.begin(episode,key):
                prep_count+=1;c.accept_prep(b3_record(True),episode,key,[])
            f=observation(claim,episode,True,"SOLO",mode="PREP_SKIPPED")
            c.feedback(episode,key,f,None)
        self.assertEqual(prep_count,16)
        self.assertTrue(any(p.get("reason")=="NEW_EVIDENCE" for k,p in self.events))


if __name__=="__main__":unittest.main()
