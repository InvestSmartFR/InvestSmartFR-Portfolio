# -*- coding: utf-8 -*-
"""Portefeuille Dynamique USD"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def simulate_portfolio(monthly_investment=100, initial_investment=10000):
    """
    Simule le portefeuille dynamique USD avec un investissement initial et des contributions mensuelles (DCA).
    
    Args:
        monthly_investment (int): Montant investi chaque mois (€).
        initial_investment (int): Investissement initial (€).
        
    Returns:
        dict: Résultats de la simulation et DataFrame contenant les valeurs simulées.
    """
    # Charger les fichiers Excel
    files = {
        "US Treasury Bond": "Us Treasury Bond 3-7Y.xlsx",
        "US Short Duration": "Short duration USD Corp.xlsx",
        "S&P 500": "IShares Core SP500.xlsx",
        "Nasdaq": "AMUNDI NASDAQ.xlsx",
        "Small Cap": "S&P SmallCap 600.xlsx",
        "Mid Cap": "S&P 400 US Mid Cap.xlsx",
    }

    # Lire les fichiers Excel
    dfs = {key: pd.read_excel(path) for key, path in files.items()}

    # Définir les frais courants pour chaque support
    fees = {
        "US Treasury Bond": 0.0007,     # 0.07%
        "US Short Duration": 0.0045,    # 0.45%
        "S&P 500": 0.0007,              # 0.07%
        "Nasdaq": 0.0022,               # 0.22%
        "Small Cap": 0.0014,            # 0.14%
        "Mid Cap": 0.0030,              # 0.30%
    }

    # Prétraitement des fichiers
    def preprocess_data(df, column_name, start_date, fee_rate):
        """
        Prépare les données : format datetime, trie par date croissante, applique les frais courants.
        """
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['Date']).sort_values(by='Date', ascending=True).reset_index(drop=True)
        df = df[df['Date'] >= start_date]  # Limiter à partir de start_date
        df.rename(columns={'NAV': column_name}, inplace=True)

        # Appliquer les frais courants (annuels transformés en journaliers)
        daily_fee_rate = (1 - fee_rate) ** (1 / 252)
        df[column_name] *= daily_fee_rate ** np.arange(len(df))
        return df

    # Définir la date de départ
    start_date = pd.to_datetime("2017-10-09")

    # Préparer chaque fichier
    for key, df in dfs.items():
        dfs[key] = preprocess_data(df, key, start_date, fees[key])

    # Fusionner les données sur la base des dates
    df_combined = dfs["US Treasury Bond"]
    for key in list(dfs.keys())[1:]:
        df_combined = pd.merge(df_combined, dfs[key][['Date', key]], on='Date', how='outer')

    # Trier et interpoler/remplir les valeurs manquantes
    df_combined = df_combined.sort_values(by='Date', ascending=True).reset_index(drop=True)
    numeric_cols = df_combined.select_dtypes(include=[np.number]).columns
    df_combined[numeric_cols] = (
        df_combined[numeric_cols]
        .interpolate(method='linear', axis=0)
        .ffill()
        .bfill()
    )

    # Définir les pondérations du portefeuille
    weights = {
        'US Treasury Bond': 0.20,
        'US Short Duration': 0.10,
        'S&P 500': 0.40,
        'Nasdaq': 0.10,
        'Small Cap': 0.10,
        'Mid Cap': 0.10,
    }

    # Calculer la valeur du portefeuille
    def calculate_portfolio_value(df, weights):
        """
        Calcule la valeur totale pondérée du portefeuille.
        """
        portfolio_value = sum(
            weights[col] * df[col] / df[col].iloc[0] for col in weights
        ) * initial_investment
        return portfolio_value

    df_combined['Portfolio_Value'] = calculate_portfolio_value(df_combined, weights)

    # Simulation DCA
    def simulate_dca(df, monthly_investment):
        """
        Simule un investissement mensuel (DCA).
        """
        portfolio_value = []
        total_invested = 0

        for i, row in df.iterrows():
            if i % 21 == 0:  # Approximation d'un mois
                total_invested += monthly_investment
            portfolio_value.append(row['Portfolio_Value'] * (total_invested / initial_investment))

        return portfolio_value, total_invested

    # Effectuer la simulation
    portfolio_dca, total_invested = simulate_dca(df_combined, monthly_investment)

    # Ajouter les résultats au DataFrame
    df_combined['Portfolio_DCA'] = portfolio_dca

    # Calcul des performances
    final_value = portfolio_dca[-1]
    total_return = (final_value / total_invested) - 1
    annualized_return = (1 + total_return) ** (1 / ((df_combined['Date'].iloc[-1] - df_combined['Date'].iloc[0]).days / 365.25)) - 1

    results = {
        "Montant total investi": f"{total_invested}€",
        "Valeur finale": f"{final_value:.2f}€",
        "Rendement cumulatif": f"{total_return * 100:.2f}%",
        "Rendement annualisé": f"{annualized_return * 100:.2f}%",
    }

    # Visualisation
    plt.figure(figsize=(10, 6))
    plt.plot(df_combined['Date'], portfolio_dca, label="Portefeuille DCA")
    plt.title("Évolution du portefeuille (DCA)")
    plt.xlabel("Date")
    plt.ylabel("Valeur (€)")
    plt.legend()
    plt.grid(True)
    plt.show()

    return results, df_combined

