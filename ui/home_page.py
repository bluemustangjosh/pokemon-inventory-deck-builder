from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QFrame
)

from PyQt6.QtCore import Qt

from db import search_cards


class HomePage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(
            60,
            40,
            60,
            40
        )

        main_layout.setSpacing(25)

        # --------------------------------------------------
        # Header
        # --------------------------------------------------

        title = QLabel(
            "Pokémon Inventory & Deck Builder"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
        """)

        main_layout.addWidget(title)

        subtitle = QLabel(
            "Manage your collection and build decks"
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtitle.setStyleSheet("""
            color: #9ba3af;
            font-size: 15px;
        """)

        main_layout.addWidget(subtitle)

        # --------------------------------------------------
        # Feature Buttons
        # --------------------------------------------------

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        inventory_button = self.create_feature_button(
            "My Inventory",
            "View and manage your owned cards"
        )

        inventory_button.clicked.connect(
            self.open_inventory
        )

        buttons_layout.addWidget(
            inventory_button
        )

        deck_button = self.create_feature_button(
            "Deck Checker",
            "Check saved decks against your collection"
        )

        deck_button.clicked.connect(
            self.open_decklist
        )

        buttons_layout.addWidget(
            deck_button
        )

        scanner_button = self.create_feature_button(
            "Card Scanner",
            "Experimental scanner coming in a future update"
        )

        scanner_button.setEnabled(
            False
        )

        buttons_layout.addWidget(
            scanner_button
        )

        main_layout.addLayout(
            buttons_layout
        )

        # --------------------------------------------------
        # Search Panel
        # --------------------------------------------------

        search_panel = QFrame()

        search_panel.setStyleSheet("""
            QFrame {
                background-color: #1f232c;
                border: 1px solid #333946;
                border-radius: 12px;
            }
        """)

        search_layout = QVBoxLayout(
            search_panel
        )

        search_layout.setContentsMargins(
            25,
            20,
            25,
            20
        )

        search_layout.setSpacing(
            12
        )

        search_title = QLabel(
            "Search Cards"
        )

        search_title.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
        """)

        search_layout.addWidget(
            search_title
        )

        self.search_bar = QLineEdit()

        self.search_bar.setPlaceholderText(
            "Search by card name..."
        )

        self.search_bar.textChanged.connect(
            self.perform_search
        )

        search_layout.addWidget(
            self.search_bar
        )

        self.results_list = QListWidget()

        self.results_list.setMinimumHeight(
            300
        )

        self.results_list.itemClicked.connect(
            self.open_card_details
        )

        search_layout.addWidget(
            self.results_list
        )

        main_layout.addWidget(
            search_panel
        )

        self.setLayout(
            main_layout
        )

    # --------------------------------------------------
    # Feature Button Helper
    # --------------------------------------------------

    def create_feature_button(
        self,
        title,
        description
    ):
        button = QPushButton(
            f"{title}\n{description}"
        )

        button.setMinimumHeight(
            100
        )

        button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 18px;
                font-size: 15px;
                border-radius: 12px;
            }
        """)

        return button

    # --------------------------------------------------
    # Search
    # --------------------------------------------------

    def perform_search(
        self,
        text
    ):
        self.results_list.clear()

        if not text.strip():
            return

        results = search_cards(
            text
        )

        for (
            card_id,
            name,
            set_id,
            number
        ) in results:

            set_display = (
                set_id.upper()
                if set_id
                else "UNKNOWN"
            )

            item_text = (
                f"{name}   •   "
                f"{set_display} #{number}"
            )

            self.results_list.addItem(
                item_text
            )

            item = self.results_list.item(
                self.results_list.count() - 1
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                card_id
            )

    # --------------------------------------------------
    # Navigation
    # --------------------------------------------------

    def open_card_details(
        self,
        item
    ):
        card_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        self.window().open_card_details(
            card_id
        )

    def open_inventory(self):
        self.window().open_inventory()

    def open_decklist(self):
        self.window().open_decklist()