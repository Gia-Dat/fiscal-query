import os

import requests
from bs4 import BeautifulSoup

import json

HEADER = {"User-Agent": "FiscalQuery giadat2359@gmail.com"}


def get_file(cik: str, form_type="10-K"):
    URL = f"https://data.sec.gov/submissions/CIK{cik}.json"
    re = requests.get(URL, headers=HEADER)
    # print(re.status_code)

    company_name = re.json().get("name", "Unknown")
    recent = re.json()['filings']['recent']
    for key in recent.keys():
        print(key)
    idx = recent["form"].index(form_type)
    # print(idx)
    acc_num = recent["accessionNumber"][idx].replace("-", "")
    doc = recent["primaryDocument"][idx]
    print(acc_num, doc)
    report_date = recent["reportDate"][idx]
    report_year = int(report_date.split("-")[0])

    file_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_num}/{doc}"
    doc_text = requests.get(file_url, headers=HEADER).text.encode(
        "utf-8", errors="ignore")

    soup = BeautifulSoup(doc_text, "html.parser")
    # Remove unused tags
    for tag in soup(["ix:header", "style", "script", "head"]):
        tag.decompose()

    clean_text = soup.get_text(separator="\n", strip=True)
    # print(clean_text)

    os.makedirs("data/", exist_ok=True)
    jsonl_path = f"data/{company_name.lower()}.jsonl"

    record = {
        "company": company_name,
        "cik": cik,
        "form": form_type,
        "year": report_year,
        "doc_name": doc,
        "char_count": len(clean_text),
        "content": clean_text,
    }

    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    get_file("0001594805")
    print("Done")


if __name__ == "__main__":
    main()
