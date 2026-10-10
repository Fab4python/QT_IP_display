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


def shorten(text, max_chars):
    """Coupe un texte trop long avec '...' (ex. alias de carte réseau)."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def format_ip_entry(index, entry, max_alias):
    """Ligne d'affichage d'une IP : retourne (ligne courte, ligne complète).

    Privée : 'IP 1    : 192.168.0.1  (Wi-Fi)'
    Publique : 'IP 2    : 8.8.8.8  (Wi-Fi - Google - Mountain View, US)'
    La ligne courte tronque l'alias, la complète sert d'info-bulle."""
    def build(alias):
        if entry["public"]:
            parts = [alias] if alias else []
            parts.append(f'{entry.get("org", "?")} - {entry.get("place", "?")}')
            text = " - ".join(parts)
        else:
            text = alias or "reseau local"
        return f'IP {index}    : {entry["ip"]}  ({text})'

    alias = entry.get("alias", "")
    return build(shorten(alias, max_alias)), build(alias)