import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# File paths (adjust based on your environment)
local_files = {
    "Euro Gov Bond": "Historique VL Euro Gov Bond.xlsx",
    "Euro STOXX 50": "HistoricalData EuroStoxx 50.xlsx",
    "NASDAQ": "AMUNDI NASDAQ.xlsx",
    "Core S&P 500": "IShares Core SP500.xlsx",
    "PIMCO Euro Short": "PIMCO Euro Short-Term High Yield Corporate Bond Index UCITS ETF.xlsx",
    "Asia EM": "Amundi MSCI Em Asia LU1681044563.xlsx",
}

# Weights for portfolio components
weights = {
    "Euro Gov Bond": 0.225,
    "Euro STOXX 50": 0.20,
    "NASDAQ": 0.15,
    "Core S&P 500": 0.15,
    "PIMCO Euro Short": 0.075,
    "Asia EM": 0.20,
}

# Annual expense ratios
frais = {
    "Euro Gov Bond": 0.15,
    "Euro STOXX 50": 0.09,
    "NASDAQ": 0.22,
    "Core S&P 500": 0.07,
    "PIMCO Euro Short": 0.50,
    "Asia EM": 0.20,
}

# Load and preprocess data
def preprocess_data(file_path, column_name, start_date="2017-10-09"):
    df = pd.read_excel(file_path)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date']).sort_values(by='Date').reset_index(drop=True)
    df.rename(columns={'NAV': column_name}, inplace=True)
    return df[df['Date'] >= start_date]

# Apply fees
def apply_fees(df, frais):
    days_in_year = 365.25
    for col, fee in frais.items():
        if col in df.columns:
            daily_fee = (1 - fee / 100) ** (1 / days_in_year)
            df[col] *= daily_fee ** np.arange(len(df))
    return df

# Calculate portfolio value
def calculate_portfolio_value(df, weights):
    return sum(weights[col] * df[col] / df[col].iloc[0] for col in weights) * 10000

# Simulate monthly investments (DCA)
def simulate_dca(df, monthly_investment):
    portfolio_value = []
    total_invested = 0

    for i, row in df.iterrows():
        if i % 21 == 0:  # Approximation: 21 trading days per month
            total_invested += monthly_investment
        portfolio_value.append(row['Portfolio_Value'] * (total_invested / 10000))

    return portfolio_value, total_invested

# Process all data files
dfs = {key: preprocess_data(path, key) for key, path in local_files.items()}
df_combined = dfs[list(dfs.keys())[0]]
for key in list(dfs.keys())[1:]:
    df_combined = pd.merge(df_combined, dfs[key][['Date', key]], on='Date', how='outer')

df_combined = apply_fees(df_combined, frais)
df_combined['Portfolio_Value'] = calculate_portfolio_value(df_combined, weights)

# Simulate DCA
monthly_investment = 100  # Example investment amount
df_combined['Portfolio_DCA'], total_invested = simulate_dca(df_combined, monthly_investment)

# Display results
final_value = df_combined['Portfolio_DCA'].iloc[-1]
print(f"Montant total investi : {total_invested} €")
print(f"Valeur finale du portefeuille : {final_value:.2f} €")

# Visualize results
plt.figure(figsize=(10, 6))
plt.plot(df_combined['Date'], df_combined['Portfolio_DCA'], label=f'DCA: {monthly_investment}€/mois')
plt.title("Évolution du portefeuille avec DCA")
plt.xlabel("Date")
plt.ylabel("Valeur (€)")
plt.legend()
plt.grid()
plt.show()

