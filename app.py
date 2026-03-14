import os
import chainlit as cl
import io
import contextlib
import asyncio

import backend.resources.state_machine_descriptions
from backend.resources.llm_tracker import llm
from backend.single_prompt import run_single_prompt, run_test_entry_exit_annotations
from backend.two_shot_prompt import run_two_shot_prompt


# ---------------------------------------------------------------------------
# Model helpers
# ---------------------------------------------------------------------------

def convert_to_openrouter_model(chat_profile):
    if not chat_profile:
        return "anthropic/claude-3.5-sonnet"

    profile_to_openrouter = {
        "anthropic:claude-3-5-sonnet-20241022": "anthropic/claude-3.5-sonnet",
        "anthropic:claude-4-5-sonnet": "anthropic/claude-4.5-sonnet",
        "anthropic:claude-sonnet-4": "anthropic/claude-sonnet-4",
        "openai:gpt-4o": "openai/gpt-4o",
        "openai:gpt-4o-mini": "openai/gpt-4o-mini",
        "openai:gpt-4-turbo": "openai/gpt-4-turbo",
        "openai:o1": "openai/o1",
        "openai:o1-mini": "openai/o1-mini",
        "google:gemini-2-0-flash-exp": "google/gemini-2.0-flash-exp",
        "google:gemini-1-5-pro-001": "google/gemini-pro-1.5",
        "google:gemini-1-5-flash": "google/gemini-flash-1.5",
        "meta:llama-3-3-70b-instruct": "meta-llama/llama-3.3-70b-instruct",
        "meta:llama-3-1-405b-instruct": "meta-llama/llama-3.1-405b-instruct",
        "meta:llama-3-1-70b-instruct": "meta-llama/llama-3.1-70b-instruct",
        "meta:llama-3-2-3b-instruct": "meta-llama/llama-3.2-3b-instruct",
        "qwen:qwq-32b": "qwen/qwq-32b",
        "qwen:qwen-2-5-72b-instruct": "qwen/qwen-2.5-72b-instruct",
        "groq:llama-3.2-3b-preview": "meta-llama/llama-3.2-3b-instruct",
    }

    return profile_to_openrouter.get(chat_profile, "anthropic/claude-3.5-sonnet")


# ---------------------------------------------------------------------------
# Chat profiles
# ---------------------------------------------------------------------------

@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(name="anthropic:claude-4-5-sonnet",       markdown_description="**Claude 4.5 Sonnet** (Anthropic)", icon="https://picsum.photos/203"),
        cl.ChatProfile(name="anthropic:claude-3-5-sonnet-20241022", markdown_description="**Claude 3.5 Sonnet** (Anthropic)", icon="https://picsum.photos/203"),
        cl.ChatProfile(name="anthropic:claude-sonnet-4",          markdown_description="**Claude Sonnet 4** (Anthropic)",    icon="https://picsum.photos/203"),
        cl.ChatProfile(name="openai:gpt-4o",                      markdown_description="**GPT-4o** (OpenAI)",                icon="https://picsum.photos/202"),
        cl.ChatProfile(name="openai:gpt-4o-mini",                 markdown_description="**GPT-4o Mini** (OpenAI)",           icon="https://picsum.photos/202"),
        cl.ChatProfile(name="openai:gpt-4-turbo",                 markdown_description="**GPT-4 Turbo** (OpenAI)",           icon="https://picsum.photos/202"),
        cl.ChatProfile(name="openai:o1",                          markdown_description="**o1** — reasoning (OpenAI)",        icon="https://picsum.photos/202"),
        cl.ChatProfile(name="openai:o1-mini",                     markdown_description="**o1-mini** — reasoning (OpenAI)",   icon="https://picsum.photos/202"),
        cl.ChatProfile(name="google:gemini-2-0-flash-exp",        markdown_description="**Gemini 2.0 Flash** (Google)",      icon="https://picsum.photos/205"),
        cl.ChatProfile(name="google:gemini-1-5-pro-001",          markdown_description="**Gemini 1.5 Pro** (Google)",        icon="https://picsum.photos/205"),
        cl.ChatProfile(name="google:gemini-1-5-flash",            markdown_description="**Gemini 1.5 Flash** (Google)",      icon="https://picsum.photos/205"),
        cl.ChatProfile(name="meta:llama-3-3-70b-instruct",        markdown_description="**Llama 3.3 70B** (Meta)",           icon="https://picsum.photos/204"),
        cl.ChatProfile(name="meta:llama-3-1-405b-instruct",       markdown_description="**Llama 3.1 405B** (Meta)",          icon="https://picsum.photos/204"),
        cl.ChatProfile(name="meta:llama-3-1-70b-instruct",        markdown_description="**Llama 3.1 70B** (Meta)",           icon="https://picsum.photos/204"),
        cl.ChatProfile(name="meta:llama-3-2-3b-instruct",         markdown_description="**Llama 3.2 3B** (Meta)",            icon="https://picsum.photos/204"),
        cl.ChatProfile(name="qwen:qwq-32b",                       markdown_description="**QwQ 32B** (Qwen)",                 icon="https://picsum.photos/200"),
        cl.ChatProfile(name="qwen:qwen-2-5-72b-instruct",         markdown_description="**Qwen 2.5 72B** (Qwen)",            icon="https://picsum.photos/201"),
    ]


