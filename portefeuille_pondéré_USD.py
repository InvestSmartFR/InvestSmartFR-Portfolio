import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# URL de base pour accéder aux fichiers sur GitHub
GITHUB_BASE_URL = "https://raw.githubusercontent.com/InvestSmartFR/InvestSmartFR-Portfolio/Configuration/"

# Fichiers à charger
files = {
    "US Treasury Bond": "Us Treasury Bond 3-7Y.xlsx",
    "US Short Duration": "Short duration USD Corp.xlsx",
    "S&P 500": "IShares Core SP500.xlsx",
    "Nasdaq": "AMUNDI NASDAQ.xlsx",
    "Small Cap": "S&P SmallCap 600.xlsx",
}

# Définir les frais courants pour chaque support
fees = {
    "US Treasury Bond": 0.0007,     # 0.07%
    "US Short Duration": 0.0045,    # 0.45%
    "S&P 500": 0.0007,              # 0.07%
    "Nasdaq": 0.0022,               # 0.22%
    "Small Cap": 0.0014,            # 0.14%
}

# Définir la date de départ
start_date = pd.to_datetime("2017-10-09")

# Prétraitement des fichiers avec les frais inclus
def preprocess_data(url, column_name, start_date, fee_rate):
    """
    Prépare les données : format datetime, trie par date croissante, limite à start_date, applique les frais courants.
    """
    df = pd.read_excel(url)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['Date']).sort_values(by='Date', ascending=True).reset_index(drop=True)
    df = df[df['Date'] >= start_date]
    df.rename(columns={'NAV': column_name}, inplace=True)
    daily_fee_rate = (1 - fee_rate) ** (1 / 252)
    df[column_name] *= daily_fee_rate ** np.arange(len(df))
    return df

# Charger et prétraiter les fichiers
dfs = []
for name, file in files.items():
    url = f"{GITHUB_BASE_URL}{file}"
    dfs.append(preprocess_data(url, f"VL_{name.replace(' ', '_')}", start_date, fees[name]))

# Fusionner les données sur les dates
df_combined = dfs[0]
for df in dfs[1:]:
    df_combined = pd.merge(df_combined, df[['Date', df.columns[-1]]], on='Date', how='outer')

df_combined = df_combined.sort_values(by='Date', ascending=True).reset_index(drop=True)
df_combined.iloc[:, 1:] = df_combined.iloc[:, 1:].interpolate(method='linear', axis=0).ffill().bfill()

# Interface utilisateur avec Streamlit
st.title("Simulateur de Portefeuille InvestSmart 🚀")

# Entrées utilisateur
initial_investment = st.sidebar.number_input("Investissement initial (€)", 0, 500_000, 10_000, step=1_000)
monthly_investment = st.sidebar.number_input("Montant mensuel (DCA) (€)", 0, 100_000, 250, step=50)

# Pondérations modifiables
weights = {}
for column in df_combined.columns[1:]:
    weights[column] = st.sidebar.slider(f"Pondération {column.replace('VL_', '').replace('_', ' ')} (%)", 0, 100, 20)

# Normaliser les pondérations pour qu'elles totalisent 100%
total_weight = sum(weights.values())
weights = {k: v / total_weight for k, v in weights.items()}

# Calculer la valeur du portefeuille
def calculate_portfolio_value(df, weights, initial_investment, monthly_investment):
    """
    Calcule la valeur du portefeuille avec investissements initiaux et mensuels (DCA).
    """
    portfolio_value = []
    total_invested = initial_investment
    cumulative_capital = initial_investment

    for i, row in df.iterrows():
        if i % 21 == 0 and i != 0:  # Simulation d'investissements mensuels (21 jours ouvrés)
            total_invested += monthly_investment
            cumulative_capital += monthly_investment

        # Calculer la valeur pondérée du portefeuille
        value = sum(weights[col] * row[col] / df[col].iloc[0] for col in weights)
        portfolio_value.append(value * total_invested)

    df['Portfolio_Value'] = portfolio_value
    df['Cumulative_Capital'] = cumulative_capital
    return df

df_combined = calculate_portfolio_value(df_combined, weights, initial_investment, monthly_investment)

# Visualisation
st.header("Évolution du portefeuille 📊")
st.line_chart(df_combined.set_index('Date')[['Portfolio_Value', 'Cumulative_Capital']])

# Performance
final_value = df_combined['Portfolio_Value'].iloc[-1]
total_invested = df_combined['Cumulative_Capital'].iloc[-1]
total_return = (final_value / total_invested) - 1
annualized_return = (1 + total_return) ** (1 / ((df_combined['Date'].iloc[-1] - df_combined['Date'].iloc[0]).days / 365.25)) - 1

st.subheader("Performance du portefeuille")
st.write(f"**Valeur finale :** {final_value:,.2f} €")
st.write(f"**Montant total investi :** {total_invested:,.2f} €")
st.write(f"**Rendement total :** {total_return * 100:.2f} %")
st.write(f"**Rendement annualisé :** {annualized_return * 100:.2f} %")
