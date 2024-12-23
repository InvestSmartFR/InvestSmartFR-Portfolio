# -*- coding: utf-8 -*-
"""Portefeuille Prudent - Simulation avec DCA et investissement initial"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def preprocess_data(df, column_name, start_date):
    """
    Prépare les données : format datetime, trie par date croissante et limite à start_date.
    """
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['Date']).sort_values(by='Date', ascending=True).reset_index(drop=True)
    df = df[df['Date'] >= start_date]  # Filtrer à partir de start_date
    df.rename(columns={'NAV': column_name}, inplace=True)
    return df

def apply_fees(df, frais):
    """
    Ajuste les VL pour prendre en compte les frais courants (journaliers).
    """
    days_in_year = 365.25
    for col, fee in frais.items():
        if col in df.columns:
            daily_fee = (1 - fee / 100) ** (1 / days_in_year)
            df[col] *= daily_fee ** np.arange(len(df))
    return df

def calculate_portfolio_value(df, weights, initial_investment):
    """
    Calcule la valeur totale du portefeuille en pondérant les VL par leurs poids.
    """
    portfolio_value = sum(
        weights[col] * df[col] / df[col].iloc[0] for col in weights
    ) * initial_investment
    return portfolio_value

def simulate_dca(df, monthly_investment):
    """
    Simule un investissement mensuel (DCA).
    Retourne une liste des valeurs du portefeuille et une liste des capitaux investis cumulés.
    """
    portfolio_values = []  # Valeurs du portefeuille
    capital_cumulative = []  # Capital investi cumulatif
    total_capital = 0  # Capital total investi

    for i, row in df.iterrows():
        # Simuler un versement tous les 21 jours (environ un mois)
        if i % 21 == 0 and i != 0:
            total_capital += monthly_investment

        capital_cumulative.append(total_capital)
        # Valeur actuelle du portefeuille en fonction du capital investi
        portfolio_value = row['Portfolio_Value'] * (total_capital / 10000)
        portfolio_values.append(portfolio_value)

    return portfolio_values, capital_cumulative

def simulate_portfolio(monthly_investment):
    """
    Simule le portefeuille prudent avec un investissement initial et/ou mensuel (DCA).
    :param monthly_investment: Montant investi chaque mois (€).
    """

    # Charger les fichiers
    files = {
        "Euro Gov Bond": "Historique VL Euro Gov Bond.xlsx",
        "Euro STOXX 50": "HistoricalData EuroStoxx 50.xlsx",
        "PIMCO Euro Short": "PIMCO Euro Short-Term High Yield Corporate Bond Index UCITS ETF.xlsx"
    }
    df_gov_bond = pd.read_excel(files["Euro Gov Bond"])
    df_stoxx50 = pd.read_excel(files["Euro STOXX 50"])
    df_pimco = pd.read_excel(files["PIMCO Euro Short"])

    # Prétraiter les données
    start_date = pd.to_datetime("2017-10-09")
    df_gov_bond = preprocess_data(df_gov_bond, 'VL_Gov_Bond', start_date)
    df_stoxx50 = preprocess_data(df_stoxx50, 'VL_Stoxx50', start_date)
    df_pimco = preprocess_data(df_pimco, 'VL_PIMCO_Short_Term', start_date)

    # Fusionner les DataFrames sur la base des dates
    dfs = [df_gov_bond, df_stoxx50, df_pimco]
    df_combined = dfs[0]
    for df in dfs[1:]:
        df_combined = pd.merge(df_combined, df[['Date', df.columns[-1]]], on='Date', how='outer')

    # Trier les dates et interpoler les valeurs manquantes
    df_combined = df_combined.sort_values(by='Date', ascending=True).reset_index(drop=True)
    numeric_cols = df_combined.select_dtypes(include=[np.number]).columns
    df_combined[numeric_cols] = df_combined[numeric_cols].interpolate(method='linear', axis=0)

    # Frais courants (en pourcentage annuel)
    frais = {
        'VL_Gov_Bond': 0.15,
        'VL_Stoxx50': 0.09,
        'VL_PIMCO_Short_Term': 0.50
    }
    df_combined = apply_fees(df_combined, frais)

    # Poids du portefeuille
    weights = {
        'VL_Gov_Bond': 0.50,
        'VL_Stoxx50': 0.30,
        'VL_PIMCO_Short_Term': 0.20
    }

    # Calculer la valeur initiale du portefeuille
    initial_investment = 10000
    df_combined['Portfolio_Value'] = calculate_portfolio_value(df_combined, weights, initial_investment)

    # Simulation DCA
    portfolio_dca, capital_cumulative = simulate_dca(df_combined, monthly_investment)

    # Ajouter les colonnes au DataFrame
    df_combined['Portfolio_DCA'] = portfolio_dca
    df_combined['Capital_Cumulative'] = capital_cumulative

    # Retourner le DataFrame complet
    return df_combined

# Exemple d'utilisation
monthly_investment = 100
df_combined = simulate_portfolio(monthly_investment)

# Afficher les 5 premières lignes pour vérification
print(df_combined.head())

# Visualisation de la courbe de valeur du portefeuille
plt.figure(figsize=(12, 6))
plt.plot(df_combined['Date'], df_combined['Portfolio_DCA'], label="Portefeuille DCA")
plt.plot(df_combined['Date'], df_combined['Capital_Cumulative'], label="Capital Investi")
plt.title(f"Évolution du portefeuille avec DCA ({monthly_investment} €/mois)")
plt.xlabel("Date")
plt.ylabel("Valeur (€)")
plt.legend()
plt.grid()
plt.show()
