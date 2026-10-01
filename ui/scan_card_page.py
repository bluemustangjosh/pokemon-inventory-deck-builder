import cv2
import numpy as np
import pillow_heif

from PIL import Image, ImageOps

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
)

from scanner.visual_search import (
    load_visual_index,
    find_closest_cards,
    rerank_candidates_with_orb,
)


# Enable iPhone HEIC / HEIF images.
pillow_heif.register_heif_opener()


class ScanCardPage(QWidget):

    def __init__(self):
        super().__init__()

        self.selected_image_path = None
        self.selected_image = None
        self.normalized_image = None

        self.visual_index = (
            load_visual_index()
        )

        print(
            "Scanner visual fingerprints:",
            len(self.visual_index)
        )

        self.build_ui()

    # ==================================================
    # UI
    # ==================================================

    def build_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            30,
            30,
            30,
            30
        )

        layout.setSpacing(15)

        # ----------------------------------------------
        # Title
        # ----------------------------------------------

        title = QLabel(
            "Card Scanner 2.0"
        )

        title.setStyleSheet("""
            font-size: 26px;
            font-weight: 700;
        """)

        layout.addWidget(
            title
        )

        subtitle = QLabel(
            "Bare-card visual scanner"
        )

        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #aaaaaa;
        """)

        layout.addWidget(
            subtitle
        )

        # ----------------------------------------------
        # Image Preview
        # ----------------------------------------------

        self.image_label = QLabel(
            "Choose a card image to begin."
        )

        self.image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.image_label.setMinimumSize(
            400,
            500
        )

        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #555555;
                border-radius: 8px;
                background-color: #111111;
                padding: 10px;
            }
        """)

        layout.addWidget(
            self.image_label,
            stretch=1
        )

        # ----------------------------------------------
        # Status
        # ----------------------------------------------

        self.status_label = QLabel(
            "Status: Waiting for image"
        )

        self.status_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.status_label
        )

        # ----------------------------------------------
        # Buttons
        # ----------------------------------------------

        buttons = QHBoxLayout()

        self.choose_button = QPushButton(
            "Choose Image"
        )

        self.choose_button.clicked.connect(
            self.choose_image
        )

        buttons.addWidget(
            self.choose_button
        )

        self.scan_button = QPushButton(
            "Scan Card"
        )

        self.scan_button.setEnabled(
            False
        )

        self.scan_button.clicked.connect(
            self.scan_card
        )

        buttons.addWidget(
            self.scan_button
        )

        self.home_button = QPushButton(
            "Back Home"
        )

        self.home_button.clicked.connect(
            self.go_home
        )

        buttons.addWidget(
            self.home_button
        )

        layout.addLayout(
            buttons
        )

    # ==================================================
    # IMAGE LOADING
    # ==================================================

    def choose_image(self):
        file_path, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Choose Pokémon Card Image",
                "",
                (
                    "Card Images "
                    "(*.png *.jpg *.jpeg "
                    "*.bmp *.webp "
                    "*.heic *.heif)"
                )
            )
        )

        if not file_path:
            return

        try:
            image = Image.open(
                file_path
            )

            # Fix iPhone rotation metadata.
            image = ImageOps.exif_transpose(
                image
            )

            image = image.convert(
                "RGB"
            )

            self.selected_image_path = (
                file_path
            )

            self.selected_image = image
            self.normalized_image = None

            self.show_image(
                image
            )

            self.status_label.setText(
                "Status: Image loaded. "
                "Ready to scan."
            )

            self.scan_button.setEnabled(
                True
            )

            print()
            print(
                "============================"
            )
            print(
                "SCANNER 2.0 - IMAGE LOADED"
            )
            print(
                "============================"
            )
            print(
                "File:",
                file_path
            )
            print(
                "Size:",
                image.size
            )

        except Exception as error:

            self.selected_image_path = None
            self.selected_image = None
            self.normalized_image = None

            self.scan_button.setEnabled(
                False
            )

            QMessageBox.warning(
                self,
                "Image Error",
                (
                    "The image could not "
                    "be opened.\n\n"
                    f"{error}"
                )
            )

    # ==================================================
    # IMAGE DISPLAY
    # ==================================================

    def show_image(self, image):
        image = image.convert(
            "RGB"
        )

        width, height = (
            image.size
        )

        data = image.tobytes(
            "raw",
            "RGB"
        )

        qimage = QImage(
            data,
            width,
            height,
            width * 3,
            QImage.Format.Format_RGB888
        )

        # Qt gets its own memory copy.
        qimage = qimage.copy()

        pixmap = QPixmap.fromImage(
            qimage
        )

        pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.image_label.setPixmap(
            pixmap
        )

    # ==================================================
    # CORNER ORDERING
    # ==================================================

    def order_points(
        self,
        points
    ):
        ordered = np.zeros(
            (4, 2),
            dtype="float32"
        )

        point_sum = points.sum(
            axis=1
        )

        point_difference = np.diff(
            points,
            axis=1
        ).flatten()

        # Top-left
        ordered[0] = points[
            np.argmin(
                point_sum
            )
        ]

        # Top-right
        ordered[1] = points[
            np.argmin(
                point_difference
            )
        ]

        # Bottom-right
        ordered[2] = points[
            np.argmax(
                point_sum
            )
        ]

        # Bottom-left
        ordered[3] = points[
            np.argmax(
                point_difference
            )
        ]

        return ordered

    # ==================================================
    # BARE CARD DETECTION
    # ==================================================

    def detect_bare_card(
        self,
        image
    ):
        rgb = np.array(
            image.convert("RGB")
        )

        original_height, original_width = (
            rgb.shape[:2]
        )

        # ----------------------------------------------
        # Work on a smaller image for detection.
        # ----------------------------------------------

        max_height = 1200

        if original_height > max_height:

            scale = (
                max_height
                / original_height
            )

            small_width = int(
                original_width
                * scale
            )

            small = cv2.resize(
                rgb,
                (
                    small_width,
                    max_height
                ),
                interpolation=cv2.INTER_AREA
            )

        else:

            scale = 1.0

            small = rgb.copy()

        gray = cv2.cvtColor(
            small,
            cv2.COLOR_RGB2GRAY
        )

        gray = cv2.GaussianBlur(
            gray,
            (7, 7),
            0
        )

        image_area = (
            small.shape[0]
            * small.shape[1]
        )

        best_box = None
        best_score = -1

        # ----------------------------------------------
        # Try several brightness thresholds.
        #
        # Bare cards should usually separate from
        # a light desk / paper / scanning background.
        # ----------------------------------------------

        thresholds = (
            90,
            110,
            130,
            150,
            170,
            190,
            210,
        )

        for threshold_value in thresholds:

            _, mask = cv2.threshold(
                gray,
                threshold_value,
                255,
                cv2.THRESH_BINARY_INV
            )

            # Join fragmented regions inside
            # the Pokémon card.
            kernel = cv2.getStructuringElement(
                cv2.MORPH_RECT,
                (17, 17)
            )

            mask = cv2.morphologyEx(
                mask,
                cv2.MORPH_CLOSE,
                kernel
            )

            contours, _ = cv2.findContours(
                mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            for contour in contours:

                contour_area = cv2.contourArea(
                    contour
                )

                # Ignore tiny shapes immediately.
                if contour_area < (
                    image_area * 0.05
                ):
                    continue

                rect = cv2.minAreaRect(
                    contour
                )

                rect_width, rect_height = (
                    rect[1]
                )

                if (
                    rect_width <= 0
                    or rect_height <= 0
                ):
                    continue

                short_side = min(
                    rect_width,
                    rect_height
                )

                long_side = max(
                    rect_width,
                    rect_height
                )

                ratio = (
                    short_side
                    / long_side
                )

                rect_area = (
                    rect_width
                    * rect_height
                )

                area_ratio = (
                    rect_area
                    / image_area
                )

                # Pokémon cards are about:
                #
                # 2.5 / 3.5 = 0.714
                #
                # Give perspective distortion
                # some breathing room.
                if not (
                    0.60 <= ratio <= 0.82
                ):
                    continue

                # The card should take up a meaningful
                # amount of the photograph.
                if not (
                    0.30 <= area_ratio <= 0.98
                ):
                    continue

                # --------------------------------------
                # Candidate scoring
                #
                # Prefer:
                # 1. ratio close to 0.714
                # 2. larger card regions
                # --------------------------------------

                ratio_error = abs(
                    ratio - 0.714
                )

                ratio_score = (
                    1.0 - ratio_error
                )

                candidate_score = (
                    ratio_score * 2
                    + area_ratio
                )

                print(
                    f"Threshold "
                    f"{threshold_value}: "
                    f"area={area_ratio:.3f}, "
                    f"ratio={ratio:.3f}, "
                    f"score="
                    f"{candidate_score:.3f}"
                )

                if (
                    candidate_score
                    > best_score
                ):

                    best_score = (
                        candidate_score
                    )

                    best_box = (
                        cv2.boxPoints(
                            rect
                        )
                        .astype(
                            "float32"
                        )
                    )

        if best_box is None:

            return None

        # Convert coordinates back to
        # the original image.
        best_box = (
            best_box
            / scale
        )

        return best_box

    # ==================================================
    # CARD NORMALIZATION
    # ==================================================

    def normalize_card_image(
        self,
        image
    ):
        rgb = np.array(
            image.convert("RGB")
        )

        card_points = (
            self.detect_bare_card(
                image
            )
        )

        if card_points is None:

            print()
            print(
                "Bare card could "
                "not be detected."
            )

            return None

        source = self.order_points(
            card_points
        )

        # Standard output size.
        target_width = 750
        target_height = 1050

        destination = np.array(
            [
                [
                    0,
                    0
                ],
                [
                    target_width - 1,
                    0
                ],
                [
                    target_width - 1,
                    target_height - 1
                ],
                [
                    0,
                    target_height - 1
                ],
            ],
            dtype="float32"
        )

        matrix = (
            cv2.getPerspectiveTransform(
                source,
                destination
            )
        )

        warped = cv2.warpPerspective(
            rgb,
            matrix,
            (
                target_width,
                target_height
            )
        )

        return Image.fromarray(
            warped
        )

    # ==================================================
    # SCAN
    # ==================================================

    def scan_card(self):
        if self.selected_image is None:

            QMessageBox.warning(
                self,
                "No Image",
                "Please choose a card "
                "image first."
            )

            return

        self.status_label.setText(
            "Status: Detecting bare card..."
        )

        normalized = (
            self.normalize_card_image(
                self.selected_image
            )
        )

        if normalized is None:

            self.status_label.setText(
                "Status: Bare card could "
                "not be detected."
            )

            return

        self.normalized_image = (
            normalized
        )

        matches = find_closest_cards(
            normalized,
            self.visual_index,
            limit=20
        )

        self.status_label.setText(
            "Status: Comparing final candidates..."
        )

        detailed_matches = (
            rerank_candidates_with_orb(
                normalized,
                matches
            )
        )

        print()
        print("============================")
        print("DETAILED VISUAL MATCHES")
        print("============================")

        for position, card in enumerate(
            detailed_matches,
            start=1
        ):

            print(
                f"{position:2}. "
                f"{card['name']} "
                f"| {card['set_id']} "
                f"#{card['number']} "
                f"| pHash="
                f"{card['distance']} "
                f"| ORB="
                f"{card['orb_score']:.2f}"
            )

        print()
        print("============================")
        print("TOP VISUAL MATCHES")
        print("============================")

        for position, card in enumerate(
            matches,
            start=1
        ):
            print(
                f"{position:2}. "
                f"{card['name']} "
                f"| {card['set_id']} "
                f"#{card['number']} "
                f"| distance="
                f"{card['distance']}"
            )

        self.show_image(
            normalized
        )

        self.status_label.setText(
            "Status: Card detected "
            "and normalized."
        )

        print()
        print(
            "============================"
        )
        print(
            "SCANNER 2.0 - NORMALIZATION"
        )
        print(
            "============================"
        )
        print(
            "Original:",
            self.selected_image.size
        )
        print(
            "Normalized:",
            normalized.size
        )

    # ==================================================
    # HOME
    # ==================================================

    def go_home(self):
        window = self.window()

        if hasattr(
            window,
            "open_home"
        ):

            window.open_home()

        elif hasattr(
            window,
            "show_home"
        ):

            window.show_home()