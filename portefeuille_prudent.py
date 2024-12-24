import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Charger les fichiers nécessaires
files = {
    "Euro Gov Bond 7-10 EUR (Acc) Amundi": "Historique VL Euro Gov Bond.xlsx",
    "Euro STOXX 50 EUR (Acc) Xtrackers": "HistoricalData EuroStoxx 50.xlsx",
    "Euro Short-Term High Yield Corp Bond EUR (Acc) PIMCO": "PIMCO Euro Short-Term High Yield Corporate Bond Index UCITS ETF.xlsx"
}

# Informations sur les supports (nom, ISIN, frais)
support_data = {
    "Euro Gov Bond 7-10 EUR (Acc) Amundi": {"ISIN": "LU1287023185", "Fee": 0.0015, "VL": "VL_Gov_Bond"},
    "Euro STOXX 50 EUR (Acc) Xtrackers": {"ISIN": "LU0380865021", "Fee": 0.0009, "VL": "VL_Stoxx50"},
    "Euro Short-Term High Yield Corp Bond EUR (Acc) PIMCO": {"ISIN": "IE00BD8D5G25", "Fee": 0.005, "VL": "VL_PIMCO"}
}

# Charger les fichiers Excel dans des DataFrames
dataframes = {}
for support, file_path in files.items():
    df = pd.read_excel(file_path)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['Date']).sort_values(by='Date').reset_index(drop=True)
    column_name = support_data[support]["VL"]
    df.rename(columns={'NAV': column_name}, inplace=True)
    dataframes[support] = df

# Fusionner les données
start_date = pd.to_datetime("2017-10-09")
df_combined = None
for support, df in dataframes.items():
    df = df[df['Date'] >= start_date]
    if df_combined is None:
        df_combined = df[['Date', support_data[support]["VL"]]]
    else:
        df_combined = pd.merge(df_combined, df[['Date', support_data[support]["VL"]]], on='Date', how='outer')

# Trier et interpoler les valeurs manquantes
df_combined = df_combined.sort_values(by='Date').reset_index(drop=True)
df_combined.iloc[:, 1:] = (
    df_combined.iloc[:, 1:]
    .interpolate(method='linear', axis=0)
    .ffill()
    .bfill()
)

# Appliquer les frais courants
def apply_fees(df, support_data):
    days_in_year = 365.25
    for support, details in support_data.items():
        vl_column = details["VL"]
        fee = details["Fee"]
        if vl_column in df.columns:
            daily_fee = (1 - fee) ** (1 / days_in_year)
            df[vl_column] = df[vl_column] * (daily_fee ** np.arange(len(df)))
    return df

df_combined = apply_fees(df_combined, support_data)

# Définir les pondérations du portefeuille
weights = {
    "Euro Gov Bond 7-10 EUR (Acc) Amundi": 0.50,
    "Euro STOXX 50 EUR (Acc) Xtrackers": 0.30,
    "Euro Short-Term High Yield Corp Bond EUR (Acc) PIMCO": 0.20
}

# Calculer la valeur totale du portefeuille
def calculate_portfolio_value(df, weights, support_data):
    df['Portfolio_Value'] = sum(
        weights[support] * df[details["VL"]] / df[details["VL"]].iloc[0]
        for support, details in support_data.items()
    ) * 100  # Base initiale de 100€
    return df

df_combined = calculate_portfolio_value(df_combined, weights, support_data)

# Répartition des supports
support_allocation = {
    support: weight * 100 for support, weight in weights.items()
}

# Afficher la répartition
plt.figure(figsize=(6, 6))
labels = [support for support, weight in support_allocation.items() if weight > 0]
sizes = [weight for weight in support_allocation.values() if weight > 0]
plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
plt.axis('equal')
plt.title("Répartition du portefeuille")
plt.show()

# Informations sur les supports
support_info = {
    "Nom": list(support_allocation.keys()),
    "ISIN": [support_data[support]["ISIN"] for support in support_allocation.keys()],
    "Frais courants (%)": [support_data[support]["Fee"] * 100 for support in support_allocation.keys()]
}
support_df = pd.DataFrame(support_info)

print("\nInformations sur les supports :")
print(support_df)

# Simulation d'investissement mensuel
def simulate_monthly_investment(df, monthly_investments):
    results = {}
    for investment in monthly_investments:
        total_capital = 0
        portfolio_value = []
        capital_cumulative = []
        interests_cumulative = []

        for i, row in df.iterrows():
            if i % 21 == 0:  # Approximativement un mois
                total_capital += investment
            portfolio_current_value = row['Portfolio_Value'] * (total_capital / 100)
            portfolio_value.append(portfolio_current_value)
            capital_cumulative.append(total_capital)
            interests_cumulative.append(portfolio_current_value - total_capital)

        results[investment] = {
            'Portfolio': portfolio_value,
            'Capital': capital_cumulative,
            'Interests': interests_cumulative
        }
    return results

# Calcul des performances (restant inchangé)
