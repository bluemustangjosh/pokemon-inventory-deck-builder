from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QListWidget,
    QLineEdit,
    QMessageBox,
    QFrame
)

from PyQt6.QtCore import Qt

from db import (
    find_card_by_set_and_number,
    get_inventory_quantity,
    save_deck,
    get_saved_decks,
    get_deck,
    update_deck,
    delete_deck
)


class DecklistPage(QWidget):
    def __init__(self):
        super().__init__()

        self.current_deck_id = None

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            40,
            30,
            40,
            30
        )

        main_layout.setSpacing(
            18
        )

        # --------------------------------------------------
        # Top Bar
        # --------------------------------------------------

        top_bar = QHBoxLayout()

        back_button = QPushButton(
            "← Back"
        )

        back_button.setFixedWidth(
            120
        )

        back_button.clicked.connect(
            self.go_home
        )

        top_bar.addWidget(
            back_button
        )

        top_bar.addStretch()

        main_layout.addLayout(
            top_bar
        )

        # --------------------------------------------------
        # Header
        # --------------------------------------------------

        title = QLabel(
            "Deck Checker"
        )

        title.setStyleSheet("""
            font-size: 30px;
            font-weight: 700;
        """)

        main_layout.addWidget(
            title
        )

        subtitle = QLabel(
            "Save decklists and compare them against your collection"
        )

        subtitle.setStyleSheet("""
            color: #9ba3af;
            font-size: 14px;
        """)

        main_layout.addWidget(
            subtitle
        )

        # --------------------------------------------------
        # Main Content
        # --------------------------------------------------

        content_layout = QHBoxLayout()

        content_layout.setSpacing(
            20
        )

        # ==================================================
        # LEFT SIDE
        # Saved Decks
        # ==================================================

        saved_panel = QFrame()

        saved_panel.setFixedWidth(
            280
        )

        saved_panel.setStyleSheet("""
            QFrame {
                background-color: #1f232c;
                border: 1px solid #333946;
                border-radius: 12px;
            }
        """)

        saved_layout = QVBoxLayout(
            saved_panel
        )

        saved_layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        saved_layout.setSpacing(
            12
        )

        saved_title = QLabel(
            "Saved Decks"
        )

        saved_title.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
        """)

        saved_layout.addWidget(
            saved_title
        )

        self.saved_decks_list = QListWidget()

        self.saved_decks_list.itemClicked.connect(
            self.load_saved_deck
        )

        saved_layout.addWidget(
            self.saved_decks_list
        )

        new_deck_button = QPushButton(
            "+ New Deck"
        )

        new_deck_button.clicked.connect(
            self.new_deck
        )

        saved_layout.addWidget(
            new_deck_button
        )

        delete_button = QPushButton(
            "Delete Deck"
        )

        delete_button.clicked.connect(
            self.delete_current_deck
        )

        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #8b2d36;
            }

            QPushButton:hover {
                background-color: #a43843;
            }

            QPushButton:pressed {
                background-color: #70242b;
            }
        """)

        saved_layout.addWidget(
            delete_button
        )

        content_layout.addWidget(
            saved_panel
        )

        # ==================================================
        # RIGHT SIDE
        # Deck Editor
        # ==================================================

        editor_panel = QFrame()

        editor_panel.setStyleSheet("""
            QFrame {
                background-color: #1f232c;
                border: 1px solid #333946;
                border-radius: 12px;
            }
        """)

        editor_layout = QVBoxLayout(
            editor_panel
        )

        editor_layout.setContentsMargins(
            22,
            22,
            22,
            22
        )

        editor_layout.setSpacing(
            12
        )

        # --------------------------------------------------
        # Deck Name
        # --------------------------------------------------

        deck_name_label = QLabel(
            "Deck Name"
        )

        deck_name_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
        """)

        editor_layout.addWidget(
            deck_name_label
        )

        self.deck_name_input = QLineEdit()

        self.deck_name_input.setPlaceholderText(
            "Enter deck name..."
        )

        editor_layout.addWidget(
            self.deck_name_input
        )

        # --------------------------------------------------
        # Decklist Input
        # --------------------------------------------------

        decklist_label = QLabel(
            "Limitless Decklist"
        )

        decklist_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
        """)

        editor_layout.addWidget(
            decklist_label
        )

        self.deck_input = QTextEdit()

        self.deck_input.setPlaceholderText(
            "Paste your Limitless decklist here...\n\n"
            "Example:\n"
            "4 Charmander PAF 7\n"
            "3 Charizard ex OBF 125\n"
            "2 Pidgeot ex OBF 164"
        )

        self.deck_input.setMinimumHeight(
            220
        )

        editor_layout.addWidget(
            self.deck_input
        )

        # --------------------------------------------------
        # Action Buttons
        # --------------------------------------------------

        action_layout = QHBoxLayout()

        check_button = QPushButton(
            "Check Deck"
        )

        check_button.clicked.connect(
            self.parse_decklist
        )

        action_layout.addWidget(
            check_button
        )

        self.save_button = QPushButton(
            "Save Deck"
        )

        self.save_button.clicked.connect(
            self.save_current_deck
        )

        action_layout.addWidget(
            self.save_button
        )

        editor_layout.addLayout(
            action_layout
        )

        # --------------------------------------------------
        # Summary Panel
        # --------------------------------------------------

        summary_panel = QFrame()

        summary_panel.setStyleSheet("""
            QFrame {
                background-color: #171a21;
                border: 1px solid #333946;
                border-radius: 10px;
            }
        """)

        summary_layout = QHBoxLayout(
            summary_panel
        )

        summary_layout.setContentsMargins(
            18,
            14,
            18,
            14
        )

        self.tracked_label = QLabel(
            "Tracked Cards: 0"
        )

        self.owned_label = QLabel(
            "Owned: 0"
        )

        self.missing_label = QLabel(
            "Missing: 0"
        )

        self.completion_label = QLabel(
            "Completion: 0%"
        )

        summary_layout.addWidget(
            self.tracked_label
        )

        summary_layout.addStretch()

        summary_layout.addWidget(
            self.owned_label
        )

        summary_layout.addStretch()

        summary_layout.addWidget(
            self.missing_label
        )

        summary_layout.addStretch()

        summary_layout.addWidget(
            self.completion_label
        )

        editor_layout.addWidget(
            summary_panel
        )

        # --------------------------------------------------
        # Results
        # --------------------------------------------------

        results_label = QLabel(
            "Deck Results"
        )

        results_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
        """)

        editor_layout.addWidget(
            results_label
        )

        self.results_list = QListWidget()

        self.results_list.setMinimumHeight(
            260
        )

        editor_layout.addWidget(
            self.results_list
        )

        content_layout.addWidget(
            editor_panel
        )

        main_layout.addLayout(
            content_layout
        )

        self.setLayout(
            main_layout
        )

        self.load_saved_decks()

    # --------------------------------------------------
    # Saved Decks
    # --------------------------------------------------

    def load_saved_decks(self):
        self.saved_decks_list.clear()

        decks = get_saved_decks()

        for deck_id, name in decks:

            self.saved_decks_list.addItem(
                name
            )

            item = self.saved_decks_list.item(
                self.saved_decks_list.count() - 1
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                deck_id
            )

    def load_saved_deck(
        self,
        item
    ):
        deck_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        deck = get_deck(
            deck_id
        )

        if deck is None:
            return

        self.current_deck_id = (
            deck_id
        )

        self.deck_name_input.setText(
            deck["name"]
        )

        self.deck_input.setPlainText(
            deck["raw_text"]
        )

        self.save_button.setText(
            "Update Deck"
        )

        self.parse_decklist()

    def new_deck(self):
        self.current_deck_id = None

        self.deck_name_input.clear()
        self.deck_input.clear()
        self.results_list.clear()

        self.saved_decks_list.clearSelection()

        self.save_button.setText(
            "Save Deck"
        )

        self.reset_summary()

    def save_current_deck(self):
        name = (
            self.deck_name_input
            .text()
            .strip()
        )

        raw_text = (
            self.deck_input
            .toPlainText()
            .strip()
        )

        if not name:

            QMessageBox.warning(
                self,
                "Missing Name",
                "Please enter a deck name."
            )

            return

        if not raw_text:

            QMessageBox.warning(
                self,
                "Missing Decklist",
                "Please paste a decklist first."
            )

            return

        if self.current_deck_id is None:

            save_deck(
                name,
                raw_text
            )

            QMessageBox.information(
                self,
                "Deck Saved",
                f"{name} was saved."
            )

        else:

            update_deck(
                self.current_deck_id,
                name,
                raw_text
            )

            QMessageBox.information(
                self,
                "Deck Updated",
                f"{name} was updated."
            )

        self.load_saved_decks()

    def delete_current_deck(self):
        if self.current_deck_id is None:

            QMessageBox.warning(
                self,
                "No Deck Selected",
                "Please select a saved deck first."
            )

            return

        deck_name = (
            self.deck_name_input
            .text()
            .strip()
        )

        answer = QMessageBox.question(
            self,
            "Delete Deck",
            f"Are you sure you want to delete "
            f"'{deck_name}'?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if (
            answer !=
            QMessageBox.StandardButton.Yes
        ):
            return

        delete_deck(
            self.current_deck_id
        )

        self.current_deck_id = None

        self.deck_name_input.clear()
        self.deck_input.clear()
        self.results_list.clear()

        self.save_button.setText(
            "Save Deck"
        )

        self.reset_summary()

        self.load_saved_decks()

        QMessageBox.information(
            self,
            "Deck Deleted",
            f"{deck_name} was deleted."
        )

    # --------------------------------------------------
    # Deck Checker
    # --------------------------------------------------

    def parse_decklist(self):
        self.results_list.clear()

        raw_text = (
            self.deck_input
            .toPlainText()
        )

        lines = raw_text.splitlines()

        basic_energies = [
            "Grass Energy",
            "Fire Energy",
            "Water Energy",
            "Lightning Energy",
            "Psychic Energy",
            "Fighting Energy",
            "Darkness Energy",
            "Metal Energy"
        ]

        total_tracked = 0
        total_owned = 0
        total_missing = 0

        for line in lines:

            line = line.strip()

            if not line:
                continue

            parts = line.split()

            if not parts[0].isdigit():
                continue

            quantity_needed = int(
                parts[0]
            )

            if len(parts) < 4:
                continue

            set_code = parts[-2]
            card_number = parts[-1]

            card_name_parts = (
                parts[1:-2]
            )

            card_name = " ".join(
                card_name_parts
            )

            # ----------------------------------------------
            # Basic Energy
            # ----------------------------------------------

            if card_name in basic_energies:

                self.results_list.addItem(
                    f"⚡ {card_name}"
                    f"   •   Needed: {quantity_needed}"
                    f"   •   Basic Energy"
                )

                continue

            # ----------------------------------------------
            # Card Lookup
            # ----------------------------------------------

            card = find_card_by_set_and_number(
                set_code,
                card_number
            )

            if card is None:

                self.results_list.addItem(
                    f"⚠ {card_name}"
                    f"   •   Card not found"
                )

                continue

            quantity_owned = (
                get_inventory_quantity(
                    card["id"]
                )
            )

            usable_owned = min(
                quantity_owned,
                quantity_needed
            )

            quantity_missing = max(
                quantity_needed -
                quantity_owned,
                0
            )

            total_tracked += (
                quantity_needed
            )

            total_owned += (
                usable_owned
            )

            total_missing += (
                quantity_missing
            )

            # ----------------------------------------------
            # Result Display
            # ----------------------------------------------

            if quantity_missing == 0:

                status = "✓"

            else:

                status = "✗"

            self.results_list.addItem(
                f"{status} {card_name}"
                f"   •   Needed: {quantity_needed}"
                f"   •   Owned: {quantity_owned}"
                f"   •   Missing: {quantity_missing}"
            )

        # --------------------------------------------------
        # Summary
        # --------------------------------------------------

        if total_tracked > 0:

            completion = (
                total_owned /
                total_tracked
            ) * 100

        else:

            completion = 0

        self.tracked_label.setText(
            f"Tracked Cards: {total_tracked}"
        )

        self.owned_label.setText(
            f"Owned: {total_owned}"
        )

        self.missing_label.setText(
            f"Missing: {total_missing}"
        )

        self.completion_label.setText(
            f"Completion: {completion:.1f}%"
        )

    # --------------------------------------------------
    # Summary Reset
    # --------------------------------------------------

    def reset_summary(self):
        self.tracked_label.setText(
            "Tracked Cards: 0"
        )

        self.owned_label.setText(
            "Owned: 0"
        )

        self.missing_label.setText(
            "Missing: 0"
        )

        self.completion_label.setText(
            "Completion: 0%"
        )

    # --------------------------------------------------
    # Navigation
    # --------------------------------------------------

    def go_home(self):
        self.window().open_home()