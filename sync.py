import os
import json
from database.models import (
    SessionLocal, Set, Card
)
from paths import (
    CARDS_DIR,
    SETS_PATH
)

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
            existing_set.release_date = s.get("releaseDate")
            existing_set.updated_at = s.get("updatedAt")
        else:
            new_set = Set(
                id=set_id,
                name=s.get("name"),
                ptcgo_code=s.get("ptcgoCode"),
                release_date=s.get("releaseDate"),
                updated_at=s.get("updatedAt")
            )

            db.add(new_set)

    db.commit()

    print(f"Synced {len(sets)} sets.")

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
            existing = db.query(Card).filter(Card.id == card_id).first()

            subtype = c.get("subtypes")[0] if c.get("subtypes") else None
            image_url = c.get("images", {}).get("small")
            set_ref = os.path.splitext(filename)[0]

            if existing:
                existing.name = c.get("name")
                existing.supertype = c.get("supertype")
                existing.subtype = subtype
                existing.number = c.get("number")
                existing.image_url = image_url
                existing.regulation_mark = c.get("regulationMark")
                existing.set_id = set_ref
            else:
                new_card = Card(
                    id=card_id,
                    name=c.get("name"),
                    supertype=c.get("supertype"),
                    subtype=subtype,
                    number=c.get("number"),
                    image_url=image_url,
                    regulation_mark=c.get("regulationMark"),
                    set_id=set_ref
                )
                db.add(new_card)

            total_cards += 1

    db.commit()
    db.close()
    print("Local dataset sync complete.")
