import sqlite3

conn = sqlite3.connect("pokemon.db")
cursor = conn.cursor()

cursor.execute("SELECT name, set_id, number FROM cards WHERE name LIKE '%Pikachu%' LIMIT 10;")
rows = cursor.fetchall()

for r in rows:
    print(r)

conn.close()
