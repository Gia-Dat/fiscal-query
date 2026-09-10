import re
from bs4 import BeautifulSoup


def clean_data(html_path: str):
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()

    body_html = str(soup.body or soup)
    print(body_html[:500])


def main():
    clean_data("data/shopify_raw.html")
    print("Done")


if __name__ == "__main__":
    main()