# ---------------------------------------------------------------------------
# Example catalogue
# ---------------------------------------------------------------------------

EXAMPLES = [
    ("printer_winter_2017",             "🖨️",  "Printer System",          "office printer with card authentication, print/scan, and error handling"),
    ("spa_manager_winter_2018",         "🧖",  "Spa Manager",             "sauna & Jacuzzi control with temperature regulation and water jets"),
    ("dishwasher_winter_2019",          "✨",  "Smart Dishwasher",        "automated dishwasher with multiple programs, drying, and door safety"),
    ("chess_clock_fall_2019",           "🕰️",  "Digital Chess Clock",     "tournament chess clock with multiple timing modes and player controls"),
    ("automatic_bread_maker_fall_2020", "🥖",  "Automatic Bread Maker",   "programmable bread maker with crust options and delayed start"),
    ("thermomix_fall_2021",             "🔪",  "Thermomix TM6",           "guided recipe steps and ingredient processing"),
    ("ATAS_fall_2022",                  "🚆",  "Train Automation System", "driverless trains across a rail network with signals and stations"),
    ("WUMPLE_fall_2023_Version_A",      "⌚",  "Wumple Watch",            "timekeeping, alarm, and countdown modes with backlight and flash alerts"),
    ("SSC7_fall_2024_Version_A",        "🛒",  "SSC7 Self-Checkout",      "supermarket self-checkout with scanning, weighing, payment, and staff override"),
]


def _system_display_name(preset: str) -> str:
    """Convert preset variable name to a readable display name."""
    words = []
    for part in preset.split("_"):
        if part.isupper() or part.isdigit():
            words.append(part)
        else:
            words.append(part.capitalize())
    return " ".join(words)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

@cl.on_chat_start
async def start():
    cl.user_session.set("diagram_path", None)
    llm.update_llm(cl.user_session.get("chat_profile"))
    await setup_flow()


# ---------------------------------------------------------------------------
# Flow helpers (re-callable)
# ---------------------------------------------------------------------------

async def setup_flow():
    """Strategy selection → input selection. Called on start and after 'Switch Mode'."""
    strategy_step = await cl.AskActionMessage(
        content=(
            "**Welcome to Sherpa 🏔️**\n\n"
            "Choose your generation strategy:"
        ),
        actions=[
            cl.Action(name="single_prompt",  value="single_prompt",  payload={}, label="🚀 Single Prompt"),
            cl.Action(name="two_shot_prompt", value="two_shot_prompt", payload={}, label="🔁 Two-Shot Prompt"),
        ],
    ).send()

    if strategy_step:
        cl.user_session.set("generation_strategy", strategy_step["name"])

    await show_input_selection()


