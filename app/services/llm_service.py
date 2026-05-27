from openai import OpenAI

from app.core.config import settings


def get_language_instruction(answer_language: str) -> str:
    language = answer_language.lower().strip()

    if language == "zh":
        return "Answer in Chinese."

    if language == "en":
        return "Answer in English."

    if language == "auto":
        return "Answer in the same language as the user's question."

    return "Answer in the same language as the user's question."


def generate_answer_with_context(
    question: str,
    context: str,
    answer_language: str = "auto",
) -> str:
    if settings.LLM_PROVIDER.lower().strip() != "aliyun":
        raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")

    if not settings.ALIYUN_API_KEY:
        raise ValueError("ALIYUN_API_KEY is not configured")

    client = OpenAI(
        api_key=settings.ALIYUN_API_KEY,
        base_url=settings.ALIYUN_BASE_URL,
    )

    language_instruction = get_language_instruction(answer_language)

    system_prompt = f"""
You are a helpful knowledge base assistant.

Answer the user's question using only the provided context.
If the answer cannot be found in the context, say you don't know based on the provided documents.
Do not invent facts.

Use citation markers like [1], [2], [3] to show which source chunks support your answer.
Only cite source numbers that appear in the provided context.

{language_instruction}
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