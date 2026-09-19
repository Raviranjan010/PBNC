import json
import httpx
from typing import List, Dict, Any
from backend.app.core.config import settings
from backend.app.services.ai.base import AIProvider, ParsedQuestion, ParsedOption
from backend.app.services.ai.heuristic import HeuristicProvider

class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str = settings.OPENAI_API_KEY):
        self.api_key = api_key
        self.heuristic_fallback = HeuristicProvider()

    async def extract_structured_questions(
        self, pages_text: List[Dict[str, Any]]
    ) -> List[ParsedQuestion]:
        if not self.api_key:
            return await self.heuristic_fallback.extract_structured_questions(pages_text)

        prompt = (
            "Extract all questions from the following exam text. Preserve source page numbers.\n"
            "Return a JSON array of objects with keys: "
            "question_number, question_text, question_type ('MCQ' or 'SHORT'), "
            "options (array of {key, text}), answer (string or null), source_pages (array of ints), confidence (float between 0 and 1).\n\n"
        )
        for p in pages_text:
            prompt += f"\n--- Page {p.get('page_number')} ---\n{p.get('text', '')}\n"

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You extract structured exam questions strictly adhering to valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    items = parsed.get("questions", parsed if isinstance(parsed, list) else [])
                    questions = []
                    for item in items:
                        opts = [ParsedOption(key=o["key"], text=o["text"]) for o in item.get("options", [])]
                        questions.append(ParsedQuestion(
                            question_number=str(item.get("question_number", "")),
                            question_text=item.get("question_text", ""),
                            question_type=item.get("question_type", "MCQ"),
                            options=opts,
                            answer=item.get("answer"),
                            answer_status="CONFIRMED" if item.get("answer") else "NOT_FOUND",
                            source_pages=item.get("source_pages", [1]),
                            confidence=float(item.get("confidence", 0.9)),
                        ))
                    return questions
        except Exception:
            pass

        return await self.heuristic_fallback.extract_structured_questions(pages_text)
