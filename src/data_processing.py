#Script de traitement des données
"""Nettoyage des Données :

Stock_Prices :
0- Gérer le formatage multiindex de yfinance : les données téléchargées ont souvent un multiindex avec le nom du ticker, il faut le supprimer pour faciliter le traitement.
1- Gérer les valeurs manquantes :
Lorsque la bourse est fermée (week-end, jours fériés), il n'y a pas de données. On peut choisir de laisser ces dates avec des valeurs manquantes ou de les supprimer. 
Si on choisit de les laisser, on peut imputer les valeurs manquantes en utilisant la dernière valeur connue (forward fill) ou la prochaine valeur connue (backward fill).
Ici on va sélectionner en forward fill pour les données boursières, cela permet de conserver les périodes sans données (ex: week-end) tout en évitant les trous dans la série temporelle.
Ou suppression des lignes/colonnes avec trop de valeurs manquantes.
2- Gérer les valeurs aberrantes :
Identifier les valeurs aberrantes (ex: prix négatifs, volumes anormalement élevés) et décider de les corriger ou de les supprimer.
ré-échantillonner (resample) les données boursières pour qu'elles correspondent aux semaines de Google Trends (ou l'inverse). On stocke d'abord les données brutes telles quelles.
Normalise les données si nécessaire (par exemple, mise à l'échelle des données Google Trends et boursières pour les rendre comparables).

Google_Trends :
1- Gérer les valeurs manquantes :
Google Trends peut ne pas fournir de données pour certaines périodes ou certains mots-clés. On peut choisir de laisser ces dates avec des valeurs manquantes ou de les supprimer.
Si on choisit de les laisser, on peut imputer les valeurs manquantes en utilisant la moyenne des valeurs précédentes et suivantes, ou en utilisant une méthode d'interpolation.
2- Gérer les valeurs aberrantes :
Identifier les valeurs aberrantes (ex: pics d'intérêt soudains) et décider de les corriger ou de les supprimer.

Alignement Temporel :
Il faut s'assurer que les données Google Trends et boursières sont alignées sur les mêmes dates.

Création de Caractéristiques (Feature Engineering) :
Ajoute des colonnes indiquant les périodes de Fashion Week par une colonne booléenne "is_fashion_week" True/False.
Calcule des indicateurs de changement (par exemple, variation quotidienne du prix, variation hebdomadaire de l'intérêt de recherche).
Enregistre les données traitées dans data/clean/.
"""

#Récupérer les données brutes depuis data/raw/, effectuer le nettoyage et les transformations nécessaires, puis sauvegarder les données traitées dans data/processed/ pour une utilisation ultérieure dans l'analyse et la visualisation.
from pathlib import Path
from matplotlib import ticker
import pandas as pd
import numpy as np
import os   
import json
import configparser

from sklearn.utils import resample


# --- CHEMINS ---
#os VS path: os.path.join() est plus compatible entre les systèmes d'exploitation et opère sur les string
#tandis que pathlib offre une syntaxe plus moderne et orientée objet.
current_file = Path(__file__).resolve()
src_dir = current_file.parent
BASE_DIR = src_dir.parent
print(f"Base directory : {BASE_DIR}")

RAW_DATA_PATH =BASE_DIR/"data"/"raw"
#PROCESSED_DATA_DIR = BASE_DIR/"data"/"processed"

#---- CONFIG ----
# Chargement du fichier config.ini
CONFIG_PATH=BASE_DIR/"config"/"config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

# Création des dossiers de sortie des données nettoyées s'ils n'existent pas
CLEAN_DATA_PATH = BASE_DIR/"data"/"clean"
TRENDS_CLEAN_PATH = CLEAN_DATA_PATH / "google_trends"
STOCKS_CLEAN_PATH = CLEAN_DATA_PATH / "stock_prices"

# Récupération des dates des FW dans le fichier de config

start_date_fw = config['DATES']['start_date']

# Création des dossiers (parents=True crée aussi 'data' et 'clean' s'ils manquent)
#parents=True pour créer les dossiers parents s'ils n'existent pas, exist_ok=True pour éviter une erreur si le dossier existe déjà
TRENDS_CLEAN_PATH.mkdir(parents=True, exist_ok=True)
STOCKS_CLEAN_PATH.mkdir(parents=True, exist_ok=True)

