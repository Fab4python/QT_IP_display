"""Petites fonctions utilitaires d'affichage (sans dépendance Qt)."""


def format_duration(seconds):
    """30 -> '30 s', 90 -> '1 min 30 s', 300 -> '5 min', 4500 -> '1 h 15 min'."""
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds} s"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes} min" + (f" {sec} s" if sec else "")
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h" + (f" {minutes:02d} min" if minutes else "")