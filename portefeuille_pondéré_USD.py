import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Fichiers Excel pour le portefeuille US
files = {
    "US Treasury Bond": "Us Treasury Bond 3-7Y.xlsx",
    "US Short Duration": "Short duration USD Corp.xlsx",
    "S&P 500": "IShares Core SP500.xlsx",
    "Nasdaq-100": "AMUNDI NASDAQ.xlsx",
    "Small Cap": "S&P SmallCap 600.xlsx",
}

# Lecture des fichiers
df_treasury = pd.read_excel(files["US Treasury Bond"])
df_short_duration = pd.read_excel(files["US Short Duration"])
df_sp500 = pd.read_excel(files["S&P 500"])
df_nasdaq = pd.read_excel(files["Nasdaq-100"])
df_small_cap = pd.read_excel(files["Small Cap"])

# Frais courants : exemple (logique dynamique Europe -> rebalancing possible)
# Valeurs alignées sur la logique US
fees = {
    "US Treasury Bond": 0.0007,     # 0.07%
    "US Short Duration": 0.0045,    # 0.45%
    "S&P 500": 0.0007,              # 0.07%
    "Nasdaq-100": 0.0022,           # 0.22%
    "Small Cap": 0.0014,            # 0.14%
}

def preprocess_data(df, column_name, start_date, fee_rate):
    """
    Reprend la logique du portefeuille dynamique Europe (application des frais journaliers
    + filtrage des dates) mais adaptée aux supports US.
    """
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['Date']).sort_values(by='Date').reset_index(drop=True)
    df = df[df['Date'] >= start_date]
    df.rename(columns={'NAV': column_name}, inplace=True)

    # Application des frais courants en base journalière
    daily_fee_rate = (1 - fee_rate) ** (1 / 252)
    df[column_name] *= daily_fee_rate ** np.arange(len(df))
    return df

# On suppose la même date de départ que dans le code dynamique Europe
start_date = pd.to_datetime("2017-10-09")

# Préparation des fichiers avec la méthode dynamique
df_treasury = preprocess_data(df_treasury, 'VL_Treasury_Bond',  start_date, fees["US Treasury Bond"])
df_short_duration = preprocess_data(df_short_duration, 'VL_Short_Duration', start_date, fees["US Short Duration"])
df_sp500 = preprocess_data(df_sp500, 'VL_SP500', start_date, fees["S&P 500"])
df_nasdaq = preprocess_data(df_nasdaq, 'VL_Nasdaq100', start_date, fees["Nasdaq-100"])
df_small_cap = preprocess_data(df_small_cap, 'VL_Small_Cap', start_date, fees["Small Cap"])

# Fusion des données (même logique que le portefeuille dynamique Europe)
dfs = [df_treasury, df_short_duration, df_sp500, df_nasdaq, df_small_cap]
df_combined = dfs[0]
for df in dfs[1:]:
    df_combined = pd.merge(df_combined, df[['Date', df.columns[-1]]], on='Date', how='outer')

# Tri, interpolation, etc.
df_combined = df_combined.sort_values(by='Date').reset_index(drop=True)
df_combined.iloc[:, 1:] = (
    df_combined.iloc[:, 1:]
    .interpolate(method='linear', axis=0)
    .ffill()
    .bfill()
)

# Allocation du portefeuille US (logique dynamique)
# Suppose par ex. un portefeuille "dynamique" identique à l'allocation mentionnée : 
weights = {
    'VL_Treasury_Bond': 0.38,
    'VL_Short_Duration': 0.12,
    'VL_SP500': 0.20,
    'VL_Nasdaq100': 0.20,
    'VL_Small_Cap': 0.10,
}

def calculate_portfolio_value(df, weights):
    """
    Logique du code dynamique Europe : calcul sur la base d'une somme pondérée, 
    éventuellement rebalancée (ici simplifié).
    """
    portfolio_value = sum(
        weights[col] * df[col] / df[col].iloc[0] for col in weights
    ) * 10000
    return portfolio_value

df_combined['Portfolio_Value'] = calculate_portfolio_value(df_combined, weights)

def simulate_monthly_investment(df, monthly_investments):
    """
    Méthode de simulation inspirée du portefeuille dynamique Europe :
    - On ajoute le capital à des périodes régulières (21 jours ouvrés = environ 1 mois)
    - On utilise la valeur instantanée du portefeuille pour calculer le total
    """
    results = {}
    for investment in monthly_investments:
        portfolio_value = []
        total_capital = 0
        capital_cumulative = []
        interests_cumulative = []

        for i, row in df.iterrows():
            # Logique identique au code dynamique : rebal possible 
            # (ici on ne rebal pas explicitement, mais on simule mensuel)
            if i % 21 == 0 and i != 0:
                total_capital += investment
            capital_cumulative.append(total_capital)
            val_actuelle = row['Portfolio_Value'] * (total_capital / 10000)
            portfolio_value.append(val_actuelle)
            interests_cumulative.append(val_actuelle - total_capital)

        results[investment] = {
            'Portfolio': portfolio_value,
            'Capital': capital_cumulative,
            'Interests': interests_cumulative
        }
    return results

monthly_investments = [100, 250, 500, 750]
simulation_results = simulate_monthly_investment(df_combined, monthly_investments)

def calculate_performance(df, results):
    """
    Méthode de calcul du rendement annualisé + PFU 30%, comme dans le code dynamique Europe.
    """
    performance_table = []
    for investment, data in results.items():
        total_return = (data['Portfolio'][-1] / data['Capital'][-1]) - 1
        # Rendement annualisé version "dynamique Europe" (ex. len(df)/252 ou en dates)
        annualized_return = (1 + total_return) ** (1 / (len(df) / 252)) - 1
        final_value = data['Portfolio'][-1]
        final_capital = data['Capital'][-1]
        gross_gain = final_value - final_capital
        net_gain = gross_gain * 0.70  # PFU
        final_value_after_tax = final_capital + net_gain
        # Durée en années 
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

if __name__ == "__main__":
    # Affichage en console
    print(performance_df)

    # Visualisation
    plt.figure(figsize=(14, 8))
    for investment, data in simulation_results.items():
        plt.plot(df_combined['Date'], data['Portfolio'], label=f'{investment}€ par mois')
        plt.text(df_combined['Date'].iloc[-1], data['Portfolio'][-1], f'{data["Portfolio"][-1]:,.2f}€',
                 color='black', ha='center', va='bottom', fontsize=10)
    plt.title("Croissance du portefeuille US (logique dynamique Europe)")
    plt.xlabel("Date")
    plt.ylabel("Valeur du portefeuille (€)")
    plt.legend()
    plt.grid(True)
    plt.show()

