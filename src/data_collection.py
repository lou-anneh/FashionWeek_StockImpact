"""
This file aims at collecting and preprocessing data for analysis.

Google Trends :
Utilise la bibliothèque pytrends pour interroger l'API de Google Trends.
Pour chaque marque listée dans config.ini, récupère les données d'intérêt de recherche pour la plage de dates définie.
Enregistre les données brutes dans data/raw/google_trends/.

Données Boursières :
Utilise une bibliothèque comme yfinance pour récupérer les données historiques des cours de bourse (prix d'ouverture, de clôture, haut, bas, volume) pour les marques cotées en bourse.
Assure-toi de mapper correctement les noms des marques aux symboles boursiers (par exemple, LVMH pour Louis Vuitton/Dior, Kering pour Gucci).
Enregistre les données brutes dans data/raw/stock_prices/.
"""

import pandas as pd
import yfinance as yf
from pytrends.request import TrendReq
import configparser
import os
import time
import json
from datetime import datetime

# --- CONFIGURATION ---
# Chargement du fichier config.ini
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '../config/config.ini'))

# Création des dossiers de sortie s'ils n'existent pas
RAW_DATA_PATH = os.path.join(os.path.dirname(__file__), '../data/raw')
os.makedirs(os.path.join(RAW_DATA_PATH, 'google_trends'), exist_ok=True)
os.makedirs(os.path.join(RAW_DATA_PATH, 'stock_prices'), exist_ok=True)

def collect_stock_data():
    """
    Récupère les données boursières via yfinance pour chaque ticker unique défini dans la config.
    """
    print("--- Démarrage de la collecte des données Boursières (yfinance) ---")
    
    # Récupération et parsing du dictionnaire des tickers depuis le config, transforme un dict
    tickers_dict = json.loads(config['BRANDS']['stock_tickers'].replace("'", '"'))
    
    # On ne veut télécharger chaque ticker qu'une seule fois (ex: LVMH sert pour Dior et LV)
    unique_tickers = set(tickers_dict.values())
    
    start_date = config['DATES']['start_date']
    end_date = config['DATES']['end_date']

    for ticker in unique_tickers:
        print(f"Téléchargement des données pour : {ticker}")
        try:
            # Téléchargement via yfinance
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if not df.empty:
                # Sauvegarde en CSV
                file_path = os.path.join(RAW_DATA_PATH, 'stock_prices', f'{ticker}_stock.csv')
                if os.path.exists(file_path):
                    print(f"⚠️ Attention : {file_path} existe déjà.")
                    continue_input = input("\n Voulez-vous continuer et écraser le fichier existant ? (y/n) : ")
                    if continue_input.lower() != 'y':
                        print(f"⛔ Skipping {ticker}...")
                        continue
                    else: 
                        print(f"⚠️ Écrasement de {file_path}...")
                        df.to_csv(file_path)
                        print(f"✅ Succès : {ticker} sauvegardé dans {file_path}")
                else:
                    df.to_csv(file_path)
                    print(f"✅ Succès : {ticker} sauvegardé dans {file_path}")
            else:
                print(f"⚠️ Attention : Aucune donnée trouvée pour {ticker}")
                
        except Exception as e:
            print(f"❌ Erreur pour {ticker}: {e}")

    print("--- Fin de la collecte Boursière ---\n")


def collect_google_trends_data():
    """
    Récupère les données Google Trends via pytrends.
    Gère les délais pour éviter le blocage par l'API Google (Error 429).
    """
    print("--- Démarrage de la collecte Google Trends (pytrends) ---")
    
    # Initialisation de pytrends
    # hl='en-US' pour avoir les résultats globaux en anglais, tz=360 pour le fuseau horaire
    pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
    
    keywords_list = config['BRANDS']['google_keywords'].split(', ')
    start_date = config['DATES']['start_date']
    end_date = config['DATES']['end_date']
    
    # Google Trends change sa granularité selon la durée.
    # Pour plusieurs années, il donne souvent des données hebdomadaires.
    timeframe = f'{start_date} {end_date}'

    # Google Trends permet de comparer jusqu'à 5 mots clés, mais ici on veut l'absolu (ou relatif global)
    # pour chaque marque individuellement pour éviter d'écraser les petites marques par les grosses dans le scaling.
    # On traite donc marque par marque.
    
    for keyword in keywords_list:
        print(f"Récupération des trends pour : {keyword}")
        try:
            # Construction de la requête
            pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo='', gprop='')
            
            # Récupération de l'intérêt au fil du temps
            data = pytrends.interest_over_time()
            
            if not data.empty:
                # Suppression de la colonne 'isPartial' si elle existe (souvent la dernière semaine incomplète)
                if 'isPartial' in data.columns:
                    del data['isPartial']
                
                # Sauvegarde en CSV
                safe_name = keyword.replace(' ', '_') # ex: "Louis Vuitton" -> "Louis_Vuitton"
                file_path = os.path.join(RAW_DATA_PATH, 'google_trends', f'{safe_name}_trends.csv')
                if os.path .exists(file_path):
                    #ajout d'une vérification de l'existence du fichier pour éviter d'écraser les données précédentes
                    #si changement de date dans le fichier config.ini, il est préférables de supprimer les fichiers existants dans data/raw/ 
                    #Si changement de nom de marque ou de tickers, supprimer seulement les fichiers concernés, 
                    #cela évite de renquêter à nouveau les données pour les marques qui n'ont pas changé, permet d'éviter d'être bloqué par Google pour trop de requêtes et de gagner du temps.
                    print(f"⚠️ Attention : {file_path} existe déjà.")
                    continue_input = input("\n Voulez-vous continuer et écraser le fichier existant ? (y/n) : ")
                    if continue_input.lower() != 'y':
                        print(f"⛔ Skipping {keyword}...")
                        continue
                    else: 
                        print(f"⚠️ Écrasement de {file_path}...")                     
                        data.to_csv(file_path)
                        print(f"✅ Succès : {keyword} sauvegardé dans {file_path}")
            else:
                print(f"⚠️ Attention : Aucune donnée trouvée pour {keyword}")
            
            # PAUSE IMPORTANTE : Google bloque si on requête trop vite.
            # On attend un temps aléatoire entre 2 et 5 secondes entre chaque requête.
            sleep_time = 5
            print(f"Pause de {sleep_time} secondes pour ménager l'API...")
            time.sleep(sleep_time)

        except Exception as e:
            print(f"❌ Erreur lors de la récupération pour {keyword}: {e}")
            if "429" in str(e):
                print("⛔ ERREUR 429 : Trop de requêtes. Arrêt du script. Réessayez plus tard.")
                break

    print("--- Fin de la collecte Google Trends ---")

if __name__ == "__main__":
    # Exécution des fonctions principales
    collect_stock_data()
    collect_google_trends_data()