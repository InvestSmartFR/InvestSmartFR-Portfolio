import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import streamlit as st

# Charger les fichiers Excel localement
files = {
    "Euro Gov Bond": "Historique VL Euro Gov Bond.xlsx",
    "Euro STOXX 50": "HistoricalData EuroStoxx 50.xlsx",
    "Small Cap": "iShares MSCI EMU Small Cap UCITS ETF.xlsx",
    "Mid Cap": "iShares MSCI Europe Mid Cap UCITS ETF.xlsx",
    "PIMCO Euro Short": "PIMCO Euro Short-Term High Yield Corporate Bond Index UCITS ETF.xlsx",
}

# Définir les frais courants pour chaque support
fees = {
    "Euro Gov Bond": 0.0015,  # 0.15%
    "Euro STOXX 50": 0.0009,  # 0.09%
    "Small Cap": 0.0058,      # 0.58%
    "Mid Cap": 0.0015,        # 0.15%
    "PIMCO Euro Short": 0.005, # 0.50%
}

def preprocess_data(df, column_name, start_date, fee_rate):
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['Date']).sort_values(by='Date').reset_index(drop=True)
    df = df[df['Date'] >= start_date]
    df.rename(columns={'NAV': column_name}, inplace=True)

    daily_fee_rate = (1 - fee_rate) ** (1 / 252)
    df[column_name] *= daily_fee_rate ** np.arange(len(df))
    return df

def load_and_preprocess():
    # Vérification des fichiers
    for key, file in files.items():
        if not os.path.exists(file):
            st.error(f"Le fichier '{file}' pour '{key}' est introuvable.")
            return None

    dfs = []
    start_date = pd.to_datetime("2017-10-09")

    for key, file in files.items():
        try:
            df = pd.read_excel(file)
            column_name = f"VL_{key.replace(' ', '_')}"
            df = preprocess_data(df, column_name, start_date, fees[key])
            dfs.append(df)
        except Exception as e:
            st.error(f"Erreur lors du traitement du fichier {file}: {str(e)}")
            return None

    df_combined = dfs[0]
    for df in dfs[1:]:
        df_combined = pd.merge(df_combined, df[['Date', df.columns[-1]]], on='Date', how='outer')

    df_combined = df_combined.sort_values(by='Date').reset_index(drop=True)
    df_combined.iloc[:, 1:] = df_combined.iloc[:, 1:].interpolate().ffill().bfill()
    return df_combined

def simulate_portfolio(df, weights):
    """
    Simule la valeur du portefeuille en fonction des pondérations.
    """
    if df is None:
        raise ValueError("Les données du portefeuille sont manquantes")
    
    # Vérifier les colonnes manquantes
    missing_columns = [col for col in weights.keys() if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colonnes manquantes : {missing_columns}")
    
    # Calculer la valeur totale du portefeuille
    df = df.copy()
    df['Portfolio_Value'] = sum(
        weights[col] * df[col] / df[col].iloc[0] for col in weights
    ) * 10000  # Base de 10 000€
    return df

def simulate_monthly_investment(df, monthly_investments):
    results = {}
    for investment in monthly_investments:
        portfolio_value = []
        total_capital = 0
        capital_cumulative = []
        interests_cumulative = []

        for i, row in df.iterrows():
            if i % 21 == 0 and i != 0:  # 21 jours ouvrés par mois
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

def calculate_performance(df, results):
    performance_table = []
    for investment, data in results.items():
        total_return = (data['Portfolio'][-1] / data['Capital'][-1]) - 1
        annualized_return = (1 + total_return) ** (1 / (len(df) / 252)) - 1
        final_value = data['Portfolio'][-1]
        final_capital = data['Capital'][-1]
        gross_gain = final_value - final_capital
        net_gain = gross_gain * 0.70  # PFU 30%
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

def plot_growth(df, results):
    plt.figure(figsize=(14, 8))
    for investment, data in results.items():
        plt.plot(df['Date'], data['Portfolio'], label=f'{investment}€ par mois')
        plt.text(df['Date'].iloc[-1], data['Portfolio'][-1], f'{data["Portfolio"][-1]:,.2f}€',
                 color='black', ha='center', va='bottom', fontsize=10)

    plt.title("Croissance du portefeuille avec investissement mensuel (avec frais)")
    plt.xlabel("Date")
    plt.ylabel("Valeur du portefeuille (€)")
    plt.legend()
    plt.grid(True)
    st.pyplot(plt)

def main():
    st.title("Simulation de Portefeuille d'Investissement 💰")
    
    # Charger les données prétraitées
    df_combined = load_and_preprocess()
    
    if df_combined is None:
        st.error("Impossible de charger les données. Veuillez vérifier les fichiers d'entrée.")
        return

    # Définir les pondérations par défaut
    default_weights = {
        'VL_Euro_Gov_Bond': 0.225,
        'VL_PIMCO_Euro_Short': 0.075,
        'VL_Euro_STOXX_50': 0.40,
        'VL_Small_Cap': 0.15,
        'VL_Mid_Cap': 0.15,
    }

    try:
        # Simulation du portefeuille
        df_combined = simulate_portfolio(df_combined, default_weights)
        
        # Simulation des investissements mensuels
        monthly_investments = [100, 250, 500, 750]
        simulation_results = simulate_monthly_investment(df_combined, monthly_investments)

        # Calcul et affichage des performances
        performance_df = calculate_performance(df_combined, simulation_results)
        st.header("Résultats de la simulation 📊")
        st.dataframe(performance_df)

        # Visualisation
        plot_growth(df_combined, simulation_results)

    except Exception as e:
        st.error(f"Une erreur est survenue lors de la simulation : {str(e)}")

if __name__ == "__main__":
    main()
