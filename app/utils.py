from html.parser import HTMLParser


class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_text(self):
        return ''.join(self.text)

def html_to_text(html_content):
    parser = HTMLStripper()
    parser.feed(html_content)

    text = parser.get_text()

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return ' '.join(lines)