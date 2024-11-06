import chainlit as cl
from sherpa import run_sherpa_task
import io
import contextlib
import asyncio

@cl.on_chat_start
def start_chat():
    cl.user_session.set("message_history", [{"role": "system", "content": "You are a helpful assistant."}])

async def stream_function_output():
    final_answer = cl.Message(content="", author="Sherpa Output")
    await final_answer.send()

    stdout_capture = io.StringIO()
    
    with contextlib.redirect_stdout(stdout_capture):
        await asyncio.to_thread(run_sherpa_task)
        stdout_capture.seek(0)
        current_output = stdout_capture.read()
        
        if current_output:
            await final_answer.stream_token(current_output)
            stdout_capture.truncate(0)
            stdout_capture.seek(0)

    await final_answer.update()

@cl.on_message
async def run_conversation(message: cl.Message):
    await stream_function_output()
