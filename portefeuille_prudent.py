import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Charger les fichiers nécessaires
files = {
    "Euro Gov Bond": "Historique VL Euro Gov Bond.xlsx",
    "Euro STOXX 50": "HistoricalData EuroStoxx 50.xlsx",
    "Euro Short-Term High Yield Corp Bond EUR (Acc) PIMCO": "PIMCO Euro Short-Term High Yield Corporate Bond Index UCITS ETF.xlsx"
}

# Charger les fichiers Excel dans des DataFrames
df_gov_bond = pd.read_excel(files["Euro Gov Bond"])
df_stoxx50 = pd.read_excel(files["Euro STOXX 50"])
df_pimco = pd.read_excel(files["Euro Short-Term High Yield Corp Bond EUR (Acc) PIMCO"])

# Définir les frais courants pour chaque support
fees = {
    "Euro Gov Bond": 0.0015,  # 0.15%
    "Euro STOXX 50": 0.0009,  # 0.09%
    "Euro Short-Term High Yield Corp Bond EUR (Acc) PIMCO": 0.005  # 0.50%
}

# Prétraitement des fichiers
def preprocess_data(df, column_name, start_date, fee_rate):
    """
    Prépare les données : conversion des dates, tri, filtre, et application des frais.
    """
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['Date']).sort_values(by='Date').reset_index(drop=True)
    df = df[df['Date'] >= start_date]  # Filtrer par la date de départ
    df.rename(columns={'NAV': column_name}, inplace=True)

    # Appliquer les frais courants
    daily_fee_rate = (1 - fee_rate) ** (1 / 252)
    df[column_name] *= daily_fee_rate ** np.arange(len(df))
    return df

# Définir la date de départ
start_date = pd.to_datetime("2017-10-09")

# Préparer chaque fichier
df_gov_bond = preprocess_data(df_gov_bond, 'VL_Gov_Bond', start_date, fees["Euro Gov Bond"])
df_stoxx50 = preprocess_data(df_stoxx50, 'VL_Stoxx50', start_date, fees["Euro STOXX 50"])
df_pimco = preprocess_data(df_pimco, 'VL_PIMCO', start_date, fees["Euro Short-Term High Yield Corp Bond EUR (Acc) PIMCO"])

# Fusionner les données
dfs = [df_gov_bond, df_stoxx50, df_pimco]
df_combined = dfs[0]
for df in dfs[1:]:
    df_combined = pd.merge(df_combined, df[['Date', df.columns[-1]]], on='Date', how='outer')

# Trier et interpoler les valeurs manquantes
df_combined = df_combined.sort_values(by='Date').reset_index(drop=True)
df_combined.iloc[:, 1:] = (
    df_combined.iloc[:, 1:]
    .interpolate(method='linear', axis=0)
    .ffill()
    .bfill()
)

# Définir les pondérations du portefeuille
weights = {
    'VL_Gov_Bond': 0.50,
    'VL_Stoxx50': 0.30,
    'VL_PIMCO': 0.20
}

# Calcul de la valeur totale du portefeuille
def calculate_portfolio_value(df, weights):
    """
    Calcule la valeur totale du portefeuille en fonction des pondérations.
    """
    df['Portfolio_Value'] = sum(
        weights[col] * df[col] / df[col].iloc[0] for col in weights
    ) * 100  # Base initiale de 100€
    return df

df_combined = calculate_portfolio_value(df_combined, weights)

# Simulation d'investissements mensuels
def simulate_monthly_investment(df, monthly_investments):
    results = {}
    for investment in monthly_investments:
        total_capital = 0
        portfolio_value = []
        capital_cumulative = []
        interests_cumulative = []

        for i, row in df.iterrows():
            if i % 21 == 0:  # Approximation d'un mois
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

monthly_investments = [100, 250, 500, 750]
simulation_results = simulate_monthly_investment(df_combined, monthly_investments)

# Calcul des performances
def calculate_performance(df, results):
    performance_table = []
    for investment, data in results.items():
        total_return = (data['Portfolio'][-1] / data['Capital'][-1]) - 1
        annualized_return = (1 + total_return) ** (1 / (len(df) / 252)) - 1
        final_value = data['Portfolio'][-1]
        gross_gain = final_value - data['Capital'][-1]
        net_gain = gross_gain * 0.70
        final_value_after_tax = data['Capital'][-1] + net_gain
        num_years = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days / 365.25

        performance_table.append([
            f"{investment}€",
            f"{annualized_return*100:.2f}%",
            f"{total_return*100:.2f}%",
            f"{final_value:,.2f}€",
            f"{final_value_after_tax:,.2f}€",
            f"{num_years:.2f} ans"
        ])
    return pd.DataFrame(performance_table, columns=[
        "Investissement Mensuel",
        "Rendement Annualisé",
        "Rendement Cumulé",
        "Valeur Finale",
        "Valeur Finale Après Impôt",
        "Durée de l'Investissement"
    ])

performance_df = calculate_performance(df_combined, simulation_results)

# Afficher le tableau des performances
print(performance_df)

# Visualiser la croissance du portefeuille
plt.figure(figsize=(14, 8))
for investment, data in simulation_results.items():
    plt.plot(df_combined['Date'], data['Portfolio'], label=f'{investment}€ par mois')
    plt.text(df_combined['Date'].iloc[-1], data['Portfolio'][-1], f'{data["Portfolio"][-1]:,.2f}€',
             ha='center', va='bottom', fontsize=10)

plt.title("Croissance du portefeuille avec investissement mensuel")
plt.xlabel("Date")
plt.ylabel("Valeur du portefeuille (€)")
plt.legend()
plt.grid(True)
plt.show()



