import unittest

from verify_runtime_manifest import freeze_digest, verify


BASELINE = {
    "runtime": {"image": "example/image@sha256:abc"},
    "external_packages": {"docassemble.Example": "1.2.3"},
}


class RuntimeManifestTests(unittest.TestCase):
    def test_freeze_digest_is_order_and_case_stable(self):
        self.assertEqual(
            freeze_digest("Zulu==2\nalpha==1\n"),
            freeze_digest("ALPHA==1\nzulu==2\n"),
        )

    def test_freeze_digest_ignores_local_interview_packages(self):
        # CI installs the docassemble.MATC* packages from uploaded zips whose
        # hashes change on every run; their commits are pinned by checkout.
        base = "alpha==1\n"
        with_local = base + (
            "docassemble.MATCFinancialStatement @ file:///x/file.zip#sha256=aaa\n"
            "docassemble.matcfindingsanddeterminations @ file:///y/file.zip#sha256=bbb\n"
        )
        self.assertEqual(freeze_digest(base), freeze_digest(with_local))

    def test_exact_manifest_passes(self):
        self.assertEqual(
            verify(
                BASELINE,
                ["example/image@sha256:abc"],
                "docassemble.Example==1.2.3\n",
            ),
            [],
        )

    def test_image_and_package_drift_fail(self):
        errors = verify(
            BASELINE,
            ["example/image@sha256:different"],
            "docassemble.Example==2.0.0\n",
        )
        self.assertEqual(len(errors), 2)
        self.assertIn("runtime image mismatch", errors[0])
        self.assertIn("package mismatch", errors[1])

    def test_parity_runtime_checks_only_its_image(self):
        baseline = dict(
            BASELINE,
            parity_runtimes={"apps-dev": {"image": "example/image@sha256:parity"}},
        )
        self.assertEqual(
            verify(
                baseline,
                ["example/image@sha256:parity"],
                "docassemble.Example==9.9.9\n",
                runtime="apps-dev",
            ),
            [],
        )
        errors = verify(baseline, ["example/image@sha256:other"], "", runtime="apps-dev")
        self.assertEqual(len(errors), 1)
        self.assertIn("runtime image mismatch", errors[0])

    def test_unknown_parity_runtime_fails(self):
        errors = verify(BASELINE, ["example/image@sha256:abc"], "", runtime="missing")
        self.assertEqual(errors, ["unknown runtime: missing"])


if __name__ == "__main__":
    unittest.main()
