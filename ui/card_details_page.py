from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame
)

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

import requests

from db import (
    get_card_details,
    increase_inventory,
    decrease_inventory,
    get_inventory_quantity
)


class CardDetailsPage(QWidget):
    def __init__(self, card_id):
        super().__init__()

        self.card_id = card_id
        self.card = get_card_details(
            card_id
        )

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
        # Back Button
        # --------------------------------------------------

        back_button = QPushButton(
            "← Back"
        )

        back_button.setFixedWidth(
            120
        )

        back_button.clicked.connect(
            self.go_home
        )

        main_layout.addWidget(
            back_button,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        # --------------------------------------------------
        # Card Not Found
        # --------------------------------------------------

        if self.card is None:

            error_label = QLabel(
                "Card not found in database."
            )

            error_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            error_label.setStyleSheet("""
                font-size: 20px;
                color: #ff6b6b;
            """)

            main_layout.addWidget(
                error_label
            )

            self.setLayout(
                main_layout
            )

            return

        # --------------------------------------------------
        # Main Card Panel
        # --------------------------------------------------

        card_panel = QFrame()

        card_panel.setStyleSheet("""
            QFrame {
                background-color: #1f232c;
                border: 1px solid #333946;
                border-radius: 14px;
            }
        """)

        content_layout = QHBoxLayout(
            card_panel
        )

        content_layout.setContentsMargins(
            30,
            30,
            30,
            30
        )

        content_layout.setSpacing(
            40
        )

        # --------------------------------------------------
        # Card Image
        # --------------------------------------------------

        image_section = QVBoxLayout()

        self.image_label = QLabel(
            "Loading image..."
        )

        self.image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.image_label.setFixedSize(
            360,
            500
        )

        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #171a21;
                border: 1px solid #333946;
                border-radius: 12px;
            }
        """)

        self.load_card_image()

        image_section.addWidget(
            self.image_label
        )

        content_layout.addLayout(
            image_section
        )

        # --------------------------------------------------
        # Information Section
        # --------------------------------------------------

        info_layout = QVBoxLayout()

        info_layout.setSpacing(
            18
        )

        name_label = QLabel(
            self.card["name"]
        )

        name_label.setWordWrap(
            True
        )

        name_label.setStyleSheet("""
            font-size: 30px;
            font-weight: 700;
        """)

        info_layout.addWidget(
            name_label
        )

        set_display = (
            self.card["set_id"].upper()
            if self.card["set_id"]
            else "UNKNOWN"
        )

        set_label = QLabel(
            f"{set_display}  •  #{self.card['number']}"
        )

        set_label.setStyleSheet("""
            color: #9ba3af;
            font-size: 17px;
        """)

        info_layout.addWidget(
            set_label
        )

        regulation_display = (
            self.card["regulation"]
            if self.card["regulation"]
            else "None"
        )

        regulation_label = QLabel(
            f"Regulation Mark: {regulation_display}"
        )

        regulation_label.setStyleSheet("""
            font-size: 15px;
        """)

        info_layout.addWidget(
            regulation_label
        )

        # --------------------------------------------------
        # Inventory Panel
        # --------------------------------------------------

        inventory_panel = QFrame()

        inventory_panel.setStyleSheet("""
            QFrame {
                background-color: #171a21;
                border: 1px solid #333946;
                border-radius: 10px;
            }
        """)

        inventory_layout = QVBoxLayout(
            inventory_panel
        )

        inventory_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        inventory_title = QLabel(
            "Inventory"
        )

        inventory_title.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
        """)

        inventory_layout.addWidget(
            inventory_title
        )

        self.quantity_label = QLabel()

        self.quantity_label.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
        """)

        inventory_layout.addWidget(
            self.quantity_label
        )

        self.refresh_quantity()

        # --------------------------------------------------
        # Quantity Buttons
        # --------------------------------------------------

        buttons_layout = QHBoxLayout()

        remove_button = QPushButton(
            "− Remove"
        )

        remove_button.clicked.connect(
            self.decrease_quantity
        )

        buttons_layout.addWidget(
            remove_button
        )

        add_button = QPushButton(
            "+ Add"
        )

        add_button.clicked.connect(
            self.increase_quantity
        )

        buttons_layout.addWidget(
            add_button
        )

        inventory_layout.addLayout(
            buttons_layout
        )

        info_layout.addWidget(
            inventory_panel
        )

        info_layout.addStretch()

        content_layout.addLayout(
            info_layout
        )

        main_layout.addWidget(
            card_panel
        )

        self.setLayout(
            main_layout
        )

    # --------------------------------------------------
    # Load Card Image
    # --------------------------------------------------

    def load_card_image(self):
        image_url = self.card[
            "image_url"
        ]

        if not image_url:

            self.image_label.setText(
                "No image available"
            )

            return

        try:

            response = requests.get(
                image_url,
                timeout=10
            )

            response.raise_for_status()

            pixmap = QPixmap()

            pixmap.loadFromData(
                response.content
            )

            if pixmap.isNull():

                self.image_label.setText(
                    "Unable to load image"
                )

                return

            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.image_label.setPixmap(
                scaled_pixmap
            )

        except Exception:

            self.image_label.setText(
                "Unable to load image"
            )

    # --------------------------------------------------
    # Inventory
    # --------------------------------------------------

    def refresh_quantity(self):
        quantity = get_inventory_quantity(
            self.card_id
        )

        self.quantity_label.setText(
            f"Owned: {quantity}"
        )

    def increase_quantity(self):
        increase_inventory(
            self.card_id
        )

        self.refresh_quantity()

    def decrease_quantity(self):
        decrease_inventory(
            self.card_id
        )

        self.refresh_quantity()

    # --------------------------------------------------
    # Navigation
    # --------------------------------------------------

    def go_home(self):
        self.window().open_home()