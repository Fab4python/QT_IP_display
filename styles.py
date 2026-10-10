"""Feuille de style Qt (QSS) du thème Matrix."""
import config as c

STYLE = f"""
QWidget {{
    background-color: {c.BACKGROUND};
    color: {c.MATRIX_GREEN};
    font-family: {c.FONT_FAMILY};
    font-size: {c.FONT_SIZE}px;
}}
QLabel#title {{ font-size: 18px; font-weight: bold; }}
QLabel#section {{ color: {c.MATRIX_DIM_GREEN}; font-weight: bold; }}
QLabel#map {{ border: 1px solid {c.MATRIX_GREEN}; }}
QPushButton {{
    border: 1px solid {c.MATRIX_GREEN};
    padding: 6px 14px;
    background: {c.BACKGROUND};
}}
QPushButton:hover {{ background: {c.MATRIX_DARK_GREEN}; }}
QPushButton:disabled {{
    color: {c.MATRIX_DISABLED_GREEN};
    border-color: {c.MATRIX_DISABLED_GREEN};
}}
QLabel#tiny {{ font-size: 9px; color: {c.MATRIX_DIM_GREEN}; }}
QCheckBox::indicator {{
    width: 12px; height: 12px;
    border: 1px solid {c.MATRIX_GREEN};
    background: {c.BACKGROUND};
}}
QCheckBox::indicator:checked {{ background: {c.MATRIX_GREEN}; }}
QSlider::groove:horizontal {{ height: 2px; background: {c.MATRIX_DISABLED_GREEN}; }}
QSlider::sub-page:horizontal {{ background: {c.MATRIX_GREEN}; }}
QSlider::handle:horizontal {{
    background: {c.MATRIX_GREEN};
    width: 10px;
    margin: -6px 0;
}}
"""