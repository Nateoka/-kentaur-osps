from copy import deepcopy as cp
import unittest
from mrab_r1.manifest import build_manifest,verify_manifest,FAMILIES
from mrab_r1.config import template
from mrab_r1.canonical import semantic_sha,integer_dsl_bytes,raw_sha
from mrab_r1.errors import Failure


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=template();cls.tuples={(f,b):dict(n=3,length=8) if f==FAMILIES[0] else dict(n=4,k=2) for f in FAMILIES for b in ("HIGH","MID")}
        cls.manifest=build_manifest(cls.config,cls.tuples,offline_fixture=True)

    def test_I16_I18_reproducible_480_separate_splits(self):
        second=build_manifest(self.config,self.tuples,offline_fixture=True)
        self.assertEqual(second["sha256"],self.manifest["sha256"])
        checked=verify_manifest(second,self.config)
        self.assertEqual(checked["episodes"],480);self.assertEqual(checked["trajectories"],40)
        pools={split:{e["record"]["latent_fingerprint"] for e in second["payload"]["tasks"].values() if e["record"]["split"]==split} for split in ("MAIN","TRANSFER")}
        self.assertFalse(pools["MAIN"]&pools["TRANSFER"])

    def test_I16_previous_calibration_fingerprint_is_regenerated(self):
        old=next(iter(self.manifest["payload"]["tasks"].values()))["record"]["latent_fingerprint"]
        second=build_manifest(self.config,self.tuples,existing_fingerprints={old:"CALIBRATION_CONFIRM"},offline_fixture=True)
        self.assertNotIn(old,{e["record"]["latent_fingerprint"] for e in second["payload"]["tasks"].values()})
        self.assertTrue(any(e["record"]["duplicate_rejections"] for e in second["payload"]["tasks"].values()))

    def test_A11_transfer_latent_duplicate_rejected_before_run(self):
        modified=cp(self.manifest)
        source=next(e for e in modified["payload"]["tasks"].values() if e["record"]["split"]=="MAIN" and e["record"]["task_view"]["task_family"]==FAMILIES[0])
        target=next(e for e in modified["payload"]["tasks"].values() if e["record"]["split"]=="TRANSFER" and e["record"]["task_view"]["task_family"]==FAMILIES[0])
        target["record"]["latent_fingerprint"]=source["record"]["latent_fingerprint"]
        target["sha256"]=raw_sha(integer_dsl_bytes(target["record"]));modified["sha256"]=semantic_sha(modified["payload"])
        with self.assertRaises(Failure):verify_manifest(modified,self.config)


if __name__=="__main__":unittest.main()
