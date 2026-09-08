from sqlalchemy import (
    create_engine, Column, String, Integer, Date, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from paths import DB_PATH

Base = declarative_base()

# -----------------------------
# Set Model
# -----------------------------
class Set(Base):
    __tablename__ = "sets"

    id = Column(String, primary_key=True)
    name = Column(String)
    ptcgo_code = Column(String)
    release_date = Column(String)
    updated_at = Column(String)

    cards = relationship("Card", back_populates="set")

# -----------------------------
# Card Model
# -----------------------------
class Card(Base):
    __tablename__ = "cards"

    id = Column(String, primary_key=True)
    name = Column(String)
    supertype = Column(String)
    subtype = Column(String)
    number = Column(String)
    image_url = Column(String)
    regulation_mark = Column(String)
    set_id = Column(String, ForeignKey("sets.id"))

    set = relationship("Set", back_populates="cards")

# -----------------------------
# Inventory Model
# -----------------------------
class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String, ForeignKey("cards.id"))
    quantity = Column(Integer)

    card = relationship("Card")

# -----------------------------
# Deck Model
# -----------------------------
class Deck(Base):
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    raw_text = Column(Text)

    cards = relationship("DeckCard", back_populates="deck")

# -----------------------------
# DeckCard Model
# -----------------------------
class DeckCard(Base):
    __tablename__ = "deck_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deck_id = Column(Integer, ForeignKey("decks.id"))
    card_id = Column(String, ForeignKey("cards.id"))
    quantity = Column(Integer)

    deck = relationship("Deck", back_populates="cards")
    card = relationship("Card")

# -----------------------------
# Database Setup
# -----------------------------
engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}"
)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
