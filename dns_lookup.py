"""Définition de l'adresse DNS / IP : identification et géolocalisation
via Internet (requests + ipinfo.io). Aucune dépendance à Qt."""
from concurrent.futures import ThreadPoolExecutor

import requests

import config as c
import quota
from local_lookup import is_public

# Lieu des serveurs DNS déjà connu : un serveur DNS ne déménage pas, inutile de
# le redemander à chaque scan (plus rapide, et moins d'appels sur le quota).
_DNS_CACHE = {}


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
    if ip in _DNS_CACHE:
        return dict(_DNS_CACHE[ip])
    entry = {"ip": ip, "public": is_public(ip)}
    if entry["public"]:
        try:
            info = _get_json(session, c.IPINFO_IP_URL.format(ip=ip))
            entry.update(
                org=info.get("org", "?"),
                place=f'{info.get("city", "?")}, {info.get("country", "?")}',
                loc=info.get("loc"),
            )
            _DNS_CACHE[ip] = dict(entry)
        except requests.RequestException:
            pass
    return entry


def describe_dns_servers(session, servers):
    """Décrit tous les serveurs en parallèle (au lieu d'un par un)."""
    if not servers:
        return []
    with ThreadPoolExecutor(max_workers=len(servers)) as pool:
        return list(pool.map(lambda ip: describe_dns_server(session, ip), servers))


def pick_map_target(my_info, dns_entries):
    """Choisit les coordonnées à afficher : 1er DNS public localisé,
    sinon la position de l'IP publique. Retourne (lat, lon, libellé) ou None."""
    for d in dns_entries:
        if d.get("loc"):
            lat, lon = map(float, d["loc"].split(","))
            return lat, lon, f'DNS {d["ip"]}'
    if my_info.get("loc"):
        lat, lon = map(float, my_info["loc"].split(","))
        return lat, lon, "IP publique"
    return None