import sys
import os

script_dir = os.path.dirname(__file__)
resources_dir = os.path.join(script_dir, '..', 'backend', 'simple_linear_smf')
print(resources_dir)
sys.path.append(resources_dir)

import chainlit as cl
from simple_linear_smf import run_sherpa_task
import io
import contextlib
import asyncio

@cl.on_chat_start
def start_chat():
    """
    initiates a new Chainlit chat
    """
    cl.user_session.set("message_history", [{"role": "system", "content": "You are a helpful assistant."}])

async def stream_function_output():
    """
    The stream_function_output runs the SMF and streams the output to the
    Chainlit UI
    """

    final_answer = cl.Message(content="", author="Sherpa Output")
    await final_answer.send()

    stdout_capture = io.StringIO()
    
    with contextlib.redirect_stdout(stdout_capture):
        task = asyncio.create_task(asyncio.to_thread(run_sherpa_task))
        
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
    await stream_function_output()
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
