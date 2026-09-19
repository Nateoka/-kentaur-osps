from copy import deepcopy as cp
import unittest
from unittest.mock import patch
from mrab_r1.evaluator import evaluate_dataset,rate,number


def reports():
    """Hand-authored trajectory-level arithmetic inputs, not model outcomes."""
    rows=[]
    for condition in ("C1","C2","C3"):
        for i in range(8):
            for arch in ("B0","B1","B2","B3","B4"):
                metrics={name:rate(1,4) for name in ("OPERATIONAL_POST_SUPPORT_TOOL_RATE","OPERATIONAL_POST_MISMATCH_AUTONOMOUS_ERROR_RATE","FIXED_TOOL_RATE","FIXED_AUTONOMOUS_ERROR_RATE")}
                metrics.update(TARGET_ACCURACY=rate(9,10),COMPLETION_RATE=rate(1,1))
                resources={name:number(10) for name in ("EXACT_MODEL_TOKENS","TOOL_UNITS","LATENCY_MS")}
                rows.append(dict(trajectory_id=f"{condition}:{i}:{arch}",block_id=f"{condition}:{i}",condition=condition,architecture=arch,
                    stratum="HIGH",target_family="SYMBOLIC_PIPELINE",valid=True,normal_execution=True,
                    metrics=metrics,resources=resources,conditional_reached=True,conditional_denominator=4,
                    c1_scopes={role:dict(outcomes=dict(accuracy=rate(9,10)),resources=cp(resources)) for role in ("TARGET","CONTROL")}))
    return rows


class CollectionTests(unittest.TestCase):
    def evaluate(self,rows,draws=10000):
        with patch("mrab_r1.evaluator.evaluate_trajectory",side_effect=lambda t,_:cp(t)):
            return evaluate_dataset(rows,"collection-unit",draws)

    def test_I23_joint_matched_block_and_structural_redundancy(self):
        result=self.evaluate(reports())
        self.assertEqual(result["unit"],"TRAJECTORY_MATCHED_BLOCK")
        self.assertEqual(result["decision"]["outcome_class"],"REDUNDANT")
        self.assertEqual(result["individual_contrasts"]["B2:C2:primary_ci"]["n_pairs"],8)
        self.assertEqual(result["bootstrap_draws"],10000)

    def test_I24_missing_conditional_not_save_known_fixed_harm(self):
        rows=reports()
        for r in rows:
            if r["condition"]=="C2":
                if int(r["block_id"].rsplit(":",1)[1])>=2:
                    r["metrics"]["OPERATIONAL_POST_SUPPORT_TOOL_RATE"]=rate(0,0)
                    r.update(conditional_reached=False,conditional_denominator=0)
                if r["architecture"]=="B3":r["metrics"]["FIXED_TOOL_RATE"]=rate(40,100)
        result=self.evaluate(rows)
        row=result["comparator_summary"]["comparators"]["B2"]["C2"]
        self.assertEqual(row["n_pairs"],8);self.assertEqual(row["primary_n_pairs"],2)
        self.assertIsNone(row["primary_ci"]);self.assertGreater(row["fixed_ci"][0],.05)
        self.assertEqual(result["decision"]["outcome_class"],"COUNTERPRODUCTIVE")
        self.assertIn("B2:C2:MISSING_CI",result["decision"]["uncertainty_reasons"])

    def test_missing_resources_zero_baseline_and_abnormal_not_savings(self):
        rows=reports()
        for r in rows:
            if r["architecture"]=="B2":r["resources"]["LATENCY_MS"]=number(0)
            if r["architecture"]=="B3":r["normal_execution"]=False
        result=self.evaluate(rows,200)
        self.assertEqual(result["individual_contrasts"]["B2:resource:latency"]["reason"],"DIVISION_BY_ZERO")
        self.assertFalse(result["comparator_summary"]["comparators"]["B2"]["normal_execution_comparison"])
        self.assertFalse(any(f["kind"]=="RESOURCE_ADVANTAGE_B3" for f in result["decision"]["comparator_findings"]))

    def test_duplicates_refused_not_double_n(self):
        from mrab_r1.errors import Failure
        rows=reports();rows.append(cp(rows[0]))
        with self.assertRaises(Failure):self.evaluate(rows,100)


if __name__=="__main__":unittest.main()
