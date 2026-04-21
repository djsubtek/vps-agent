import json
import os

from openai import OpenAI

CATEGORIES = {"restaurant", "idea", "document", "other"}


def classify_text(text):
    if not text:
        return None

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    client = OpenAI(api_key=api_key)
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the input into one category: restaurant, idea, document, or other. "
                    "Generate a one-sentence summary and 3-5 concise tags. "
                    "Return strict JSON with keys: category, tags, summary."
                ),
            },
            {"role": "user", "content": text[:8000]},
        ],
        temperature=0.1,
    )

    content = response.choices[0].message.content or "{}"
    data = json.loads(content)

    category = data.get("category") if data.get("category") in CATEGORIES else "other"
    tags = data.get("tags") if isinstance(data.get("tags"), list) else []
    summary = data.get("summary") if isinstance(data.get("summary"), str) else None

    return {
        "category": category,
        "tags": [str(tag).strip() for tag in tags if str(tag).strip()][:5],
        "summary": summary,
    }
