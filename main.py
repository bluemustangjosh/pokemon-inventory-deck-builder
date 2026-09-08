import sys

from PyQt6.QtWidgets import QApplication

from paths import (
    ensure_local_database,
    DB_PATH
)

from ui.styles import APP_STYLE


def main():

    # --------------------------------------------------
    # FIRST: migrate/create user database
    # --------------------------------------------------

    ensure_local_database()

    print(
        "Database:",
        DB_PATH
    )

    # --------------------------------------------------
    # IMPORTANT:
    # Import database models only AFTER migration.
    #
    # This prevents SQLite/SQLAlchemy from creating
    # an empty database before our old database is copied.
    # --------------------------------------------------

    from database.models import init_db
    from sync import sync_all
    from ui.main_window import MainWindow

    # Make sure tables exist
    init_db()

    # --------------------------------------------------
    # Sync Pokemon Data
    # --------------------------------------------------

    print(
        "Checking for updates..."
    )

    sync_all()

    # --------------------------------------------------
    # Start App
    # --------------------------------------------------

    print(
        "Starting app..."
    )

    app = QApplication(
        sys.argv
    )

    app.setStyleSheet(
        APP_STYLE
    )

    window = MainWindow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()