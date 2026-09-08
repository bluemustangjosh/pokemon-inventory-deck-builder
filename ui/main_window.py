from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QIcon

from ui.home_page import HomePage
from ui.card_details_page import CardDetailsPage
from ui.inventory_page import InventoryPage
from ui.decklist_page import DecklistPage

from version import APP_NAME, APP_VERSION
from paths import resource_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # --------------------------------------------------
        # Window Settings
        # --------------------------------------------------

        self.setWindowTitle(
            f"{APP_NAME} v{APP_VERSION}"
        )

        self.setWindowIcon(
            QIcon(
                str(
                    resource_path(
                        "assets",
                        "app_icon.png"
                    )
                )
            )
        )

        self.setMinimumSize(
            1200,
            800
        )

        # --------------------------------------------------
        # Home Page
        # --------------------------------------------------

        self.home_page = HomePage()

        self.setCentralWidget(
            self.home_page
        )

    # --------------------------------------------------
    # Card Details
    # --------------------------------------------------

    def open_card_details(
        self,
        card_id
    ):
        self.details_page = CardDetailsPage(
            card_id
        )

        self.setCentralWidget(
            self.details_page
        )

    # --------------------------------------------------
    # Inventory
    # --------------------------------------------------

    def open_inventory(self):
        self.inventory_page = InventoryPage()

        self.setCentralWidget(
            self.inventory_page
        )

    # --------------------------------------------------
    # Deck Checker
    # --------------------------------------------------

    def open_decklist(self):
        self.decklist_page = DecklistPage()

        self.setCentralWidget(
            self.decklist_page
        )

    # --------------------------------------------------
    # Home
    # --------------------------------------------------

    def open_home(self):
        self.home_page = HomePage()

        self.setCentralWidget(
            self.home_page
        )