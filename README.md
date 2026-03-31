# Anki Card Generator — Wrong Answer Screenshot Tool

Converts any IT exam wrong-answer screenshots into fully formatted Anki cards using Claude Vision. One command, one card, no manual work.

## What it does

**Side A (Front):** Question text + all answer options

**Side B (Back):**
- All options highlighted (correct in green, wrong in red)
- Explanation of why the correct answer is right
- Per-wrong-answer explanations of why each distractor is wrong
- Optional SVG diagram for visual concepts (network topology, OSI layers, IAM hierarchy, etc.)
- Topic tags auto-generated from the question content

---

## Setup

### 1. Prerequisites

- Python 3.10+
- Anki open and running
- AnkiConnect add-on installed in Anki (see below)
- An Anthropic API key with billing set up (see below)

### 2. Install AnkiConnect

AnkiConnect is a free Anki add-on that lets external programs create cards while Anki is running. It exposes a local REST API on `http://localhost:8765`.

1. Open Anki
2. Go to **Tools > Add-ons > Get Add-ons**
3. Enter code: **`2055492159`**
4. Restart Anki
5. Confirm it's working by visiting http://localhost:8765 in a browser — you should see a JSON response with a version number

### 3. Get an Anthropic API key

This tool uses the Claude API, which is **separate from a Claude.ai subscription**. You need to set up API billing even if you already have Claude Pro.

1. Go to **console.anthropic.com** and sign in
2. Navigate to **Settings > Billing** and add a credit card
3. Load some credits — $5 is more than enough, each card costs a fraction of a cent
4. Go to **API Keys** and generate a new key
5. Set the key in your terminal:

```bash
# Mac/Linux/Git Bash
export ANTHROPIC_API_KEY=sk-ant-...

# Windows (Command Prompt)
set ANTHROPIC_API_KEY=sk-ant-...

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

To make this permanent, add the export line to your `~/.zshrc` or `~/.bashrc`, or set it as a system environment variable on Windows.

> **Note:** If you get a 401 authentication error, double-check that billing is active on your account and that you copied the full key without any typos. Keys generated before billing is activated can sometimes need to be regenerated.

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### Basic — add card to default "IT Certs" deck

```bash
python main.py path/to/screenshot.png
```

> **Windows users:** Use forward slashes or wrap the path in quotes to avoid shell escaping issues.
> ```bash
> python main.py "C:\Users\you\Desktop\screenshot.png" --deck AZ-104
> # or
> python main.py C:/Users/you/Desktop/screenshot.png --deck AZ-104
> ```

### Specify a deck

```bash
python main.py screenshot.png --deck "AZ-104"
```

### Add tags

```bash
python main.py screenshot.png --deck "AZ-104" --tags networking subnetting
```

### Dry run — preview the card without adding to Anki

```bash
python main.py screenshot.png --dry-run
```

---

## File structure

```
anki-screenshot-tool/
├── main.py           # Entry point — CLI argument handling and orchestration
├── claude_parser.py  # Sends screenshot to Claude Vision, returns structured JSON
├── card_builder.py   # Converts JSON into styled HTML for Anki front/back
├── anki_connect.py   # AnkiConnect API client (localhost:8765)
├── requirements.txt  # Python dependencies (just anthropic)
└── README.md
```

---

## Workflow tips

- **Screenshot the full question** — include the question text, all answer options, and ideally the correct answer highlighted by the test platform. The more context Claude has, the better the explanations.
- **Works with any multiple choice exam** — IT certs (AZ-104, Security+, CISSP), bar prep, med school, real estate licensing, nursing boards, or any practice test with multiple choice questions.
- **Decks** — Consider a deck per certification (e.g., "AZ-104", "Security+") rather than one big deck so you can review by exam.
- **Tags** — Claude auto-generates topic tags, but you can add your own with `--tags` for finer-grained filtering inside Anki.
- **Diagrams** — Claude generates an SVG when a diagram genuinely helps (e.g., subnetting, OSI model, IAM trust relationships). For straightforward recall questions it skips the diagram and keeps the card clean.

---

## Troubleshooting

**"Cannot reach AnkiConnect"**
Make sure Anki is open. Visit http://localhost:8765 in a browser — you should see a version number JSON response.

**401 authentication error from Claude**
This means your API key is invalid or billing isn't active yet. Go to console.anthropic.com, confirm your billing is set up under Settings > Billing, then generate a fresh API key. Keys created before billing is activated may need to be regenerated even if they look valid.

**Card not appearing in Anki**
AnkiConnect blocks duplicate cards by default (same question in the same deck). If you're re-running on the same screenshot, either use `--dry-run` to inspect or delete the existing card first.

**Claude returns bad JSON**
Rare but possible. Re-run the command — Claude's responses are non-deterministic and a retry usually succeeds. If it fails consistently, check that the screenshot is legible and includes the full question.
