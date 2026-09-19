from typing import List, Any
from backend.app.core.config import settings

class ConfidenceCalculator:
    @classmethod
    def calculate_question_confidence(
        cls,
        question: Any,
        page_ocr_conf: float = 1.0,
        is_digital: bool = True
    ) -> float:
        """
        Calculates a real multi-signal confidence score (0.0 to 1.0)
        based on OCR quality, prompt clarity, options structure, and answer association.
        """
        # 1. Base OCR / extraction quality signal (weight: 0.25)
        ocr_signal = 1.0 if is_digital else max(0.2, min(1.0, page_ocr_conf))
        
        # 2. Question Prompt Quality Signal (weight: 0.25)
        prompt = getattr(question, 'question_text', '').strip()
        if len(prompt) >= 30 and (prompt.endswith('?') or ':' in prompt or '___' in prompt):
            prompt_signal = 1.0
        elif len(prompt) >= 15:
            prompt_signal = 0.85
        elif len(prompt) >= 8:
            prompt_signal = 0.65
        else:
            prompt_signal = 0.35

        # 3. Option Completeness Signal (weight: 0.25)
        q_type = getattr(question, 'question_type', 'MCQ')
        options = getattr(question, 'options', [])
        opt_count = len(options)

        if q_type == "MCQ":
            if opt_count >= 4:
                option_signal = 1.0
            elif opt_count == 3:
                option_signal = 0.80
            elif opt_count == 2:
                option_signal = 0.65
            elif opt_count == 1:
                option_signal = 0.30
            else:
                option_signal = 0.40
        else:
            option_signal = 0.90  # Short answer / subjective

        # 4. Answer Association Signal (weight: 0.25)
        ans_status = getattr(question, 'answer_status', 'NOT_FOUND')
        if ans_status == "CONFIRMED":
            answer_signal = 1.0
        elif ans_status == "NOT_FOUND":
            answer_signal = 0.80  # Questions often don't have answer keys attached
        else:  # UNCERTAIN
            answer_signal = 0.40

        # Weighted combination
        raw_score = (
            (ocr_signal * 0.25) +
            (prompt_signal * 0.25) +
            (option_signal * 0.25) +
            (answer_signal * 0.25)
        )

        # Multi-page slight penalty for boundary risk
        source_pages = getattr(question, 'source_pages', [])
        if len(source_pages) > 1:
            raw_score = raw_score * 0.95

        # Apply penalty if warnings exist
        warnings = getattr(question, 'warnings', [])
        if warnings:
            raw_score = raw_score * (0.90 ** len(warnings))

        score = round(max(0.1, min(0.99, raw_score)), 2)
        return score

    @classmethod
    def determine_status_and_review(cls, confidence: float, has_warnings: bool, is_uncertain: bool) -> tuple[str, bool]:
        """
        Maps confidence score to (status, review_required).
        Thresholds are configurable via environment variables:
        >= CONFIDENCE_VERIFIED_MIN (0.90) -> VERIFIED
        >= CONFIDENCE_PARTIAL_MIN (0.70)  -> PARTIAL
        < CONFIDENCE_PARTIAL_MIN          -> REVIEW_REQUIRED
        """
        if confidence >= settings.CONFIDENCE_VERIFIED_MIN and not has_warnings and not is_uncertain:
            return "VERIFIED", False
        elif confidence >= settings.CONFIDENCE_PARTIAL_MIN and not is_uncertain:
            return "PARTIAL", False
        else:
            return "REVIEW_REQUIRED", True
