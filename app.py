import os
from openai import AsyncOpenAI

import chainlit as cl

api_key = os.environ.get("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)

cl.instrument_openai()

@cl.on_chat_start
def start_chat():
    cl.user_session.set("message_history", [{"role": "system", "content": "You are a helpful assistant."}])

async def call_gpt4(message_history):
    settings = { "model": "gpt-4" }
    stream = await client.chat.completions.create(messages=message_history, stream=True, **settings)
    final_answer = cl.Message(content="", author="Answer")

    async for part in stream:
        new_delta = part.choices[0].delta
 
        if new_delta.content:
            if not final_answer.content:
                await final_answer.send()
            await final_answer.stream_token(new_delta.content)

    if final_answer.content:
        await final_answer.update()

@cl.on_message
async def run_conversation(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"name": "user", "role": "user", "content": message.content})

    message = await call_gpt4(message_history)
    await cl.Message(content=message.content, author="Answer").send()
