"""Recherche LOCALE : ce que la machine sait d'elle-même (aucun appel Internet).

- serveurs DNS configurés sur le système, avec le nom de la carte réseau (alias)
- type d'adresse (privée / publique)
- nom d'hôte via DNS inverse
"""
import ipaddress
import json
import platform
import re
import socket
import subprocess

import config as c

IPV4_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")

# Commande PowerShell (Windows) : une entrée par carte réseau, avec son alias.
# Sortie en JSON, sans BOM, pour être lue de façon fiable par Python.
PS_DNS_COMMAND = (
    "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false; "
    "Get-DnsClientServerAddress -AddressFamily IPv4 | "
    "Select-Object InterfaceAlias, ServerAddresses | ConvertTo-Json -Compress"
)


def _run(cmd, encoding=None):
    """Lance une commande sans ouvrir de fenêtre console (Windows)."""
    flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
    return subprocess.run(
        cmd, capture_output=True, text=True, errors="ignore", encoding=encoding,
        timeout=c.LOCAL_COMMAND_TIMEOUT, creationflags=flags,
    ).stdout


# ------------------------------------------------------------ lecture des DNS
def _dns_windows_powershell():
    """[{'ip': ..., 'alias': ...}] via Get-DnsClientServerAddress."""
    out = _run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_DNS_COMMAND],
        encoding="utf-8-sig",
    )
    if not out.strip():
        return []
    data = json.loads(out)
    if isinstance(data, dict):  # une seule carte : PowerShell renvoie un objet
        data = [data]
    result = []
    for item in data:
        alias = item.get("InterfaceAlias") or ""
        addresses = item.get("ServerAddresses") or []
        if isinstance(addresses, str):
            addresses = [addresses]
        result += [{"ip": ip, "alias": alias} for ip in addresses]
    return result


def _dns_windows_ipconfig():
    """Solution de secours (sans alias) si PowerShell est indisponible."""
    servers, in_dns = [], False
    for line in _run(["ipconfig", "/all"]).splitlines():
        ips = IPV4_RE.findall(line)
        if "DNS" in line and ":" in line:
            in_dns = True
            servers += ips
        elif in_dns and ips and ":" not in line:
            servers += ips  # ligne de continuation
        else:
            in_dns = False
    return servers


def _dns_macos():
    return re.findall(r"nameserver\[\d+\]\s*:\s*(\S+)", _run(["scutil", "--dns"]))


def _dns_linux():
    with open("/etc/resolv.conf") as f:
        servers = re.findall(r"^nameserver\s+(\S+)", f.read(), re.M)
    # systemd-resolved : on n'a que le stub local, on cherche les vrais serveurs
    if all(s.startswith("127.") for s in servers):
        real = IPV4_RE.findall(_run(["resolvectl", "dns"]))
        servers = real or servers
    return servers


def _merge(entries):
    """Une ligne par IP ; si elle sert sur plusieurs cartes, les alias sont réunis."""
    merged = {}
    for e in entries:
        aliases = merged.setdefault(e["ip"], [])
        if e["alias"] and e["alias"] not in aliases:
            aliases.append(e["alias"])
    return [{"ip": ip, "alias": ", ".join(a)} for ip, a in merged.items()]


def get_dns_servers_detailed():
    """Serveurs DNS configurés : [{'ip': '192.168.0.1', 'alias': 'Wi-Fi'}, ...].
    L'alias (nom de la carte réseau) n'est disponible que sous Windows."""
    system = platform.system()
    entries = []
    try:
        if system == "Windows":
            try:
                entries = _dns_windows_powershell()
            except Exception:
                entries = []
            if not entries:
                entries = [{"ip": ip, "alias": ""} for ip in _dns_windows_ipconfig()]
        elif system == "Darwin":
            entries = [{"ip": ip, "alias": ""} for ip in _dns_macos()]
        else:
            entries = [{"ip": ip, "alias": ""} for ip in _dns_linux()]
    except Exception:
        entries = []
    return _merge(entries)


def get_dns_servers():
    """Liste simple des adresses DNS (sans alias)."""
    return [e["ip"] for e in get_dns_servers_detailed()]


# ------------------------------------------------------------------- adresses
def is_public(ip):
    """True si l'adresse est routable sur Internet."""
    try:
        a = ipaddress.ip_address(ip)
        return not (a.is_private or a.is_loopback or a.is_link_local)
    except ValueError:
        return False


def get_reverse_hostname(ip, default="n/a"):
    """Nom d'hôte associé à une IP (DNS inverse)."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return default