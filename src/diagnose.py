import os
from openai import OpenAI

llm_client = OpenAI()


def diagnose(prompt):
    print("Calling diagnose function, passing the prompt to llm")
    response = llm_client.responses.create(
        model="gpt-6-astra",
        input=prompt,
    )
    return response.output_text
