import hashlib
import json
import os
import re

from database.models import (
    Card,
    Set,
    SessionLocal
)

from paths import (
    CARDS_DIR,
    SETS_PATH
)


# ==========================================================
# TEXT NORMALIZATION
# ==========================================================

def normalize_text(value):
    if value is None:
        return ""

    value = str(value)

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip().lower()


def normalize_list(values):
    if not values:
        return []

    return [
        normalize_text(value)
        for value in values
    ]


def normalize_attack_cost(values):
    """
    Some Pokémon card datasets represent
    a zero-energy attack as:

        []

    while others represent the same thing as:

        ["Free"]

    For gameplay-equivalence purposes,
    both should be treated as zero cost.
    """

    if not values:
        return []

    normalized = []

    for value in values:

        value = normalize_text(
            value
        )

        if value == "free":
            continue

        normalized.append(
            value
        )

    return normalized


# ==========================================================
# GAMEPLAY FINGERPRINT
# ==========================================================

def build_gameplay_key(card_data):
    """
    Build a fingerprint representing the actual
    gameplay characteristics of a Pokémon card.

    Set, collector number, rarity, artwork, etc.
    are deliberately ignored so equivalent
    reprints can match one another.
    """

    if (
        card_data.get("supertype")
        != "Pokémon"
    ):
        return None

    # ------------------------------------------------------
    # Abilities
    # ------------------------------------------------------

    abilities = []

    for ability in (
        card_data.get("abilities")
        or []
    ):

        abilities.append({
            "name": normalize_text(
                ability.get("name")
            ),

            "type": normalize_text(
                ability.get("type")
            ),

            "text": normalize_text(
                ability.get("text")
            )
        })

    # ------------------------------------------------------
    # Attacks
    # ------------------------------------------------------

    attacks = []

    for attack in (
        card_data.get("attacks")
        or []
    ):

        normalized_cost = (
            normalize_attack_cost(
                attack.get("cost")
            )
        )

        attacks.append({
            "name": normalize_text(
                attack.get("name")
            ),

            "cost": normalized_cost,

            # Do not trust convertedEnergyCost from
            # the dataset because "Free" has been
            # represented inconsistently.
            "converted_energy_cost":
                len(normalized_cost),

            "damage": normalize_text(
                attack.get("damage")
            ),

            "text": normalize_text(
                attack.get("text")
            )
        })

    # ------------------------------------------------------
    # Weaknesses
    # ------------------------------------------------------

    weaknesses = []

    for weakness in (
        card_data.get("weaknesses")
        or []
    ):

        weaknesses.append({
            "type": normalize_text(
                weakness.get("type")
            ),

            "value": normalize_text(
                weakness.get("value")
            )
        })

    # ------------------------------------------------------
    # Resistances
    # ------------------------------------------------------

    resistances = []

    for resistance in (
        card_data.get("resistances")
        or []
    ):

        resistances.append({
            "type": normalize_text(
                resistance.get("type")
            ),

            "value": normalize_text(
                resistance.get("value")
            )
        })

    # ------------------------------------------------------
    # Gameplay data
    # ------------------------------------------------------

    gameplay_data = {
        "name": normalize_text(
            card_data.get("name")
        ),

        "supertype": normalize_text(
            card_data.get("supertype")
        ),

        "subtypes": normalize_list(
            card_data.get("subtypes")
        ),

        "hp": normalize_text(
            card_data.get("hp")
        ),

        "types": normalize_list(
            card_data.get("types")
        ),

        "evolves_from": normalize_text(
            card_data.get(
                "evolvesFrom"
            )
        ),

        "abilities": abilities,

        "attacks": attacks,

        "weaknesses": weaknesses,

        "resistances": resistances,

        "retreat_cost": normalize_list(
            card_data.get(
                "retreatCost"
            )
        ),

        "rules": normalize_list(
            card_data.get("rules")
        )
    }

    serialized = json.dumps(
        gameplay_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    )

    return hashlib.sha256(
        serialized.encode(
            "utf-8"
        )
    ).hexdigest()


# ==========================================================
# SAFE MODEL ATTRIBUTE SETTER
# ==========================================================

def set_if_available(
    model,
    field_name,
    value
):
    """
    Set a database model field only if that
    field exists on the SQLAlchemy model.

    This keeps sync.py tolerant of fields that
    may differ between database versions.
    """

    if hasattr(
        model,
        field_name
    ):

        setattr(
            model,
            field_name,
            value
        )


# ==========================================================
# SET SYNC
# ==========================================================

