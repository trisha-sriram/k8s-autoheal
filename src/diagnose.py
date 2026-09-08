import os
from openai import OpenAI

llm_client = OpenAI()


def diagnose(prompt):
    print("Calling diagnose function, passing the prompt to llm")
    response = llm_client.chat.completions.create(
        model="gpt-6-astra",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