# for trend_csv in os.listdir(os.path.join(os.path.dirname(__file__), '../data/raw/google_trends')):

# for stock_csv in os.listdir(os.path.join(os.path.dirname(__file__), '../data/raw/stock_prices')):
    
#fonction de parsing des dates de FW pour différentes saison et différentes villes
def get_fashion_week_periods(config, city):
    """
    Extrait les périodes de Fashion Week pour une ville donnée depuis le fichier de config.
    
    Args:
        config: ConfigParser object
        city: str, ex: "Paris", "Milan", "London", "New York" 
    
    Returns:
        list of tuples: [(start_date, end_date), ...]
    """
    #conversion pour matcher avec les clés ex : new_york_ss20
    city_key = city.lower().replace(' ', '_')  # "New York" -> "new_york"
    periods = []
    
    #on récupère tous les couples sous forme de tuples : 
    #("new_york_ss20", "2019-09-06, 2019-09-12")
    for key, value in config['FASHION_WEEKS'].items():
        # On filtre les clés qui correspondent à la ville et divise en 2 termes en supprimant les espaces
        if key.startswith(city_key + '_'):
            dates = [d.strip() for d in value.split(',')]
            start = pd.Timestamp(dates[0]) #conversion en timestamp
            end = pd.Timestamp(dates[1])
            periods.append((start, end))
            # Résultat pour "New York" :
            # [(Timestamp('2019-09-06'), Timestamp('2019-09-12')),
    
    return periods


#fonction définissant si une semaine est en période de fashion week
# !!!pb de chevauchement car nos dates sont basées sur le dimanche (W-SUN)
#et que les FW commencent le mercredi 
# + !! la FW 2020 commence en 2019

def is_in_fashion_week(date, fw_periods):
    """
    Vérifie si une date (fin de semaine W-SUN) chevauche une période de FW.
    La semaine couvre [date - 6 jours, date].
    
    Args:
        date: pd.Timestamp (fin de semaine, dimanche)
        fw_periods: list of tuples [(start, end), ...]
    
    Returns:
        bool
    """
    week_start = date - pd.Timedelta(days=6)
    week_end = date
    
    for fw_start, fw_end in fw_periods:
        # Chevauchement si : semaine_start <= fw_end ET semaine_end >= fw_start
        if week_start <= fw_end and week_end >= fw_start:
            return True
    return False


#focntion de traitement des données boursières        
def process_stock_data(ticker):
    """
    Traite les données boursières : nettoyage, gestion des valeurs manquantes, création de caractéristiques, etc.
    Enregistre les données traitées dans data/processed/stock_prices/.
    """
    print(f"Traitement des actions pour : {ticker}")
    file_path=os.path.join(RAW_DATA_PATH, 'stock_prices', f'{ticker}_stock.csv')
    
    if not os.path.exists(file_path):
        print(f"⚠️ Fichier introuvable : {file_path}")
        return None
    
    df = pd.read_csv(file_path)
    
    #supprimer la 1ere ligne qui contient le nom du ticker et la 2eme ligne qui contient date et des Nan
    df = df.drop([0,1])

    #se débarasser du multiindex créé par yfinance (Price et Date sont sur 2 lignes différentes)
    df.rename(columns={'Price': 'Date'}, inplace=True)

    #réinitialiser les index après suppression
    df = df.reset_index(drop=True)

    #arrondir les valeurs à 2 décimales
    df['Open'] = df['Open'].astype(float).round(2)
    df['High'] = df['High'].astype(float).round(2)
    df['Low'] = df['Low'].astype(float).round(2)
    df['Close'] = df['Close'].astype(float).round(2)

    index_with_nan = df.index[df.isnull().any(axis=1)]
    if not index_with_nan.empty:
        print(f"⚠️ Attention : Valeurs manquantes trouvées aux index suivants : {index_with_nan.tolist()}")
        df = df.ffill()
    
    #Les dates sont type object open en float et volume en object
    #Conversion de date en datetime et volume en int
    df['Date'] = pd.to_datetime(df['Date'])
    df['Volume'] = df['Volume'].astype(int)
    
    #problème : les données sont en daily alors que les données Google Trends sont en hebdo, 
    # est ce que je réechantillone les données boursières en hebdo ou est ce que je fais un join avec les données Google Trends qui sont déjà en hebdo ?
    #Join compliqué car les dates de google trends sont basées sur le dimanche alors que les données boursières sont basées sur les jours de la  semaine
  
    # 3. Ré-échantillonnage (Resampling) en Hebdomadaire (Weekly - 'W')
    # Est ce que je réechantillone directe en hebdo ou je fais un join avec les données Google Trends qui sont déjà en hebdo ?
    # join basé sur la date 

    # On aligne sur le Dimanche ('W-SUN') pour matcher Google Trends
    # Logique d'agrégation :
    # - Open : Premier prix de la semaine
    # - High : Prix max de la semaine
    # - Low : Prix min de la semaine
    # - Close : Dernier prix de la semaine
    # - Volume : Somme des volumes de la semaine
    #Pandas va mettre la colonne Date en INDEX et non en colonne ordinaire, alors il sera légérement décalé
    df.set_index('Date', inplace=True)

    df = df.resample('W-SUN').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })
    # 4. Feature Engineering (Création de nouvelles colonnes utiles)
    # Calcul du rendement hebdomadaire en % : (Prix Fin - Prix Début) / Prix Début
    #pct_change() (percentage chnage) calcule la variation du pourcentage entre une ligne et la précédente, ce qui correspond au rendement hebdomadaire dans ce cas.

    df = df.copy() # Utiliser df (qui est déjà weekly) pour éviter de réappliquer le resample
    df['Weekly_Return'] =df['Close'].pct_change().round(4)
    
    # Volatilité en % (écart-type des rendements sur une fenêtre glissante, ex: 4 semaines)
    #Intéressant dans nore cas pour voir si la volatilité augmente pendant les Fashion Weeks, ce qui pourrait indiquer une incertitude accrue des investisseurs (marché nerveux)
    df = df.copy()
    df['Volatility_4W'] = df['Weekly_Return'].rolling(window=4).std().round(4)
    
 
