import contextlib
import os
import json
import re
import subprocess
import sys
import threading
import time
import tempfile
import requests
from transitions.extensions import HierarchicalGraphMachine
import mermaid as md
from mermaid.graph import Graph
from sherpa_ai.memory.state_machine import SherpaStateMachine

# DO NOT import pythonmonkey-dependent modules at module level
# This causes segmentation faults in Chainlit's async context.
# Instead, use lazy imports inside functions that are called via asyncio.to_thread()

# OpenRouter API key for single prompt
openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")

# pythonmonkey / SpiderMonkey is unstable under overlapping threaded access in this app.
# Serialize Mermaid parser/render usage to avoid native crashes when requests overlap.
MERMAID_RENDER_LOCK = threading.Lock()


def call_openrouter_llm(
    prompt, max_tokens=15000, temperature=0.7, model="anthropic/claude-3.5-sonnet"
):
    """
    Call OpenRouter API for LLM requests specifically for single prompt technique
    """
    import requests

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ECSE458-Multi-Agent-LLM/StateMachineLLM",
        "X-Title": "StateMachineLLM Single Prompt",
    }

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant specialized in generating state machines using Mermaid stateDiagram-v2 syntax. Analyze problem descriptions and generate complete UML state machines with states, transitions, guards, actions, hierarchical states, parallel regions, and history states.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        raise Exception(
            f"OpenRouter API call failed with status {response.status_code}: {response.text}"
        )


def mermaidCodeSearch(
    llm_response: str, generated_mermaid_code_path: str, writeFile=True
):
    """Function that extracts mermaid code from an LLM response
    params:
    llm_response is the string response from the LLM
    generated_mermaid_code_path is the path of the file in which to write the extracted mermaid code. The file path must have the extension ".mmd"

    raises:
    Exception if no mermaid code is found in the extracted code"""

    # Try to find code wrapped in XML-style tags first
    generated_mermaid_code_search = re.search(
        r"<mermaid_code_solution>\s*(.*?)\s*</mermaid_code_solution>",
        llm_response,
        re.DOTALL,
    )

    if generated_mermaid_code_search:
        generated_mermaid_code = generated_mermaid_code_search.group(1).strip()
    else:
        # Try to find code in markdown code blocks with mermaid language tag
        mermaid_block_search = re.search(
            r"```mermaid\s*(.*?)```", llm_response, re.DOTALL
        )
        if mermaid_block_search:
            generated_mermaid_code = mermaid_block_search.group(1).strip()
        else:
            # Try to find stateDiagram-v2 directly (last resort)
            # Look for stateDiagram-v2 and capture everything after it
            if "stateDiagram-v2" in llm_response:
                start_idx = llm_response.find("stateDiagram-v2")
                generated_mermaid_code = llm_response[start_idx:]
            else:
                raise Exception("No mermaid code found in LLM response")

    # Defensive sanitization: remove common copy/paste artifacts that break the JS parser
    # - remove markdown fences and mermaid code fences
    generated_mermaid_code = re.sub(
        r"```(?:mermaid)?\s*", "", generated_mermaid_code, flags=re.IGNORECASE
    )
    # - remove Python/JS triple-quote artifacts that sometimes are included in LLM outputs
    generated_mermaid_code = generated_mermaid_code.replace('"""', "").replace(
        "'''", ""
    )
    # - strip surrounding backticks, quotes and whitespace
    generated_mermaid_code = generated_mermaid_code.strip("` \t\r\n'\"")
    # - remove any trailing unmatched triple quotes
    generated_mermaid_code = re.sub(r'("{3,}|\'{3,})\s*$', "", generated_mermaid_code)

    # ALWAYS clean up - find stateDiagram-v2 and take ONLY from that point forward
    if "stateDiagram-v2" in generated_mermaid_code:
        start_idx = generated_mermaid_code.find("stateDiagram-v2")
        generated_mermaid_code = generated_mermaid_code[start_idx:]

    # Remove any trailing closing tags or extra text after the diagram
    # Find the last closing brace at the root level (end of state machine)
    lines = generated_mermaid_code.split("\n")
    # Keep lines until we find a line that's just a closing tag or starts with <
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if (
            stripped.startswith("</")
            or stripped.startswith("<mermaid")
            or stripped == "```"
            or stripped.startswith('"""')
            or stripped.startswith("'''")
            or stripped.endswith('"""')
            or stripped.endswith("'''")
        ):
            break
        cleaned_lines.append(line)

    generated_mermaid_code = "\n".join(cleaned_lines).strip()

    if writeFile:
        # Create a file to store generated code
        with open(generated_mermaid_code_path, "w") as file:
            file.write(generated_mermaid_code)

    return generated_mermaid_code


