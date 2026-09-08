import re
import os
import json
import io

import cv2
import numpy as np
import requests
import pytesseract
from rapidfuzz import fuzz

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox
)

from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer
from pillow_heif import register_heif_opener
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

register_heif_opener()

from db import (
    get_cards_by_number,
    get_cards_by_set_ids,
    increase_inventory,
    get_inventory_quantity
)


# --------------------------------------------------
# Tesseract Location
# --------------------------------------------------

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# --------------------------------------------------
# Local Set Data
# --------------------------------------------------

SETS_PATH = "data/sets/en.json"

IMAGE_CACHE_DIR = "data/image_cache"

os.makedirs(
    IMAGE_CACHE_DIR,
    exist_ok=True
)

FEATURE_CACHE_DIR = "data/feature_cache"

os.makedirs(
    FEATURE_CACHE_DIR,
    exist_ok=True
)

SCAN_DIR = "data/scans"

os.makedirs(
    SCAN_DIR,
    exist_ok=True
)

# Webcam scanner settings
STABLE_FRAMES_REQUIRED = 15
MOTION_THRESHOLD = 4.5
REMOVAL_FRAMES_REQUIRED = 8
CAMERA_WARMUP_FRAMES = 75


class ScanCardPage(QWidget):
    def __init__(self):
        super().__init__()

        self.selected_image_path = None
        self.detected_card = None

        # --------------------------------------------------
        # Webcam Scanner State
        # --------------------------------------------------

        self.camera = None

        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(
            self.update_camera_frame
        )

        self.current_camera_frame = None
        self.current_card_roi = None

        self.previous_roi_gray = None
        self.stable_frame_count = 0

        self.waiting_for_card_removal = False
        self.removal_frame_count = 0

        self.scanning_in_progress = False

        self.camera_warmup_count = 0
        self.scanner_armed = False

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # -----------------------------
        # Title
        # -----------------------------

        title = QLabel("Scan Card")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
        """)
        layout.addWidget(title)

        # --------------------------------------------------
        # Webcam Buttons
        # --------------------------------------------------

        self.start_camera_button = QPushButton(
            "Start Scanner"
        )

        self.start_camera_button.clicked.connect(
            self.start_camera
        )

        layout.addWidget(
            self.start_camera_button
        )


        self.stop_camera_button = QPushButton(
            "Stop Scanner"
        )

        self.stop_camera_button.clicked.connect(
            self.stop_camera
        )

        layout.addWidget(
            self.stop_camera_button
)

        # -----------------------------
        # Instructions
        # -----------------------------

        instructions = QLabel(
            "Choose a photo of a Pokemon card."
        )
        layout.addWidget(instructions)

        # -----------------------------
        # Choose Image Button
        # -----------------------------

        choose_button = QPushButton(
            "Choose Card Image"
        )
        choose_button.clicked.connect(
            self.choose_image
        )
        layout.addWidget(choose_button)

        # -----------------------------
        # Image Preview
        # -----------------------------

        self.image_label = QLabel(
            "No image selected"
        )

        self.image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.image_label.setFixedSize(
            400,
            560
        )

        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #888;
                background-color: #eeeeee;
            }
        """)

        layout.addWidget(
            self.image_label
        )

        # -----------------------------
        # Detection Result
        # -----------------------------

        self.detected_label = QLabel(
            "Detected Card: Not scanned yet"
        )

        self.detected_label.setWordWrap(True)

        layout.addWidget(
            self.detected_label
        )

        # -----------------------------
        # Identify Button
        # -----------------------------

        self.identify_button = QPushButton(
            "Identify Card"
        )

        self.identify_button.clicked.connect(
            self.identify_card
        )

        layout.addWidget(
            self.identify_button
        )

        # -----------------------------
        # Add to Inventory Button
        # -----------------------------

        self.add_button = QPushButton(
            "Add to Inventory"
        )

        self.add_button.setEnabled(False)

        self.add_button.clicked.connect(
            self.add_to_inventory
        )

        layout.addWidget(
            self.add_button
        )

        # -----------------------------
        # Back Button
        # -----------------------------

        back_button = QPushButton(
            "Back to Home"
        )

        back_button.clicked.connect(
            self.go_home
        )

        layout.addWidget(
            back_button
        )

        self.setLayout(layout)

    # --------------------------------------------------
    # Choose Image
    # --------------------------------------------------

    def choose_image(self):
        self.stop_camera()
    
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Card Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.heic *.heif)"
        )
    
        if not file_path:
            return
    
        try:
            extension = os.path.splitext(
                file_path
            )[1].lower()
    
            # ------------------------------------------
            # HEIC / HEIF
            #
            # Convert to PNG so PyQt and the rest of
            # our scanner can use it normally.
            # ------------------------------------------
    
            if extension in [".heic", ".heif"]:
    
                image = Image.open(
                    file_path
                )
    
                # Correct iPhone orientation
                image = ImageOps.exif_transpose(
                    image
                )
    
                image = image.convert(
                    "RGB"
                )
    
                converted_path = os.path.join(
                    SCAN_DIR,
                    "selected_heic.png"
                )
    
                image.save(
                    converted_path,
                    format="PNG"
                )
    
                self.selected_image_path = (
                    converted_path
                )
    
            else:
    
                self.selected_image_path = (
                    file_path
                )
    
            self.detected_card = None
    
            # ------------------------------------------
            # Preview
            # ------------------------------------------
    
            pixmap = QPixmap(
                self.selected_image_path
            )
    
            if pixmap.isNull():
    
                QMessageBox.warning(
                    self,
                    "Image Error",
                    "The selected image could not be loaded."
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
    
            self.detected_label.setText(
                "Detected Card: Ready to scan"
            )
    
            self.add_button.setEnabled(
                False
            )
    
        except Exception as error:
    
            QMessageBox.critical(
                self,
                "Image Error",
                f"The image could not be opened.\n\n{error}"
            )
    
    def prepare_image_for_ocr(self, image):
        image = image.convert("L")

        image = ImageEnhance.Contrast(
            image
        ).enhance(2.5)

        image = image.filter(
            ImageFilter.SHARPEN
        )

        width, height = image.size

        # Enlarge tiny text
        image = image.resize(
            (
                width * 3,
                height * 3
            )
        )

        return image

    # --------------------------------------------------
    # Read Collector Number
    # --------------------------------------------------

    def read_collector_number(self, image):
        width, height = image.size

        # Try several crops around the
        # bottom-left collector-number area.
        crop_areas = [
            (
                int(width * 0.02),
                int(height * 0.86),
                int(width * 0.45),
                int(height * 0.99)
            ),
            (
                int(width * 0.02),
                int(height * 0.88),
                int(width * 0.42),
                int(height * 0.99)
            ),
            (
                int(width * 0.05),
                int(height * 0.89),
                int(width * 0.50),
                int(height * 0.98)
            )
        ]

        possible_results = []

        for crop_index, crop_area in enumerate(
            crop_areas
        ):

            number_crop = image.crop(
                crop_area
            )

            crop_array = np.array(
                number_crop.convert("RGB")
            )

            gray = cv2.cvtColor(
                crop_array,
                cv2.COLOR_RGB2GRAY
            )

            # Make tiny text much larger
            gray = cv2.resize(
                gray,
                None,
                fx=5,
                fy=5,
                interpolation=cv2.INTER_CUBIC
            )

            versions = []

            # Version 1 - grayscale
            versions.append(
                gray
            )

            # Version 2 - Otsu threshold
            _, otsu = cv2.threshold(
                gray,
                0,
                255,
                cv2.THRESH_BINARY
                + cv2.THRESH_OTSU
            )

            versions.append(
                otsu
            )

            # Version 3 - inverted Otsu
            versions.append(
                cv2.bitwise_not(
                    otsu
                )
            )

            # Version 4 - adaptive threshold
            adaptive = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31,
                8
            )

            versions.append(
                adaptive
            )

            for version_index, version in enumerate(
                versions
            ):

                text = pytesseract.image_to_string(
                    version,
                    config="--psm 6"
                ).strip()

                print(
                    f"CROP {crop_index + 1} "
                    f"OCR VERSION {version_index + 1}: "
                    f"{repr(text)}"
                )

                # ------------------------------------------
                # Best case:
                #
                # 193/182
                # ------------------------------------------

                exact_match = re.search(
                    r"(\d{1,4})\s*[/|]\s*(\d{1,4})",
                    text
                )

                if exact_match:
                    return {
                        "card_number":
                            exact_match.group(1),

                        "set_total":
                            exact_match.group(2),

                        "exact": True
                    }

                # ------------------------------------------
                # Imperfect OCR examples:
                #
                # 739,182
                # 703,182
                #
                # The numerator may be wrong,
                # but 182 keeps appearing correctly.
                # ------------------------------------------

                loose_matches = re.findall(
                    r"(\d{2,4})\s*[,.:;]\s*(\d{2,4})",
                    text
                )

                for first, second in loose_matches:

                    possible_results.append(
                        {
                            "card_number": first,
                            "set_total": second,
                            "exact": False
                        }
                    )

        # ----------------------------------------------
        # If we did not get a perfect 193/182,
        # trust the denominator that appeared most.
        # ----------------------------------------------

        if possible_results:

            denominator_counts = {}

            for result in possible_results:

                denominator = result[
                    "set_total"
                ]

                denominator_counts[
                    denominator
                ] = (
                    denominator_counts.get(
                        denominator,
                        0
                    ) + 1
                )

            best_denominator = max(
                denominator_counts,
                key=denominator_counts.get
            )

            print()
            print(
                "Trusted set total:",
                best_denominator
            )

            return {
                "card_number": None,
                "set_total": best_denominator,
                "exact": False
            }

        return None

    # --------------------------------------------------
    # Load Set Printed Totals
    # --------------------------------------------------

    def load_set_totals(self):
        set_totals = {}

        try:

            with open(
                SETS_PATH,
                "r",
                encoding="utf-8"
            ) as file:

                sets = json.load(
                    file
                )

            for pokemon_set in sets:

                set_id = pokemon_set.get(
                    "id"
                )

                printed_total = pokemon_set.get(
                    "printedTotal"
                )

                if (
                    set_id
                    and printed_total is not None
                ):

                    set_totals[
                        set_id
                    ] = str(
                        printed_total
                    )

        except Exception as error:

            print(
                "Could not load set totals:",
                error
            )

        return set_totals

    # --------------------------------------------------
    # Download Official Card Image
    # --------------------------------------------------

    def download_card_image(
        self,
        card_id,
        image_url
    ):
        if not image_url:
            return None

        # Make a safe filename
        safe_card_id = card_id.replace(
            "/",
            "_"
        )

        cache_path = os.path.join(
            IMAGE_CACHE_DIR,
            f"{safe_card_id}.png"
        )

        # ----------------------------------------------
        # Use cached image if we already downloaded it
        # ----------------------------------------------

        if os.path.exists(cache_path):

            try:
                print(
                    f"CACHE HIT: {card_id}"
                )

                image = Image.open(
                    cache_path
                )

                image.load()

                return image

            except Exception as error:

                print(
                    f"Cache error for {card_id}:",
                    error
                )

                # Delete corrupted cache file
                try:
                    os.remove(
                        cache_path
                    )
                except Exception:
                    pass

        # ----------------------------------------------
        # Not cached yet - download it
        # ----------------------------------------------

        try:

            print(
                f"DOWNLOADING: {card_id}"
            )

            response = requests.get(
                image_url,
                timeout=10
            )

            response.raise_for_status()

            image = Image.open(
                io.BytesIO(
                    response.content
                )
            )

            image.load()

            # Save a local copy
            image.save(
                cache_path,
                format="PNG"
            )

            return image

        except Exception as error:

            print(
                f"Could not download {card_id}:",
                error
            )

            return None

    def get_orb_descriptors(self, image):
        try:
            image_array = np.array(
                image.convert("RGB")
            )

            gray = cv2.cvtColor(
                image_array,
                cv2.COLOR_RGB2GRAY
            )

            gray = cv2.resize(
                gray,
                (400, 560)
            )

            orb = cv2.ORB_create(
                nfeatures=2000
            )

            keypoints, descriptors = (
                orb.detectAndCompute(
                    gray,
                    None
                )
            )

            return descriptors

        except Exception as error:
            print(
                "ORB descriptor error:",
                error
            )

            return None

    def get_cached_card_descriptors(
        self,
        card_id,
        image_url
    ):
        safe_card_id = card_id.replace(
            "/",
            "_"
        )

        feature_path = os.path.join(
            FEATURE_CACHE_DIR,
            f"{safe_card_id}.npz"
        )

        # ----------------------------------------------
        # Load cached ORB descriptors
        # ----------------------------------------------

        if os.path.exists(feature_path):

            try:
                print(
                    f"FEATURE CACHE HIT: {card_id}"
                )

                data = np.load(
                    feature_path
                )

                return data[
                    "descriptors"
                ]

            except Exception as error:

                print(
                    f"Feature cache error "
                    f"for {card_id}:",
                    error
                )

                # Remove corrupted cache file
                try:
                    os.remove(
                        feature_path
                    )
                except Exception:
                    pass

        # ----------------------------------------------
        # No feature cache yet
        # ----------------------------------------------

        print(
            f"BUILDING FEATURES: {card_id}"
        )

        official_image = (
            self.download_card_image(
                card_id,
                image_url
            )
        )

        if official_image is None:
            return None

        descriptors = (
            self.get_orb_descriptors(
                official_image
            )
        )

        if descriptors is None:
            return None

        # Save descriptors for future scans
        try:
            np.savez_compressed(
                feature_path,
                descriptors=descriptors
            )

        except Exception as error:
            print(
                f"Could not save feature cache "
                f"for {card_id}:",
                error
            )

        return descriptors

    def compare_descriptors(
        self,
        scanned_descriptors,
        official_descriptors
    ):
        if (
            scanned_descriptors is None
            or official_descriptors is None
        ):
            return 0

        try:
            matcher = cv2.BFMatcher(
                cv2.NORM_HAMMING
            )

            matches = matcher.knnMatch(
                scanned_descriptors,
                official_descriptors,
                k=2
            )

            good_matches = []

            for match_pair in matches:

                if len(match_pair) < 2:
                    continue

                first, second = match_pair

                if first.distance < (
                    0.75 * second.distance
                ):
                    good_matches.append(
                        first
                    )

            score = min(
                len(good_matches) * 2,
                100
            )

            return score

        except Exception as error:
            print(
                "Descriptor comparison error:",
                error
            )

            return 0

    # --------------------------------------------------
    # Identify Card
    # --------------------------------------------------

    def identify_card(self):
        if self.selected_image_path is None:

            QMessageBox.warning(
                self,
                "No Image",
                "Please choose a card image first."
            )

            return

        self.detected_label.setText(
            "Detected Card: Scanning..."
        )

        self.detected_card = None
        self.add_button.setEnabled(False)

        try:

            image = Image.open(
                self.selected_image_path
            )

            width, height = image.size

            # ------------------------------------------
            # Top section for card-name OCR
            # ------------------------------------------

            top_crop = image.crop(
                (
                    int(width * 0.05),
                    int(height * 0.02),
                    int(width * 0.95),
                    int(height * 0.20)
                )
            )

            top_processed = (
                self.prepare_image_for_ocr(
                    top_crop
                )
            )

            top_text = (
                pytesseract.image_to_string(
                    top_processed,
                    config="--psm 6"
                )
            )

            print()
            print("----------------------------")
            print("TOP OCR TEXT")
            print("----------------------------")
            print(top_text)
            print("----------------------------")

        except Exception as error:

            QMessageBox.critical(
                self,
                "OCR Error",
                str(error)
            )

            self.detected_label.setText(
                "Detected Card: OCR failed"
            )

            return

        # --------------------------------------------------
        # Read Collector Number / Set Total
        # --------------------------------------------------

        collector_result = (
            self.read_collector_number(
                image
            )
        )

        if collector_result is None:

            QMessageBox.warning(
                self,
                "Card Number Not Found",
                "The scanner could not reliably "
                "read the collector number.\n\n"
                "Check the PowerShell OCR output."
            )

            self.detected_label.setText(
                "Detected Card: "
                "Could not read card number"
            )

            return

        card_number = collector_result[
            "card_number"
        ]

        set_total = collector_result[
            "set_total"
        ]

        exact_number = collector_result[
            "exact"
        ]

        # --------------------------------------------------
        # Normalize numeric collector values
        #
        # Example:
        # "094" -> "94"
        # "007" -> "7"
        # --------------------------------------------------

        if card_number and card_number.isdigit():
            card_number = str(
                int(card_number)
            )

        if set_total and set_total.isdigit():
            set_total = str(
                int(set_total)
            )

        print()
        print("----------------------------")
        print("COLLECTOR RESULT")
        print("----------------------------")
        print(
            "Detected card number:",
            card_number
        )
        print(
            "Detected set total:",
            set_total
        )
        print(
            "Exact number reading:",
            exact_number
        )

        # --------------------------------------------------
        # Find Sets With This Printed Total
        # --------------------------------------------------

        set_totals = (
            self.load_set_totals()
        )

        matching_set_ids = [
            set_id
            for set_id, total
            in set_totals.items()
            if total == set_total
        ]

        print()
        print(
            "Sets matching printed total:",
            matching_set_ids
        )

        # --------------------------------------------------
        # Build Candidate List
        # --------------------------------------------------

        if matching_set_ids:

            # ----------------------------------------------
            # Best case:
            # collector number + set total both worked
            # ----------------------------------------------

            if exact_number and card_number:

                print(
                    "Using exact collector-number "
                    "and set-total search."
                )

                candidates = (
                    get_cards_by_number(
                        card_number
                    )
                )

                candidates = [
                    card
                    for card in candidates
                    if card["set_id"]
                    in matching_set_ids
                ]

            # ----------------------------------------------
            # We only trust the set total
            # ----------------------------------------------

            else:

                print(
                    "Collector number was unclear."
                )

                print(
                    "Using cards from matching set(s) "
                    "for visual comparison."
                )

                candidates = (
                    get_cards_by_set_ids(
                        matching_set_ids
                    )
                )

        else:

            # --------------------------------------------------
            # Set total OCR failed.
            #
            # Example:
            # actual card = 085/086
            # OCR reads   = 85/4
            #
            # If we still have a card number, search by that
            # number and let visual/name matching choose.
            # --------------------------------------------------

            print()
            print(
                "Set total does not match a known set."
            )

            if card_number:

                print(
                    f"Falling back to card number "
                    f"#{card_number}."
                )

                candidates = (
                    get_cards_by_number(
                        card_number
                    )
                )

            else:

                QMessageBox.warning(
                    self,
                    "Card Not Identified",
                    "The scanner could not reliably "
                    "read either the card number or "
                    "the set information."
                )

                self.detected_label.setText(
                    "Detected Card: "
                    "Could not identify collector number"
                )

                return

        print()
        print(
            "Visual candidates:",
            len(candidates)
        )

        if not candidates:

            self.detected_label.setText(
                "Detected Card: "
                "No candidates found"
            )

            QMessageBox.warning(
                self,
                "No Candidates",
                "The set was detected, but "
                "there were no cards available "
                "to compare."
            )

            return

        # --------------------------------------------------
        # Compare Candidate Cards
        # --------------------------------------------------

        best_card = None
        best_score = -1

        top_text_lower = (
            top_text.lower()
        )

        # --------------------------------------------------
