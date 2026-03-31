#!/usr/bin/env python3
"""
Anki Card Generator from Wrong Answer Screenshots
Uses Claude Vision to parse IT cert exam screenshots into structured Anki cards.
"""

import sys
import argparse
from pathlib import Path
from claude_parser import parse_screenshot
from anki_connect import create_anki_card, check_anki_connection, ensure_deck_exists
from card_builder import build_card_html


def main():
    parser = argparse.ArgumentParser(
        description="Convert a wrong-answer screenshot into an Anki card."
    )
    parser.add_argument(
        "screenshot",
        help="Path to the screenshot image (PNG, JPG, etc.)"
    )
    parser.add_argument(
        "--deck",
        default="IT Certs",
        help="Anki deck name to add the card to (default: 'IT Certs')"
    )
    parser.add_argument(
        "--tags",
        nargs="*",
        default=[],
        help="Optional tags for the card e.g. --tags AZ-104 networking"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and preview the card without sending it to Anki"
    )
    args = parser.parse_args()

    screenshot_path = Path(args.screenshot)
    if not screenshot_path.exists():
        print(f"[ERROR] Screenshot not found: {screenshot_path}")
        sys.exit(1)

    # Step 1: Check Anki is running (skip in dry-run)
    if not args.dry_run:
        print("[1/4] Checking AnkiConnect...")
        if not check_anki_connection():
            print("[ERROR] Cannot reach AnkiConnect at http://localhost:8765")
            print("       Make sure Anki is open and AnkiConnect is installed.")
            sys.exit(1)
        print("      AnkiConnect OK")

        print(f"[2/4] Ensuring deck '{args.deck}' exists...")
        ensure_deck_exists(args.deck)
        print(f"      Deck ready")
    else:
        print("[DRY RUN] Skipping Anki connection check\n")

    # Step 2: Parse screenshot with Claude
    print(f"[3/4] Sending screenshot to Claude for parsing...")
    print(f"      File: {screenshot_path.name}")
    card_data = parse_screenshot(screenshot_path)

    if not card_data:
        print("[ERROR] Claude could not parse the screenshot into a card.")
        sys.exit(1)

    print("      Parsed successfully")

    # Step 3: Build HTML for both sides
    front_html, back_html = build_card_html(card_data)

    # Step 4: Preview or send to Anki
    if args.dry_run:
        print("\n" + "="*60)
        print("DRY RUN PREVIEW")
        print("="*60)
        print("\n--- SIDE A (Front) ---")
        print(front_html)
        print("\n--- SIDE B (Back) ---")
        print(back_html)
        print("\n--- RAW PARSED DATA ---")
        import json
        print(json.dumps(card_data, indent=2))
    else:
        print(f"[4/4] Creating card in Anki deck '{args.deck}'...")
        note_id = create_anki_card(
            deck=args.deck,
            front=front_html,
            back=back_html,
            tags=args.tags
        )
        print(f"      Card created! Note ID: {note_id}")
        print(f"\n[DONE] Card added to '{args.deck}'")
        if args.tags:
            print(f"       Tags: {', '.join(args.tags)}")


if __name__ == "__main__":
    main()
