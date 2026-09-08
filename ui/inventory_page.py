from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QLineEdit,
    QFrame
)

from PyQt6.QtCore import Qt

from db import get_inventory


class InventoryPage(QWidget):
    def __init__(self):
        super().__init__()

        self.full_inventory = []

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            50,
            35,
            50,
            35
        )

        main_layout.setSpacing(
            20
        )

        # --------------------------------------------------
        # Top Bar
        # --------------------------------------------------

        top_layout = QHBoxLayout()

        back_button = QPushButton(
            "← Back"
        )

        back_button.setFixedWidth(
            120
        )

        back_button.clicked.connect(
            self.go_home
        )

        top_layout.addWidget(
            back_button
        )

        top_layout.addStretch()

        main_layout.addLayout(
            top_layout
        )

        # --------------------------------------------------
        # Header
        # --------------------------------------------------

        title = QLabel(
            "My Inventory"
        )

        title.setStyleSheet("""
            font-size: 30px;
            font-weight: 700;
        """)

        main_layout.addWidget(
            title
        )

        subtitle = QLabel(
            "Browse and manage your Pokémon card collection"
        )

        subtitle.setStyleSheet("""
            color: #9ba3af;
            font-size: 14px;
        """)

        main_layout.addWidget(
            subtitle
        )

        # --------------------------------------------------
        # Stats Panel
        # --------------------------------------------------

        stats_panel = QFrame()

        stats_panel.setStyleSheet("""
            QFrame {
                background-color: #1f232c;
                border: 1px solid #333946;
                border-radius: 12px;
            }
        """)

        stats_layout = QHBoxLayout(
            stats_panel
        )

        stats_layout.setContentsMargins(
            20,
            16,
            20,
            16
        )

        self.unique_cards_label = QLabel(
            "Unique Cards: 0"
        )

        self.unique_cards_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
        """)

        stats_layout.addWidget(
            self.unique_cards_label
        )

        stats_layout.addStretch()

        self.total_cards_label = QLabel(
            "Total Cards: 0"
        )

        self.total_cards_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
        """)

        stats_layout.addWidget(
            self.total_cards_label
        )

        main_layout.addWidget(
            stats_panel
        )

        # --------------------------------------------------
        # Search
        # --------------------------------------------------

        self.search_bar = QLineEdit()

        self.search_bar.setPlaceholderText(
            "Search your inventory..."
        )

        self.search_bar.textChanged.connect(
            self.filter_inventory
        )

        main_layout.addWidget(
            self.search_bar
        )

        # --------------------------------------------------
        # Inventory List
        # --------------------------------------------------

        self.inventory_list = QListWidget()

        self.inventory_list.setMinimumHeight(
            450
        )

        self.inventory_list.itemClicked.connect(
            self.open_card_details
        )

        main_layout.addWidget(
            self.inventory_list
        )

        self.setLayout(
            main_layout
        )

        self.load_inventory()

    # --------------------------------------------------
    # Load Inventory
    # --------------------------------------------------

    def load_inventory(self):
        self.full_inventory = get_inventory()

        unique_cards = len(
            self.full_inventory
        )

        total_cards = sum(
            quantity
            for (
                card_id,
                name,
                set_id,
                number,
                quantity
            ) in self.full_inventory
        )

        self.unique_cards_label.setText(
            f"Unique Cards: {unique_cards}"
        )

        self.total_cards_label.setText(
            f"Total Cards: {total_cards}"
        )

        self.display_inventory(
            self.full_inventory
        )

    # --------------------------------------------------
    # Display Inventory
    # --------------------------------------------------

    def display_inventory(
        self,
        inventory
    ):
        self.inventory_list.clear()

        for (
            card_id,
            name,
            set_id,
            number,
            quantity
        ) in inventory:

            set_display = (
                set_id.upper()
                if set_id
                else "UNKNOWN"
            )

            text = (
                f"{name}   •   "
                f"{set_display} #{number}"
                f"   •   Owned: {quantity}"
            )

            self.inventory_list.addItem(
                text
            )

            item = self.inventory_list.item(
                self.inventory_list.count() - 1
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                card_id
            )

    # --------------------------------------------------
    # Search / Filter
    # --------------------------------------------------

    def filter_inventory(
        self,
        text
    ):
        text = text.strip().lower()

        if not text:
            self.display_inventory(
                self.full_inventory
            )
            return

        filtered = []

        for item in self.full_inventory:

            (
                card_id,
                name,
                set_id,
                number,
                quantity
            ) = item

            searchable_text = (
                f"{name} "
                f"{set_id or ''} "
                f"{number}"
            ).lower()

            if text in searchable_text:
                filtered.append(
                    item
                )

        self.display_inventory(
            filtered
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

    def go_home(self):
        self.window().open_home()