import json
import os
import sys


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from resources.util import _create_single_prompt_gsm_diagram_with_sherpa_in_process


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: sherpa_render_worker.py <request-json>", file=sys.stderr)
        return 2

    request_path = sys.argv[1]
    with open(request_path, "r") as f:
        payload = json.load(f)

    success = _create_single_prompt_gsm_diagram_with_sherpa_in_process(
        payload["mermaid_code"],
        payload["diagram_file_path"],
    )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
