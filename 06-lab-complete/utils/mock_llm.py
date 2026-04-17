"""
Mock LLM — dùng chung cho tất cả ví dụ.
Không cần API key thật. Trả lời giả lập để focus vào deployment concept.
"""
import time
import random


MOCK_RESPONSES = {
    "default": [
        "Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.",
        "Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.",
        "Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.",
    ],
    "docker": ["Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!"],
    "deploy": ["Deployment là quá trình đưa code từ máy bạn lên server để người khác dùng được."],
    "health": ["Agent đang hoạt động bình thường. All systems operational."],
}


def ask(question: str, delay: float = 0.1) -> str:
    """Gọi LLM THẬT nếu có API Key, nếu không sẽ dùng Mock LLM chống cháy."""
    from app.config import settings

    if settings.openai_api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI Agent running in production."},
                    {"role": "user", "content": question}
                ],
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Lỗi gọi LLM thật: {str(e)}"

    # ────────────────────────────────────
    # Fallback to Mock LLM
    # ────────────────────────────────────
    time.sleep(delay + random.uniform(0, 0.05))  # simulate API latency

    question_lower = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in question_lower:
            return random.choice(responses)

    return random.choice(MOCK_RESPONSES["default"])


def ask_stream(question: str):
    """
    Mock streaming response — yield từng token.
    """
    response = ask(question)
    words = response.split()
    for word in words:
        time.sleep(0.05)
        yield word + " "
