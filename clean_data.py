import json
import os
import re
from typing import Any, Dict, List, Tuple


class SECReportExtractor:
    """Universal extractor for Form 10-K and Form 40-F financial filings."""

    TARGET_KEYS = ["item_1", "item_1a", "item_7", "item_7a", "item_8"]

    PATTERNS_10K: List[Tuple[str, str]] = [
        ("item_1", r"item\s+1\b[.:\-–—]?\s*(?:business)?"),
        ("item_1a", r"item\s+1a\b[.:\-–—]?\s*(?:risk\s+factors)?"),
        ("item_1b",
         r"item\s+1b\b[.:\-–—]?\s*(?:unresolved\s+staff\s+comments)?"),
        ("item_2", r"item\s+2\b[.:\-–—]?\s*(?:properties)?"),
        (
            "item_7",
            r"item\s+7\b[.:\-–—]?\s*(?:management['’]s\s+discussion\s+and\s+analysis)?",
        ),
        (
            "item_7a",
            r"item\s+7a\b[.:\-–—]?\s*(?:quantitative\s+and\s+qualitative\s+disclosures)?",
        ),
        (
            "item_8",
            r"item\s+8\b[.:\-–—]?\s*(?:financial\s+statements\s+and\s+supplementary\s+data)?",
        ),
        (
            "item_9",
            r"item\s+9\b[.:\-–—]?\s*(?:changes\s+in\s+and\s+disagreements\s+with\s+accountants)?",
        ),
        ("signatures", r"\bsignatures\b"),
    ]

    PATTERNS_40F: List[Tuple[str, str]] = [
        (
            "item_1",
            r"(?:corporate\s+structure|general\s+development\s+of\s+the\s+business|description\s+of\s+the\s+business|business\s+overview)\b",
        ),
        (
            "item_1a",
            r"(?:risk\s+factors|risks\s+and\s+uncertainties|principal\s+risks)\b",
        ),
        (
            "item_7",
            r"(?:management['’]s\s+discussion\s+and\s+analysis|m\s*d\s*&\s*a)\b",
        ),
        (
            "item_7a",
            r"(?:quantitative\s+and\s+qualitative\s+disclosures\s+about\s+market\s+risk|financial\s+instruments\s+and\s+risk\s+management|market\s+risk\s+disclosures)\b",
        ),
        (
            "item_8",
            r"(?:audited\s+consolidated\s+financial\s+statements|consolidated\s+financial\s+statements|report\s+of\s+independent\s+registered\s+public\s+accounting\s+firm)\b",
        ),
        ("exhibits", r"(?:index\s+to\s+exhibits|exhibit\s+index|signatures)\b"),
    ]

    @staticmethod
    def clean_boilerplate(text: str) -> str:
        text = re.sub(r"[\xa0\u200b\t]+", " ", text)
        text = re.sub(r"[—–―_]{3,}", "\n", text)
        text = re.sub(r"(?im)^\s*table\s+of\s+contents\s*$", "", text)
        text = re.sub(r"(?im)^\s*\d+\s*$", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @classmethod
    def _locate_toc_offset(cls, text: str, patterns: List[Tuple[str, str]]) -> int:
        first_key, first_regex = patterns[0]
        matches = list(re.finditer(rf"(?im)^\s*{first_regex}", text))
        if len(matches) >= 2:
            return matches[1].start()
        elif len(matches) == 1:
            return matches[0].start()
        return 0

    @classmethod
    def extract_sections(cls, raw_content: str, form_type: str = "10-K") -> Dict[str, str]:
        cleaned_text = cls.clean_boilerplate(raw_content)
        norm_form = form_type.upper().replace(" ", "").strip()
        active_patterns = cls.PATTERNS_40F if "40-F" in norm_form or "40F" in norm_form else cls.PATTERNS_10K

        toc_offset = cls._locate_toc_offset(cleaned_text, active_patterns)
        search_space = cleaned_text[toc_offset:]

        markers: List[Tuple[int, str]] = []
        for tag, pattern in active_patterns:
            regex = re.compile(rf"(?im)^\s*{pattern}", re.IGNORECASE)
            matches = list(regex.finditer(search_space))
            if matches:
                start_idx = matches[0].start() + toc_offset
                markers.append((start_idx, tag))

        markers.sort(key=lambda x: x[0])

        extracted_sections: Dict[str, str] = {}
        for i in range(len(markers) - 1):
            curr_start, curr_tag = markers[i]
            next_start, _ = markers[i + 1]

            if curr_tag in cls.TARGET_KEYS:
                section_body = cleaned_text[curr_start:next_start].strip()
                if len(section_body) > 200:
                    extracted_sections[curr_tag] = section_body

        if markers and markers[-1][1] in cls.TARGET_KEYS:
            last_start, last_tag = markers[-1]
            extracted_sections[last_tag] = cleaned_text[last_start:].strip()

        return extracted_sections


def sanitize_filename(name: str) -> str:
    """Normalizes company name for filesystem safety."""
    cleaned = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "_", cleaned)


def process_crawled_file(input_file: str, output_dir: str = "data/") -> str:
    extractor = SECReportExtractor()
    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as f_in:
        for line in f_in:
            if not line.strip():
                continue

            doc_entry = json.loads(line)
            company_raw = doc_entry.get("company", "unknown_company")
            cik = doc_entry.get("cik", "")
            form = doc_entry.get("form", "10-K")
            year = doc_entry.get("year", 0)
            raw_content = doc_entry.get("content", "")

            sections = extractor.extract_sections(raw_content, form_type=form)

            filtered_sections = {
                item_key: {
                    "char_count": len(sections[item_key]),
                    "content": sections[item_key],
                }
                for item_key in extractor.TARGET_KEYS
                if item_key in sections
            }

            output_data = {
                "company": company_raw,
                "cik": cik,
                "form": form,
                "year": year,
                "available_sections": list(filtered_sections.keys()),
                "sections": filtered_sections,
            }

            safe_name = sanitize_filename(company_raw)
            output_filename = f"{safe_name}_cleaned.json"
            output_path = os.path.join(output_dir, output_filename)

            with open(output_path, "w", encoding="utf-8") as f_out:
                json.dump(output_data, f_out, ensure_ascii=False, indent=2)

            print(f"Successfully processed: {output_path}")
            return output_path

    return ""


if __name__ == "__main__":
    INPUT_FILE = "data/shopify inc..jsonl"
    OUTPUT_DIRECTORY = "data/"

    process_crawled_file(input_file=INPUT_FILE, output_dir=OUTPUT_DIRECTORY)
