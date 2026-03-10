#script d'analyse des données
"""Analyse Descriptive :
Statistiques de base (moyenne, médiane, écart-type).

Analyse de Corrélation :

Calcule des coefficients de corrélation (Pearson, Spearman) entre l'intérêt de recherche et les variations boursières.

Analyse des corrélations avant, pendant et après les Fashion Weeks.

Analyse d'Événements (Event Study) :

Examine l'évolution de l'intérêt de recherche et des cours boursiers autour des dates clés des Fashion Weeks.

Modélisation (Optionnel) :

Tu pourrais envisager des modèles de séries temporelles (ARIMA, Prophet) ou une régression pour modéliser l'impact, en utilisant les données de Google Trends comme variable explicative."""


from pathlib import Path
import pandas as pd
import os

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_STOCK_PATH = BASE_DIR / "data" / "clean" / "stock_prices"
CLEAN_TRENDS_PATH = BASE_DIR / "data" / "clean" / "google_trends"
MASTER_DATA_PATH = BASE_DIR / "data" / "master"
MASTER_DATA_PATH.mkdir(parents=True, exist_ok=True)


