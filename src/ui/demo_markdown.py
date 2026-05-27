"""Standalone demo: shows all supported Markdown elements.
Run: cd src && python -m ui.demo_markdown
Delete after testing.
"""

import sys

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from ui.status_card import _ReplyBrowser, _md_to_html

_SAMPLE = """\
# Heading 1
## Heading 2
### Heading 3
#### Heading 4

---

**Bold text**, *italic text*, ~~strikethrough text~~

Combined: ***bold and italic***, **bold with ~~strikethrough~~**

`inline code` and regular text mixed together

```python
def hello(name: str) -> str:
    # Greet someone
    return f"Hello, {name}!"

for i in range(5):
    print(hello(f"User {i}"))
```

```json
{
  "key": "value",
  "number": 42,
  "nested": {"a": true}
}
```

> This is a blockquote
> It can span multiple lines
>
> > And be nested too

[Link to Google](https://www.google.com) | [Link to GitHub](https://github.com)

Image (loaded from network):

![Python logo](https://www.python.org/static/community_logos/python-logo.png)

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1A   | Row 1B   | Row 1C   |
| Row 2A   | Row 2B   | Row 2C   |
| Row 3A   | Row 3B   | Row 3C   |

Unordered list:
- Item one
- Item two
  - Nested item
  - Another nested
- Item three

Ordered list:
1. First step
2. Second step
3. Third step

Task list:
- [x] Completed task
- [x] Another done task
- [ ] Pending task
- [ ] Another pending task

---

Paragraph with various inline elements: **bold**, *italic*, `code`, ~~deleted~~, and a [link](https://example.com).
"""


def main() -> None:
    app = QApplication(sys.argv)

    win = QWidget()
    win.setWindowTitle("Markdown Rendering Demo")
    win.setStyleSheet("background: #1a1a2e;")
    win.resize(540, 750)

    layout = QVBoxLayout(win)
    layout.setContentsMargins(16, 16, 16, 16)

    browser = _ReplyBrowser()
    browser.setOpenExternalLinks(True)
    browser.setStyleSheet("""
        QTextBrowser {
            color: #c0c0c0;
            background: #1a1a2e;
            border: 1px solid #3a3a5e;
            border-radius: 8px;
            padding: 8px;
        }
        QScrollBar:vertical {
            width: 6px; background: transparent;
        }
        QScrollBar::handle:vertical {
            background: #3a3a5e; border-radius: 3px; min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """)

    html = _md_to_html(_SAMPLE, font_size=10)
    browser.setHtml(html)
    layout.addWidget(browser)

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
