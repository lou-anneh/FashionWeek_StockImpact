#script de visulaisation des données
"""Crée des fonctions pour générer des graphiques :

Graphiques de séries temporelles : Intérêt de recherche et prix boursiers sur la même échelle de temps.

Graphiques d'événements : Zoom sur les périodes de Fashion Week, montrant l'évolution avant, pendant et après.

Heatmaps de corrélation.

Graphiques comparatifs entre différentes marques.

Enregistre les graphiques dans data/results/graphs/.

Par exemple, un graphique montrant l'intérêt de recherche pour "Chanel" superposé avec le cours de l'action LVMH (si Chanel est une marque clé pour LVMH ou une entreprise distincte cotée en bourse)."""

import matplotlib.pyplot as plt
import pandas as pd

def plot_brand_impact(df_trends, df_stock, brand_name, stock_ticker):
    fig, ax1 = plt.subplots(figsize=(12, 6))

    color = 'tab:red'
    ax1.set_xlabel('Date')
    ax1.set_ylabel(f'Google Trends Index for {brand_name}', color=color)
    ax1.plot(df_trends.index, df_trends[brand_name], color=color, label=f'{brand_name} Search Interest')
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  
    color = 'tab:blue'
    ax2.set_ylabel(f'{stock_ticker} Stock Price', color=color)  # we already handled the x-label with ax1
    ax2.plot(df_stock.index, df_stock['Close'], color=color, label=f'{stock_ticker} Close Price')
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.title(f'Google Trends vs. Stock Price for {brand_name} / {stock_ticker}')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.show()

# Exemple d'utilisation (à appeler depuis analysis.py ou notebooks)
# df_processed_trends = pd.read_csv('data/processed/processed_trends.csv', index_col='Date', parse_dates=True)
# df_processed_stock = pd.read_csv('data/processed/processed_stock_LVMH.csv', index_col='Date', parse_dates=True)
# plot_brand_impact(df_processed_trends, df_processed_stock, 'Louis Vuitton', 'LVMH')