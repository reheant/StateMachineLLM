import chainlit as cl
import io
import contextlib
import asyncio

import backend.resources.state_machine_descriptions
from backend.resources.llm_tracker import llm
from backend.start_event_driven_smf import run_sherpa_task

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

async def stream_function_output(system_prompt):
    """
    The stream_function_output runs the SMF and streams the output to the
    Chainlit UI
    """

    final_answer = cl.Message(content="", author="Sherpa Output")
    await final_answer.send()

    stdout_capture = io.StringIO()
    
    with contextlib.redirect_stdout(stdout_capture):
        task = asyncio.create_task(asyncio.to_thread(run_sherpa_task(system_prompt)))
        
        while not task.done():
            await asyncio.sleep(0.1)

            stdout_capture.seek(0)
            current_output = stdout_capture.read()
            
            if current_output:
                await final_answer.stream_token(current_output)
                stdout_capture.truncate(0)
                stdout_capture.seek(0)

        stdout_capture.seek(0)
        final_output = stdout_capture.read()
        if final_output:
            await final_answer.stream_token(final_output)

    await final_answer.update()

@cl.on_message
async def run_conversation(message: cl.Message):
    await stream_function_output(message.content)
    await display_image()


async def display_image():
    """
    The display_image() function displays the state machine diagram after it has been translated into
    mermaid syntax and converted into an image
    """
    image = cl.Image(path="ExhibitA.png", name="State Machine Image", display="inline", size='large')
    
    # Attach the image to the message
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
