"""Thread de travail : orchestre local_lookup + dns_lookup + map_builder.

Les résultats sont envoyés AU FUR ET À MESURE (IP d'abord, puis DNS, puis carte)
et les opérations lentes tournent en parallèle."""
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from PySide6.QtCore import QThread, Signal

import config as c
import dns_lookup
import local_lookup
import quota
from map_builder import build_map


class Worker(QThread):
    ip_ready = Signal(object)         # infos de la connexion (dict)
    host_ready = Signal(str)          # nom d'hôte (DNS inverse)
    dns_ready = Signal(object)        # liste des IP / DNS décrits
    map_ready = Signal(object, str)   # QImage (ou None), libellé
    done = Signal(object)             # fin du scan : {"api_calls": n}
    failed = Signal(str)

    def run(self):
        try:
            if quota.remaining_today() <= 0:
                raise RuntimeError("quota journalier d'appels atteint")
            calls_before = quota.calls_today()
            session = requests.Session()

            # 1) IP publique (ce thread) pendant que les DNS locaux sont lus à côté
            with ThreadPoolExecutor(max_workers=1) as pool:
                f_servers = pool.submit(local_lookup.get_dns_servers_detailed)
                my_info = dns_lookup.fetch_public_ip_info(session)
                self.ip_ready.emit(my_info)  # l'IP s'affiche tout de suite
                servers = f_servers.result()

            # 2) Nom d'hôte : fourni par ipinfo, sinon DNS inverse en tâche de fond
            #    (peut être très lent s'il n'existe pas, on ne l'attend pas longtemps)
            reverse_thread, reverse_box, reverse_deadline = None, {}, 0
            if my_info.get("hostname"):
                self.host_ready.emit(my_info["hostname"])
            else:
                ip = my_info.get("ip", "")
                reverse_thread = threading.Thread(
                    target=lambda: reverse_box.update(
                        name=local_lookup.get_reverse_hostname(ip)),
                    daemon=True,
                )
                reverse_thread.start()
                reverse_deadline = time.monotonic() + c.REVERSE_DNS_TIMEOUT

            # 3) DNS : localisation des serveurs publics en parallèle
            entries = dns_lookup.describe_dns_servers(session, [s["ip"] for s in servers])
            for entry, s in zip(entries, servers):
                entry["alias"] = s["alias"]  # nom de la carte réseau (Windows)
            self.dns_ready.emit(entries)

            # 4) Carte
            image, label = None, ""
            target = dns_lookup.pick_map_target(my_info, entries)
            if target:
                lat, lon, label = target
                try:
                    image = build_map(lat, lon, session)
                except Exception:
                    image = None
            self.map_ready.emit(image, label)

            # 5) Nom d'hôte (attente plafonnée)
            if reverse_thread is not None:
                # le délai court depuis le lancement : on n'attend que le reste
                reverse_thread.join(timeout=max(0, reverse_deadline - time.monotonic()))
                self.host_ready.emit(reverse_box.get("name", "n/a"))

            self.done.emit({"api_calls": quota.calls_today() - calls_before})
        except Exception as e:
            self.failed.emit(str(e))