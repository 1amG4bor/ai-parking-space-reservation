import re


def format_html(text: str) -> str:
    """Formats html elements to markdown format."""
    anchor_tag_pattern = r'<a\s+(?:[^>]*?\s+)?href="([^"]*)">(.*?)</a>'
    bold_tag_pattern = r"<b>(.*?)</b>"
    italic_tag_pattern = r"<i>(.*?)</i>"
    list_item_pattern = r"<li>(.*?)</li>"
    newline_pattern = r"<br\s*/?>"

    replacements = [
        (anchor_tag_pattern, r"[\2](\1)"),
        (bold_tag_pattern, r"**\1**"),
        (italic_tag_pattern, r"_\1_"),
        (list_item_pattern, r"- \1"),
        (newline_pattern, r"\n"),
    ]

    for pattern, replacement in replacements:
        if bool(re.search(pattern, text)):
            text = re.sub(pattern, replacement, text)

    return text