# 5. Nettoyage final (suppression des lignes vides créées par le pct_change au début)
    df.dropna(inplace=True)
    print(df.head(5))
    
    return df

#              Open    High     Low   Close    Volume  Weekly_Return  Volatility_4W
# Date
# 2020-02-02  365.38  381.48  357.40  358.49   4926090        -0.0504         0.0444
# 2020-02-09  357.90  380.98  354.63  375.40   3268543         0.0472         0.0538
# 2020-02-16  372.73  385.15  371.55  376.31   2673984         0.0024         0.0475
# 2020-02-23  377.03  380.43  365.65  366.83   2629901        -0.0252         0.0418

   
#focntion de traitement des données Google Trends        
def process_trend_data(brand):
    """
    Traite les données Google Trends : nettoyage, gestion des valeurs manquantes, création de caractéristiques, etc.
    Enregistre les données traitées dans data/clean/google_trends/.
    """
    print(f"Traitement des tendances pour : {brand}")
    
    
    #récupérer la ville de Fashion Week associée à la marque depuis le config.ini pour créer une colonne is_fashion_week
    brand_fw_dict = json.loads(config['BRANDS']['brands_fw'].replace("'", '"'))
    safe_name = brand.replace('_', ' ') # ex: "Louis_Vuitton" -> "Louis Vuitton"
    city = brand_fw_dict.get(safe_name, None)
                                                                                                                                 
    file_path=os.path.join(RAW_DATA_PATH, 'google_trends', f'{brand}_trends.csv')
    df = pd.read_csv(file_path)
    
    col_name=df.columns[1] # la 1ère colonne est "date", la 2ème colonne porte le nom de la marque (ex: "Ralph Lauren")
    df.rename(columns={col_name: 'Search'}, inplace=True)
    df.rename(columns={'date': 'Date'}, inplace=True)
    
    # 2. Nettoyage des données "<1"
    # Google met "<1" quand le volume est très faible. C'est du texte, il faut le passer en nombre.
    # On remplace "<1" par 0.5 (valeur arbitraire faible) ou 0.
    if df['Search'].dtype == object: # Si la colonne est considérée comme du texte
        df['Search'] = df['Search'].replace('<1', '0.5')
        df['Search'] = pd.to_numeric(df['Search'])
    
    #convertir en date (timestamp)
    df['Date'] = pd.to_datetime(df['Date'])
    
    #2- Gérer les valeurs manquantes : 
    # les remplacer par la méthode de forward fill (ffill) qui propage la dernière valeur valide connue vers les valeurs manquantes suivantes,
    # ce qui est logique pour les données boursières (le prix ne change pas si la bourse est fermée).
    # 2. Gestion des données manquantes (jours fériés boursiers)

    index_with_nan = df.index[df.isnull().any(axis=1)]
    if not index_with_nan.empty:
        print(f"⚠️ Attention : Valeurs manquantes trouvées aux index suivants : {index_with_nan.tolist()}")
        df = df.ffill()
        
    #Pour être sur les mêmes index que les données boursières, on peut faire df.set_index('Date') pour la mettre en index.
    df.set_index('Date', inplace=True)

    # 3. Ré-échantillonnage pour être sûr d'avoir des semaines complètes finissant le Dimanche
    # Même si Trends est déjà hebdomadaire, cela force l'alignement des dates avec la Bourse
    df = df.resample('W-SUN').mean()

    # 4. Feature Engineering (Création de nouvelles colonnes utiles)
    # Lissage : moyenne mobile sur 4 semaines pour lisser les évéentuels pics et voir les tendances
    df['Interest_MA4'] = df['Search'].rolling(window=4).mean()
    
    #Créatoin de la colonne "is_fashion_week", colonne de booléen basée sur les dates de Fashion Week de la ville associée à la marque
    #True (période de FW)
    if city:
        fw_periods = get_fashion_week_periods(config, city)
        #df.index contient les
        df['is_fashion_week'] = df.index.map(
            lambda date: is_in_fashion_week(date, fw_periods)
        )
        print(f"   → {city} : {len(fw_periods)} périodes FW chargées")
        print(f"   → Semaines en FW : {df['is_fashion_week'].sum()}")
    else:
        print(f"⚠️ Aucune FW trouvée pour {brand}")
        df['is_fashion_week'] = False

    #Suppression des elements NAN crées par le rolling (les 3 premières lignes) et les éventuelles lignes vides restantes
    df.dropna(inplace=True)
    print(df.head(5))

    
    return df
                
