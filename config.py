"""Configuration centrale : toutes les constantes de l'application."""
import os

# --- Fenêtre ---------------------------------------------------------------
APP_TITLE = "MATRIX -- NETINFO EXPOSITION"
WINDOW_MIN_SIZE = (500, 740)

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
HTTP_TIMEOUT = 8  # secondes
IPINFO_SELF_URL = "https://ipinfo.io/json"
IPINFO_IP_URL = "https://ipinfo.io/{ip}/json"

# --- Carte -------------------------------------------------------------------
OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
TILE_SIZE = 256
MAP_ZOOM = 12  # 5 = pays, 8 = région, 12 = ville, 15 = quartier
MAP_WIDTH = 440
MAP_HEIGHT = 240
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