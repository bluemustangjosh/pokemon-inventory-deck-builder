APP_STYLE = """
QWidget {
    background-color: #171a21;
    color: #f4f4f4;
    font-family: Segoe UI, Arial, sans-serif;
    font-size: 14px;
}

QMainWindow {
    background-color: #171a21;
}

QLabel {
    color: #f4f4f4;
}

QPushButton {
    background-color: #2d6cdf;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #3d7cf0;
}

QPushButton:pressed {
    background-color: #245bbd;
}

QPushButton:disabled {
    background-color: #444a55;
    color: #8b919a;
}

QLineEdit,
QTextEdit {
    background-color: #222630;
    color: #ffffff;
    border: 1px solid #3a404c;
    border-radius: 8px;
    padding: 10px;
    selection-background-color: #2d6cdf;
}

QLineEdit:focus,
QTextEdit:focus {
    border: 1px solid #2d6cdf;
}

QListWidget {
    background-color: #222630;
    color: #ffffff;
    border: 1px solid #3a404c;
    border-radius: 8px;
    padding: 6px;
    outline: none;
}

QListWidget::item {
    padding: 10px;
    border-radius: 6px;
}

QListWidget::item:hover {
    background-color: #2b303b;
}

QListWidget::item:selected {
    background-color: #2d6cdf;
    color: white;
}

QScrollBar:vertical {
    background-color: #222630;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #555d6b;
    min-height: 30px;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background-color: #687180;
}

QMessageBox {
    background-color: #222630;
}

QMessageBox QLabel {
    color: #f4f4f4;
}
"""