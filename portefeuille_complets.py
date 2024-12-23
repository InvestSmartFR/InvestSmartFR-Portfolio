# -*- coding: utf-8 -*-
"""Portefeuille complets - Simulation réaliste avec DCA"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# Titre de l'application
st.title("Simulateur de portefeuilles InvestSmart 🚀")

# Obtenir le répertoire actuel où le script est exécuté
current_dir = os.path.dirname(os.path.abspath(__file__))

# Fichiers stockés localement dans le même dossier
local_files = {
    "Euro Gov Bond": os.path.join(current_dir, "Historique VL Euro Gov Bond.xlsx"),
    "Euro STOXX 50": os.path.join(current_dir, "HistoricalData EuroStoxx 50.xlsx"),
    "NASDAQ": os.path.join(current_dir, "AMUNDI NASDAQ.xlsx"),
    "Core S&P 500": os.path.join(current_dir, "IShares Core SP500.xlsx"),
    "PIMCO Euro Short": os.path.join(current_dir, "PIMCO Euro Short-Term High Yield Corporate Bond Index UCITS ETF.xlsx"),
    "Asia EM": os.path.join(current_dir, "Amundi MSCI Em Asia LU1681044563.xlsx"),
}

# Prétraitement des fichiers Excel
def preprocess_data(file_path, column_name, start_date="2017-01-09"):
    """Prépare les données en format datetime, trie par date, et filtre par la date de départ"""
    try:
        df = pd.read_excel(file_path)
        if 'Date' not in df.columns or 'NAV' not in df.columns:
            st.error(f"Le fichier {column_name} doit contenir les colonnes 'Date' et 'NAV'.")
            return None

        # Conversion des dates et filtrage
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date']).sort_values(by='Date', ascending=True).reset_index(drop=True)
        df.rename(columns={'NAV': column_name}, inplace=True)
        df = df[df['Date'] >= start_date]
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données pour {column_name} : {e}")
        return None

# Charger les fichiers depuis le dossier local
dfs = {}
for key, path in local_files.items():
    dfs[key] = preprocess_data(path, key)
    if dfs[key] is None:
        st.stop()

# Fusionner les données sur la base des dates
df_combined = dfs[list(dfs.keys())[0]]
for key in list(dfs.keys())[1:]:
    df_combined = pd.merge(df_combined, dfs[key][['Date', key]], on='Date', how='outer')

# Trier les dates et interpoler/remplir les valeurs manquantes
df_combined = df_combined.sort_values(by='Date', ascending=True).reset_index(drop=True)
df_combined.iloc[:, 1:] = (
    df_combined.iloc[:, 1:]
    .interpolate(method='linear', axis=0)
    .ffill()
    .bfill()
)

# Frais courants (en pourcentage annuel)
frais = {
    "Euro Gov Bond": 0.15,
    "Euro STOXX 50": 0.09,
    "NASDAQ": 0.22,
    "Core S&P 500": 0.07,
    "PIMCO Euro Short": 0.50,
    "Asia EM": 0.20,
}

# Appliquer les frais courants
def apply_fees(df, frais):
    """Ajuste les VL pour prendre en compte les frais courants (quotidiennement)"""
    days_in_year = 365.25
    for col, fee in frais.items():
        if col in df.columns:
            daily_fee = (1 - fee / 100) ** (1 / days_in_year)
            df[col] = df[col] * (daily_fee ** np.arange(len(df)))
    return df

df_combined = apply_fees(df_combined, frais)

# Pondérations des portefeuilles (exemple : Dynamique)
weights = {
    "Euro Gov Bond": 0.225,
    "Euro STOXX 50": 0.20,
    "NASDAQ": 0.15,
    "Core S&P 500": 0.15,
    "PIMCO Euro Short": 0.075,
    "Asia EM": 0.20,
}

# Calculer la valeur totale du portefeuille
def calculate_portfolio_value(df, weights):
    """Calcule la valeur totale du portefeuille pondéré"""
    portfolio_value = sum(
        weights[col] * df[col] / df[col].iloc[0] for col in weights
    ) * 10000  # Base initiale : 10 000 €
    return portfolio_value

df_combined['Portfolio_Value'] = calculate_portfolio_value(df_combined, weights)

# Simulation d'investissement mensuel (DCA) - Correction ajoutée
def simulate_dca_fixed(df, monthly_investment, annual_return):
    """
    Simule DCA (Dollar Cost Averaging) avec contributions mensuelles et rendement annuel.
    """
    portfolio_values = []
    total_invested = 0
    monthly_return = (1 + annual_return / 100) ** (1 / 12) - 1  # Rendement mensuel

    portfolio_value = 0  # Valeur initiale du portefeuille

    for i, row in df.iterrows():
        # Ajouter des contributions tous les 21 jours (environ un mois de trading)
        if i % 21 == 0:
            total_invested += monthly_investment
            portfolio_value += monthly_investment

        # Appliquer le rendement mensuel
        portfolio_value *= (1 + monthly_return)
        portfolio_values.append(portfolio_value)

    return portfolio_values, total_invested

# Choix du montant mensuel
monthly_investment = st.selectbox("Montant investi chaque mois (€)", [100, 250, 500, 750])
annual_return = st.slider("Rendement annuel (%)", 1.0, 10.0, 5.0)
portfolio_dca, total_invested = simulate_dca_fixed(df_combined, monthly_investment, annual_return)

# Ajouter au DataFrame
df_combined['Portfolio_DCA'] = portfolio_dca

# Afficher les résultats
st.header("Simulation d'investissement 📊")
st.write(f"Montant total investi : {total_invested:,.2f} €")
st.write(f"Valeur finale du portefeuille : {portfolio_dca[-1]:,.2f} €")

# Visualisation
fig, ax = plt.subplots()
ax.plot(df_combined['Date'], portfolio_dca, label="Valeur du portefeuille (DCA)")
ax.set_title(f"Évolution du portefeuille avec DCA ({monthly_investment}€/mois)")
ax.set_xlabel("Date")
ax.set_ylabel("Valeur (€)")
ax.legend()
st.pyplot(fig)

