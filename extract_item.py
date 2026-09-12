import os
import unicodedata

from bs4 import BeautifulSoup


class Extract:
    def __init__(self, file_path):
        self.file_path = file_path
        self.soup = None
        self._load_html()

    # Load HTML content from the specified file path
    def _load_html(self):
        with open(self.file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        self.soup = BeautifulSoup(html_content, 'html.parser')

    # Normalize unicode characters, replace non-breaking spaces, and convert to lower case
    def normalize_text(self, text):
        return unicodedata.normalize('NFKD', text).lower()

    # Find all tags that contain the item_text
    def find_second_occurrence(self, item_text):
        tags = [
            tag for tag in self.soup.find_all(
                text=lambda text: text and item_text.lower() in self.normalize_text(text)
            )
        ]
        # Return the second occurrence if it exists (first occurrence is the table of contents)
        if len(tags) >= 2:
            return tags[1].parent
        return None

    # Extract the content between from_tag and to_tag (excluding to_tag)
    def extract_content(self, from_tag, to_tag):
        content = ''
        if from_tag and to_tag:
            content += from_tag.get_text(separator=' ', strip=True) + '\n'
            element = from_tag.find_next()
            while element and element != to_tag:
                if element.name == 'div' and element.find_parent('div') is None:
                    text = element.get_text(separator=' ', strip=True)
                    if text:
                        content += text + '\n'
                element = element.find_next()

        return content

    def extract_item_content(self, start: str, end: str):
        item_start_tag = self.find_second_occurrence(start)
        item_end_tag = self.find_second_occurrence(end)
        return self.extract_content(item_start_tag, item_end_tag)

    # Save the extracted content to a file
    def save_content(self, content, output_path):
        directory = os.path.dirname(output_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)
