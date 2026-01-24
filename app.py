import os
import chainlit as cl
import io
import contextlib
import asyncio

import backend.resources.state_machine_descriptions
from backend.resources.llm_tracker import llm
from backend.event_driven_smf.event_driven_smf import run_event_driven_smf
from backend.simple_linear_smf.simple_linear_smf import run_simple_linear_smf
from backend.single_prompt import run_single_prompt

def convert_to_openrouter_model(chat_profile):
    """Convert Chainlit chat profile to OpenRouter model name"""
    if not chat_profile:
        return "anthropic/claude-3.5-sonnet"  # default
    
    profile_to_openrouter = {
        # Anthropic
        "anthropic:claude-3-5-sonnet-20241022": "anthropic/claude-3.5-sonnet", 
        "anthropic:claude-4-5-sonnet": "anthropic/claude-4.5-sonnet",
        "anthropic:claude-sonnet-4": "anthropic/claude-sonnet-4",
        # OpenAI
        "openai:gpt-4o": "openai/gpt-4o",
        "openai:gpt-4o-mini": "openai/gpt-4o-mini",
        "openai:gpt-4-turbo": "openai/gpt-4-turbo",
        "openai:o1": "openai/o1",
        "openai:o1-mini": "openai/o1-mini",
        # Google
        "google:gemini-2-0-flash-exp": "google/gemini-2.0-flash-exp",
        "google:gemini-1-5-pro-001": "google/gemini-pro-1.5",
        "google:gemini-1-5-flash": "google/gemini-flash-1.5",
        # Meta
        "meta:llama-3-3-70b-instruct": "meta-llama/llama-3.3-70b-instruct",
        "meta:llama-3-1-405b-instruct": "meta-llama/llama-3.1-405b-instruct",
        "meta:llama-3-1-70b-instruct": "meta-llama/llama-3.1-70b-instruct",
        "meta:llama-3-2-3b-instruct": "meta-llama/llama-3.2-3b-instruct",
        # Qwen
        "qwen:qwq-32b": "qwen/qwq-32b",
        "qwen:qwen-2-5-72b-instruct": "qwen/qwen-2.5-72b-instruct",
        # Legacy
        "groq:llama-3.2-3b-preview": "meta-llama/llama-3.2-3b-instruct",
    }
    
    return profile_to_openrouter.get(chat_profile, "anthropic/claude-3.5-sonnet")

@cl.set_chat_profiles
async def chat_profile():
    return [
        # Anthropic Models
        cl.ChatProfile(
            name="anthropic:claude-3-5-sonnet-20241022",
            markdown_description="The underlying LLM model is Anthropic's **Claude 3.5 Sonnet**.",
            icon="https://picsum.photos/203"
        ),
        cl.ChatProfile(
            name="anthropic:claude-4-5-sonnet",
            markdown_description="The underlying LLM model is Anthropic's **Claude 4.5 Sonnet**.",
            icon="https://picsum.photos/203"
        ),
        cl.ChatProfile(
            name="anthropic:claude-sonnet-4",
            markdown_description="The underlying LLM model is Anthropic's **Claude Sonnet 4**.",
            icon="https://picsum.photos/203"
        ),
        # OpenAI Models
        cl.ChatProfile(
            name="openai:gpt-4o",
            markdown_description="The underlying LLM model is OpenAI's **GPT-4o**.",
            icon="https://picsum.photos/202"
        ),
        cl.ChatProfile(
            name="openai:gpt-4o-mini",
            markdown_description="The underlying LLM model is OpenAI's **GPT-4o Mini**.",
            icon="https://picsum.photos/202"
        ),
        cl.ChatProfile(
            name="openai:gpt-4-turbo",
            markdown_description="The underlying LLM model is OpenAI's **GPT-4 Turbo**.",
            icon="https://picsum.photos/202"
        ),
        cl.ChatProfile(
            name="openai:o1",
            markdown_description="The underlying LLM model is OpenAI's **o1** (reasoning model).",
            icon="https://picsum.photos/202"
        ),
        cl.ChatProfile(
            name="openai:o1-mini",
            markdown_description="The underlying LLM model is OpenAI's **o1-mini** (reasoning model).",
            icon="https://picsum.photos/202"
        ),
        # Google Models
        cl.ChatProfile(
            name="google:gemini-2-0-flash-exp",
            markdown_description="The underlying LLM model is Google's **Gemini 2.0 Flash** (experimental).",
            icon="https://picsum.photos/205"
        ),
        cl.ChatProfile(
            name="google:gemini-1-5-pro-001",
            markdown_description="The underlying LLM model is Google's **Gemini 1.5 Pro**.",
            icon="https://picsum.photos/205"
        ),
        cl.ChatProfile(
            name="google:gemini-1-5-flash",
            markdown_description="The underlying LLM model is Google's **Gemini 1.5 Flash**.",
            icon="https://picsum.photos/205"
        ),
        # Meta Models
        cl.ChatProfile(
            name="meta:llama-3-3-70b-instruct",
            markdown_description="The underlying LLM model is Meta's **Llama 3.3 70B Instruct**.",
            icon="https://picsum.photos/204"
        ),
        cl.ChatProfile(
            name="meta:llama-3-1-405b-instruct",
            markdown_description="The underlying LLM model is Meta's **Llama 3.1 405B Instruct**.",
            icon="https://picsum.photos/204"
        ),
        cl.ChatProfile(
            name="meta:llama-3-1-70b-instruct",
            markdown_description="The underlying LLM model is Meta's **Llama 3.1 70B Instruct**.",
            icon="https://picsum.photos/204"
        ),
        cl.ChatProfile(
            name="meta:llama-3-2-3b-instruct",
            markdown_description="The underlying LLM model is Meta's **Llama 3.2 3B Instruct**.",
            icon="https://picsum.photos/204"
        ),
        # Qwen Models
        cl.ChatProfile(
            name="qwen:qwq-32b",
            markdown_description="The underlying LLM model is Qwen's **QwQ 32B**.",
            icon="https://picsum.photos/200"
        ),
        cl.ChatProfile(
            name="qwen:qwen-2-5-72b-instruct",
            markdown_description="The underlying LLM model is Qwen's **Qwen 2.5 72B Instruct**.",
            icon="https://picsum.photos/201"
        )
    ]