async def show_input_selection():
    """Input mode selection. Called after strategy is set."""
    step1 = await cl.AskActionMessage(
        content="How would you like to provide input?",
        actions=[
            cl.Action(name="custom",         value="custom",         payload={}, label="✍️ Describe Your Own System"),
            cl.Action(name="example",        value="example",        payload={}, label="🤖 Use One of Our Examples"),
            cl.Action(name="show_history",   value="show_history",   payload={}, label="📚 View History"),
            cl.Action(name="custom_mermaid", value="custom_mermaid", payload={}, label="🎨 Test Custom Mermaid"),
            cl.Action(name="dev_tests",      value="dev_tests",      payload={}, label="🧪 Developer Tests"),
        ],
    ).send()

    step1_value = step1.get("name") if step1 else None

    if step1_value == "show_history":
        await show_history()
        await show_input_selection()  # loop back so user can pick next action
        return

    if step1_value == "example":
        description = await pick_and_run_example()
        if description:
            await post_run_loop()

    elif step1_value == "custom_mermaid":
        cl.user_session.set("mode", "custom_mermaid")
        cl.user_session.set("generation_strategy", "single_prompt")
        await cl.Message(
            content=(
                "🎨 **Test Custom Mermaid Code**\n\n"
                "Paste your Mermaid state diagram below. "
                "You can keep pasting diagrams — type `exit` to leave this mode."
            )
        ).send()
        mermaid_input = await cl.AskUserMessage(content="Paste your Mermaid code:", timeout=300).send()
        if mermaid_input:
            await _process_custom_mermaid(mermaid_input["output"])

    elif step1_value == "dev_tests":
        await run_dev_tests()

    else:  # custom
        cl.user_session.set("system_name", "Custom")
        await cl.Message(
            content="Describe any process, workflow, or behavior you'd like to model."
        ).send()


async def pick_and_run_example() -> str | None:
    """Show example picker, set session state, run the grading. Returns description or None."""
    description_lines = "\n".join(
        f"**{emoji} {name}** — {blurb}"
        for _, emoji, name, blurb in EXAMPLES
    )
    actions = [
        cl.Action(name=preset, value=preset, payload={}, label=f"{emoji} {name}")
        for preset, emoji, name, _ in EXAMPLES
    ]

    step2 = await cl.AskActionMessage(
        content=f"Choose an example:\n\n{description_lines}",
        actions=actions,
    ).send()

    if not step2:
        return None

    system_preset = step2.get("name")
    description = getattr(backend.resources.state_machine_descriptions, system_preset)
    cl.user_session.set("system_name", _system_display_name(system_preset))

    await _run_grading(description)
    return description


async def post_run_loop():
    """
    Shown after every completed grading run.
    Loops until the user wants to type a new custom description (on_message takes over).
    """
    while True:
        action = await cl.AskActionMessage(
            content="**Run complete ✅  What next?**",
            actions=[
                cl.Action(name="new_custom",   value="new_custom",   payload={}, label="✍️ New Custom Input"),
                cl.Action(name="new_example",  value="new_example",  payload={}, label="🤖 Use An Example"),
                cl.Action(name="switch_mode",  value="switch_mode",  payload={}, label="🔀 Switch Mode"),
                cl.Action(name="show_history", value="show_history", payload={}, label="📚 View History"),
            ],
        ).send()

        name = action.get("name") if action else None

        if name == "show_history":
            await show_history()

        elif name == "new_example":
            await pick_and_run_example()

        elif name == "switch_mode":
            strategy_step = await cl.AskActionMessage(
                content="Choose strategy:",
                actions=[
                    cl.Action(name="single_prompt",   value="single_prompt",   payload={}, label="🚀 Single Prompt"),
                    cl.Action(name="two_shot_prompt",  value="two_shot_prompt",  payload={}, label="🔁 Two-Shot Prompt"),
                ],
            ).send()
            if strategy_step:
                cl.user_session.set("generation_strategy", strategy_step["name"])
            # Stay in loop — user can now pick new_example or new_custom

        elif name == "new_custom":
            cl.user_session.set("system_name", "Custom")
            await cl.Message(content="Describe your system below.").send()
            return  # Let on_message fire for the user's next message

        else:
            return  # Timeout — exit loop gracefully


# ---------------------------------------------------------------------------
# Core grading runner
# ---------------------------------------------------------------------------

