"""Compteur d'appels API (ipinfo.io) : persistant, remis à zéro chaque jour,
et calculs de cadence. Aucune dépendance à Qt.

Le compteur est LOCAL : il ne compte que les appels faits par cette
application sur cette machine."""
import json
import os
import threading
from datetime import date

import config as c

_lock = threading.Lock()


def _today():
    return date.today().isoformat()


def _load():
    """Nombre d'appels déjà faits aujourd'hui (0 si nouveau jour ou fichier absent)."""
    try:
        with open(c.QUOTA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("date") == _today():
            return int(data.get("count", 0))
    except (OSError, ValueError):
        pass
    return 0


def _save(count):
    try:
        os.makedirs(os.path.dirname(c.QUOTA_FILE), exist_ok=True)
        with open(c.QUOTA_FILE, "w", encoding="utf-8") as f:
            json.dump({"date": _today(), "count": count}, f)
    except OSError:
        pass


def record_call(n=1):
    """Enregistre n appels et retourne le total du jour."""
    with _lock:
        count = _load() + n
        _save(count)
        return count


def calls_today():
    with _lock:
        return _load()


def remaining_today():
    return max(0, c.API_DAILY_LIMIT - calls_today())


def calls_per_hour(interval_seconds, calls_per_scan):
    return 3600 / interval_seconds * calls_per_scan


def hours_until_exhausted(remaining, per_hour):
    """Heures avant d'épuiser le quota restant au rythme donné."""
    return remaining / per_hour if per_hour > 0 else float("inf")