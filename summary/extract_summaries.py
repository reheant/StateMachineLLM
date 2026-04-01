#!/usr/bin/env python3

import json
import re
import sys
import zipfile
from collections import OrderedDict
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
PKG_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
TEXT_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
CATEGORY_ORDER = [
    "Composite State",
    "State",
    "Transition",
    "Action",
    "Region",
    "History State",
    "Guard",
]


def null_metrics():
    return {"precision": None, "recall": None, "f1": None}


def empty_block():
    return {
        "overall": null_metrics(),
        "by_category": OrderedDict((category, null_metrics()) for category in CATEGORY_ORDER),
    }


def empty_kappa_block():
    return {
        "overall": None,
        "by_category": OrderedDict((category, None) for category in CATEGORY_ORDER),
    }


def parse_shared_strings(workbook_zip):
    try:
        root = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
    except KeyError:
        return []

    values = []
    for item in root.findall("a:si", NS):
        values.append("".join(node.text or "" for node in item.iter(TEXT_NS)))
    return values


def cell_value(cell, shared_strings):
    cell_type = cell.attrib.get("t")
    value_node = cell.find("a:v", NS)
    inline_node = cell.find("a:is", NS)

    if cell_type == "s" and value_node is not None:
        return shared_strings[int(value_node.text)]
    if cell_type == "inlineStr" and inline_node is not None:
        return "".join(node.text or "" for node in inline_node.iter(TEXT_NS))
    if value_node is not None:
        return value_node.text
    return None


def sheet_values(workbook_zip, sheet_path):
    shared_strings = parse_shared_strings(workbook_zip)
    root = ET.fromstring(workbook_zip.read(sheet_path))
    values = {}

    for cell in root.findall(".//a:c", NS):
        value = cell_value(cell, shared_strings)
        if value not in (None, ""):
            values[cell.attrib["r"]] = value

    return values


def metrics_sheet_path(workbook_zip):
    return named_sheet_path(workbook_zip, "Metrics")


def named_sheet_path(workbook_zip, sheet_name):
    workbook_root = ET.fromstring(workbook_zip.read("xl/workbook.xml"))
    rels_root = ET.fromstring(workbook_zip.read("xl/_rels/workbook.xml.rels"))
    rel_targets = {
        rel.attrib["Id"]: "xl/" + rel.attrib["Target"]
        for rel in rels_root.findall(PKG_REL_NS)
        if rel.attrib.get("Type", "").endswith("/worksheet")
    }

    for sheet in workbook_root.find("a:sheets", NS).findall("a:sheet", NS):
        if sheet.attrib["name"] == sheet_name:
            rel_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            return rel_targets[rel_id]

    raise ValueError(f"{sheet_name} sheet not found")


def state_machine_name(workbook_zip):
    workbook_root = ET.fromstring(workbook_zip.read("xl/workbook.xml"))
    return workbook_root.find("a:sheets", NS).findall("a:sheet", NS)[0].attrib["name"]


def normalize_number(value):
    if value is None:
        return None

    text = str(value).strip()
    if not text or text.lower() == "not available":
        return None

    number = float(text)
    if number > 1:
        number /= 100.0
    return number


def normalize_category(raw_value):
    normalized = " ".join(str(raw_value or "").strip().split()).lower()
    mapping = {
        "composite state": "Composite State",
        "state": "State",
        "transition": "Transition",
        "action": "Action",
        "region": "Region",
        "history state": "History State",
        "guard": "Guard",
        "overall score": "Overall Score",
    }
    return mapping.get(normalized)


def infer_stage(folder_name):
    lowered = folder_name.lower()
    if any(token in lowered for token in ("1 shot", "1-step", "1 step")):
        return "1_stage"
    if any(token in lowered for token in ("2 shot", "2-step", "2 step")):
        return "2_stage"
    raise ValueError(f"Could not infer stage from folder name: {folder_name}")


