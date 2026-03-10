""" Data Merging       
"""

from pathlib import Path
import pandas as pd
import json
import configparser

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parent.parent
print(f"Base directory : {BASE_DIR}")
CLEAN_STOCK_PATH = BASE_DIR / "data" / "clean" / "stock_prices"
CLEAN_TRENDS_PATH = BASE_DIR / "data" / "clean" / "google_trends"
TEST_DATA_PATH = BASE_DIR / "data" / "test"
TEST_DATA_PATH.mkdir(parents=True, exist_ok=True)

# Chargement du fichier config.ini
CONFIG_PATH=BASE_DIR/"config"/"config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

def merge_brand_data(brand_name, ticker):
    print(f"--- Fusion des données pour {brand_name} ({ticker}) ---")
    
    # 1. Chargement des fichiers propres
    stock_file = CLEAN_STOCK_PATH / f"{ticker}_processed.csv" 
    trends_file = CLEAN_TRENDS_PATH / f"{brand_name.replace(' ', '_')}_trends_clean.csv"
    
    if not stock_file.exists() or not trends_file.exists():
        print(f"⚠️ Fichiers manquants pour {trends_file}. Vérifie data/clean/.")
        return None

    df_stock = pd.read_csv(stock_file, index_col='Date', parse_dates=True)
    df_trends = pd.read_csv(trends_file, index_col='Date', parse_dates=True)

    # 2. Le Merge (Fusion)
    # On utilise un 'inner' join pour ne garder que les dates présentes dans les DEUX fichiers
    merge_df = pd.merge(df_stock, df_trends, left_index=True, right_index=True, how='inner')
    
    if len(merge_df) != len(df_stock) or len(merge_df) != len(df_trends):
        print("⚠️ Avertissement : Les DataFrames n'ont pas le même nombre de lignes après le merge.")
        print(f"Nombre de lignes dans df_stock : {len(df_stock)}")
        print(f"Nombre de lignes dans df_trends : {len(df_trends)}")
        print(f"Nombre de lignes dans merge_df : {len(merge_df)}")
    
        #afficher les lignes qui n'ont pas été mergées
        stock_only = df_stock[~df_stock.index.isin(merge_df.index)]
        trends_only = df_trends[~df_trends.index.isin(merge_df.index)]
    
        print(f"Dates présentes uniquement dans df_trends : {trends_only.index.tolist()}")
        print(f"Dates présentes uniquement dans df_stock : {stock_only.index.tolist()}")
    
    # 3. Feature Engineering Final : Le décalage (Lag)
    # Hypothèse : l'impact boursier arrive peut-être 1 semaine APRÈS le pic de recherche
    merge_df['Search_Lag_1'] = merge_df['Search'].shift(1)

    # 4. Sauvegarde du fichier maître
    output_file = TEST_DATA_PATH / f"{brand_name.replace(' ', '_')}_merge.csv"
    merge_df.to_csv(output_file)
    print(f"✅ Fichier mergé créé : {output_file}")
    
    return merge_df

def main() :
    # Récupération et parsing du dictionnaire des tickers depuis le config, transforme un dict
    tickers_dict = json.loads(config['BRANDS']['stock_tickers'].replace("'", '"'))
    keywords_list = config['BRANDS']['google_keywords'].split(', ')

    for keyword in keywords_list :
        safe_name = keyword.replace(' ', '_') # ex: "Louis Vuitton" -> "Louis_Vuitton"
        df = merge_brand_data(safe_name, tickers_dict[keyword])
        if df is None:
            print(f"❌ Erreur lors de la fusion des données pour {keyword}")

if __name__ == "__main__":
    main()
