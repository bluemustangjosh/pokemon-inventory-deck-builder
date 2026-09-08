import os
import sys
import shutil

from pathlib import Path


APP_FOLDER_NAME = "PokemonInventoryDeckBuilder"


# --------------------------------------------------
# Bundled / Read-Only Resources
# --------------------------------------------------

def resource_path(*parts):
    """
    Returns the correct location for bundled files.

    Works both:
    - while running from VS Code
    - after packaging with PyInstaller
    """

    if getattr(sys, "frozen", False):
        base_dir = Path(
            getattr(
                sys,
                "_MEIPASS",
                Path(sys.executable).parent
            )
        )

    else:
        base_dir = Path(
            __file__
        ).resolve().parent

    return base_dir.joinpath(
        *parts
    )


# --------------------------------------------------
# User Data Folder
# --------------------------------------------------

local_appdata = os.getenv(
    "LOCALAPPDATA"
)

if local_appdata:

    APP_DATA_DIR = (
        Path(local_appdata)
        / APP_FOLDER_NAME
    )

else:

    APP_DATA_DIR = (
        Path.home()
        / ".pokemon_inventory_deck_builder"
    )


APP_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------------
# Database
# --------------------------------------------------

DB_PATH = (
    APP_DATA_DIR
    / "pokemon.db"
)


# --------------------------------------------------
# Pokémon Dataset
# --------------------------------------------------

CARDS_DIR = resource_path(
    "data",
    "cards",
    "en"
)

SETS_PATH = resource_path(
    "data",
    "sets",
    "en.json"
)


# --------------------------------------------------
# One-Time Migration
# --------------------------------------------------

def ensure_local_database():
    """
    Copies the existing development database into
    AppData the first time the application uses
    local application storage.
    """

    old_database = (
        Path(__file__)
        .resolve()
        .parent
        / "pokemon.db"
    )

    # If the AppData database already exists,
    # leave it alone.
    if DB_PATH.exists():
        print(
            "Local database already exists:",
            DB_PATH
        )
        return

    # Copy our existing development database
    if old_database.exists():

        shutil.copy2(
            old_database,
            DB_PATH
        )

        print(
            "Existing database migrated to:",
            DB_PATH
        )

    else:

        print(
            "No existing database found. "
            "A new database will be created."
        )