def main():
         
    # Récupération et parsing du dictionnaire des tickers depuis le config, transforme un dict
    tickers_dict = json.loads(config['BRANDS']['stock_tickers'].replace("'", '"'))
    
    unique_tickers = set(tickers_dict.values())
    for ticker in unique_tickers:
        #mettre une condition pour ne pas rééxécuter le traitement si le fichier traité existe déjà dans data/processed/stock_prices/
        #ou l'écraser si l'utilisateur le souhaite
        output_path = os.path.join(STOCKS_CLEAN_PATH , f'{ticker}_processed.csv')
        if os.path.exists(output_path):
            print(f"⚠️ Attention : {output_path} existe déjà.")
            continue_input = input("\n Voulez-vous continuer et écraser le fichier existant ? (y/n) : ")
            if continue_input.lower() != 'y':
                print(f"⛔ Skipping {ticker}...")
                continue
            else: 
                print(f"⚠️ Écrasement de {output_path}...")
                df = process_stock_data(ticker)
                df.to_csv(output_path)
                print(f"✅ Succès : {ticker} sauvegardé dans {output_path}")
        else:
            df = process_stock_data(ticker)
            df.to_csv(output_path)
            print(f"✅ Succès : {ticker} sauvegardé dans {output_path}") 
    
    keywords_list = config['BRANDS']['google_keywords'].split(', ')
    
    for keyword in keywords_list :
        safe_name = keyword.replace(' ', '_') # ex: "Louis Vuitton" -> "Louis_Vuitton"
        output_path = os.path.join(TRENDS_CLEAN_PATH , f'{safe_name}_trends_clean.csv')
        if os.path.exists(output_path):
            print(f"⚠️ Attention : {output_path} existe déjà.")
            continue_input = input("\n Voulez-vous continuer et écraser le fichier existant ? (y/n) : ")
            if continue_input.lower() != 'y':
                print(f"⛔ Skipping {keyword}...")
                continue
            else: 
                print(f"⚠️ Écrasement de {output_path}...")
                df = process_trend_data(safe_name)
                df.to_csv(output_path)
                print(f"✅ Succès : {keyword} sauvegardé dans {output_path}")
        else:
            df = process_trend_data(safe_name)
            df.to_csv(output_path)
            print(f"✅ Succès : {keyword} sauvegardé dans {output_path}")
        
if __name__ == "__main__":    
    main()
    