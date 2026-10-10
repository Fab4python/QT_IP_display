"""Configuration centrale : toutes les constantes de l'application."""
import os

# --- Fenêtre ---------------------------------------------------------------
APP_TITLE = "MATRIX // NETINFO"
WINDOW_SIZE = (500, 740)  # taille initiale, carte dépliée

# --- Couleurs (thème Matrix) -----------------------------------------------
MATRIX_GREEN = "#00ff41"
MATRIX_GREEN_RGB = (0, 255, 65)
MATRIX_DIM_GREEN = "#00b32d"
MATRIX_DARK_GREEN = "#003b0f"
MATRIX_DISABLED_GREEN = "#006618"
BACKGROUND = "#000000"
WARNING_COLOR = "#ffb000"  # ambre : alerte quota
FONT_FAMILY = '"Consolas", "Courier New", monospace'
FONT_SIZE = 13

# --- Réseau (requests) ------------------------------------------------------
HTTP_HEADERS = {"User-Agent": "MatrixNetInfo/1.0 (desktop app)"}
HTTP_TIMEOUT = 5  # secondes (appels ipinfo.io)
IPINFO_SELF_URL = "https://ipinfo.io/json"
IPINFO_IP_URL = "https://ipinfo.io/{ip}/json"

# --- Carte -------------------------------------------------------------------
OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
TILE_SIZE = 256
MAP_ZOOM = 12  # 5 = pays, 8 = région, 12 = ville, 15 = quartier
MAP_WIDTH = 440
MAP_HEIGHT = 240
MAP_EXPANDED_DEFAULT = True  # carte dépliée au démarrage
MAP_MATRIX_FILTER = False  # True = carte verte, False = couleurs réelles
MARKER_COLOR = "#e60000"
MARKER_OUTLINE_COLOR = "#ffffff"

# --- Rafraîchissement automatique et quota ----------------------------------
REFRESH_MIN_SECONDS = 5
REFRESH_MAX_SECONDS = 300
REFRESH_DEFAULT_SECONDS = 30
REFRESH_STEP_SECONDS = 5          # pas du curseur
API_DAILY_LIMIT = 1000            # appels ipinfo.io par jour
DEFAULT_CALLS_PER_SCAN = 2        # estimation avant le 1er scan (1 IP + 1 DNS public)
QUOTA_FILE = os.path.join(os.path.expanduser("~"), ".matrix_netinfo", "quota.json")

# --- Séparateurs en pointillés ----------------------------------------------
SEPARATOR_COLOR = MATRIX_DIM_GREEN
SEPARATOR_DASH = 4        # longueur d'un tiret (px)
SEPARATOR_GAP = 4         # espace entre deux tirets (px)
SEPARATOR_LINE_GAP = 3    # espace entre les 2 lignes du double trait (px)

# --- Performance --------------------------------------------------------------
TILE_TIMEOUT = 4            # secondes par tuile de carte
TILE_WORKERS = 6            # tuiles téléchargées en parallèle
TILE_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".matrix_netinfo", "tiles")
TILE_CACHE_MAX_AGE = 7 * 24 * 3600   # durée de vie d'une tuile en cache (7 jours)
REVERSE_DNS_TIMEOUT = 2     # attente max du nom d'hôte (DNS inverse), en secondes

# --- Affichage -----------------------------------------------------------------
TIME_FORMAT = "%H:%M:%S"  # format de l'heure du dernier scan