#!/usr/bin/env python3

import json
import sys
from collections import OrderedDict
from pathlib import Path


def merge_dicts(target, source):
    for state_machine, weeks in source.items():
        state_entry = target.setdefault(state_machine, OrderedDict())
        for week_name, stages in weeks.items():
            week_entry = state_entry.setdefault(week_name, OrderedDict())
            for stage_name, metrics in stages.items():
                week_entry[stage_name] = metrics


def combine_summaries(root):
    combined = OrderedDict()

    for folder in sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")):
        summary_path = folder / "summary.json"
        if not summary_path.exists():
            continue

        with summary_path.open() as handle:
            merge_dicts(combined, json.load(handle, object_pairs_hook=OrderedDict))

    return combined


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    output_path = root / "master_summary.json"
    combined = combine_summaries(root)
    output_path.write_text(json.dumps(combined, indent=2, ensure_ascii=False) + "\n")
    print(output_path)


if __name__ == "__main__":
    main()
