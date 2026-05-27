from openai import OpenAI

from app.core.config import settings


def generate_answer_with_context(
    question: str,
    context: str,
) -> str:
    if settings.LLM_PROVIDER.lower().strip() != "aliyun":
        raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")

    if not settings.ALIYUN_API_KEY:
        raise ValueError("ALIYUN_API_KEY is not configured")

    client = OpenAI(
        api_key=settings.ALIYUN_API_KEY,
        base_url=settings.ALIYUN_BASE_URL,
    )

    system_prompt = """
    You are a helpful knowledge base assistant.

    Answer the user's question using only the provided context.
    If the answer cannot be found in the context, say you don't know based on the provided documents.
    Do not invent facts.

    Use citation markers like [1], [2], [3] to show which source chunks support your answer.
    Only cite source numbers that appear in the provided context.
    """.strip()

    user_prompt = f"""
    Question:
    {question}

    Context:
    {context}
    """.strip()

    response = client.chat.completions.create(
        model=settings.ALIYUN_CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or ""
