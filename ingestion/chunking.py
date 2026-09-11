import re
from typing import List, Dict, Any

from bs4 import BeautifulSoup

from langchain_text_splitters import RecursiveCharacterTextSplitter

# from clean_data import clean_data


def chunking(section_dict: Dict[str, str], company_name: str) -> List[Dict[str, Any]]:
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=600,
        chunk_overlap=80,
    )
    final_chunks = []

    for item_name, sec_html in section_dict.items():
        soup = BeautifulSoup(sec_html, "html.parser")

        for tag in soup.find_all(['table', 'p', 'div']):
            # Add prefix for better context
            prefix = f"[{company_name} 10-K | {item_name}]\n"

            # Handle Table
            if tag.name == 'table':
                rows = []
                for tr in tag.find_all('tr'):
                    cells = [re.sub(r'\s+', ' ', td.get_text().strip())
                             for td in tr.find_all(['td', 'th'])]
                    if any(cells):
                        rows.append(cells)

                if len(rows) >= 2:
                    header = "| " + \
                        " | ".join(rows[0]) + " |\n| " + \
                        " | ".join(["---"] * len(rows[0])) + " |\n"
                    table_body = ""
                    for r in rows[1:]:
                        padded = r + [""] * (len(rows[0]) - len(r))
                        table_body += "| " + \
                            " | ".join(padded[:len(rows[0])]) + " |\n"

                    full_table = prefix + header + table_body
                    final_chunks.append({
                        "text": full_table,
                        "metadata": {"company": company_name, "item": item_name, "type": "table"}
                    })

            # Handle Text
            elif tag.name in ['p', 'div'] and not tag.find('table'):
                raw_text = re.sub(r'\s+', ' ', tag.get_text().strip())
                if len(raw_text) > 60:
                    for sub in splitter.split_text(raw_text):
                        final_chunks.append({
                            "text": prefix + sub,
                            "metadata": {"company": company_name, "item": item_name, "type": "text"}
                        })

    return final_chunks


# def main():
#     sec = clean_data("data/shopify_raw.html")
#     chunks = chunking(sec, "Shopify")
#     print(chunks[390])
#     print("Done")


# if __name__ == "__main__":
#     main()
