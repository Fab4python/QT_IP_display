"""Partie graphique uniquement : aucune logique réseau ici."""
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
from utils import format_duration
from worker import Worker


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(c.APP_TITLE)
        self.setMinimumSize(*c.WINDOW_MIN_SIZE)
        self.setStyleSheet(STYLE)

        self.calls_per_scan = c.DEFAULT_CALLS_PER_SCAN
        self.worker = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)

        # --- affichage des résultats ---
        self.title = QLabel("> NETWORK IP-EXPOSITION SCAN")
        self.title.setObjectName("title")

        self.ip_header = self._section("[ IDENTITE INTERNET]")
        self.ip_label = QLabel("...")

        self.dns_header = self._section("[ IP-PRIVEE ]")
        self.dns_label = QLabel("...")

        self.map_header = self._section("[ LOCALISATION ]")
        self.map_label = QLabel("scan en cours...")
        self.map_label.setObjectName("map")
        self.map_label.setAlignment(Qt.AlignCenter)
        self.map_label.setFixedSize(c.MAP_WIDTH + 2, c.MAP_HEIGHT + 2)

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
        self.quota_label = QLabel()
        self.quota_label.setObjectName("tiny")
        self.button = QPushButton("[ REFRESH ]")
        self.button.clicked.connect(self.refresh)

        # --- mise en page ---
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 12)
        lay.setSpacing(8)
        for w in (self.title, self.ip_header, self.ip_label,
                  self.dns_header, self.dns_label, self.map_header):
            lay.addWidget(w)
        lay.addWidget(self.map_label, alignment=Qt.AlignHCenter)
        lay.addStretch()

        lay.addWidget(self.auto_header)
        auto_row = QHBoxLayout()
        auto_row.addWidget(self.auto_check)
        auto_row.addWidget(self.slider, 1)
        auto_row.addWidget(self.interval_label)
        lay.addLayout(auto_row)
        lay.addWidget(self.rate_label)

        lay.addWidget(self.status)
        bottom = QHBoxLayout()
        bottom.addWidget(self.quota_label, alignment=Qt.AlignBottom)
        bottom.addStretch()
        bottom.addWidget(self.button)
        lay.addLayout(bottom)

        self.update_quota_info()
        self.refresh()

    @staticmethod
    def _section(text):
        label = QLabel(text)
        label.setObjectName("section")
        return label

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
        self.worker.done.connect(self.on_done)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def on_done(self, d):
        me = d["me"]
        self.ip_label.setText(
            f'IP      : {me.get("ip", "?")}\n'
            f'Host    : {d["reverse"]}\n'
            f'FAI     : {me.get("org", "?")}\n'
            f'Lieu    : {me.get("city", "?")}, {me.get("country", "?")}\n'
            f'Fuseau  : {me.get("timezone", "?")}'
        )

        if d["dns"]:
            lines = []
            for i, s in enumerate(d["dns"], 1):
                if s["public"]:
                    lines.append(f'DNS {i}   : {s["ip"]}  ({s.get("org", "?")} - {s.get("place", "?")})')
                else:
                    lines.append(f'IP {i}   : {s["ip"]}  (reseau local)')
            self.dns_label.setText("\n".join(lines))
        else:
            self.dns_label.setText("Aucun serveur DNS detecte")

        if d["image"] is not None:
            self.map_label.setPixmap(QPixmap.fromImage(d["image"]))
            self.map_header.setText(f'[ LOCALISATION : {d["label"]} ]')
        else:
            self.map_label.setText("carte indisponible")

        if d.get("api_calls"):
            self.calls_per_scan = d["api_calls"]
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