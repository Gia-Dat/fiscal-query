import re
from typing import Dict
from bs4 import BeautifulSoup


def clean_data(html_path: str) -> Dict[str, str]:
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()

    body_html = str(soup.body or soup)
    target_items = ["1", "1A", "7", "7A", "8"]
    all_markers = ["1", "1A", "1B", "1C", "2", "3",
                   "4", "5", "6", "7", "7A", "8", "9", "9A"]

    pattern = re.compile(
        r"(?:^|\n|>)\s*(?:PART\s+[I|V|X]+\s+)?ITEM\s+("
        + "|".join(all_markers)
        + r")[\.:\s\-]+([^<>\n]+)",
        re.IGNORECASE
    )

    matches = list(pattern.finditer(body_html))

    # Remove Table of Content
    body_start = 0
    for m in matches:
        if m.group(1).upper() == "1":
            pos = m.start()
            if len(body_html) - pos > 50000:
                body_start = pos
                break

    valid_matches = [m for m in matches if m.start() >= body_start]
    sections = {}

    for idx, m in enumerate(valid_matches):
        item_id = m.group(1).upper()
        if item_id in target_items and item_id not in sections:
            start_pos = m.end()
            end_pos = valid_matches[idx + 1].start() if idx + \
                1 < len(valid_matches) else len(body_html)
            content = body_html[start_pos:end_pos].strip()

            if len(content) > 500:
                sections[f"Item {item_id}"] = content

    return sections


# def main():
#     sec = clean_data("data/shopify_raw.html")
#     print(sec["Item 1"])
#     print("Done")


# if __name__ == "__main__":
#     main()
