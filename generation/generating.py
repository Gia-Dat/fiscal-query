from typing import List, Dict, Any
from openai import OpenAI
from config import Config


def generating(query: str, context_chunks: List[Dict[str, Any]], stream: bool = True) -> str:
    client = OpenAI(api_key=Config.OPENAI_API_KEY)

    system_prompt = (
        "You are an expert SEC Form 10-K analyst.\n"
        "Guidelines:\n"
        "1. ONLY use facts, figures, and tables provided in the CONTEXT to answer.\n"
        "2. Accurately interpret fiscal year columns, reporting periods, and units of measurement (e.g., in millions, thousands).\n"
        "3. Explicitly cite sources for every point using the format: [Company Name, Item X].\n"
        "4. If the context does not contain the required information, state honestly that the data is not available."
    )

    context_str = "\n\n".join(
        [f"--- CHUNK {i+1} ---\n{c['content']}" for i, c in enumerate(context_chunks)])
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",
            "content": f"[CONTEXT]:\n{context_str}\n\n[QUESTION]: {query}"}
    ]

    response = client.chat.completions.create(
        model=Config.LLM_MODEL,
        messages=messages,
        temperature=0.0,
        stream=stream
    )

    if stream:
        collected = []
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            print(content, end="", flush=True)
            collected.append(content)
        print()
        return "".join(collected)
    else:
        return response.choices[0].message.content
