import json
import os
import time

from pathlib import Path
from io import BytesIO

import requests

from PIL import Image

from db import get_all_cards_for_scanner
from scanner.visual_search import calculate_phash


# ==================================================
# PATHS
# ==================================================

IMAGE_CACHE_DIR = Path(
    "data/image_cache"
)

INDEX_PATH = Path(
    "data/feature_cache/scanner_index.json"
)

INDEX_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ==================================================
# LOAD / SAVE
# ==================================================

def load_index():

    if not INDEX_PATH.exists():
        return {}

    with open(
        INDEX_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )


def save_index(index):

    temp = INDEX_PATH.with_suffix(
        ".tmp"
    )

    with open(
        temp,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            index,
            file,
            indent=2,
            ensure_ascii=False
        )

    os.replace(
        temp,
        INDEX_PATH
    )


# ==================================================
# FIND LOCAL IMAGE
# ==================================================

def find_cached_image(card_id):

    extensions = (
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    )

    for ext in extensions:

        path = (
            IMAGE_CACHE_DIR
            / f"{card_id}{ext}"
        )

        if path.exists():
            return path

    return None


# ==================================================
# DOWNLOAD IMAGE TEMPORARILY
# ==================================================

def download_image(url):

    attempts = 3

    for attempt in range(
        attempts
    ):

        try:

            response = requests.get(
                url,
                timeout=20,
                headers={
                    "User-Agent":
                    "PokemonInventoryScanner/2.0"
                }
            )

            response.raise_for_status()

            return Image.open(
                BytesIO(
                    response.content
                )
            ).convert(
                "RGB"
            )


        except Exception as error:

            print(
                "Download attempt",
                attempt + 1,
                "failed:",
                error
            )

            time.sleep(
                2 ** attempt
            )


    return None


# ==================================================
# PROCESS CARD
# ==================================================

def process_card(card):

    card_id = card["id"]

    # ----------------------------------------------
    # Try local cache first
    # ----------------------------------------------

    image_path = find_cached_image(
        card_id
    )

    if image_path:

        try:

            image = Image.open(
                image_path
            ).convert(
                "RGB"
            )

            source = "cache"

        except:

            image = None

    else:

        image = None


    # ----------------------------------------------
    # Download if needed
    # ----------------------------------------------

    if image is None:

        image = download_image(
            card["image_url"]
        )

        source = "download"


    if image is None:

        return None, "Could not load image"


    try:

        phash = calculate_phash(
            image
        )

        return (
            {
                "name": card["name"],
                "set_id": card["set_id"],
                "number": card["number"],
                "phash": phash,
                "image_url": card["image_url"],
            },
            source
        )


    except Exception as error:

        return None, str(error)


# ==================================================
# BUILD INDEX
# ==================================================

def build_index():

    cards = get_all_cards_for_scanner()

    index = load_index()


    print()
    print("============================")
    print("SCANNER 2.0 VISUAL INDEX")
    print("============================")

    print(
        "Database cards:",
        len(cards)
    )

    print(
        "Existing fingerprints:",
        len(index)
    )


    completed = 0
    failed = 0
    from_cache = 0
    downloaded = 0


    for number, card in enumerate(
        cards,
        start=1
    ):

        card_id = card["id"]


        # Already done
        if (
            card_id in index
            and index[card_id].get(
                "phash"
            )
        ):
            continue


        result, source = (
            process_card(
                card
            )
        )


        if result:

            index[card_id] = result

            completed += 1


            if source == "cache":
                from_cache += 1

            else:
                downloaded += 1


        else:

            failed += 1

            print(
                "Failed:",
                card_id,
                source
            )


        # Save often
        if completed % 100 == 0:

            save_index(
                index
            )

            print(
                f"{number}/{len(cards)} "
                f"| Added: {completed} "
                f"| Cache: {from_cache} "
                f"| Downloaded: {downloaded} "
                f"| Failed: {failed}"
            )


    save_index(
        index
    )


    print()
    print("============================")
    print("INDEX COMPLETE")
    print("============================")

    print(
        "Total fingerprints:",
        len(index)
    )

    print(
        "Added this run:",
        completed
    )

    print(
        "From cache:",
        from_cache
    )

    print(
        "Downloaded:",
        downloaded
    )

    print(
        "Failed:",
        failed
    )


if __name__ == "__main__":

    build_index()