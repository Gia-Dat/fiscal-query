import os
import requests
from config import Config


def crawl_file(company_name="Shopify", form_type="10-K"):
    cik = Config.CIKS.get(company_name)
    HEADER = {"User-Agent": Config.SEC_USER_AGENT}

    URL = f"https://data.sec.gov/submissions/CIK{cik}.json"
    re = requests.get(URL, headers=HEADER)
    print(re.status_code)

    recent = re.json()['filings']['recent']
    # for key in recent.keys():
    #     print(key)
    idx = recent["form"].index(form_type)
    # print(idx)
    acc_num = recent["accessionNumber"][idx].replace("-", "")
    doc = recent["primaryDocument"][idx]
    print(acc_num, doc)

    file_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_num}/{doc}"
    doc_text = requests.get(file_url, headers=HEADER).text

    with open(f"data/{company_name.lower()}_raw.html", "w", encoding="utf-8") as f:
        f.write(doc_text)


# def main():
#     crawl_file()
#     print("Done")


# if __name__ == "__main__":
#     main()
