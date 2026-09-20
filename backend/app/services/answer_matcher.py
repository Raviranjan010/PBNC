import re
from typing import Dict, List, Tuple, Optional, Any

ANSWER_KEY_BOUNDARY_REGEX = re.compile(
    r'(?:\n|\A)\s*(?:[-=_]{3,}\s*\n\s*)?(?:(?:Answer(?:\(s\)|s)?\s*Key|Answer(?:\(s\)|s)?|Solutions?|Key\s*(?:Sheet)?)\s*(?:[:\-]|\n|\Z)|(?:Q(?:uestion)?\.?\s*|\(?)\s*\d+\)?[\s:\.\-]+(?:\(?[A-Da-d1-4]\)?))',
    re.IGNORECASE
)

class DetectedAnswerKey:
    def __init__(self, mappings: Dict[str, str], raw_text: str, detected_format: str, source_page: Optional[int] = None):
        self.mappings = mappings  # {"1": "A", "2": "B"}
        self.raw_text = raw_text
        self.detected_format = detected_format
        self.source_page = source_page

class AnswerMatcher:
    # Patterns for answer keys
    # 1. Block header: e.g. "Answer Key", "Answers:", "Key:"
    KEY_HEADER_REGEX = re.compile(r'(?:Answer(?:\(s\)|s)?\s*Key|Answer(?:\(s\)|s)?|Solutions?|Key\s*(?:Sheet)?)[\s:\-]+(.*?)(?=\n\s*\n|\Z)', re.IGNORECASE | re.DOTALL)

    # 2. Pair patterns: "1. A", "1-A", "1: A", "Q1 A", "Q1: (A)", "(1) A"
    PAIR_REGEX = re.compile(r'(?:Q(?:uestion)?\.?\s*|\(?)\s*(\d+)\)?[\s:\.\-]+(?:\(?([A-Da-d1-4]|True|False)\)?)', re.IGNORECASE)

    @classmethod
    def find_answer_key_in_pages(cls, pages: List[Dict[str, Any]]) -> Optional[DetectedAnswerKey]:
        """
        Scans document pages (especially the last pages or dedicated answer sections) for an answer key.
        """
        all_mappings: Dict[str, str] = {}
        matched_format = "INLINE"
        matched_page = None
        matched_text = ""

        # Scan backwards from the last page
        for page in reversed(pages):
            page_num = page.get("page_number", 1)
            text = page.get("text", "")
            
            # Check for header
            header_match = cls.KEY_HEADER_REGEX.search(text)
            target_text = header_match.group(1) if header_match else text

            pairs = cls.PAIR_REGEX.findall(target_text)
            if len(pairs) >= 2:  # At least 2 pairs to be confident it's an answer key
                for q_num, ans_val in pairs:
                    val = ans_val.upper()
                    # Map numbers 1-4 to A-D if MCQ
                    key_map = {"1": "A", "2": "B", "3": "C", "4": "D"}
                    val = key_map.get(val, val)
                    all_mappings[str(q_num)] = val

                matched_page = page_num
                matched_format = "SECTION" if header_match else "LIST"
                matched_text = header_match.group(0) if header_match else target_text[:500]
                break

        if all_mappings:
            return DetectedAnswerKey(
                mappings=all_mappings,
                raw_text=matched_text,
                detected_format=matched_format,
                source_page=matched_page,
            )
        return None

    @classmethod
    def associate_answers(
        cls, questions: List[Any], answer_key: Optional[DetectedAnswerKey], doc_id: str
    ) -> None:
        """
        Associates detected answer key mappings to questions.
        - Matches confirmed answers to question options.
        - Flags mismatched keys (e.g. key E for options A-D) as INVALID.
        - Leaves unmapped questions as NOT_FOUND unless already UNCERTAIN/flagged.
        """
        if not answer_key:
            for q in questions:
                if not getattr(q, 'answer', None):
                    setattr(q, 'answer', None)
                    setattr(q, 'answer_status', "NOT_FOUND")
            return

        for q in questions:
            q_num = str(getattr(q, 'question_number', '')).strip()
            
            # If already has inline confirmed answer, preserve it
            if getattr(q, 'answer', None) and getattr(q, 'answer_status', '') == "CONFIRMED":
                continue

            if q_num in answer_key.mappings:
                matched_ans = answer_key.mappings[q_num]
                # Validate that the option actually exists if options are present
                options = getattr(q, 'options', [])
                has_option = any(
                    (opt.option_key if hasattr(opt, 'option_key') else (opt.key if hasattr(opt, 'key') else opt.get('option_key', opt.get('key', '')))) == matched_ans
                    for opt in options
                ) if options else True

                if options and not has_option:
                    # Mismatch: Answer key says 'E' but question only has options A-D!
                    setattr(q, 'answer', None)
                    setattr(q, 'answer_status', "INVALID")
                    setattr(q, 'review_required', True)
                    warn_msg = f"Answer key indicates '{matched_ans}', but options do not contain this key."
                    if hasattr(q, 'warnings') and isinstance(q.warnings, list):
                        q.warnings.append(warn_msg)
                else:
                    setattr(q, 'answer', matched_ans)
                    setattr(q, 'answer_status', "CONFIRMED")
                    setattr(q, 'answer_source_page', answer_key.source_page)
                    setattr(q, 'answer_source_document_id', doc_id)
            else:
                # No mapping found for this question
                current_status = getattr(q, 'answer_status', 'NOT_FOUND')
                if current_status not in ["UNCERTAIN", "INVALID"]:
                    setattr(q, 'answer_status', "NOT_FOUND")
                setattr(q, 'answer', None)