async def _run_grading(description: str):
    """Execute one grading cycle: run strategy, stream steps, show mermaid + diagram."""
    strategy = cl.user_session.get("generation_strategy", "single_prompt")
    chat_profile = cl.user_session.get("chat_profile")
    openrouter_model = convert_to_openrouter_model(chat_profile)
    system_name = cl.user_session.get("system_name", "Custom")

    await cl.Message(content=description, author="Input").send()

    stdout_capture = io.StringIO()
    current_step = None
    current_step_content = []

    async def run_and_capture():
        with contextlib.redirect_stdout(stdout_capture):
            if strategy == "single_prompt":
                success = await asyncio.to_thread(
                    run_single_prompt, description, openrouter_model, system_name
                )
            else:  # two_shot_prompt
                success = await asyncio.to_thread(
                    run_two_shot_prompt, description, openrouter_model, system_name
                )
        cl.user_session.set("generation_success", success)

    task = asyncio.create_task(run_and_capture())

    while not task.done():
        await asyncio.sleep(0.1)
        stdout_capture.seek(0)
        current_output = stdout_capture.read()

        if current_output:
            lines = current_output.splitlines()
            for line in lines:
                is_step_start = line.startswith("Running")
                if is_step_start:
                    if current_step is not None:
                        current_step.output = "\n".join(current_step_content)
                        await current_step.update()
                        await current_step.__aexit__(None, None, None)
                    step_name = (
                        line[8:].replace("...", "").replace("start_", "") + " action"
                        if line.startswith("Running ")
                        else line
                    )
                    current_step = cl.Step(name=step_name)
                    await current_step.__aenter__()
                    current_step_content = [line]
                elif current_step is not None:
                    current_step_content.append(line)
            stdout_capture.truncate(0)
            stdout_capture.seek(0)

    if current_step is not None:
        current_step.output = "\n".join(current_step_content)
        await current_step.update()
        await current_step.__aexit__(None, None, None)

    await task

    async with cl.Step(name="Mermaid Code"):
        await display_mermaid_code_from_log()

    async with cl.Step(name="Diagram"):
        await display_image()


# ---------------------------------------------------------------------------
# Developer tests
# ---------------------------------------------------------------------------

async def run_dev_tests():
    test_choice = await cl.AskActionMessage(
        content="**🧪 Developer Tests**\n\nThese use hardcoded Mermaid (no LLM call):",
        actions=[
            cl.Action(name="test_entry_exit", value="test_entry_exit", payload={}, label="🧪 Entry/Exit Annotations"),
        ],
    ).send()

    if not test_choice:
        return

    cl.user_session.set("generation_strategy", "single_prompt")

    if test_choice.get("name") == "test_entry_exit":
        await cl.Message(content="🧪 Running: Entry/Exit Annotations…").send()
        async with cl.Step(name="Running Test") as test_step:
            stdout_capture = io.StringIO()
            with contextlib.redirect_stdout(stdout_capture):
                success = await asyncio.to_thread(run_test_entry_exit_annotations)
            cl.user_session.set("generation_success", success)
            test_step.output = stdout_capture.getvalue()

        async with cl.Step(name="Diagram"):
            await display_image()


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

