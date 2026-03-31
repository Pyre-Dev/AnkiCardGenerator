"""
anki_connect.py
Handles all communication with the AnkiConnect local API (http://localhost:8765).
"""

import json
import urllib.request
import urllib.error

ANKI_CONNECT_URL = "http://localhost:8765"
ANKI_CONNECT_VERSION = 6
NOTE_TYPE = "Basic"  # Front/Back note type — standard in all Anki installs


def _invoke(action: str, **params) -> any:
    """Send a request to AnkiConnect and return the result."""
    payload = json.dumps({
        "action": action,
        "version": ANKI_CONNECT_VERSION,
        "params": params,
    }).encode("utf-8")

    request = urllib.request.Request(
        ANKI_CONNECT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Could not connect to AnkiConnect at {ANKI_CONNECT_URL}. "
            f"Is Anki open? Error: {e}"
        )

    if result.get("error") is not None:
        raise RuntimeError(f"AnkiConnect error: {result['error']}")

    return result["result"]


def check_anki_connection() -> bool:
    """Returns True if AnkiConnect is reachable."""
    try:
        _invoke("version")
        return True
    except (ConnectionError, RuntimeError):
        return False


def ensure_deck_exists(deck_name: str) -> None:
    """Create the deck if it doesn't already exist."""
    _invoke("createDeck", deck=deck_name)


def get_available_note_types() -> list[str]:
    """Return all note type names available in Anki."""
    return _invoke("modelNames")


def create_anki_card(
    deck: str,
    front: str,
    back: str,
    tags: list[str] | None = None,
) -> int:
    """
    Create a Basic note in Anki with the given front/back HTML.
    Returns the new note ID.
    """
    note = {
        "deckName": deck,
        "modelName": NOTE_TYPE,
        "fields": {
            "Front": front,
            "Back": back,
        },
        "options": {
            "allowDuplicate": False,
            "duplicateScope": "deck",
        },
        "tags": tags or [],
    }

    note_id = _invoke("addNote", note=note)
    return note_id