# Calculate scanned card features ONCE
# --------------------------------------------------

        print()
        print(
            "Calculating scanned card features..."
        )

        scanned_descriptors = (
            self.get_orb_descriptors(
                image
            )
        )

        if scanned_descriptors is None:

            self.detected_label.setText(
                "Detected Card: "
                "Could not process scanned image"
            )

            QMessageBox.warning(
                self,
                "Image Processing Error",
                "The scanner could not calculate "
                "visual features for this image."
            )

            return

        print(
            "Scanned card features ready."
        )

        print()
        print("----------------------------")
        print("CANDIDATE COMPARISON")
        print("----------------------------")

        for card in candidates:

            # ------------------------------------------
            # Name OCR score
            # ------------------------------------------

            name_score = (
                fuzz.partial_ratio(
                    card["name"].lower(),
                    top_text_lower
                )
            )

            # ------------------------------------------
            # Visual score
            # ------------------------------------------

            visual_score = 0

            official_descriptors = (
                self.get_cached_card_descriptors(
                    card["id"],
                    card["image_url"]
                )
            )

            if official_descriptors is not None:

                visual_score = (
                    self.compare_descriptors(
                        scanned_descriptors,
                        official_descriptors
                    )
                )

            # ------------------------------------------
            # Combined score
            #
            # Visual match matters much more
            # than OCR name matching.
            # ------------------------------------------

            combined_score = (
                visual_score * 0.75
                + name_score * 0.25
            )

            print()
            print(
                card["name"]
            )

            print(
                "Set:",
                card["set_id"]
            )

            print(
                "Number:",
                card["number"]
            )

            print(
                "Name OCR:",
                round(
                    name_score,
                    1
                )
            )

            print(
                "Visual:",
                round(
                    visual_score,
                    1
                )
            )

            print(
                "Combined:",
                round(
                    combined_score,
                    1
                )
            )

            if combined_score > best_score:

                best_score = (
                    combined_score
                )

                best_card = card

        # --------------------------------------------------
        # No Result
        # --------------------------------------------------

        if best_card is None:

            self.detected_label.setText(
                "Detected Card: "
                "No match found"
            )

            return

        # --------------------------------------------------
        # Card Identified
        # --------------------------------------------------

        self.detected_card = best_card

        set_display = (
            best_card["set_id"].upper()
            if best_card["set_id"]
            else "UNKNOWN"
        )

        collector_display = ""

        if card_number:
            collector_display = (
                f"{card_number}/{set_total}"
            )
        else:
            collector_display = (
                f"?/{set_total}"
            )

        self.detected_label.setText(
            f"Detected Card:\n"
            f"{best_card['name']}\n"
            f"{set_display} "
            f"#{best_card['number']}\n"
            f"Collector Reading: "
            f"{collector_display}\n"
            f"Match Score: "
            f"{best_score:.0f}%"
        )

        self.add_button.setEnabled(
            True
        )

    # --------------------------------------------------
    # Add Card to Inventory
    # --------------------------------------------------

    def add_to_inventory(self):
        if self.detected_card is None:
            return

        card_id = self.detected_card[
            "id"
        ]

        increase_inventory(
            card_id
        )

        quantity = (
            get_inventory_quantity(
                card_id
            )
        )

        QMessageBox.information(
            self,
            "Inventory Updated",
            f"{self.detected_card['name']} "
            f"was added to your inventory.\n\n"
            f"Owned: {quantity}"
        )

        self.add_button.setEnabled(
            False
        )

        # Resume webcam scanner after adding
        # this card.

        if (
            self.camera is not None
            and self.camera.isOpened()
        ):
            self.waiting_for_card_removal = True
            self.removal_frame_count = 0
            self.previous_roi_gray = None
            self.stable_frame_count = 0

            self.detected_label.setText(
                f"{self.detected_card['name']} added.\n"
                f"Remove the card to scan the next one."
            )

            self.camera_timer.start(30)
        else:
            self.detected_label.setText(
                f"{self.detected_card['name']} added to inventory."
            )

    # --------------------------------------------------
    # Navigation
    # --------------------------------------------------

    def go_home(self):
        self.stop_camera()
        self.window().open_home()

    def start_camera(self):
        if self.camera is not None:
            self.stop_camera()

        self.camera = cv2.VideoCapture(0)

        if not self.camera.isOpened():

            self.camera = None

            QMessageBox.warning(
                self,
                "Camera Error",
                "The webcam could not be opened."
            )

            return

        # Request HD webcam resolution
        self.camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            1920
        )

        self.camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            1080
        )

        actual_width = self.camera.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )

        actual_height = self.camera.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )

        print(
            "Camera resolution:",
            actual_width,
            "x",
            actual_height
        )

        self.previous_roi_gray = None
        self.stable_frame_count = 0
        self.waiting_for_card_removal = False
        self.removal_frame_count = 0
        self.scanning_in_progress = False
        self.camera_warmup_count = 0
        self.scanner_armed = False

        self.camera_timer.start(30)

        self.detected_label.setText(
            "Camera warming up...\n"
            "Wait for the scanner to become ready."
        )

    def get_card_roi(self, frame):
        frame_height, frame_width = frame.shape[:2]

        # Card ratio is roughly 2.5 x 3.5
        card_height = int(
            frame_height * 0.82
        )

        card_width = int(
            card_height * (2.5 / 3.5)
        )

        center_x = frame_width // 2
        center_y = frame_height // 2

        x1 = center_x - card_width // 2
        x2 = center_x + card_width // 2

        y1 = center_y - card_height // 2
        y2 = center_y + card_height // 2

        roi = frame[
            y1:y2,
            x1:x2
        ]

        return (
            roi,
            x1,
            y1,
            x2,
            y2
        )

    def card_is_present(self, roi):
        if roi is None or roi.size == 0:
            return False

        gray = cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.GaussianBlur(
            gray,
            (5, 5),
            0
        )

        edges = cv2.Canny(
            gray,
            50,
            150
        )

        edge_ratio = (
            np.count_nonzero(edges)
            / edges.size
        )

        # A blank background normally has very
        # few edges. A Pokemon card has lots.
        if edge_ratio < 0.02:
            return False

        return True

    def card_is_stable(self, roi):
        gray = cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.resize(
            gray,
            (160, 224)
        )

        gray = cv2.GaussianBlur(
            gray,
            (5, 5),
            0
        )

        if self.previous_roi_gray is None:

            self.previous_roi_gray = gray

            return False

        difference = cv2.absdiff(
            gray,
            self.previous_roi_gray
        )

        motion_score = np.mean(
            difference
        )

        self.previous_roi_gray = gray

        return (
            motion_score <
            MOTION_THRESHOLD
        )

    def update_camera_frame(self):
        if self.camera is None:
            return

        success, frame = self.camera.read()

        if not success:
            return

        self.current_camera_frame = frame.copy()

        (
            card_roi,
            x1,
            y1,
            x2,
            y2
        ) = self.get_card_roi(frame)

        self.current_card_roi = card_roi.copy()

        # --------------------------------------------------
        # Check whether a card is present
        # --------------------------------------------------

        card_present = self.card_is_present(
            card_roi
        )

        # --------------------------------------------------
        # Draw guide box
        # --------------------------------------------------

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            3
        )

        # --------------------------------------------------
        # Camera warm-up
        # --------------------------------------------------

        if not self.scanner_armed:

            self.camera_warmup_count += 1

            cv2.putText(
                frame,
                "Camera warming up...",
                (x1, max(y1 - 10, 25)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            if (
                self.camera_warmup_count >=
                CAMERA_WARMUP_FRAMES
            ):
                self.scanner_armed = True

                self.stable_frame_count = 0
                self.previous_roi_gray = None

                self.detected_label.setText(
                    "Scanner ready.\n"
                    "Place a card inside the guide box "
                    "and hold it still."
                )

        # --------------------------------------------------
        # Scanner is armed
        # --------------------------------------------------

        else:

            cv2.putText(
                frame,
                "Place card here",
                (x1, max(y1 - 10, 25)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            # --------------------------------------------------
            # Waiting for previous card to be removed
            # --------------------------------------------------

            if self.waiting_for_card_removal:

                if not card_present:

                    self.removal_frame_count += 1

                    if (
                        self.removal_frame_count >=
                        REMOVAL_FRAMES_REQUIRED
                    ):
                        self.waiting_for_card_removal = False

                        self.removal_frame_count = 0
                        self.stable_frame_count = 0
                        self.previous_roi_gray = None

                        self.detected_label.setText(
                            "Scanner ready.\n"
                            "Place the next card "
                            "inside the guide box."
                        )

                else:
                    self.removal_frame_count = 0

            # --------------------------------------------------
            # Card detected - check stability
            # --------------------------------------------------

            elif (
                card_present
                and not self.scanning_in_progress
            ):

                if self.card_is_stable(
                    card_roi
                ):

                    self.stable_frame_count += 1

                else:

                    self.stable_frame_count = 0

                # ----------------------------------------------
                # Stable long enough -> automatically capture
                # ----------------------------------------------

                if (
                    self.stable_frame_count >=
                    STABLE_FRAMES_REQUIRED
                ):

                    self.auto_capture_card(
                        card_roi
                    )

                    return

            else:

                self.stable_frame_count = 0
                self.previous_roi_gray = None

        # --------------------------------------------------
        # Show Webcam Preview
        # --------------------------------------------------

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        height, width, channels = (
            rgb_frame.shape
        )

        bytes_per_line = (
            channels * width
        )

        qimage = QImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )

        pixmap = QPixmap.fromImage(
            qimage
        )

        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.image_label.setPixmap(
            scaled_pixmap
        )

    def auto_capture_card(self, card_roi):
        if self.scanning_in_progress:
            return

        self.scanning_in_progress = True
        self.stable_frame_count = 0

        # Pause webcam while recognition runs
        self.camera_timer.stop()

        scan_path = os.path.join(
            SCAN_DIR,
            "latest_scan.jpg"
        )

        success = cv2.imwrite(
            scan_path,
            card_roi
        )

        if not success:

            self.scanning_in_progress = False

            QMessageBox.warning(
                self,
                "Capture Error",
                "The scanner could not save "
                "the webcam image."
            )

            self.camera_timer.start(30)

            return

        self.selected_image_path = (
            scan_path
        )

        self.detected_card = None

        # Show exactly what was captured
        pixmap = QPixmap(
            scan_path
        )

        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.image_label.setPixmap(
            scaled_pixmap
        )

        self.detected_label.setText(
            "Card detected automatically.\n"
            "Identifying..."
        )

        # Use the scanner we've already built
        self.identify_card()

        self.scanning_in_progress = False

    def stop_camera(self):
        self.camera_timer.stop()

        if self.camera is not None:
            self.camera.release()
            self.camera = None

        self.current_camera_frame = None
        self.current_card_roi = None
        self.previous_roi_gray = None

        self.stable_frame_count = 0
        self.removal_frame_count = 0

        self.waiting_for_card_removal = False
        self.scanning_in_progress = False

        self.camera_warmup_count = 0
        self.scanner_armed = False

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()