async def show_history():
    """Scan output folders and display a summary table + recent images."""
    base = os.path.join(os.path.dirname(__file__), "backend", "resources")
    runs = []

    for strategy in ("single_prompt", "two_shot_prompt"):
        outputs_dir = os.path.join(base, f"{strategy}_outputs")
        if not os.path.exists(outputs_dir):
            continue
        for date_folder in os.listdir(outputs_dir):
            date_path = os.path.join(outputs_dir, date_folder)
            if not os.path.isdir(date_path):
                continue
            for model_folder in os.listdir(date_path):
                model_path = os.path.join(date_path, model_folder)
                if not os.path.isdir(model_path):
                    continue
                for system_folder in os.listdir(model_path):
                    system_path = os.path.join(model_path, system_folder)
                    if not os.path.isdir(system_path):
                        continue
                    for time_folder in os.listdir(system_path):
                        time_path = os.path.join(system_path, time_folder)
                        if not os.path.isdir(time_path):
                            continue
                        png_files = [f for f in os.listdir(time_path) if f.endswith(".png")]
                        png_path = os.path.join(time_path, png_files[0]) if png_files else None
                        runs.append({
                            "strategy": strategy,
                            "date": date_folder,
                            "model": model_folder,
                            "system": system_folder,
                            "time": time_folder,
                            "png": png_path,
                            "sort_key": f"{date_folder}_{time_folder}",
                        })

    if not runs:
        await cl.Message(content="📚 No history found yet.").send()
        return

    runs.sort(key=lambda r: r["sort_key"], reverse=True)

    # Build summary table
    table_rows = []
    for r in runs[:30]:
        mode_icon = "🚀" if r["strategy"] == "single_prompt" else "🔁"
        date_fmt = r["date"].replace("_", "-")
        time_fmt = r["time"].replace("_", ":")
        table_rows.append(
            f"| {date_fmt} {time_fmt} | {mode_icon} {r['strategy'].replace('_', ' ').title()} | {r['model']} | {r['system']} |"
        )

    table = (
        "### 📚 Run History (most recent first)\n\n"
        "| Date & Time | Mode | Model | System |\n"
        "|-------------|------|-------|--------|\n"
        + "\n".join(table_rows)
    )
    await cl.Message(content=table).send()

    # Show images for the 5 most recent runs that have a PNG
    recent_with_images = [r for r in runs if r["png"] and os.path.exists(r["png"])][:5]
    for r in recent_with_images:
        date_fmt = r["date"].replace("_", "-")
        time_fmt = r["time"].replace("_", ":")
        label = f"{date_fmt} {time_fmt} · {r['model']} · {r['system']}"
        image = cl.Image(path=r["png"], name=os.path.basename(r["png"]), display="inline", size="large")
        await cl.Message(content=f"**{label}**", elements=[image]).send()


# ---------------------------------------------------------------------------
# Custom Mermaid handler (called from on_message when in custom_mermaid mode)
# ---------------------------------------------------------------------------

async def _process_custom_mermaid(mermaid_code: str):
    cl.user_session.set("diagram_path", None)
    async with cl.Step(name="Rendering Diagram") as render_step:
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            from backend.single_prompt import process_custom_mermaid
            success, diagram_path = await asyncio.to_thread(
                process_custom_mermaid, mermaid_code, "CustomMermaid"
            )
        cl.user_session.set("generation_success", success)
        cl.user_session.set("diagram_path", diagram_path)
        render_step.output = stdout_capture.getvalue()

    if success:
        await display_image()
        await cl.Message(
            content="✅ Rendered! Paste another diagram or type `exit` to leave this mode."
        ).send()
    else:
        await cl.Message(
            content="❌ Render failed. Check the step output above and try again, or type `exit`."
        ).send()


# ---------------------------------------------------------------------------
# on_message
# ---------------------------------------------------------------------------

@cl.on_message
async def run_conversation(message: cl.Message):
    mode = cl.user_session.get("mode")

    if mode == "custom_mermaid":
        if message.content.strip().lower() in ("exit", "quit", "stop"):
            cl.user_session.set("mode", None)
            await cl.Message(content="Exited custom Mermaid mode.").send()
            await show_input_selection()
            return
        await _process_custom_mermaid(message.content.strip())
        return

    # Normal grading run triggered by user typing a description
    await _run_grading(message.content)
    await post_run_loop()


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _find_deepest_folder(folder_path, depth=0, max_depth=3):
    if depth >= max_depth:
        return folder_path
    subfolders = [
        d for d in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, d))
    ]
    if subfolders:
        latest = max(
            (os.path.join(folder_path, d) for d in subfolders),
            key=os.path.getmtime,
        )
        return _find_deepest_folder(latest, depth + 1, max_depth)
    return folder_path


