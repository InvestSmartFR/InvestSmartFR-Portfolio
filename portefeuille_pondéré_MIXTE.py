# -*- coding: utf-8 -*-
"""Portefeuille Dynamique MIXTE"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def simulate_portfolio(monthly_investment=100, initial_investment=10000):
    """
    Simule le portefeuille dynamique mixte avec investissement initial et DCA.
    
    Args:
        monthly_investment (int): Montant investi chaque mois (€).
        initial_investment (int): Investissement initial (€).
        
    Returns:
        dict: Résultats de la simulation avec valeurs finales et courbes.
    """

    # Charger les fichiers
    files = {
        "Euro Gov Bond": "Historique VL Euro Gov Bond.xlsx",
        "Euro STOXX 50": "HistoricalData EuroStoxx 50.xlsx",
        "NASDAQ": "AMUNDI NASDAQ.xlsx",
        "Core S&P 500": "IShares Core SP500.xlsx",
        "PIMCO Euro Short": "PIMCO Euro Short-Term High Yield Corporate Bond Index UCITS ETF.xlsx",
    }
    
    dfs = {key: pd.read_excel(path) for key, path in files.items()}

    # Prétraitement des données
    def preprocess_data(df, column_name):
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['Date']).sort_values(by='Date', ascending=True).reset_index(drop=True)
        df.rename(columns={'NAV': column_name}, inplace=True)
        return df

    for key, df in dfs.items():
        dfs[key] = preprocess_data(df, key)

    # Définir la date minimale
    start_date = pd.to_datetime("2017-10-09")
    for key, df in dfs.items():
        dfs[key] = df[df['Date'] >= start_date]

    # Fusionner les DataFrames sur les dates
    df_combined = dfs["Euro Gov Bond"]
    for key in list(dfs.keys())[1:]:
        df_combined = pd.merge(df_combined, dfs[key][['Date', key]], on='Date', how='outer')

    # Trier les dates et interpoler les données manquantes
    df_combined = df_combined.sort_values(by='Date', ascending=True).reset_index(drop=True)
    numeric_cols = df_combined.select_dtypes(include=[np.number]).columns
    df_combined[numeric_cols] = (
        df_combined[numeric_cols]
        .interpolate(method='linear', axis=0)
        .ffill()
        .bfill()
    )

    # Appliquer les frais
    frais = {
        "Euro Gov Bond": 0.15,
        "Euro STOXX 50": 0.09,
        "NASDAQ": 0.22,
        "Core S&P 500": 0.07,
        "PIMCO Euro Short": 0.50,
    }

    def apply_fees(df, frais):
        days_in_year = 365.25
        for col, fee in frais.items():
            if col in df.columns:
                daily_fee = (1 - fee / 100) ** (1 / days_in_year)
                df[col] = df[col] * (daily_fee ** np.arange(len(df)))
        return df

    df_combined = apply_fees(df_combined, frais)

    # Poids du portefeuille
    weights = {
        "Euro Gov Bond": 0.20,
        "Euro STOXX 50": 0.20,
        "NASDAQ": 0.20,
        "Core S&P 500": 0.20,
        "PIMCO Euro Short": 0.20,
    }

    # Calcul de la valeur totale du portefeuille
    def calculate_portfolio_value(df, weights):
        portfolio_value = sum(
            weights[col] * df[col] / df[col].iloc[0] for col in weights
        ) * initial_investment
        return portfolio_value

    df_combined['Portfolio_Value'] = calculate_portfolio_value(df_combined, weights)

    # Simulation DCA
    def simulate_dca(df, monthly_investment):
        portfolio_value = []
        total_invested = 0

        for i, row in df.iterrows():
            if i % 21 == 0:  # Approximation d'un mois ouvré
                total_invested += monthly_investment
            portfolio_value.append(row['Portfolio_Value'] * (total_invested / initial_investment))

        return portfolio_value, total_invested

    # Effectuer la simulation
    portfolio_dca, total_invested = simulate_dca(df_combined, monthly_investment)

    # Ajouter les résultats de la simulation
    df_combined['Portfolio_DCA'] = portfolio_dca

    # Calcul de performance
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
