"""Partie graphique uniquement : aucune logique réseau ici."""
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

import config as c
import quota
from styles import STYLE
from utils import format_duration, format_ip_entry
from widgets import DashedSeparator
from worker import Worker


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(c.APP_TITLE)
        self.setStyleSheet(STYLE)

        self.calls_per_scan = c.DEFAULT_CALLS_PER_SCAN
        self.my_info = {}
        self.host = "..."
        self.worker = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)

        # --- affichage des résultats ---
        self.title = QLabel("> NETWORK_SCAN_")
        self.title.setObjectName("title")

        self.ip_header = self._section("[ IDENTITE RESEAU ]")
        self.ip_label = QLabel("...")

        self.dns_header = self._section("[ IP PRIVE ]")
        self.dns_label = QLabel("...")

        self.map_title = "LOCALISATION"
        self.map_toggle = QPushButton()
        self.map_toggle.setObjectName("toggle")
        self.map_toggle.setCheckable(True)
        self.map_toggle.setChecked(c.MAP_EXPANDED_DEFAULT)
        self.map_toggle.setCursor(Qt.PointingHandCursor)
        self.map_toggle.toggled.connect(self.on_map_toggled)
        self.update_map_toggle_text()
        self.map_label = QLabel("scan en cours...")
        self.map_label.setObjectName("map")
        self.map_label.setAlignment(Qt.AlignCenter)
        self.map_label.setFixedSize(c.MAP_WIDTH + 2, c.MAP_HEIGHT + 2)
        self.map_label.setVisible(c.MAP_EXPANDED_DEFAULT)

        # --- rafraîchissement automatique ---
        self.auto_header = self._section("[ REFRESH AUTO ]")
        self.auto_check = QCheckBox("ON")
        self.auto_check.toggled.connect(self.on_auto_toggled)

        step = c.REFRESH_STEP_SECONDS
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(c.REFRESH_MIN_SECONDS // step, c.REFRESH_MAX_SECONDS // step)
        self.slider.setValue(c.REFRESH_DEFAULT_SECONDS // step)
        self.slider.valueChanged.connect(self.on_slider_changed)

        self.interval_label = QLabel()
        self.interval_label.setMinimumWidth(80)
        self.interval_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.rate_label = QLabel()

        # --- bas de fenêtre ---
        self.status = QLabel("")
        self.last_scan_label = QLabel("dernier scan : --:--:--")
        self.quota_label = QLabel()
        self.quota_label.setObjectName("tiny")
        self.button = QPushButton("[ REFRESH ]")
        self.button.clicked.connect(self.refresh)

        # --- mise en page ---
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 12)
        lay.setSpacing(8)
        for w in (self.title, self.ip_header, self.ip_label,
                  self.dns_header, self.dns_label,
                  self._separator(), self.map_toggle):
            lay.addWidget(w)
        lay.addWidget(self.map_label, alignment=Qt.AlignHCenter)
        lay.addStretch()

        lay.addWidget(self._separator(lines=2))  # double trait avant REFRESH AUTO
        lay.addWidget(self.auto_header)
        auto_row = QHBoxLayout()
        auto_row.addWidget(self.auto_check)
        auto_row.addWidget(self.slider, 1)
        auto_row.addWidget(self.interval_label)
        lay.addLayout(auto_row)
        lay.addWidget(self.rate_label)

        lay.addWidget(self.status)
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        info_col.addStretch()
        info_col.addWidget(self.last_scan_label)
        info_col.addWidget(self.quota_label)
        bottom = QHBoxLayout()
        bottom.addLayout(info_col)
        bottom.addStretch()
        bottom.addWidget(self.button)
        lay.addLayout(bottom)

        width, height = c.WINDOW_SIZE
        if not c.MAP_EXPANDED_DEFAULT:
            height -= self.map_extra_height()
        self.resize(width, height)

        self.update_quota_info()
        self.refresh()

    @staticmethod
    def _section(text):
        label = QLabel(text)
        label.setObjectName("section")
        return label

    @staticmethod
    def _separator(lines=1):
        """Trait en pointillés (lines=2 pour un double trait)."""
        return DashedSeparator(lines)

    # --------------------------------------------------------- carte dépliable
    def map_extra_height(self):
        """Hauteur gagnée/perdue quand la carte est dépliée/repliée."""
        return c.MAP_HEIGHT + 2 + self.layout().spacing()

    def update_map_toggle_text(self):
        sign = "-" if self.map_toggle.isChecked() else "+"
        self.map_toggle.setText(f"[{sign}] {self.map_title}")

    def on_map_toggled(self, expanded):
        self.map_label.setVisible(expanded)
        self.update_map_toggle_text()
        self.fit_height_to_content()
        # 2e passage une fois que Qt a fini de recalculer la mise en page
        QTimer.singleShot(0, self.fit_height_to_content)

    def fit_height_to_content(self):
        """Ajuste la hauteur de la fenêtre au contenu affiché (plus d'espace vide)."""
        if self.isMaximized() or self.isFullScreen():
            return
        lay = self.layout()
        lay.invalidate()  # oublie les tailles mises en cache (ancien état de la carte)
        lay.activate()    # recalcule la taille minimale de la fenêtre
        self.resize(self.width(), lay.sizeHint().height())

    # ------------------------------------------------------------ réglages
    def interval_seconds(self):
        return self.slider.value() * c.REFRESH_STEP_SECONDS

    def update_rate_info(self):
        """Affiche le nombre d'appels/heure selon le curseur."""
        interval = self.interval_seconds()
        self.interval_label.setText(format_duration(interval))

        per_hour = quota.calls_per_hour(interval, self.calls_per_scan)
        over_limit = per_hour * 24 > c.API_DAILY_LIMIT
        if over_limit:
            hours = quota.hours_until_exhausted(quota.remaining_today(), per_hour)
            line2 = f"limite de {c.API_DAILY_LIMIT} atteinte en ~{format_duration(hours * 3600)}"
        else:
            line2 = f"compatible avec la limite de {c.API_DAILY_LIMIT} appels/jour"
        self.rate_label.setText(
            f"≈ {per_hour:.0f} appels/h ({self.calls_per_scan} par scan)\n{line2}"
        )
        self.rate_label.setStyleSheet(f"color: {c.WARNING_COLOR};" if over_limit else "")

    def update_quota_info(self):
        remaining = quota.remaining_today()
        self.quota_label.setText(
            f"appels restants aujourd'hui : {remaining}/{c.API_DAILY_LIMIT}"
        )
        self.update_rate_info()
        if remaining <= 0 and self.auto_check.isChecked():
            self.auto_check.setChecked(False)
            self.status.setText("> quota atteint : auto-refresh arrete")

    def on_slider_changed(self, _value):
        self.update_rate_info()
        if self.timer.isActive():
            self.timer.start(self.interval_seconds() * 1000)

    def on_auto_toggled(self, checked):
        if checked:
            if quota.remaining_today() <= 0:
                self.auto_check.setChecked(False)
                self.status.setText("> quota journalier atteint")
                return
            self.timer.start(self.interval_seconds() * 1000)
            self.status.setText(
                f"> auto-refresh : toutes les {format_duration(self.interval_seconds())}"
            )
        else:
            self.timer.stop()
            self.status.setText("> auto-refresh arrete")

    def on_timer(self):
        self.refresh()

    # --------------------------------------------------------------- scan
    def refresh(self):
        if self.worker is not None and self.worker.isRunning():
            return  # un scan est déjà en cours
        if quota.remaining_today() <= 0:
            self.auto_check.setChecked(False)
            self.status.setText("> quota journalier atteint : scan bloque")
            self.update_quota_info()
            return
        self.button.setEnabled(False)
        self.status.setText("> scan en cours...")
        self.worker = Worker()
        self.worker.ip_ready.connect(self.on_ip_ready)
        self.worker.host_ready.connect(self.on_host_ready)
        self.worker.dns_ready.connect(self.on_dns_ready)
        self.worker.map_ready.connect(self.on_map_ready)
        self.worker.done.connect(self.on_done)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def render_ip(self):
        me = self.my_info
        self.ip_label.setText(
            f'IP      : {me.get("ip", "?")}\n'
            f'Host    : {self.host}\n'
            f'FAI     : {me.get("org", "?")}\n'
            f'Lieu    : {me.get("city", "?")}, {me.get("country", "?")}\n'
            f'Fuseau  : {me.get("timezone", "?")}'
        )

    def on_ip_ready(self, me):
        self.my_info = me
        self.host = me.get("hostname") or "recherche..."
        self.render_ip()
        self.status.setText("> IP recue, analyse DNS et carte...")

    def on_host_ready(self, name):
        self.host = name
        self.render_ip()

    def on_dns_ready(self, entries):
        if not entries:
            self.dns_label.setText("Aucune IP detectee")
            self.dns_label.setToolTip("")
            return
        short, full = [], []
        for i, entry in enumerate(entries, 1):
            line_short, line_full = format_ip_entry(i, entry, c.ALIAS_MAX_CHARS)
            short.append(line_short)
            full.append(line_full)
        self.dns_label.setText("\n".join(short))
        self.dns_label.setToolTip("\n".join(full))  # alias complets au survol

    def on_map_ready(self, image, label):
        if image is not None:
            self.map_label.setPixmap(QPixmap.fromImage(image))
            self.map_title = f'LOCALISATION : {label}'
            self.update_map_toggle_text()
        else:
            self.map_label.setText("carte indisponible")

    def on_done(self, d):
        if d.get("api_calls"):
            self.calls_per_scan = d["api_calls"]
        stamp = datetime.now().strftime(c.TIME_FORMAT)
        self.last_scan_label.setText(f"dernier scan : {stamp}")
        self.status.setText("> scan termine")
        self.button.setEnabled(True)
        self.update_quota_info()

    def on_failed(self, msg):
        self.status.setText(f"> ERREUR : {msg[:80]}")
        self.button.setEnabled(True)
        self.update_quota_info()

    def closeEvent(self, event):
        self.timer.stop()
        if self.worker is not None and self.worker.isRunning():
            self.worker.wait(3000)
        super().closeEvent(event)