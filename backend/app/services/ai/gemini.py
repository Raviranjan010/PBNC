import json
import httpx
from typing import List, Dict, Any
from backend.app.core.config import settings
from backend.app.services.ai.base import AIProvider, ParsedQuestion, ParsedOption
from backend.app.services.ai.heuristic import HeuristicProvider

class GeminiProvider(AIProvider):
    def __init__(self, api_key: str = settings.GEMINI_API_KEY):
        self.api_key = api_key
        self.heuristic_fallback = HeuristicProvider()

    async def extract_structured_questions(
        self, pages_text: List[Dict[str, Any]]
    ) -> List[ParsedQuestion]:
        if not self.api_key:
            # Fallback cleanly if no API key provided
            return await self.heuristic_fallback.extract_structured_questions(pages_text)

        prompt = (
            "You are an expert document intelligence engine. Extract all questions from the following "
            "document text. Preserve source page provenance. If a question spans across pages, record all page numbers in source_pages.\n"
            "Return valid JSON array of objects with keys: "
            "question_number (string), question_text (string), question_type ('MCQ' or 'SHORT'), "
            "options (array of {key, text}), answer (string or null), source_pages (array of ints), confidence (float between 0 and 1).\n\n"
            "Document Pages Content:\n"
        )
        for p in pages_text:
            prompt += f"\n--- Page {p.get('page_number')} ---\n{p.get('text', '')}\n"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.AI_MODEL_NAME}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed_json = json.loads(raw_text)
                    questions = []
                    for item in parsed_json:
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

        # If call failed, do not fabricate success; fallback to deterministic heuristic
        return await self.heuristic_fallback.extract_structured_questions(pages_text)
