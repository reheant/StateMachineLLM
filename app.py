import os
import chainlit as cl
import io
import contextlib
import asyncio

import backend.resources.state_machine_descriptions
from backend.resources.llm_tracker import llm
from backend.event_driven_smf.event_driven_smf import run_event_driven_smf
from backend.simple_linear_smf.simple_linear_smf import run_simple_linear_smf

@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="openai:gpt-4o",
            markdown_description="The underlying LLM model is OpenAI's **gpt-4o**.",
            icon="https://picsum.photos/200"
        ),
        cl.ChatProfile(
            name="anthropic:claude-3-5-sonnet-20241022",
            markdown_description="The underlying LLM model is Anthropic's **claude-3-5-sonnet**.",
            icon="https://picsum.photos/201"
        ),
        cl.ChatProfile(
            name="groq:llama-3.2-3b-preview",
            markdown_description="The underlying LLM model is Meta's **llama-3.2-3b-preview**.",
            icon="https://picsum.photos/202"
        ),        cl.ChatProfile(
            name="google:gemini-1.5-pro-001",
            markdown_description="The underlying LLM model is Google's **gemini-1.5-pro**.",
            icon="https://picsum.photos/203"
        )
    ]

@cl.on_message
async def run_conversation(message: cl.Message):
    final_answer = cl.Message(content="", author="Sherpa Output")
    await final_answer.send()

    stdout_capture = io.StringIO()
    current_step = None
    current_step_content = []

    async def run_and_capture():
        with contextlib.redirect_stdout(stdout_capture):
            await asyncio.to_thread(run_simple_linear_smf, message.content)

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
    image_directory = os.path.join(os.path.dirname(__file__), "backend", "resources", "simple_linear_diagrams")

    # Get the path of the most recently created diagram
    try:
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

    step1 = await cl.AskActionMessage(
        content="""
        <b>Hi there!</b> 
        \nLet's create a state machine diagram!
        \nYou can either: 
        \n ✍️ 1. Describe your own system
        \n 🤖 2. Try one of our examples
        \nWhat would you like to explore?""",
        actions=[
            cl.Action(name="custom", value="custom", label="✍️ Describe Your Own System"),
            cl.Action(name="example", value="example", label="🤖 Use One Of Our Examples"),
        ],
    ).send()

    if step1 and step1.get("value") == "example":
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
                cl.Action(name="printer", value="printer_winter_2017", label="🖨️ Printer System"),
                cl.Action(name="spa", value="spa_manager_winter_2018", label="🧖‍♂️ Spa Manager"),
                cl.Action(name="dishwasher", value="dishwasher_winter_2019", label="✨ Smart Dishwasher"),
                cl.Action(name="chess", value="chess_clock_fall_2019", label="🕰️ Digital Chess Clock"),
                cl.Action(name="bread", value="automatic_bread_maker_fall_2020", label="🥖 Automatic Bread Maker"),
                cl.Action(name="thermomix", value="thermomix_fall_2021", label="🔪 Thermomix TM6"),
                cl.Action(name="train", value="ATAS_fall_2022", label="🚆 Train Automation System"),
            ],
        ).send()

        if step2:
            system_preset = step2.get("value")
            system_description = getattr(backend.resources.state_machine_descriptions, system_preset)

            await run_conversation(cl.Message(content=system_description))
    else:
        await cl.Message(content="""Tell me about any process, workflow, or behavior you'd like to model. It could be anything from a coffee maker's operations to a complex authentication flow!""").send()
