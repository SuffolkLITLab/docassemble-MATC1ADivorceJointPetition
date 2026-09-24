#!/usr/bin/env python3
"""Build docs/data_dictionary.xlsx from the interview YAML.

Reads the combined 1A interview and its sibling packages (checked out next to
this repository, as in the certification workspace) and writes two sheets:

  Questions    every screen field: package, file, screen id, heading,
               variable, label, datatype, required, show/hide condition
  Form fields  every attachment field: package, template, PDF/DOCX field
               name, and the expression that fills it

    python scripts/build_data_dictionary.py [--workspace ..] [--output docs/data_dictionary.xlsx]
"""
from __future__ import annotations

import argparse
import datetime
import re
import subprocess
from pathlib import Path

import xlsxwriter
import yaml

HERE = Path(__file__).resolve().parent
PACKAGES = [
    "docassemble-MATC1ADivorceJointPetition",
    "docassemble-MATCMotionToAmend",
    "docassemble-MATCFinancialStatement",
    "docassemble-MATCSeparationAgreement",
    "docassemble-MATCChildCareOrCustodyDisclosureAffidavit",
    "docassemble-MATCCSGWorksheet",
    "docassemble-MATCFindingsAndDeterminations",
]
MODIFIERS = {
    "accept", "address autocomplete", "all of the above", "choices", "code", "css class",
    "datatype", "default", "disable if", "disable others", "enable if", "exclude", "field",
    "field metadata", "file css class", "floating label", "grid", "help", "hide if", "hint",
    "html", "image upload type", "inline width", "input type", "item grid", "js hide if",
    "js show if", "label", "label above field", "max", "maximum image size", "maxlength",
    "min", "minlength", "none of the above", "note", "object labeler", "raw html",
    "required", "rows", "show if", "shuffle", "step", "uncheck others", "under text",
    "validate",
}


class IgnoreTags(yaml.SafeLoader):
    pass


IgnoreTags.add_multi_constructor("", lambda loader, suffix, node: None)


def clean(text) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:300]


def condition(field: dict) -> str:
    for key in ("show if", "hide if", "js show if", "js hide if"):
        if key in field:
            value = field[key]
            if isinstance(value, dict):
                value = "; ".join(f"{k}: {clean(v)}" for k, v in value.items())
            return f"{key}: {clean(value)}"
    return ""


def field_rows(package: str, path: Path, block: dict):
    heading = clean(str(block.get("question", "")).splitlines()[0] if block.get("question") else "")
    fields = block.get("fields")
    if isinstance(fields, dict):
        fields = [fields]
    if isinstance(fields, list):
        for field in fields:
            if not isinstance(field, dict) or "code" in field and len(field) == 1:
                continue
            if "note" in field or "html" in field:
                continue
            variable, label = field.get("field"), field.get("label", "")
            if variable is None:
                for key, value in field.items():
                    if key not in MODIFIERS and isinstance(value, str):
                        variable, label = value, key
                        break
            if variable is None:
                continue
            yield [package, path.name, block.get("id", ""), heading, variable, clean(label),
                   field.get("datatype", field.get("input type", "text")),
                   "no" if field.get("required") is False else "yes", condition(field)]
    for key in ("yesno", "noyes", "field", "continue button field", "signature"):
        if isinstance(block.get(key), str) and not isinstance(fields, list):
            yield [package, path.name, block.get("id", ""), heading, block[key], "",
                   key, "yes", ""]


def attachment_rows(package: str, path: Path, block: dict):
    attachments = block.get("attachment") or block.get("attachments")
    if isinstance(attachments, dict):
        attachments = [attachments]
    for attachment in attachments or []:
        if not isinstance(attachment, dict):
            continue
        template = attachment.get("pdf template file") or attachment.get("docx template file") or ""
        target = attachment.get("variable name", attachment.get("name", ""))
        fields = attachment.get("fields") or []
        if isinstance(fields, dict):
            fields = [{k: v} for k, v in fields.items()]
        for field in fields:
            if isinstance(field, dict):
                for pdf_field, expression in field.items():
                    yield [package, path.name, str(target), str(template), str(pdf_field), clean(expression)]


def sha(repo: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "?"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=HERE.parents[1])
    parser.add_argument("--output", type=Path, default=HERE.parent / "docs" / "data_dictionary.xlsx")
    args = parser.parse_args()

    questions, form_fields, sources = [], [], []
    for package in PACKAGES:
        root = args.workspace / package
        if not root.is_dir():
            continue
        sources.append([package, sha(root)])
        for path in sorted(root.glob("docassemble/*/data/questions/*.yml")):
            for block in yaml.load_all(path.read_text(), Loader=IgnoreTags):
                if not isinstance(block, dict):
                    continue
                questions.extend(field_rows(package.replace("docassemble-", ""), path, block))
                form_fields.extend(attachment_rows(package.replace("docassemble-", ""), path, block))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    book = xlsxwriter.Workbook(str(args.output))
    bold = book.add_format({"bold": True, "text_wrap": True, "valign": "top", "bg_color": "#E8EEF4"})
    wrap = book.add_format({"text_wrap": True, "valign": "top"})
    about = book.add_worksheet("About")
    about.set_column(0, 0, 34)
    about.set_column(1, 1, 90)
    lines = [
        ["Generated", datetime.date.today().isoformat()],
        ["Regenerate", "python scripts/build_data_dictionary.py (sibling packages checked out next to this repo)"],
        ["Questions", "Every field on every screen, with the variable it sets."],
        ["Form fields", "Every PDF/DOCX field and the expression that fills it."],
    ] + [[f"Source: {name}", commit] for name, commit in sources]
    for row, (key, value) in enumerate(lines):
        about.write(row, 0, key, bold)
        about.write(row, 1, value, wrap)
    for name, header, rows, widths in (
        ("Questions", ["Package", "File", "Screen id", "Heading", "Variable", "Label", "Datatype", "Required", "Condition"],
         questions, [22, 30, 32, 36, 40, 44, 14, 9, 40]),
        ("Form fields", ["Package", "File", "Document", "Template", "Form field", "Filled from"],
         form_fields, [22, 30, 30, 34, 34, 70]),
    ):
        sheet = book.add_worksheet(name)
        sheet.freeze_panes(1, 0)
        for column, width in enumerate(widths):
            sheet.set_column(column, column, width, wrap)
        sheet.write_row(0, 0, header, bold)
        for row, values in enumerate(rows, start=1):
            sheet.write_row(row, 0, [str(v) for v in values])
        sheet.autofilter(0, 0, max(len(rows), 1), len(header) - 1)
    book.close()
    print(f"{args.output}: {len(questions)} question fields, {len(form_fields)} form fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
