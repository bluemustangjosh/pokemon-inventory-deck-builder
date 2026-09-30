import os
import hashlib
import re
import json
from database.models import (
    SessionLocal, Set, Card
)
from paths import (
    CARDS_DIR,
    SETS_PATH
)

def normalize_text(value):
    if value is None:
        return ""

    value = str(value)

    # Normalize spacing so harmless formatting
    # differences do not create different keys.
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


def build_gameplay_key(card_data):
    # Only Pokémon need gameplay-equivalence
    # grouping right now.
    if card_data.get("supertype") != "Pokémon":
        return None

    abilities = []

    for ability in card_data.get(
        "abilities",
        []
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

    attacks = []

    for attack in card_data.get(
        "attacks",
        []
    ):
        attacks.append({
            "name": normalize_text(
                attack.get("name")
            ),
            "cost": normalize_list(
                attack.get("cost")
            ),
            "converted_energy_cost":
                attack.get(
                    "convertedEnergyCost",
                    0
                ),
            "damage": normalize_text(
                attack.get("damage")
            ),
            "text": normalize_text(
                attack.get("text")
            )
        })

    weaknesses = []

    for weakness in card_data.get(
        "weaknesses",
        []
    ):
        weaknesses.append({
            "type": normalize_text(
                weakness.get("type")
            ),
            "value": normalize_text(
                weakness.get("value")
            )
        })

    resistances = []

    for resistance in card_data.get(
        "resistances",
        []
    ):
        resistances.append({
            "type": normalize_text(
                resistance.get("type")
            ),
            "value": normalize_text(
                resistance.get("value")
            )
        })

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
            card_data.get("evolvesFrom")
        ),

        "abilities": abilities,

        "attacks": attacks,

        "weaknesses": weaknesses,

        "resistances": resistances,

        "retreat_cost": normalize_list(
            card_data.get("retreatCost")
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
        serialized.encode("utf-8")
    ).hexdigest()

def sync_all():
    db = SessionLocal()

    print("Loading local dataset...")

    # -----------------------------
    # Sync Sets
    # -----------------------------
    sets_path = SETS_PATH

    with open(sets_path, "r", encoding="utf-8") as f:
        sets = json.load(f)

    for s in sets:
        set_id = s.get("id")

        existing_set = db.query(Set).filter(Set.id == set_id).first()

        if existing_set:
            existing_set.name = s.get("name")
            existing_set.ptcgo_code = s.get("ptcgoCode")
            existing_set.printed_total = s.get("printedTotal")
            existing_set.release_date = s.get("releaseDate")
            existing_set.updated_at = s.get("updatedAt")
        else:
            new_set = Set(
                id=set_id,
                name=s.get("name"),
                ptcgo_code=s.get("ptcgoCode"),
                printed_total=s.get("printedTotal"),
                release_date=s.get("releaseDate"),
                updated_at=s.get("updatedAt")
            )

            db.add(new_set)

    db.commit()

    print(f"Synced {len(sets)} sets.")

    # -----------------------------
    # Preload Existing Cards
    # -----------------------------
    existing_cards = {
        card.id: card
        for card in db.query(Card).all()
    }

    print(
        f"Loaded {len(existing_cards)} "
        f"existing cards into memory."
    )

    # -----------------------------
    # Sync Cards (one file per set)
    # -----------------------------
    cards_folder = CARDS_DIR

    set_files = [
        f for f in os.listdir(cards_folder)
        if f.endswith(".json")
    ]

    total_cards = 0

    for filename in set_files:
        path = os.path.join(cards_folder, filename)

        with open(path, "r", encoding="utf-8") as f:
            cards = json.load(f)

        set_ref = os.path.splitext(filename)[0]

        for c in cards:
            card_id = c.get("id")

            existing = existing_cards.get(
                card_id
            )

            subtype = (
                c.get("subtypes")[0]
                if c.get("subtypes")
                else None
            )

            image_url = (
                c.get("images", {}).get("small")
            )

            set_ref = os.path.splitext(
                filename
            )[0]

            # Only calculate the gameplay key
            # if this card does not already have one.
            if (
                existing
                and existing.gameplay_key
            ):
                gameplay_key = (
                    existing.gameplay_key
                )
            else:
                gameplay_key = (
                    build_gameplay_key(c)
                )

                if existing:
                    existing.name = c.get("name")
                    existing.supertype = c.get("supertype")
                    existing.subtype = subtype
                    existing.number = c.get("number")
                    existing.image_url = image_url
                    existing.regulation_mark = c.get("regulationMark")
                    existing.set_id = set_ref
                    existing.gameplay_key = gameplay_key

                else:
                    new_card = Card(
                        id=card_id,
                        name=c.get("name"),
                        supertype=c.get("supertype"),
                        subtype=subtype,
                        number=c.get("number"),
                        image_url=image_url,
                        regulation_mark=c.get("regulationMark"),
                        set_id=set_ref,
                        gameplay_key=gameplay_key
                    )

                    db.add(new_card)

                total_cards += 1
            
            if existing:
                existing.name = c.get("name")
                existing.supertype = c.get("supertype")
                existing.subtype = subtype
                existing.number = c.get("number")
                existing.image_url = image_url
                existing.regulation_mark = c.get("regulationMark")
                existing.set_id = set_ref
                existing.gameplay_key = gameplay_key

            else:
                new_card = Card(
                    id=card_id,
                    name=c.get("name"),
                    supertype=c.get("supertype"),
                    subtype=subtype,
                    number=c.get("number"),
                    image_url=image_url,
                    regulation_mark=c.get("regulationMark"),
                    set_id=set_ref,
                    gameplay_key=gameplay_key
                )

                db.add(new_card)

                existing_cards[card_id] = new_card

                total_cards += 1

    db.commit()
    db.close()
    print("Local dataset sync complete.")
