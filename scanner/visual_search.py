import cv2
import numpy as np

from PIL import Image

from io import BytesIO

import requests


# ==================================================
# PERCEPTUAL HASH
# ==================================================

def calculate_phash(image):
    """
    Create a 64-bit perceptual fingerprint.

    Similar-looking images should produce hashes
    with relatively small Hamming distances.
    """

    if isinstance(image, Image.Image):
        image = np.array(
            image.convert("RGB")
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )

    # pHash normally uses a small 32x32 image.
    small = cv2.resize(
        gray,
        (32, 32),
        interpolation=cv2.INTER_AREA
    )

    small = small.astype(
        np.float32
    )

    # Discrete cosine transform.
    dct = cv2.dct(
        small
    )

    # Keep the low-frequency information.
    low_frequency = dct[
        :8,
        :8
    ]

    # Ignore the DC component when determining
    # the median brightness threshold.
    values = low_frequency.flatten()

    median = np.median(
        values[1:]
    )

    bits = (
        low_frequency
        > median
    ).flatten()

    hash_value = 0

    for bit in bits:
        hash_value <<= 1

        if bit:
            hash_value |= 1

    # 64-bit hash represented by 16 hex characters.
    return f"{hash_value:016x}"


# ==================================================
# HASH DISTANCE
# ==================================================

def hash_distance(
    hash_a,
    hash_b
):
    """
    Smaller number = more visually similar.

    0 means identical perceptual hashes.
    """

    value_a = int(
        hash_a,
        16
    )

    value_b = int(
        hash_b,
        16
    )

    difference = (
        value_a
        ^ value_b
    )

    return difference.bit_count()

import json
from pathlib import Path


INDEX_PATH = Path(
    "data/feature_cache/scanner_index.json"
)


def load_visual_index():
    if not INDEX_PATH.exists():
        return {}

    with open(
        INDEX_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def find_closest_cards(
    image,
    visual_index,
    limit=20
):
    scan_hash = calculate_phash(
        image
    )

    matches = []

    for card_id, card in (
        visual_index.items()
    ):

        card_hash = card.get(
            "phash"
        )

        if not card_hash:
            continue

        distance = hash_distance(
            scan_hash,
            card_hash
        )

        matches.append({
            "id": card_id,
            "name": card.get("name"),
            "set_id": card.get("set_id"),
            "number": card.get("number"),
            "image_url": card.get(
                "image_url"
            ),
            "distance": distance,
        })

    matches.sort(
        key=lambda card: card[
            "distance"
        ]
    )

    return matches[:limit]

# ==================================================
# LOAD OFFICIAL CARD IMAGE
# ==================================================

def download_candidate_image(
    image_url
):
    try:
        response = requests.get(
            image_url,
            timeout=15,
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
        ).convert("RGB")

    except Exception as error:
        print(
            "Candidate image failed:",
            error
        )

        return None


# ==================================================
# ORB DESCRIPTORS
# ==================================================

def calculate_orb_descriptors(
    image
):
    if isinstance(
        image,
        Image.Image
    ):
        image = np.array(
            image.convert("RGB")
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )

    # Use a consistent size.
    gray = cv2.resize(
        gray,
        (750, 1050),
        interpolation=cv2.INTER_AREA
    )

    orb = cv2.ORB_create(
        nfeatures=2000
    )

    _, descriptors = (
        orb.detectAndCompute(
            gray,
            None
        )
    )

    return descriptors


# ==================================================
# ORB SIMILARITY
# ==================================================

def compare_orb(
    descriptors_a,
    descriptors_b
):
    if (
        descriptors_a is None
        or descriptors_b is None
    ):
        return 0.0

    matcher = cv2.BFMatcher(
        cv2.NORM_HAMMING,
        crossCheck=True
    )

    matches = matcher.match(
        descriptors_a,
        descriptors_b
    )

    if not matches:
        return 0.0

    matches = sorted(
        matches,
        key=lambda match: match.distance
    )

    # Strong ORB matches generally have
    # lower Hamming distances.
    good_matches = [
        match
        for match in matches
        if match.distance <= 50
    ]

    denominator = max(
        min(
            len(descriptors_a),
            len(descriptors_b)
        ),
        1
    )

    score = (
        len(good_matches)
        / denominator
        * 100
    )

    return score


# ==================================================
# DETAILED CANDIDATE RANKING
# ==================================================

def rerank_candidates_with_orb(
    scanned_image,
    candidates
):
    scanned_descriptors = (
        calculate_orb_descriptors(
            scanned_image
        )
    )

    results = []

    for card in candidates:

        official_image = (
            download_candidate_image(
                card["image_url"]
            )
        )

        if official_image is None:
            continue

        official_descriptors = (
            calculate_orb_descriptors(
                official_image
            )
        )

        orb_score = compare_orb(
            scanned_descriptors,
            official_descriptors
        )

        result = card.copy()

        result["orb_score"] = (
            orb_score
        )

        results.append(
            result
        )

    results.sort(
        key=lambda card: card[
            "orb_score"
        ],
        reverse=True
    )

    return results
