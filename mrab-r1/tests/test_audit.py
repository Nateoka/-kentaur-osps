import unittest
from mrab_r1.audit import design_checker, e07_conflict
from mrab_r1.canonical import loads
from mrab_r1.schemas import DESIGN


class AuditTests(unittest.TestCase):
    def test_existing_19_classifier_goldens_unchanged(self):
        module = design_checker()
        goldens = loads((DESIGN/"design_checks/goldens.json").read_bytes())
        for case in goldens["summary_cases"]:
            with self.subTest(id=case["id"]):
                result = module.classify_summary(case["input"])
                self.assertEqual(result["outcome_class"], case["expected_outcome"])
                for expected in case.get("required_findings", []):
                    self.assertTrue(any(all(f.get(k) == v for k, v in expected.items()) for f in result["comparator_findings"]))

    def test_E07_discrepancy_is_reproduced_not_fixed(self):
        result = e07_conflict()
        self.assertTrue(result["reproduced"])
        self.assertEqual(result["existing_checker_result"]["decision_status"], "INSUFFICIENT_EVIDENCE")
        self.assertIsNone(result["existing_checker_result"]["outcome_class"])
        self.assertFalse(result["expected_requirement_is_new_authorized_golden"])


if __name__ == "__main__":
    unittest.main()
