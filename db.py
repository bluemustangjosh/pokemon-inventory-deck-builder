# db.py

import sqlite3

from paths import DB_PATH

def search_cards(query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    search = f"%{query.strip()}%"

    cursor.execute("""
        SELECT
            cards.id,
            cards.name,
            COALESCE(sets.name, cards.set_id),
            cards.number,
            sets.printed_total
        FROM cards
        LEFT JOIN sets
            ON cards.set_id = sets.id
        WHERE cards.name LIKE ?
           OR cards.number LIKE ?
           OR cards.set_id LIKE ?
           OR sets.ptcgo_code LIKE ?
           OR sets.name LIKE ?
        ORDER BY
            cards.name ASC,
            cards.set_id DESC
        LIMIT 200
    """, (
        search,
        search,
        search,
        search,
        search
    ))

    results = cursor.fetchall()
    conn.close()

    return results

def get_card_details(card_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, set_id, number, regulation_mark, image_url
        FROM cards
        WHERE id = ?
        LIMIT 1
    """, (card_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "set_id": row[2],
        "number": row[3],
        "regulation": row[4],
        "image_url": row[5]
    }


def add_to_inventory(card_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, quantity
        FROM inventory
        WHERE card_id = ?
        LIMIT 1
    """, (card_id,))

    row = cursor.fetchone()

    if row:
        cursor.execute("""
            UPDATE inventory
            SET quantity = ?
            WHERE id = ?
        """, (row[1] + 1, row[0]))
    else:
        cursor.execute("""
            INSERT INTO inventory (card_id, quantity)
            VALUES (?, 1)
        """, (card_id,))

    conn.commit()
    conn.close()


def get_inventory_quantity(card_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT quantity
        FROM inventory
        WHERE card_id = ?
        LIMIT 1
    """, (card_id,))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else 0

def get_inventory():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            cards.id,
            cards.name,
            COALESCE(
                sets.name,
                cards.set_id
            ),
            CASE
                WHEN sets.printed_total IS NOT NULL
                THEN cards.number || '/' || sets.printed_total
                ELSE cards.number
            END,
            inventory.quantity
        FROM inventory
        JOIN cards
            ON inventory.card_id = cards.id
        LEFT JOIN sets
            ON cards.set_id = sets.id
        WHERE inventory.quantity > 0
        ORDER BY cards.name ASC
    """)

    results = cursor.fetchall()

    conn.close()

    return results

def increase_inventory(card_id):
    add_to_inventory(card_id)


def decrease_inventory(card_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, quantity
        FROM inventory
        WHERE card_id = ?
        LIMIT 1
    """, (card_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return

    inventory_id = row[0]
    quantity = row[1]

    if quantity > 1:
        cursor.execute("""
            UPDATE inventory
            SET quantity = ?
            WHERE id = ?
        """, (quantity - 1, inventory_id))
    else:
        cursor.execute("""
            DELETE FROM inventory
            WHERE id = ?
        """, (inventory_id,))

    conn.commit()
    conn.close()

def find_card_by_set_and_number(
    set_code,
    card_number
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            cards.id,
            cards.name,
            cards.set_id,
            cards.number,
            cards.supertype,
            cards.gameplay_key
        FROM cards
        JOIN sets
            ON cards.set_id = sets.id
        WHERE UPPER(sets.ptcgo_code) = UPPER(?)
          AND cards.number = ?
        LIMIT 1
    """, (
        set_code,
        card_number
    ))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "set_id": row[2],
        "number": row[3],
        "supertype": row[4],
        "gameplay_key": row[5]
    }

def save_deck(name, raw_text):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO decks (name, raw_text)
        VALUES (?, ?)
    """, (name, raw_text))

    conn.commit()
    conn.close()


def get_saved_decks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM decks
        ORDER BY name ASC
    """)

    results = cursor.fetchall()
    conn.close()

    return results


def get_deck(deck_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, raw_text
        FROM decks
        WHERE id = ?
        LIMIT 1
    """, (deck_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "raw_text": row[2]
    }

def update_deck(deck_id, name, raw_text):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE decks
        SET name = ?, raw_text = ?
        WHERE id = ?
    """, (name, raw_text, deck_id))

    conn.commit()
    conn.close()


def delete_deck(deck_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM decks
        WHERE id = ?
    """, (deck_id,))

def get_cards_by_number(card_number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               name,
               set_id,
               number,
               image_url
        FROM cards
        WHERE number = ?
    """, (card_number,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "set_id": row[2],
            "number": row[3],
            "image_url": row[4]
        }
        for row in rows
    ]

def get_cards_by_set_ids(set_ids):
    if not set_ids:
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    placeholders = ",".join(
        "?" for _ in set_ids
    )

    cursor.execute(
        f"""
        SELECT id,
               name,
               set_id,
               number,
               image_url
        FROM cards
        WHERE set_id IN ({placeholders})
        """,
        set_ids
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "set_id": row[2],
            "number": row[3],
            "image_url": row[4]
        }
        for row in rows
    ]

def get_inventory_by_card_name(card_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            cards.id,
            cards.name,
            cards.set_id,
            cards.number,
            inventory.quantity
        FROM inventory
        JOIN cards
            ON inventory.card_id = cards.id
        WHERE LOWER(TRIM(cards.name)) = LOWER(TRIM(?))
          AND inventory.quantity > 0
        ORDER BY cards.set_id, cards.number
    """, (card_name,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_total_inventory_by_card_name(card_name):
    rows = get_inventory_by_card_name(card_name)

    return sum(
        row[4]
        for row in rows
    )

def get_total_inventory_by_card_name(
    card_name,
    supertype
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(
            SUM(inventory.quantity),
            0
        )
        FROM inventory
        JOIN cards
            ON inventory.card_id = cards.id
        WHERE LOWER(TRIM(cards.name))
              = LOWER(TRIM(?))
          AND cards.supertype = ?
    """, (
        card_name,
        supertype
    ))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else 0

def get_total_inventory_by_gameplay_key(
    gameplay_key
):
    if not gameplay_key:
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(
            SUM(inventory.quantity),
            0
        )
        FROM inventory
        JOIN cards
            ON inventory.card_id = cards.id
        WHERE cards.gameplay_key = ?
    """, (gameplay_key,))

    row = cursor.fetchone()

    conn.close()

    return row[0] if row else 0



    conn.commit()
    conn.close()