@cl.on_message
async def run_conversation(message: cl.Message):
    await message.send() # Print the problem description as is
    final_answer = cl.Message(content="", author="Sherpa Output")
    await final_answer.send()

    # Get the chosen generation strategy
    strategy = cl.user_session.get("generation_strategy", "event_driven")

    stdout_capture = io.StringIO()
    current_step = None
    current_step_content = []

    async def run_and_capture():
        with contextlib.redirect_stdout(stdout_capture):
            if strategy == "single_prompt":
                # Convert chat profile to OpenRouter model
                chat_profile = cl.user_session.get("chat_profile")
                openrouter_model = convert_to_openrouter_model(chat_profile)
                await asyncio.to_thread(run_single_prompt, message.content, openrouter_model)
            elif strategy == "structure_driven":
                await asyncio.to_thread(run_simple_linear_smf, message.content)
            else:  # default to event_driven
                await asyncio.to_thread(run_event_driven_smf, message.content)

    task = asyncio.create_task(run_and_capture())

    while not task.done():
        await asyncio.sleep(0.1)

        stdout_capture.seek(0)
        current_output = stdout_capture.read()
        
        if current_output:
            lines = current_output.splitlines()
            for line in lines:
                if line.startswith("Running"):
                    if current_step is not None:
                        step_content = "\n".join(current_step_content)
                        current_step.output = step_content
                        await current_step.update()
                        await current_step.__aexit__(None, None, None)
                    
                    step_name = line[8:].replace("...", "").replace("start_", "") + " action" if line.startswith("Running ") else line
                    current_step = cl.Step(name=step_name)
                    await current_step.__aenter__()
                    current_step_content = [line]
                elif current_step is not None:
                    current_step_content.append(line)

            stdout_capture.truncate(0)
            stdout_capture.seek(0)

    if current_step is not None:
        step_content = "\n".join(current_step_content)
        current_step.output = step_content
        await current_step.update()
        await current_step.__aexit__(None, None, None)

    await task 
    
    step_outputs = []
    for line in final_answer.content.splitlines():
        if line.strip():
            step_outputs.append(line)
    final_answer.content = "\n".join(step_outputs)
    await final_answer.update()

    async with cl.Step(name="Rendering Diagram") as diagram_step:
        await display_image()


async def display_image():
    """
    The display_image() function displays the state machine diagram after it has been translated into
    mermaid syntax and converted into an image
    """
    # Choose the appropriate directory based on strategy
    strategy = cl.user_session.get("generation_strategy", "event_driven")
    
    if strategy == "single_prompt":
        image_directory = os.path.join(os.path.dirname(__file__), "backend", "resources", "single_prompt_diagrams")
    elif strategy == "structure_driven":
        image_directory = os.path.join(os.path.dirname(__file__), "backend", "resources", "simple_linear_diagrams")
    else:  # event_driven
        image_directory = os.path.join(os.path.dirname(__file__), "backend", "resources", "event_driven_diagrams")

    # Get the path of the most recently created diagram
    try:
        # For single prompt, look specifically for .png files
        if strategy == "single_prompt":
            png_files = [f for f in os.listdir(image_directory) if f.endswith('.png')]
            if not png_files:
                await cl.Message(content="No PNG images found in the directory.").send()
                return
            latest_file = max(
                (os.path.join(image_directory, f) for f in png_files),
                key=os.path.getmtime,
            )
        else:
            # For other strategies, use all files
            latest_file = max(
                (os.path.join(image_directory, f) for f in os.listdir(image_directory)),
                key=os.path.getmtime,
            )
    except ValueError:
        # Handle the case where the directory is empty
        await cl.Message(content="No images found in the directory.").send()
        return

    # Attach the most recent file to the message
    image = cl.Image(path=latest_file, name="State Machine Image", display="inline", size='large')
    
    await cl.Message(
        content="State Machine Image Rendered",
        elements=[image],
    ).send()


