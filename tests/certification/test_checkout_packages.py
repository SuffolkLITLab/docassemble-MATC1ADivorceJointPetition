import unittest

from checkout_packages import target_ref


class CheckoutPackagesTests(unittest.TestCase):
    SPEC = {"repository": "SuffolkLITLab/docassemble-MATCFinancialStatement", "sha": "a" * 40}

    def test_pinned_by_default(self):
        self.assertEqual(target_ref("docassemble.MATCFinancialStatement", self.SPEC, False), "a" * 40)

    def test_track_main_follows_local_interview_packages(self):
        self.assertEqual(target_ref("docassemble.MATCFinancialStatement", self.SPEC, True), "origin/main")
        self.assertEqual(target_ref("docassemble.matcfindingsanddeterminations", self.SPEC, True), "origin/main")

    def test_track_main_keeps_framework_packages_pinned(self):
        self.assertEqual(target_ref("docassemble.AssemblyLine", self.SPEC, True), "a" * 40)


if __name__ == "__main__":
    unittest.main()
