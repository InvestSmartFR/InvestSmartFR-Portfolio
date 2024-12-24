import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Charger les fichiers Excel
files = {
    "US Treasury Bond": "Us Treasury Bond 3-7Y.xlsx",
    "US Short Duration": "Short duration USD Corp.xlsx",
    "S&P 500": "IShares Core SP500.xlsx",
    "Nasdaq-100": "AMUNDI Nasdaq-100.xlsx",
    "Small Cap": "S&P SmallCap 600.xlsx",
    "Mid Cap": "S&P 400 US Mid Cap.xlsx",
}

df_treasury = pd.read_excel(files["US Treasury Bond"])
df_short_duration = pd.read_excel(files["US Short Duration"])
df_sp500 = pd.read_excel(files["S&P 500"])
df_Nasdaq-100 = pd.read_excel(files["Nasdaq-100"])
df_small_cap = pd.read_excel(files["Small Cap"])
df_mid_cap = pd.read_excel(files["Mid Cap"])

# Définir les frais courants pour chaque support
fees = {
    "US Treasury Bond": 0.0007,     # 0.07%
    "US Short Duration": 0.0045,    # 0.45%
    "S&P 500": 0.0007,              # 0.07%
    "Nasdaq-100": 0.0022,               # 0.22%
    "Small Cap": 0.0014,            # 0.14%
}

# Prétraitement des fichiers avec les frais inclus
def preprocess_data(df, column_name, start_date, fee_rate):
    """
    Prépare les données : format datetime, trie par date croissante, limite à start_date, applique les frais courants.
    """
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['Date']).sort_values(by='Date', ascending=True).reset_index(drop=True)
    df = df[df['Date'] >= start_date]  # Filtrer à partir de start_date
    df.rename(columns={'NAV': column_name}, inplace=True)

    # Appliquer les frais courants (annuels transformés en journaliers)
    daily_fee_rate = (1 - fee_rate) ** (1 / 252)
    df[column_name] *= daily_fee_rate ** np.arange(len(df))
    return df

# Définir la date de départ
start_date = pd.to_datetime("2017-10-09")

# Préparer chaque fichier
df_treasury = preprocess_data(df_treasury, 'VL_Treasury', start_date, fees["US Treasury Bond"])
df_short_duration = preprocess_data(df_short_duration, 'VL_Short_Duration', start_date, fees["US Short Duration"])
df_sp500 = preprocess_data(df_sp500, 'VL_SP500', start_date, fees["S&P 500"])
df_Nasdaq-100 = preprocess_data(df_Nasdaq-100, 'VL_Nasdaq-100', start_date, fees["Nasdaq-100"])
df_small_cap = preprocess_data(df_small_cap, 'VL_Small_Cap', start_date, fees["Small Cap"])

# Fusionner les données sur la base des dates
dfs = [df_treasury, df_short_duration, df_sp500, df_Nasdaq-100, df_small_cap]
df_combined = dfs[0]
for df in dfs[1:]:
    df_combined = pd.merge(df_combined, df[['Date', df.columns[-1]]], on='Date', how='outer')

# Trier les dates et interpoler/remplir les valeurs manquantes
df_combined = df_combined.sort_values(by='Date', ascending=True).reset_index(drop=True)
df_combined.iloc[:, 1:] = (
    df_combined.iloc[:, 1:]
    .interpolate(method='linear', axis=0)
    .ffill()  # Remplit les NaN par les valeurs précédentes
    .bfill()  # Remplit les NaN restants par les valeurs suivantes
)

# Définir les pondérations du portefeuille
weights = {
    'VL_Treasury': 0.38,         # US Treasury Bond
    'VL_Short_Duration': 0.12,  # US Short Duration
    'VL_SP500': 0.20,            # S&P 500
    'VL_Nasdaq-100': 0.20,           # Nasdaq-100
    'VL_Small_Cap': 0.10,        # Small Cap
}

# Calculer la valeur du portefeuille
def calculate_portfolio_value(df, weights):
    """
    Calcule la valeur totale du portefeuille en pondérant les VL par leurs poids.
    """
    portfolio_value = sum(
        weights[col] * df[col] / df[col].iloc[0] for col in weights
    ) * 10000  # Base initiale de 10 000€
    return portfolio_value

df_combined['Portfolio_Value'] = calculate_portfolio_value(df_combined, weights)

# Simulation d'investissement mensuel
def simulate_monthly_investment(df, monthly_investments):
    """
    Simule des investissements mensuels et retourne les résultats pour chaque montant.
    """
    results = {}
    for investment in monthly_investments:
        portfolio_value = []
        total_capital = 0
        capital_cumulative = []
        interests_cumulative = []
        
        for i, row in df.iterrows():
            if i % 21 == 0 and i != 0:  # Approximation : 21 jours ouvrés par mois
                total_capital += investment
            capital_cumulative.append(total_capital)
            portfolio_value.append(row['Portfolio_Value'] * (total_capital / 10000))
            interests_cumulative.append(portfolio_value[-1] - capital_cumulative[-1])
        
        results[investment] = {
            'Portfolio': portfolio_value,
            'Capital': capital_cumulative,
            'Interests': interests_cumulative
        }
    
    return results

# Configurer les montants mensuels
monthly_investments = [100, 250, 500, 750]
simulation_results = simulate_monthly_investment(df_combined, monthly_investments)

# Calcul de la performance
def calculate_performance(df, results):
    """
    Calcule la performance du portefeuille pour chaque scénario d'investissement.
    """
    performance_table = []
    for investment, data in results.items():
        total_return = (data['Portfolio'][-1] / data['Capital'][-1]) - 1  # Rendement cumulé
        annualized_return = (1 + total_return) ** (1 / (len(df) / 252)) - 1  # Rendement annualisé
        final_value = data['Portfolio'][-1]
        final_capital = data['Capital'][-1]
        gross_gain = final_value - final_capital
        net_gain = gross_gain * 0.70  # Appliquer la fiscalité (PFU 30%)
        final_value_after_tax = final_capital + net_gain
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

# Affichage du tableau de performance
print(performance_df)

# Visualisation de la croissance du portefeuille
plt.figure(figsize=(14, 8))
for investment, data in simulation_results.items():
    plt.plot(df_combined['Date'], data['Portfolio'], label=f'{investment}€ par mois')
    plt.text(df_combined['Date'].iloc[-1], data['Portfolio'][-1], f'{data["Portfolio"][-1]:,.2f}€',
             color='black', ha='center', va='bottom', fontsize=10)

plt.title("Croissance du portefeuille avec investissement mensuel")
plt.xlabel("Date")
plt.ylabel("Valeur du portefeuille (€)")
plt.legend()
plt.grid(True)
plt.show()