def sync_sets(db):
    print(
        "Syncing sets..."
    )

    if not os.path.exists(
        SETS_PATH
    ):
        print(
            "Set data not found:",
            SETS_PATH
        )

        return 0

    with open(
        SETS_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        sets_data = json.load(
            file
        )

    existing_sets = {
        pokemon_set.id:
            pokemon_set

        for pokemon_set
        in db.query(Set).all()
    }

    total_sets = 0

    for set_data in sets_data:

        set_id = set_data.get(
            "id"
        )

        if not set_id:
            continue

        existing = (
            existing_sets.get(
                set_id
            )
        )

        if existing:

            pokemon_set = existing

        else:

            pokemon_set = Set()

            set_if_available(
                pokemon_set,
                "id",
                set_id
            )

            db.add(
                pokemon_set
            )

            existing_sets[
                set_id
            ] = pokemon_set

        set_if_available(
            pokemon_set,
            "name",
            set_data.get(
                "name"
            )
        )

        set_if_available(
            pokemon_set,
            "series",
            set_data.get(
                "series"
            )
        )

        set_if_available(
            pokemon_set,
            "printed_total",
            set_data.get(
                "printedTotal"
            )
        )

        set_if_available(
            pokemon_set,
            "total",
            set_data.get(
                "total"
            )
        )

        set_if_available(
            pokemon_set,
            "ptcgo_code",
            set_data.get(
                "ptcgoCode"
            )
        )

        set_if_available(
            pokemon_set,
            "release_date",
            set_data.get(
                "releaseDate"
            )
        )

        total_sets += 1

    db.commit()

    print(
        f"Sets synced: "
        f"{total_sets}"
    )

    return total_sets


# ==========================================================
# CARD SYNC
# ==========================================================

def sync_cards(db):
    print(
        "Syncing cards..."
    )

    if not os.path.exists(
        CARDS_DIR
    ):

        print(
            "Card data folder "
            "not found:",
            CARDS_DIR
        )

        return 0

    # ------------------------------------------------------
    # Load existing cards ONCE
    # ------------------------------------------------------

    existing_cards = {
        card.id: card

        for card
        in db.query(Card).all()
    }

    print(
        f"Loaded "
        f"{len(existing_cards)} "
        f"existing cards into memory."
    )

    total_cards = 0

    filenames = sorted(
        os.listdir(
            CARDS_DIR
        )
    )

    for filename in filenames:

        if not filename.lower().endswith(
            ".json"
        ):
            continue

        file_path = os.path.join(
            CARDS_DIR,
            filename
        )

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                cards = json.load(
                    file
                )

        except Exception as error:

            print(
                "Could not read:",
                filename,
                error
            )

            continue

        set_ref = os.path.splitext(
            filename
        )[0]

        for card_data in cards:

            card_id = card_data.get(
                "id"
            )

            if not card_id:
                continue

            existing = (
                existing_cards.get(
                    card_id
                )
            )

            if existing:

                card = existing

            else:

                card = Card()

                set_if_available(
                    card,
                    "id",
                    card_id
                )

                db.add(
                    card
                )

                existing_cards[
                    card_id
                ] = card

            subtypes = (
                card_data.get(
                    "subtypes"
                )
                or []
            )

            subtype = (
                subtypes[0]
                if subtypes
                else None
            )

            image_url = (
                card_data
                .get(
                    "images",
                    {}
                )
                .get(
                    "small"
                )
            )

            # IMPORTANT:
            # Recalculate this every sync.
            #
            # Do NOT reuse an old stored
            # gameplay_key. If our fingerprint
            # algorithm improves, old cards need
            # to receive the new key.
            gameplay_key = (
                build_gameplay_key(
                    card_data
                )
            )

            # --------------------------------------------------
            # Core card fields
            # --------------------------------------------------

            set_if_available(
                card,
                "name",
                card_data.get(
                    "name"
                )
            )

            set_if_available(
                card,
                "supertype",
                card_data.get(
                    "supertype"
                )
            )

            set_if_available(
                card,
                "subtype",
                subtype
            )

            set_if_available(
                card,
                "hp",
                card_data.get(
                    "hp"
                )
            )

            set_if_available(
                card,
                "set_id",
                card_data.get(
                    "set",
                    {}
                ).get(
                    "id",
                    set_ref
                )
            )

            set_if_available(
                card,
                "number",
                card_data.get(
                    "number"
                )
            )

            set_if_available(
                card,
                "rarity",
                card_data.get(
                    "rarity"
                )
            )

            set_if_available(
                card,
                "artist",
                card_data.get(
                    "artist"
                )
            )

            set_if_available(
                card,
                "image_url",
                image_url
            )

            set_if_available(
                card,
                "gameplay_key",
                gameplay_key
            )

            # --------------------------------------------------
            # Extra fields, if your Card model has them
            # --------------------------------------------------

            set_if_available(
                card,
                "types",
                json.dumps(
                    card_data.get(
                        "types"
                    )
                    or []
                )
            )

            set_if_available(
                card,
                "rules",
                json.dumps(
                    card_data.get(
                        "rules"
                    )
                    or []
                )
            )

            set_if_available(
                card,
                "retreat_cost",
                json.dumps(
                    card_data.get(
                        "retreatCost"
                    )
                    or []
                )
            )

            set_if_available(
                card,
                "converted_retreat_cost",
                card_data.get(
                    "convertedRetreatCost"
                )
            )

            set_if_available(
                card,
                "evolves_from",
                card_data.get(
                    "evolvesFrom"
                )
            )

            total_cards += 1

    db.commit()

    print(
        f"Cards synced: "
        f"{total_cards}"
    )

    return total_cards


# ==========================================================
# SYNC EVERYTHING
# ==========================================================

def sync_all():
    db = SessionLocal()

    try:

        sync_sets(
            db
        )

        sync_cards(
            db
        )

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()