def parse_kappa_value(value):
    if value is None:
        return None

    text = str(value).strip()
    if not text or text.lower() == "not available" or text.startswith("#"):
        return None

    return float(text)


def parse_weighted_cohens_kappa(workbook_zip):
    values = sheet_values(workbook_zip, named_sheet_path(workbook_zip, "Weighted Cohens Kappa"))
    result = empty_kappa_block()
    current_category = None

    max_row = 0
    for cell_ref in values:
        digits = "".join(ch for ch in cell_ref if ch.isdigit())
        if digits:
            max_row = max(max_row, int(digits))

    for row in range(1, max_row + 1):
        section_label = values.get(f"F{row}")
        if section_label == "Confusion Matrix":
            current_category = "overall"
        elif isinstance(section_label, str) and section_label.startswith("Confusion Matrix (") and section_label.endswith(")"):
            current_category = normalize_category(section_label[len("Confusion Matrix (") : -1])

        if values.get(f"V{row}") != "Cohen's Kappa":
            continue

        kappa_value = parse_kappa_value(values.get(f"W{row}"))
        if current_category == "overall":
            result["overall"] = kappa_value
        elif current_category in result["by_category"]:
            result["by_category"][current_category] = kappa_value

    return result


def infer_week(folder_name):
    lowered = folder_name.lower().replace("-", " ")
    for month in ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"):
        match = re.search(rf"{month}[a-z]*\s*(\d{{1,2}})", lowered)
        if match:
            return f"week_{month}_{int(match.group(1))}"
    raise ValueError(f"Could not infer week from folder name: {folder_name}")


def parse_metrics_file(path):
    with zipfile.ZipFile(path) as workbook_zip:
        values = sheet_values(workbook_zip, metrics_sheet_path(workbook_zip))
        weighted_cohens_kappa = parse_weighted_cohens_kappa(workbook_zip)
        block_labels = {1: values.get("A1", ""), 2: values.get("A12", "")}
        role_map = {1: "Human", 2: "LLM"}

        for index, label in block_labels.items():
            lowered = label.lower()
            if "human" in lowered:
                role_map[index] = "Human"
            elif re.search(r"\bllm\b", lowered):
                role_map[index] = "LLM"

        result = {"Human": empty_block(), "LLM": empty_block()}
        for index, rows in ((1, range(3, 11)), (2, range(14, 22))):
            block = empty_block()
            for row in rows:
                category = normalize_category(values.get(f"A{row}"))
                if not category:
                    continue

                metrics = {
                    "precision": normalize_number(values.get(f"F{row}")),
                    "recall": normalize_number(values.get(f"G{row}")),
                    "f1": normalize_number(values.get(f"H{row}")),
                }

                if category == "Overall Score":
                    block["overall"] = metrics
                else:
                    block["by_category"][category] = metrics

            result[role_map[index]] = block

        return state_machine_name(workbook_zip), result, weighted_cohens_kappa


def build_summary(folder):
    week = infer_week(folder.name)
    stage = infer_stage(folder.name)
    summary = OrderedDict()

    for workbook in sorted(folder.glob("*.xlsx")):
        name, metrics, weighted_cohens_kappa = parse_metrics_file(workbook)
        summary.setdefault(name, OrderedDict())
        summary[name].setdefault(week, OrderedDict())
        summary[name][week][stage] = OrderedDict(
            [
                ("Human", metrics["Human"]),
                ("LLM", metrics["LLM"]),
                ("weighted_cohens_kappa", weighted_cohens_kappa),
            ]
        )

    return summary


def write_summary(folder):
    summary = build_summary(folder)
    output_path = folder / "summary.json"
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return output_path


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    folders = [path for path in sorted(root.iterdir()) if path.is_dir() and not path.name.startswith(".")]

    written = []
    for folder in folders:
        if list(folder.glob("*.xlsx")):
            written.append(write_summary(folder))

    for path in written:
        print(path)


if __name__ == "__main__":
    main()
