"""A plain-string ``show if`` must name another field on the same screen.

Docassemble treats ``show if: some_name`` as "show this field when the field
``some_name`` on this screen is true" and wires it up in the browser. A Python
expression such as ``not defined("x")`` names no field, so the browser hides the
field and never shows it. The user sees a screen without inputs, and Next
returns the same screen with no error. Server-side conditions must use
``show if: code: ...``.

The API-driven runtime certification cannot see this, because it assigns
variables without rendering the browser form.
"""
from pathlib import Path
import unittest

import yaml


HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
PACKAGE_DIRS = [
    "docassemble-MATC1ADivorceJointPetition",
    "docassemble-MATCMotionToAmend",
    "docassemble-MATCFinancialStatement",
    "docassemble-MATCSeparationAgreement",
    "docassemble-MATCChildCareOrCustodyDisclosureAffidavit",
    "docassemble-MATCCSGWorksheet",
    "docassemble-MATCFindingsAndDeterminations",
]
FIELD_MODIFIERS = {
    "accept", "address autocomplete", "all of the above", "choices", "code", "css class",
    "datatype", "default", "disable if", "disable others", "enable if", "exclude", "field",
    "field metadata", "file css class", "floating label", "grid", "help", "hide if", "hint",
    "html", "image upload type", "inline width", "input type", "item grid", "js hide if",
    "js show if", "label", "label above field", "max", "maximum image size", "maxlength",
    "min", "minlength", "none of the above", "note", "object labeler", "raw html",
    "required", "rows", "show if", "shuffle", "step", "uncheck others", "under text",
    "validate",
}


class _IgnoreTags(yaml.SafeLoader):
    pass


_IgnoreTags.add_multi_constructor("", lambda loader, suffix, node: None)


def field_variable(field: dict) -> str | None:
    if "field" in field:
        return field["field"]
    for key, value in field.items():
        if key not in FIELD_MODIFIERS and isinstance(value, str):
            return value
    return None


def unreachable_show_ifs(question_file: Path) -> list[str]:
    problems = []
    for block in yaml.load_all(question_file.read_text(), Loader=_IgnoreTags):
        if not isinstance(block, dict) or not isinstance(block.get("fields"), list):
            continue
        fields = [field for field in block["fields"] if isinstance(field, dict)]
        names = {field_variable(field) for field in fields}
        for field in fields:
            for key in ("show if", "hide if"):
                condition = field.get(key)
                if isinstance(condition, str) and condition.strip() not in names:
                    problems.append(
                        f"{question_file.name} id={block.get('id')!r}: "
                        f"{key}: {condition.strip()!r} names no field on this screen"
                    )
    return problems


class ShowIfReferenceTests(unittest.TestCase):
    def test_string_show_if_names_a_field_on_the_same_screen(self):
        package_roots = [WORKSPACE / name for name in PACKAGE_DIRS if (WORKSPACE / name).is_dir()]
        self.assertIn(WORKSPACE / "docassemble-MATC1ADivorceJointPetition", package_roots)
        problems = [
            problem
            for root in package_roots
            for question_file in sorted((root / "docassemble").rglob("data/questions/*.yml"))
            for problem in unreachable_show_ifs(question_file)
        ]
        self.assertEqual(problems, [], "\n".join(problems))

    def test_checker_accepts_same_screen_names_and_code_conditions(self):
        source = """
id: sample
question: Sample
fields:
  - Has a lawyer?: has_lawyer
    datatype: yesnoradio
  - Lawyer name: lawyer_name
    show if: has_lawyer
  - Sex: sex
    show if:
      code: |
        not defined("sex")
  - Broken: broken_field
    show if: not defined("broken_field")
"""
        path = HERE / "artifacts" / "show_if_sample.yml"
        path.parent.mkdir(exist_ok=True)
        path.write_text(source)
        try:
            problems = unreachable_show_ifs(path)
        finally:
            path.unlink()
        self.assertEqual(len(problems), 1)
        self.assertIn("broken_field", problems[0])


if __name__ == "__main__":
    unittest.main()
