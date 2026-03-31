"""
card_builder.py
Converts parsed card data dict into styled HTML for Anki's Front and Back fields.
Anki renders HTML in both fields, so we can make these look great.
"""


def build_card_html(card_data: dict) -> tuple[str, str]:
    """
    Build (front_html, back_html) from parsed card data.
    Both sides include embedded CSS for consistent styling.
    """
    front = _build_front(card_data)
    back = _build_back(card_data)
    return front, back


# ---------------------------------------------------------------------------
# Shared styles — injected into both sides
# ---------------------------------------------------------------------------

CARD_CSS = """
<style>
  body, .card {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 15px;
    color: #1a1a2e;
    background: #f9f9fb;
    margin: 0;
    padding: 0;
  }
  .card-wrapper {
    max-width: 720px;
    margin: 0 auto;
    padding: 16px;
  }
  .question-block {
    background: #1a1a2e;
    color: #e8e8f0;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 14px;
    font-size: 16px;
    line-height: 1.5;
    font-weight: 500;
  }
  .options-block {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 10px;
  }
  .option {
    background: #fff;
    border: 1.5px solid #dde1f0;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 14px;
    line-height: 1.4;
    color: #2a2a40;
  }
  .option.correct {
    background: #edfaf3;
    border-color: #34c779;
    color: #155a35;
    font-weight: 600;
  }
  .option.incorrect {
    background: #fff5f5;
    border-color: #f87171;
    color: #7f1d1d;
  }
  .section-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #888aaa;
    margin: 14px 0 6px 0;
  }
  .explanation-box {
    background: #edfaf3;
    border-left: 4px solid #34c779;
    border-radius: 0 6px 6px 0;
    padding: 12px 16px;
    font-size: 14px;
    line-height: 1.5;
    color: #155a35;
    margin-bottom: 10px;
  }
  .wrong-item {
    background: #fff;
    border: 1.5px solid #dde1f0;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 13.5px;
    line-height: 1.4;
  }
  .wrong-item .wrong-letter {
    display: inline-block;
    background: #f87171;
    color: white;
    border-radius: 4px;
    padding: 1px 7px;
    font-weight: 700;
    font-size: 12px;
    margin-right: 8px;
  }
  .wrong-item .wrong-reason {
    color: #555570;
    font-size: 13px;
    margin-top: 4px;
    padding-left: 32px;
  }
  .diagram-block {
    background: #fff;
    border: 1.5px solid #dde1f0;
    border-radius: 8px;
    padding: 16px;
    margin-top: 12px;
    text-align: center;
  }
  .tags-block {
    margin-top: 14px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  .tag {
    background: #e8eaf6;
    color: #3949ab;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
  }
</style>
"""


# ---------------------------------------------------------------------------
# Front (Side A): Question + all answer options
# ---------------------------------------------------------------------------

def _build_front(card_data: dict) -> str:
    question = card_data.get("question", "")
    options = card_data.get("answer_options", [])

    options_html = ""
    for option in options:
        options_html += f'<div class="option">{_escape(option)}</div>\n'

    return f"""{CARD_CSS}
<div class="card-wrapper">
  <div class="question-block">{_escape(question)}</div>
  <div class="section-label">Answer Options</div>
  <div class="options-block">
    {options_html}
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Back (Side B): Correct answer + explanation + wrong answer breakdowns + diagram
# ---------------------------------------------------------------------------

def _build_back(card_data: dict) -> str:
    question = card_data.get("question", "")
    options = card_data.get("answer_options", [])
    correct_letter = card_data.get("correct_answer_letter", "")
    correct_text = card_data.get("correct_answer_text", "")
    correct_explanation = card_data.get("correct_explanation", "")
    wrong_explanations = card_data.get("wrong_answer_explanations", {})
    diagram_svg = card_data.get("diagram_svg")
    topic_tags = card_data.get("topic_tags", [])

    # Render options with correct/incorrect highlighting
    options_html = ""
    for option in options:
        letter = option[0] if option else ""
        css_class = "correct" if letter == correct_letter else "incorrect"
        marker = " ✓" if letter == correct_letter else " ✗"
        options_html += f'<div class="option {css_class}">{_escape(option)}{marker}</div>\n'

    # Wrong answer breakdowns
    wrong_html = ""
    for letter, reason in wrong_explanations.items():
        wrong_html += f"""
    <div class="wrong-item">
      <span class="wrong-letter">{_escape(letter)}</span>
      <strong>{_option_text_for_letter(options, letter)}</strong>
      <div class="wrong-reason">{_escape(reason)}</div>
    </div>"""

    # Diagram block
    diagram_html = ""
    if diagram_svg:
        diagram_html = f"""
  <div class="section-label">Diagram</div>
  <div class="diagram-block">
    {diagram_svg}
  </div>"""

    # Tags
    tags_html = ""
    if topic_tags:
        tags_inner = "".join(f'<span class="tag">{_escape(t)}</span>' for t in topic_tags)
        tags_html = f'<div class="tags-block">{tags_inner}</div>'

    return f"""{CARD_CSS}
<div class="card-wrapper">
  <div class="question-block">{_escape(question)}</div>

  <div class="section-label">All Options</div>
  <div class="options-block">
    {options_html}
  </div>

  <div class="section-label">Why {_escape(correct_letter)} is Correct</div>
  <div class="explanation-box">{_escape(correct_explanation)}</div>

  <div class="section-label">Why the Others are Wrong</div>
  {wrong_html}

  {diagram_html}

  {tags_html}
</div>"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _escape(text: str) -> str:
    """Basic HTML escaping for safe insertion."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _option_text_for_letter(options: list[str], letter: str) -> str:
    """Find the option text matching a given letter."""
    for opt in options:
        if opt.startswith(letter + ".") or opt.startswith(letter + ")"):
            # Return just the text after the letter prefix
            return _escape(opt[2:].strip())
    return ""
