import os

ESTADOS = ["PE", "PB", "RN", "AL", "BA", "SE"]

ESCOLARIDADES_ACEITAS = ["Médio", "Superior"]

CALLMEBOT_PHONE = os.environ.get("CALLMEBOT_PHONE", "")
CALLMEBOT_APIKEY = os.environ.get("CALLMEBOT_APIKEY", "")

SEEN_FILE = os.path.join(os.path.dirname(__file__), "data", "seen.json")