async def display_mermaid_code_from_log():
    strategy = cl.user_session.get("generation_strategy", "single_prompt")
    try:
        outputs_base = os.path.join(
            os.path.dirname(__file__), "backend", "resources", f"{strategy}_outputs"
        )
        if not os.path.exists(outputs_base):
            await cl.Message(content="⚠️ No outputs directory found.").send()
            return

        date_folders = [d for d in os.listdir(outputs_base) if os.path.isdir(os.path.join(outputs_base, d))]
        if not date_folders:
            await cl.Message(content="⚠️ No output folders found.").send()
            return

        latest_date_folder = max(
            (os.path.join(outputs_base, d) for d in date_folders),
            key=os.path.getmtime,
        )
        latest_folder = _find_deepest_folder(latest_date_folder)

        mmd_files = [f for f in os.listdir(latest_folder) if f.endswith(".mmd")]
        if not mmd_files:
            await cl.Message(content="⚠️ No .mmd file in latest output folder.").send()
            return

        latest_mmd = os.path.join(latest_folder, sorted(mmd_files)[-1])
        with open(latest_mmd) as f:
            mermaid_code = f.read()

        relative_path = os.path.relpath(latest_mmd, os.path.dirname(__file__))
        await cl.Message(
            content=f"### 📝 Generated Mermaid Code\n\n📁 `{relative_path}`\n\n```mermaid\n{mermaid_code}\n```"
        ).send()

    except Exception as e:
        await cl.Message(content=f"⚠️ Error reading Mermaid code: {e}").send()


async def display_image():
    import json

    generation_success = cl.user_session.get("generation_success", True)
    if not generation_success:
        await cl.Message(content="❌ State machine generation failed after 5 attempts. Check logs.").send()
        return

    strategy = cl.user_session.get("generation_strategy", "single_prompt")
    outputs_directory = os.path.join(
        os.path.dirname(__file__), "backend", "resources", f"{strategy}_outputs"
    )

    # Check for error marker files
    try:
        if os.path.exists(outputs_directory):
            timestamped_folders = [
                d for d in os.listdir(outputs_directory)
                if os.path.isdir(os.path.join(outputs_directory, d))
            ]
            if timestamped_folders:
                latest_folder = max(
                    (os.path.join(outputs_directory, d) for d in timestamped_folders),
                    key=os.path.getmtime,
                )
                error_files = [f for f in os.listdir(latest_folder) if f.endswith("_error.json")]
                if error_files:
                    latest_error = max(
                        (os.path.join(latest_folder, f) for f in error_files),
                        key=os.path.getmtime,
                    )
                    with open(latest_error) as f:
                        error_data = json.load(f)

                    await cl.Message(content=(
                        f"### ❌ Diagram Generation Failed\n\n"
                        f"**Error Type:** {error_data.get('error_type', 'Unknown').replace('_', ' ').title()}\n\n"
                        f"**Error:**\n```\n{error_data.get('error_message', 'Unknown error')}\n```"
                    )).send()
                    os.remove(latest_error)
                    return
    except Exception as e:
        print(f"Error checking error files: {e}")

    # Find the PNG
    try:
        stored_path = cl.user_session.get("diagram_path")
        if stored_path and os.path.exists(stored_path):
            latest_file = stored_path
            cl.user_session.set("diagram_path", None)
        else:
            if not os.path.exists(outputs_directory):
                await cl.Message(content="⚠️ No outputs directory found.").send()
                return

            date_folders = [
                d for d in os.listdir(outputs_directory)
                if os.path.isdir(os.path.join(outputs_directory, d))
            ]
            if not date_folders:
                await cl.Message(content="⚠️ No output folders found.").send()
                return

            latest_date_folder = max(
                (os.path.join(outputs_directory, d) for d in date_folders),
                key=os.path.getmtime,
            )
            latest_folder = _find_deepest_folder(latest_date_folder)

            png_files = [f for f in os.listdir(latest_folder) if f.endswith(".png")]
            if not png_files:
                await cl.Message(content="⚠️ No PNG found in latest output folder.").send()
                return

            latest_file = max(
                (os.path.join(latest_folder, f) for f in png_files),
                key=os.path.getmtime,
            )

    except ValueError:
        await cl.Message(content="⚠️ No images found.").send()
        return

    relative_path = os.path.relpath(latest_file, os.path.dirname(__file__))
    image = cl.Image(path=latest_file, name=os.path.basename(latest_file), display="inline", size="large")
    await cl.Message(
        content=f"### ✅ State Machine Diagram\n\n📁 `{relative_path}`",
        elements=[image],
    ).send()
