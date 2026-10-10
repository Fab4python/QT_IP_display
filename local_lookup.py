"""Recherche LOCALE : ce que la machine sait d'elle-même (aucun appel Internet).

- serveurs DNS configurés sur le système
- type d'adresse (privée / publique)
- nom d'hôte via DNS inverse
"""
import ipaddress
import platform
import re
import socket
import subprocess

IPV4_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")


def _run(cmd):
    flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
    return subprocess.run(
        cmd, capture_output=True, text=True, errors="ignore", creationflags=flags
    ).stdout


def _dns_windows():
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


def get_dns_servers():
    """Retourne la liste (sans doublons) des serveurs DNS configurés."""
    system = platform.system()
    try:
        if system == "Windows":
            servers = _dns_windows()
        elif system == "Darwin":
            servers = _dns_macos()
        else:
            servers = _dns_linux()
    except Exception:
        servers = []
    return list(dict.fromkeys(servers))


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