import re
from typing import List, Dict, Any, Optional
from backend.app.services.ai.base import AIProvider, ParsedQuestion, ParsedOption
from backend.app.services.answer_matcher import ANSWER_KEY_BOUNDARY_REGEX

class HeuristicProvider(AIProvider):
    """
    Deterministic structural parser that accurately parses exam documents,
    tracks multi-page boundaries, extracts options, and provides reliable confidence signals.
    """
    ANSWER_KEY_BOUNDARY_REGEX = ANSWER_KEY_BOUNDARY_REGEX

    QUESTION_REGEX = re.compile(
        r'(?:^|\n)\s*(?:(?:Q(?:uestion)?\.?\s*(\d+)[\.\:]?)|(?:\((\d+)\))|(?:(\d+)\s*[\.\)]))\s+(.+?)(?=(?:\n\s*(?:Q(?:uestion)?\.?\s*\d+[\.\:]?|\(\d+\)|\d+\s*[\.\)])\s+)|\Z)',
        re.DOTALL | re.IGNORECASE
    )

    OPTION_REGEX = re.compile(
        r'(?:^|\n|\s{2,})(?:\(([a-dA-D1-4])\)|([a-dA-D1-4])[\.\)])\s+(.*?)(?=(?:(?:\s{2,}|\n)(?:\([a-dA-D1-4]\)|[a-dA-D1-4][\.\)])\s+)|\Z)',
        re.DOTALL
    )

    ANSWER_REGEX = re.compile(
        r'(?:(?:Ans(?:wer)?|Key)[\s:\.\-]+(?:\(?([A-Da-d1-4])\)?))',
        re.IGNORECASE
    )

    async def extract_structured_questions(
        self, pages_text: List[Dict[str, Any]]
    ) -> List[ParsedQuestion]:
        """
        Parses questions across pages, preserving page provenance and handling cross-page questions.
        """
        questions: List[ParsedQuestion] = []
        
        # Build page-mapped tokenized stream to track exact source pages
        page_chunks = []
        for p in pages_text:
            text = p.get("text", "").strip()
            if text:
                page_chunks.append((p.get("page_number", 1), text))

        if not page_chunks:
            return []

        # Find questions in each page or spanning adjacent pages
        for idx, (page_num, text) in enumerate(page_chunks):
            # Also check if next page continues this page's last question
            combined_text = text
            next_page_num = None
            if idx + 1 < len(page_chunks):
                combined_text += "\n" + page_chunks[idx + 1][1]
                next_page_num = page_chunks[idx + 1][0]

            matches = list(self.QUESTION_REGEX.finditer(text))
            
            for m in matches:
                q_num = m.group(1) or m.group(2) or m.group(3)
                raw_body = m.group(4).strip()
                
                # Check if this question seems truncated and continues on next page
                source_pages = [page_num]
                
                # Extract inline answer if present
                ans_match = self.ANSWER_REGEX.search(raw_body)
                inline_answer = ans_match.group(1).upper() if ans_match else None
                if ans_match:
                    raw_body = self.ANSWER_REGEX.sub('', raw_body).strip()

                # Extract options
                options: List[ParsedOption] = []
                opt_matches = list(self.OPTION_REGEX.finditer(raw_body))
                
                # Check if options are missing or cut off, and if next page contains the options
                if len(opt_matches) < 2 and next_page_num:
                    next_text = page_chunks[idx + 1][1]
                    # Check if next page starts with options (e.g. (c) ... (d) ...)
                    next_opt_matches = list(self.OPTION_REGEX.finditer(next_text[:300]))
                    if next_opt_matches:
                        # Multi-page question detected!
                        source_pages.append(next_page_num)
                        raw_body += "\n" + next_text[:300]
                        opt_matches = list(self.OPTION_REGEX.finditer(raw_body))

                warnings = []
                # Clean question prompt text by removing options block
                q_prompt = raw_body
                if opt_matches:
                    first_opt_start = opt_matches[0].start()
                    q_prompt = raw_body[:first_opt_start].strip()
                    
                    for om in opt_matches:
                        k = (om.group(1) or om.group(2)).upper()
                        # Map 1,2,3,4 to A,B,C,D if needed
                        key_map = {"1": "A", "2": "B", "3": "C", "4": "D"}
                        k = key_map.get(k, k)
                        v = om.group(3).strip()
                        # Truncate at answer key boundary if present
                        b_match = self.ANSWER_KEY_BOUNDARY_REGEX.search(v)
                        if b_match:
                            v = v[:b_match.start()].strip()
                        v = re.sub(r'\n\s*[-=_]{3,}\s*$', '', v).strip()
                        options.append(ParsedOption(key=k, text=v))
                else:
                    # Truncate question prompt at answer key boundary if no options
                    b_match = self.ANSWER_KEY_BOUNDARY_REGEX.search(q_prompt)
                    if b_match:
                        q_prompt = q_prompt[:b_match.start()].strip()

                q_prompt = re.sub(r'\n\s*[-=_]{3,}\s*$', '', q_prompt).strip()

                # Question type determination
                q_type = "MCQ" if len(options) >= 2 else "SHORT"
                if len(options) == 1:
                    warnings.append(f"Incomplete options: Question {q_num} has only 1 extracted option.")
                
                # Initial confidence score
                conf = 0.95
                if len(source_pages) > 1:
                    conf = 0.92
                if len(options) == 1:
                    conf = 0.65
                if len(q_prompt) < 10:
                    conf = min(conf, 0.60)
                    warnings.append(f"Question prompt is unusually short ({len(q_prompt)} chars).")

                # If inline answer found, map it
                ans_status = "CONFIRMED" if inline_answer else "NOT_FOUND"

                # Deduplicate by question_number
                if not any(q.question_number == q_num for q in questions):
                    questions.append(ParsedQuestion(
                        question_number=str(q_num),
                        question_text=q_prompt,
                        question_type=q_type,
                        options=options,
                        answer=inline_answer,
                        answer_status=ans_status,
                        source_pages=source_pages,
                        confidence=conf,
                        warnings=warnings,
                    ))

        return questions