def setup_file_paths(
    base_dir: str,
    file_type: str = "single_prompt",
    system_name: str = None,
    model_name: str = None,
) -> dict:
    """
    Setup file paths for logs, Mermaid code, and diagrams
    Args:
        base_dir: Base directory path
        file_type: Type of file (default: "single_prompt")
        system_name: Optional name of the system being generated (e.g., "Printer", "Custom")
        model_name: Optional name of the model used (e.g., "claude-4-5-sonnet", "gpt-4o")
    Returns:
        dict: Dictionary containing all necessary file paths
    """

    # For generation/compiler/grader runs, organize files in timestamped folders
    if file_type in (
        "single_prompt",
        "two_stage_prompt",
        "mermaid_compiler",
        "automatic_grader",
    ):
        # Create date and time parts separately
        date_folder = time.strftime("%Y_%m_%d")  # e.g., 2026_01_30
        time_folder = time.strftime("%H_%M_%S")  # e.g., 16_38_49

        # Create single output directory with structure: date/model_name/system_name/time
        # Sanitize model_name to be filesystem-safe
        if model_name:
            safe_model_name = model_name.replace("/", "-").replace(":", "-")
        else:
            safe_model_name = "unknown_model"

        if system_name:
            # Sanitize system_name to be filesystem-safe
            safe_system_name = "".join(
                c if c.isalnum() or c in (" ", "-", "_") else "_" for c in system_name
            )
            safe_system_name = safe_system_name.strip().replace(" ", "_")
            output_base_dir = os.path.join(
                base_dir,
                "resources",
                f"{file_type}_outputs",
                date_folder,
                safe_model_name,
                safe_system_name,
                time_folder,
            )
        else:
            output_base_dir = os.path.join(
                base_dir,
                "resources",
                f"{file_type}_outputs",
                date_folder,
                safe_model_name,
                time_folder,
            )
        os.makedirs(output_base_dir, exist_ok=True)

        # Generate file names (simpler since they're in a timestamped folder)
        file_prefix = (
            "output_stage2"
            if file_type == "two_stage_prompt"
            else f"output_{file_type}"
        )
        log_file_name = f"{file_prefix}.txt"

        return {
            "log_base_dir": output_base_dir,
            "log_file_path": os.path.join(output_base_dir, log_file_name),
            "generated_mermaid_code_path": os.path.join(
                output_base_dir, f"{file_prefix}.mmd"
            ),
            "diagram_base_dir": output_base_dir,
            "diagram_file_path": os.path.join(output_base_dir, file_prefix),
            "llm_log_path": os.path.join(output_base_dir, "LLM_log.txt"),
            "grading_prompt_path": os.path.join(output_base_dir, "grading_prompt.txt"),
            "grading_output_path": os.path.join(output_base_dir, "grading_output.txt"),
            "grading_csv_path": os.path.join(output_base_dir, "grading_results.csv"),
            "grading_tsv_path": os.path.join(output_base_dir, "grading_results.tsv"),
        }


