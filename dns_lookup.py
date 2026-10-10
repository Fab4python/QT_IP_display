"""Définition de l'adresse DNS / IP : identification et géolocalisation
via Internet (requests + ipinfo.io). Aucune dépendance à Qt."""
import requests

import config as c
import quota
from local_lookup import is_public


def _get_json(session, url):
    quota.record_call()  # chaque appel ipinfo.io compte dans le quota
    r = session.get(url, headers=c.HTTP_HEADERS, timeout=c.HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()


def fetch_public_ip_info(session):
    """Infos sur la connexion actuelle : ip, org, ville, pays, loc, fuseau."""
    return _get_json(session, c.IPINFO_SELF_URL)


def describe_dns_server(session, ip):
    """Décrit un serveur DNS : public/local, opérateur, lieu, coordonnées."""
    entry = {"ip": ip, "public": is_public(ip)}
    if entry["public"]:
        try:
            info = _get_json(session, c.IPINFO_IP_URL.format(ip=ip))
            entry.update(
                org=info.get("org", "?"),
                place=f'{info.get("city", "?")}, {info.get("country", "?")}',
                loc=info.get("loc"),
            )
        except requests.RequestException:
            pass
    return entry


def describe_dns_servers(session, servers):
    return [describe_dns_server(session, ip) for ip in servers]


def pick_map_target(my_info, dns_entries):
    """Choisit les coordonnées à afficher : 1er DNS public localisé,
    sinon la position de l'IP publique. Retourne (lat, lon, libellé) ou None."""
    for d in dns_entries:
        if d.get("loc"):
            lat, lon = map(float, d["loc"].split(","))
            return lat, lon, f'IP {d["ip"]}'
    if my_info.get("loc"):
        lat, lon = map(float, my_info["loc"].split(","))
        return lat, lon, "IP publique"
    return None