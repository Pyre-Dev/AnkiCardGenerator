"""
claude_parser.py
Sends a screenshot to Claude Vision and returns structured card data as a dict.
"""

import os
import base64
import json
from pathlib import Path
import anthropic

SYSTEM_PROMPT = """You are an expert IT certification study assistant. 
Your job is to analyze screenshots of wrong answers from IT certification practice exams 
and extract structured data to build high-quality Anki flashcards.

You must return ONLY valid JSON with no markdown fencing, no preamble, no explanation.
The JSON must match this exact schema:

{
  "question": "The full question text exactly as shown",
  "answer_options": [
    "A. Full text of option A",
    "B. Full text of option B",
    "C. Full text of option C",
    "D. Full text of option D"
  ],
  "correct_answer_letter": "B",
  "correct_answer_text": "Full text of the correct answer option",
  "correct_explanation": "Clear explanation of WHY this answer is correct. Be thorough and educational.",
  "wrong_answer_explanations": {
    "A": "Why option A is wrong. Be specific.",
    "C": "Why option C is wrong. Be specific.",
    "D": "Why option D is wrong. Be specific."
  },
  "diagram_svg": null,
  "topic_tags": ["networking", "subnetting"]
}

Rules:
- answer_options must include ALL options shown (typically 4, sometimes 5)
- wrong_answer_explanations must include ALL incorrect options, keyed by letter
- correct_answer_letter should only appear in wrong_answer_explanations if it appears as a wrong option (it won't)
- diagram_svg: if a visual diagram would genuinely help understand the concept (e.g. network topology, OSI layers, subnetting, IAM hierarchy), generate a clean inline SVG string. Otherwise set to null. Keep SVGs simple, monochrome-friendly, and under 2000 characters.
- topic_tags: 2-4 short lowercase tags for the concept being tested (e.g. "iam", "azure-ad", "subnetting", "osi-model")
- If the screenshot shows the correct answer highlighted or marked, use that to determine correct_answer_letter
- Explanations should be written for someone studying for IT certifications — be precise and use correct terminology
"""

USER_PROMPT = """Analyze this practice exam screenshot. I got this question wrong.
Extract all information and return the structured JSON card data."""


def parse_screenshot(screenshot_path: Path) -> dict | None:
    """
    Send screenshot to Claude Vision and return parsed card data dict.
    Returns None if parsing fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable is not set.\n"
            "Set it with: export ANTHROPIC_API_KEY=your_key_here"
        )

    # Read and encode image
    image_data = screenshot_path.read_bytes()
    b64_image = base64.standard_b64encode(image_data).decode("utf-8")

    # Detect media type
    suffix = screenshot_path.suffix.lower()
    media_type_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    media_type = media_type_map.get(suffix, "image/png")

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": USER_PROMPT,
                        },
                    ],
                }
            ],
        )
    except anthropic.APIError as e:
        print(f"[ERROR] Anthropic API error: {e}")
        return None

    raw_text = response.content[0].text.strip()

    # Strip markdown fences if Claude added them despite instructions
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1])

    try:
        card_data = json.loads(raw_text)
        return card_data
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse Claude's JSON response: {e}")
        print(f"[DEBUG] Raw response:\n{raw_text}")
        return None