def fix_hierarchical_state_transitions(graph):
    """
    Fix GraphViz edges for two cases pytransitions doesn't handle:

    1. Composite state self-loop (e.g. Active -> Active):
       GraphViz cannot render ltail=X lhead=X on the same cluster.
       Solution: Replace with an intermediate dot node placed in the parent
       cluster so the arrows visually loop around the cluster boundary.

    2. Composite state -> own child (e.g. Cleaning -> Cleaning_HistoryPoint):
       ltail alone is ignored by GraphViz when the destination is inside the
       same cluster.  Solution: route through an intermediate dot node placed
       in the parent cluster — one arrow exits the cluster to the dot, a
       second arrow re-enters the cluster to the specific child node.

    Note: pytransitions already handles lhead (external -> composite) and
    ltail (composite -> external), so those cases are left untouched.

    Args:
        graph: GraphViz Digraph object from pytransitions

    Returns:
        Modified graph with fixes applied to hierarchical transitions
    """
    import re
    from collections import defaultdict

    try:
        # ── Pass 1: build cluster hierarchy ───────────────────────────────────
        # Real composite clusters (skip internal _root clusters).
        # pytransitions names the initial-point node of cluster_X as X.
        composite_clusters = set()
        cluster_parent = {}  # cluster_name -> parent cluster name (or None)
        cluster_stack = []  # all clusters incl. _root for correct brace matching

        for item in graph.body:
            m = re.search(r"subgraph\s+(cluster_\w+)", item)
            if m:
                cname = m.group(1)
                parent = cluster_stack[-1] if cluster_stack else None
                if not cname.endswith("_root"):
                    composite_clusters.add(cname)
                    cluster_parent[cname] = parent
                cluster_stack.append(cname)
            elif item.strip() == "}" and cluster_stack:
                cluster_stack.pop()

        # initial-point name -> cluster  e.g. 'Active' -> 'cluster_Active'
        initial_to_cluster = {c[len("cluster_") :]: c for c in composite_clusters}

        # ── Pass 2: identify edges to fix ─────────────────────────────────────
        # Regex handles both quoted ("_initial") and unquoted (Active) node names.
        edge_re = re.compile(
            r'(\s*)("(?:[^"]+)"|[A-Za-z_]\w*)\s*->\s*("(?:[^"]+)"|[A-Za-z_][^\s\[]*)(.*)',
            re.DOTALL,
        )

        lines_to_skip = set()  # indices of body items to drop
        residuals = {}  # index -> trailing content to preserve
        deferred_nodes = defaultdict(
            list
        )  # parent_cluster (or None) -> [node_def, ...]
        extra_edges = []  # replacement edge strings (top-level)
        counter = 0

        for i, item in enumerate(graph.body):
            m = edge_re.match(item)
            if not m:
                continue

            indent = m.group(1)
            source_raw = m.group(2)
            target_raw = m.group(3).rstrip()
            rest = m.group(4)

            source = source_raw.strip('"')
            target = target_raw.strip('"')

            source_cluster = initial_to_cluster.get(source)
            target_cluster = initial_to_cluster.get(target)
            if not source_cluster and not target_cluster:
                continue

            # Skip auto-generated pytransitions initial-state edges.
            # Inner composite initial edges use headlabel=""; the outermost composite's
            # initial edge (e.g. Active -> Active_WashCycle produced by pytransitions
            # when initial='WashCycle' is set) uses label="" instead.  Both must be
            # left untouched so the [*]->Child arrow stays in the diagram.
            if re.search(r'headlabel=""', rest) or re.search(
                r'(?<![a-z])label=""', rest
            ):
                continue

            # Extract just this edge's attribute block; anything after belongs to
            # a second statement packed in the same body item by pytransitions.
            edge_attrs, after_edge = rest, ""
            bracket_depth = 0
            for idx, ch in enumerate(rest):
                if ch == "[":
                    bracket_depth += 1
                elif ch == "]":
                    bracket_depth -= 1
                    if bracket_depth == 0:
                        edge_attrs = rest[: idx + 1]
                        after_edge = rest[idx + 1 :]
                        break

            if not source_cluster:
                # ── Case 3b: non-composite → composite ancestor ────────────────
                # pytransitions emits no lhead when the source lives inside the
                # destination cluster (e.g. Printing → LoggedIn).  Adding lhead
                # alone doesn't work because GraphViz ignores lhead when the tail
                # is also inside the same cluster.  Use an intermediate dot placed
                # outside the target cluster so the arrow forms a clean self-loop
                # on the target cluster's outer boundary (same trick as Case 1).
                if target_cluster and source.startswith(target + "_"):
                    node_name = f"_escape_{target}_{counter}"
                    counter += 1
                    target_parent_cluster = cluster_parent.get(target_cluster)
                    deferred_nodes[target_parent_cluster].append(
                        f'\t"{node_name}" '
                        f'[shape=point width=0 height=0 style=invis label=""]'
                    )
                    clean = re.sub(r"\bltail=[^\s\]]+\s*", "", edge_attrs).strip()
                    clean = re.sub(r"\blhead=[^\s\]]+\s*", "", clean).strip()
                    # Clean merged labels from pytransitions (e.g. "reset | " → "reset")
                    clean = re.sub(r'\s*\|\s*"', '"', clean)
                    clean = re.sub(r'="\s*\|\s*', '="', clean)
                    # No ltail needed: source is a leaf node (non-composite),
                    # so the edge should start directly from the source node
                    # rather than being clipped at a cluster boundary.
                    if clean.startswith("["):
                        out_attrs = clean[:-1] + " dir=none]"
                    elif clean:
                        out_attrs = "[" + clean.strip("[]") + " dir=none]"
                    else:
                        out_attrs = "[dir=none]"
                    # Edge 1: source node → dot (no arrowhead)
                    extra_edges.append(
                        f'{indent}{source_raw} -> "{node_name}" {out_attrs}'
                    )
                    # Edge 2: dot → arrowhead re-enters target cluster boundary
                    extra_edges.append(
                        f'{indent}"{node_name}" -> {target_raw} '
                        f"[lhead={target_cluster} constraint=false]"
                    )
                    lines_to_skip.add(i)
                    if after_edge.strip():
                        residuals[i] = "\t" + after_edge.lstrip("\t ")
                continue

            cluster_prefix = source
            parent_cluster = cluster_parent.get(source_cluster)  # None = top level

            # Strip any previously-added ltail/lhead from edge_attrs (clean slate).
            # lhead belongs only on Edge 2 (dot → target); keeping it on Edge 1
            # (source → dot) clips the edge at a cluster boundary the dot is
            # outside of, causing GraphViz to mis-route the arrow.
            clean_attrs = re.sub(r"\bltail=[^\s\]]+\s*", "", edge_attrs).strip()
            clean_attrs = re.sub(r"\blhead=[^\s\]]+\s*", "", clean_attrs).strip()
            # Clean merged labels from pytransitions (e.g. "reset | " → "reset")
            clean_attrs = re.sub(r'\s*\|\s*"', '"', clean_attrs)
            clean_attrs = re.sub(r'="\s*\|\s*', '="', clean_attrs)

            if source == target:
                # ── Case 1: self-loop on composite ────────────────────────────
                node_name = f"_selfloop_{source}_{counter}"
                counter += 1

                # Dot node goes in the parent cluster (inside Active for Cleaning,
                # at top level for Active itself).
                deferred_nodes[parent_cluster].append(
                    f'\t"{node_name}" '
                    f'[shape=point width=0 height=0 style=invis label=""]'
                )

                if clean_attrs.startswith("["):
                    out_attrs = "[ltail=" + source_cluster + " " + clean_attrs[1:]
                elif clean_attrs:
                    out_attrs = (
                        "[ltail=" + source_cluster + " " + clean_attrs.strip("[]") + "]"
                    )
                else:
                    out_attrs = f"[ltail={source_cluster}]"

                # Edge 1: cluster boundary ──(label)──> dot  (no arrowhead)
                extra_edges.append(
                    f'{indent}{source_raw} -> "{node_name}" {out_attrs[:-1]} dir=none]'
                    if out_attrs.endswith("]")
                    else f'{indent}{source_raw} -> "{node_name}" {out_attrs} [dir=none]'
                )
                # Edge 2: dot ──> cluster boundary (constraint=false avoids
                # pushing the dot node out of the parent cluster rank)
                extra_edges.append(
                    f'{indent}"{node_name}" -> {target_raw} '
                    f"[lhead={source_cluster} constraint=false]"
                )

                lines_to_skip.add(i)
                if after_edge.strip():
                    residuals[i] = "\t" + after_edge.lstrip("\t ")

            elif target.startswith(cluster_prefix + "_"):
                # ── Case 2: composite -> own child ────────────────────────────
                # ltail is silently ignored by GraphViz when the destination is
                # inside the ltail cluster.  Route through an intermediate dot.
                node_name = f"_entry_{source}_{counter}"
                counter += 1

                deferred_nodes[parent_cluster].append(
                    f'\t"{node_name}" '
                    f'[shape=point width=0 height=0 style=invis label=""]'
                )

                if clean_attrs.startswith("["):
                    out_attrs = "[ltail=" + source_cluster + " " + clean_attrs[1:]
                elif clean_attrs:
                    out_attrs = (
                        "[ltail=" + source_cluster + " " + clean_attrs.strip("[]") + "]"
                    )
                else:
                    out_attrs = f"[ltail={source_cluster}]"

                # Edge 1: cluster boundary ──(label)──> dot  (no arrowhead)
                extra_edges.append(
                    f'{indent}{source_raw} -> "{node_name}" {out_attrs[:-1]} dir=none]'
                    if out_attrs.endswith("]")
                    else f'{indent}{source_raw} -> "{node_name}" {out_attrs} [dir=none]'
                )
                # Edge 2: dot ──> target child (enters the cluster).
                # If the child is itself composite, add lhead so the arrowhead
                # stops at the cluster border rather than the inner black dot.
                target_child_cluster = initial_to_cluster.get(target)
                if target_child_cluster:
                    extra_edges.append(
                        f'{indent}"{node_name}" -> {target_raw} '
                        f"[lhead={target_child_cluster} constraint=false]"
                    )
                else:
                    extra_edges.append(f'{indent}"{node_name}" -> {target_raw}')

                lines_to_skip.add(i)
                if after_edge.strip():
                    residuals[i] = "\t" + after_edge.lstrip("\t ")

            elif target_cluster and source.startswith(target + "_"):
                # ── Case 3a: composite → composite ancestor ────────────────────
                # e.g. LoggedIn → On.  pytransitions adds ltail but not lhead
                # when dest is an ancestor of source.  lhead alone also fails
                # because the source is inside the lhead cluster.  Use the same
                # intermediate-dot self-loop approach as Case 1.
                node_name = f"_escape_{target}_{counter}"
                counter += 1
                target_parent_cluster = cluster_parent.get(target_cluster)
                deferred_nodes[target_parent_cluster].append(
                    f'\t"{node_name}" '
                    f'[shape=point width=0 height=0 style=invis label=""]'
                )
                if clean_attrs.startswith("["):
                    out_attrs = "[ltail=" + source_cluster + " " + clean_attrs[1:]
                elif clean_attrs:
                    out_attrs = (
                        "[ltail=" + source_cluster + " " + clean_attrs.strip("[]") + "]"
                    )
                else:
                    out_attrs = f"[ltail={source_cluster}]"
                # Edge 1: tail exits source cluster boundary (no arrowhead)
                extra_edges.append(
                    f'{indent}{source_raw} -> "{node_name}" {out_attrs[:-1]} dir=none]'
                    if out_attrs.endswith("]")
                    else f'{indent}{source_raw} -> "{node_name}" {out_attrs} [dir=none]'
                )
                # Edge 2: dot → arrowhead re-enters target cluster boundary
                extra_edges.append(
                    f'{indent}"{node_name}" -> {target_raw} '
                    f"[lhead={target_cluster} constraint=false]"
                )
                lines_to_skip.add(i)
                if after_edge.strip():
                    residuals[i] = "\t" + after_edge.lstrip("\t ")

        # ── Pass 3: rebuild body, inject dot nodes at correct cluster boundaries ─
        fixed_body = []
        cluster_stack_build = []

        for i, item in enumerate(graph.body):
            if i in lines_to_skip:
                # Preserve any secondary statement packed in the same body item.
                if i in residuals:
                    fixed_body.append(residuals[i])
                continue

            m = re.search(r"subgraph\s+(cluster_\w+)", item)
            if m:
                cluster_stack_build.append(m.group(1))
                fixed_body.append(item)
                continue

            if item.strip() == "}" and cluster_stack_build:
                closing = cluster_stack_build[-1]
                cluster_stack_build.pop()
                # Inject dot nodes deferred to this cluster before its closing brace.
                if closing in deferred_nodes:
                    fixed_body.extend(deferred_nodes[closing])
                fixed_body.append(item)
                continue

            fixed_body.append(item)

        # Top-level dot nodes (for root-level composite self-loops / own-child).
        fixed_body.extend(deferred_nodes.get(None, []))
        # All replacement edges go at the top level.
        fixed_body.extend(extra_edges)

        graph.body = fixed_body

        # compound=true is required for lhead/ltail to take effect.
        graph.graph_attr["compound"] = "true"
        # ortho routing gives right-angle bends, making self-loops look rectangular.
        graph.graph_attr["splines"] = "ortho"

    except Exception as e:
        print(f"Warning: Could not apply hierarchical state fix: {e}")
        import traceback

        traceback.print_exc()

    return graph


