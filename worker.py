"""Thread de travail : orchestre local_lookup + dns_lookup + map_builder
pour ne pas bloquer l'interface."""
import requests
from PySide6.QtCore import QThread, Signal

import dns_lookup
import local_lookup
import quota
from map_builder import build_map


class Worker(QThread):
    done = Signal(object)   # dict de résultats
    failed = Signal(str)    # message d'erreur

    def run(self):
        try:
            if quota.remaining_today() <= 0:
                raise RuntimeError("quota journalier d'appels atteint")
            calls_before = quota.calls_today()
            session = requests.Session()

            my_info = dns_lookup.fetch_public_ip_info(session)
            servers = local_lookup.get_dns_servers()
            dns_entries = dns_lookup.describe_dns_servers(session, servers)

            image, label = None, ""
            target = dns_lookup.pick_map_target(my_info, dns_entries)
            if target:
                lat, lon, label = target
                image = build_map(lat, lon, session)

            reverse = local_lookup.get_reverse_hostname(
                my_info.get("ip", ""), default=my_info.get("hostname", "n/a")
            )

            self.done.emit({
                "me": my_info,
                "dns": dns_entries,
                "reverse": reverse,
                "image": image,
                "label": label,
                "api_calls": quota.calls_today() - calls_before,
            })
        except Exception as e:
            self.failed.emit(str(e))