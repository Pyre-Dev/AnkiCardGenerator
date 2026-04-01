#!/usr/bin/env python3
"""
Anki Card Generator from Wrong Answer Screenshots
Uses Claude Vision to parse practice exam screenshots into structured Anki cards.
Pass a single image file or a folder of images.
"""

import sys
import time
import argparse
import json
from pathlib import Path
from claude_parser import parse_screenshot
from anki_connect import create_anki_card, check_anki_connection, ensure_deck_exists
from card_builder import build_card_html

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
DELAY_BETWEEN_CALLS = 2  # seconds between API calls in batch mode


def process_single(screenshot_path: Path, deck: str, tags: list, dry_run: bool) -> bool:
    """
    Process one screenshot into an Anki card.
    Returns True on success, False on failure.
    """
    print(f"  Sending to Claude: {screenshot_path.name}")
    card_data = parse_screenshot(screenshot_path)

    if not card_data:
        print(f"  [FAILED] Claude could not parse: {screenshot_path.name}")
        return False

    front_html, back_html = build_card_html(card_data)

    if dry_run:
        print(f"\n{'='*60}")
        print(f"DRY RUN PREVIEW: {screenshot_path.name}")
        print(f"{'='*60}")
        print("\n--- SIDE A (Front) ---")
        print(front_html)
        print("\n--- SIDE B (Back) ---")
        print(back_html)
        print("\n--- RAW PARSED DATA ---")
        print(json.dumps(card_data, indent=2))
        return True

    try:
        note_id = create_anki_card(
            deck=deck,
            front=front_html,
            back=back_html,
            tags=tags,
        )
        print(f"  [OK] Card created (Note ID: {note_id})")
        return True
    except RuntimeError as e:
        # AnkiConnect raises RuntimeError for duplicates and other errors
        print(f"  [SKIPPED] {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert wrong-answer screenshots into Anki cards. Pass a single image or a folder."
    )
    parser.add_argument(
        "input",
        help="Path to a screenshot image OR a folder of screenshots"
    )
    parser.add_argument(
        "--deck",
        default="Study Cards",
        help="Anki deck name to add cards to (default: 'Study Cards')"
    )
    parser.add_argument(
        "--tags",
        nargs="*",
        default=[],
        help="Optional tags for the cards e.g. --tags AZ-104 networking"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and preview cards without sending to Anki"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Path not found: {input_path}")
        sys.exit(1)

    # Collect files to process
    if input_path.is_dir():
        files = sorted([
            f for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ])
        if not files:
            print(f"[ERROR] No image files found in: {input_path}")
            sys.exit(1)
        print(f"[INFO] Found {len(files)} image(s) in '{input_path.name}'")
    else:
        if input_path.suffix.lower() not in IMAGE_EXTENSIONS:
            print(f"[ERROR] Unsupported file type: {input_path.suffix}")
            sys.exit(1)
        files = [input_path]

    # Check Anki connection once upfront (skip in dry-run)
    if not args.dry_run:
        print("[*] Checking AnkiConnect...")
        if not check_anki_connection():
            print("[ERROR] Cannot reach AnkiConnect at http://localhost:8765")
            print("        Make sure Anki is open and AnkiConnect is installed.")
            sys.exit(1)
        print(f"[*] AnkiConnect OK")
        print(f"[*] Ensuring deck '{args.deck}' exists...")
        ensure_deck_exists(args.deck)
        print(f"[*] Deck ready\n")
    else:
        print("[DRY RUN] Skipping Anki connection check\n")

    # Process all files
    total = len(files)
    success_count = 0
    fail_count = 0

    for i, filepath in enumerate(files, start=1):
        print(f"[{i}/{total}] {filepath.name}")
        ok = process_single(filepath, args.deck, args.tags, args.dry_run)
        if ok:
            success_count += 1
        else:
            fail_count += 1

        # Delay between calls in batch mode to avoid rate limiting
        if total > 1 and i < total:
            time.sleep(DELAY_BETWEEN_CALLS)

    # Summary
    print(f"\n{'='*40}")
    if args.dry_run:
        print(f"DRY RUN COMPLETE: {total} card(s) previewed")
    else:
        print(f"DONE: {success_count}/{total} card(s) added to '{args.deck}'")
        if fail_count:
            print(f"      {fail_count} skipped (duplicates or parse errors)")
    print(f"{'='*40}")


if __name__ == "__main__":
    main()