def _create_single_prompt_gsm_diagram_with_sherpa_in_process(
    mermaid_code: str, diagram_file_path: str
):
    """
    Create a state machine diagram from Mermaid code using Sherpa

    params:
    mermaid_code: The Mermaid stateDiagram-v2 code as a string
    diagram_file_path: Path where to save the PNG diagram
    """
    with MERMAID_RENDER_LOCK:
        try:
            from .mermaid_to_sherpa_parser import parse_mermaid_with_library
        except (ImportError, KeyError):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from mermaid_to_sherpa_parser import parse_mermaid_with_library

        (
            states_list,
            transitions_list,
            hierarchical_dict,
            initial_state,
            parallel_regions,
            state_annotations,
            root_initial_state,
            nested_initial_states,
            state_declarations_map,
        ) = parse_mermaid_with_library(mermaid_code)

        def _collect_parallel_composite_paths(states, prefix=""):
            paths = set()
            for st in states:
                if not isinstance(st, dict):
                    continue
                name = st.get("name")
                if not name:
                    continue
                full_name = f"{prefix}_{name}" if prefix else name
                if isinstance(st.get("initial"), list):
                    paths.add(full_name)
                paths.update(
                    _collect_parallel_composite_paths(st.get("children", []), full_name)
                )
            return paths

        parallel_composite_paths = _collect_parallel_composite_paths(states_list)

        print("\nParser Debug Output:")
        print("─" * 60)
        print("\nState Declarations Map (from raw mermaid scan):")
        if state_declarations_map:
            for state_name, parent_id in sorted(state_declarations_map.items()):
                parent_str = parent_id if parent_id else "ROOT"
                print(f"  {state_name} → {parent_str}")
        else:
            print("  (empty)")

        print("\nParsed States:")
        print(f"  {states_list}")

        print("\nParsed Transitions:")
        for trans in transitions_list:
            source = trans.get("source", "?")
            dest = trans.get("dest", "?")
            trigger = trans.get("trigger", "?")
            print(f"  {source} --{trigger}--> {dest}")

        print(f"\nInitial State: {initial_state}")
        print("─" * 60)

        if not initial_state:
            print("Warning: No initial state found, using first state")
            if states_list:
                initial_state = (
                    states_list[0]
                    if isinstance(states_list[0], str)
                    else states_list[0]["name"]
                )
            else:
                raise ValueError("No states found in Mermaid diagram")

        try:
            gsm = SherpaStateMachine(
                states=states_list,
                transitions=transitions_list,
                initial=initial_state,
                sm_cls=HierarchicalGraphMachine,
            )

            try:
                node_defaults = (
                    gsm.sm.style_attributes.get("node", {}).get("default", {}).copy()
                )
                graph_defaults = (
                    gsm.sm.style_attributes.get("graph", {}).get("default", {}).copy()
                )
                gsm.sm.style_attributes.setdefault("node", {})["active"] = node_defaults
                gsm.sm.style_attributes.setdefault("graph", {})[
                    "active"
                ] = graph_defaults
            except Exception:
                pass

            png_file_path = (
                f"{diagram_file_path}.png"
                if not diagram_file_path.endswith(".png")
                else diagram_file_path
            )

            graph = gsm.sm.get_graph()
            graph = fix_hierarchical_state_transitions(graph)

            try:
                new_body = []
                current_subgraphs = []
                i = 0
                while i < len(graph.body):
                    line = graph.body[i]
                    if "subgraph" in line:
                        match = re.search(r"subgraph\s+(\S+)", line)
                        if match:
                            subgraph_name = match.group(1)
                            indent_match = re.match(r"(\s*)", line)
                            indent_level = (
                                len(indent_match.group(1)) if indent_match else 0
                            )
                            current_subgraphs.append((subgraph_name, indent_level))
                            new_body.append(line)
                            i += 1
                            continue

                    if line.strip() == "}":
                        if current_subgraphs:
                            indent_match = re.match(r"(\s*)", line)
                            current_indent = (
                                len(indent_match.group(1)) if indent_match else 0
                            )
                            while (
                                current_subgraphs
                                and current_subgraphs[-1][1] >= current_indent
                            ):
                                current_subgraphs.pop()

                    new_body.append(line)
                    i += 1

                if root_initial_state:
                    insert_index = 0
                    for idx, line in enumerate(new_body):
                        if (
                            "digraph" in line
                            or "graph [" in line
                            or "node [" in line
                            or "edge [" in line
                        ):
                            insert_index = idx + 1
                        elif "subgraph" in line:
                            break

                    root_marker = "_initial"
                    new_body.insert(
                        insert_index,
                        f'\t"{root_marker}" [fillcolor=black color=black height=0.15 label="" shape=point width=0.15]',
                    )

                    root_cluster = f"cluster_{root_initial_state}"
                    cluster_names_in_graph = [
                        re.search(r"subgraph\s+(\S+)", l).group(1)
                        for l in new_body
                        if "subgraph" in l and re.search(r"subgraph\s+(\S+)", l)
                    ]
                    if root_cluster in cluster_names_in_graph:
                        new_body.insert(
                            insert_index + 1,
                            f'\t"{root_marker}" -> "{root_initial_state}" [lhead={root_cluster}]',
                        )
                    else:
                        new_body.insert(
                            insert_index + 1,
                            f'\t"{root_marker}" -> "{root_initial_state}"',
                        )

                # Inject [*]→Child initial-state edges for nested composites.
                # pytransitions merges [*]→Child with regular transitions that
                # target the same child (e.g. "reset | ").  When Case 2 of
                # fix_hierarchical_state_transitions replaces that merged edge
                # with an intermediate-dot pair, the composite's entry black dot
                # loses its outgoing edge.  Re-inject it here using
                # nested_initial_states from the parser.
                if nested_initial_states:
                    _cluster_names_set = {
                        m.group(1)
                        for l in new_body
                        for m in [re.search(r"subgraph\s+(\S+)", l)]
                        if m
                    }
                    for _parent_id, _child_bare in nested_initial_states.items():
                        _child_full = f"{_parent_id}_{_child_bare}"

                        # For parallel composites, pytransitions does not
                        # create an initial point node inside the cluster.
                        # We must create one explicitly so the black dot
                        # is visible.
                        if _parent_id in parallel_composite_paths:
                            _init_node = f"_initial_{_parent_id}"
                            _parent_cluster = f"cluster_{_parent_id}"
                            # Insert the point node inside the parent's
                            # cluster subgraph (right after the subgraph
                            # opening line).
                            for _idx, _line in enumerate(new_body):
                                if (
                                    "subgraph" in _line
                                    and re.search(
                                        rf"subgraph\s+{re.escape(_parent_cluster)}\b",
                                        _line,
                                    )
                                ):
                                    new_body.insert(
                                        _idx + 1,
                                        f'\t\t"{_init_node}" [fillcolor=black color=black height=0.15 label="" shape=point width=0.15]',
                                    )
                                    break
                            _child_cluster = f"cluster_{_child_full}"
                            if _child_cluster in _cluster_names_set:
                                new_body.append(
                                    f'\t"{_init_node}" -> "{_child_full}" '
                                    f'[headlabel="" lhead={_child_cluster}]'
                                )
                            else:
                                new_body.append(
                                    f'\t"{_init_node}" -> "{_child_full}" [headlabel=""]'
                                )
                            continue

                        _pat = re.compile(
                            rf'"?{re.escape(_parent_id)}"?\s*->\s*"?{re.escape(_child_full)}"?'
                        )
                        if not any(_pat.search(l) for l in new_body):
                            _child_cluster = f"cluster_{_child_full}"
                            if _child_cluster in _cluster_names_set:
                                new_body.append(
                                    f'\t"{_parent_id}" -> "{_child_full}" '
                                    f'[headlabel="" lhead={_child_cluster}]'
                                )
                            else:
                                new_body.append(
                                    f'\t"{_parent_id}" -> "{_child_full}" [headlabel=""]'
                                )

                point_node_re = re.compile(
                    r'^\s*"?([A-Za-z_][A-Za-z0-9_]*)"?\s*\[.*\bshape=point\b.*\]'
                )
                edge_re = re.compile(
                    r'^\s*("?[A-Za-z_][A-Za-z0-9_]*"?)\s*->\s*("?[A-Za-z_][^\s\[]*"?)'
                )
                point_nodes = set()
                nodes_with_edges = set()

                for body_line in new_body:
                    m_node = point_node_re.match(body_line)
                    if m_node:
                        point_nodes.add(m_node.group(1))

                    m_edge = edge_re.match(body_line)
                    if m_edge:
                        src = m_edge.group(1).strip('"')
                        dst = m_edge.group(2).strip('"')
                        nodes_with_edges.add(src)
                        nodes_with_edges.add(dst)

                for node_name in sorted(point_nodes - nodes_with_edges):
                    new_body.append(
                        f'\t"{node_name}" [style=invis width=0 height=0 label=""]'
                    )

                for node_name in sorted(parallel_composite_paths):
                    new_body.append(
                        f'\t"{node_name}" [style=invis width=0 height=0 label=""]'
                    )

                graph.body = new_body
            except Exception as e:
                print(f"Warning: Could not add initial state markers: {e}")
                import traceback

                traceback.print_exc()

            if state_annotations:
                annotation_text = "\\l".join(state_annotations) + "\\l"
                graph.graph_attr["label"] = annotation_text
                graph.graph_attr["labelloc"] = "b"
                graph.graph_attr["labeljust"] = "l"
                graph.graph_attr["fontsize"] = "10"

            gv_debug_path = png_file_path.replace(".png", ".gv")
            with open(gv_debug_path, "w") as f:
                f.write(graph.source)
            print(f"GraphViz source saved to: {gv_debug_path}")

            graph.draw(png_file_path, prog="dot", format="png")
            print(f"Sherpa diagram saved to: {png_file_path}")
            return True
        except Exception as e:
            print(f"Error creating Sherpa state machine: {str(e)}")
            import traceback

            traceback.print_exc()
            return False


def create_single_prompt_gsm_diagram_with_sherpa(
    mermaid_code: str, diagram_file_path: str
):
    """
    Run Mermaid parsing/rendering in a child process so native parser crashes
    do not take down the main backend process.
    """
    worker_script = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "sherpa_render_worker.py"
    )

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as request_file:
        request_path = request_file.name
        json.dump(
            {
                "mermaid_code": mermaid_code,
                "diagram_file_path": diagram_file_path,
            },
            request_file,
        )

    try:
        result = subprocess.run(
            [sys.executable, worker_script, request_path],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        with contextlib.suppress(OSError):
            os.unlink(request_path)

    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(
            result.stderr,
            file=sys.stderr,
            end="" if result.stderr.endswith("\n") else "\n",
        )

    if result.returncode == 0:
        return True

    print(f"Renderer subprocess failed with exit code {result.returncode}")
    return False