@cl.on_chat_start
async def start():
    llm.update_llm(cl.user_session.get("chat_profile"))

    # First, choose generation strategy
    strategy_step = await cl.AskActionMessage(
        content="""
        <b>Hi there!</b> 
        \nLet's create a state machine diagram!
        \nFirst, choose your generation strategy:
        \n 🚀 <b>Single Prompt (OpenRouter)</b>: Fast, direct generation using OpenRouter API
        \n 🔄 <b>Event-Driven SMF</b>: Multi-step process focusing on events
        \n 📊 <b>Structure-Driven SMF</b>: Multi-step process focusing on structure
        """,
        actions=[
            cl.Action(name="single_prompt", value="single_prompt", payload={}, label="🚀 Single Prompt (OpenRouter)"),
            cl.Action(name="event_driven", value="event_driven", payload={}, label="🔄 Event-Driven SMF"),
            cl.Action(name="structure_driven", value="structure_driven", payload={}, label="📊 Structure-Driven SMF"),
        ],
    ).send()
    
    # Store the chosen strategy in user session
    if strategy_step:
        strategy_value = strategy_step.get("name")
        cl.user_session.set("generation_strategy", strategy_value)

    step1 = await cl.AskActionMessage(
        content="""
        Now choose your input:
        \n ✍️ 1. Describe your own system
        \n 🤖 2. Try one of our examples
        \nWhat would you like to explore?""",
        actions=[
            cl.Action(name="custom", value="custom", payload={}, label="✍️ Describe Your Own System"),
            cl.Action(name="example", value="example", payload={}, label="🤖 Use One Of Our Examples"),
        ],
    ).send()

    # Extract action name from result
    step1_value = step1.get("name") if step1 else None

    if step1_value == "example":
        step2 = await cl.AskActionMessage(
            content="""
            Choose one of these interesting examples:
            \n 1. 🖨️ <b>Printer System</b>: A modern office printer with card authentication, print/scan capabilities, and error handling for paper jams
            \n 2. 🧖‍♂️ <b>Spa Manager</b>: A control system for saunas and Jacuzzis with temperature regulation and water jet controls
            \n 3. ✨ <b>Smart Dishwasher</b>: An automated dishwasher with multiple programs, adjustable drying times, and door safety features
            \n 4. 🕰️ <b>Digital Chess Clock</b>: A tournament chess clock with multiple timing modes and player controls
            \n 5. 🥖 <b>Automatic Bread Maker</b>: A programmable bread maker with different courses, crust options, and delayed start features
            \n 6. 🔪 <b>Thermomix TM6</b>: An all-in-one kitchen appliance with guided recipe steps and ingredient processing
            \n 7. 🚆 <b>Train Automation System</b>: An advanced system managing driverless trains across a rail network with traffic signals and stations
            """,
            actions=[
                cl.Action(name="printer_winter_2017", value="printer_winter_2017", payload={}, label="🖨️ Printer System"),
                cl.Action(name="spa_manager_winter_2018", value="spa_manager_winter_2018", payload={}, label="🧖‍♂️ Spa Manager"),
                cl.Action(name="dishwasher_winter_2019", value="dishwasher_winter_2019", payload={}, label="✨ Smart Dishwasher"),
                cl.Action(name="chess_clock_fall_2019", value="chess_clock_fall_2019", payload={}, label="🕰️ Digital Chess Clock"),
                cl.Action(name="automatic_bread_maker_fall_2020", value="automatic_bread_maker_fall_2020", payload={}, label="🥖 Automatic Bread Maker"),
                cl.Action(name="thermomix_fall_2021", value="thermomix_fall_2021", payload={}, label="🔪 Thermomix TM6"),
                cl.Action(name="ATAS_fall_2022", value="ATAS_fall_2022", payload={}, label="🚆 Train Automation System"),
            ],
        ).send()

        if step2:
            # Extract action name from result
            system_preset = step2.get("name")
            system_description = getattr(backend.resources.state_machine_descriptions, system_preset)

            await run_conversation(cl.Message(content=system_description))
    else:
        await cl.Message(content="""Tell me about any process, workflow, or behavior you'd like to model. It could be anything from a coffee maker's operations to a complex authentication flow!""").send()
