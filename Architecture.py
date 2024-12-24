import streamlit as st
import requests
import matplotlib.pyplot as plt
import pandas as pd

# Base URL GitHub pour accéder aux scripts
GITHUB_BASE_URL = "https://raw.githubusercontent.com/InvestSmartFR/InvestSmartFR-Portfolio/Portefeuilles/"

# Titre de l'application
st.title("Simulateur de portefeuilles InvestSmart 🚀")

# Options pour les portefeuilles et stratégies
portfolio_options = {
    "100% US": {
        "Prudent": "portefeuille_prudent.py",
        "Pondéré": "portefeuille_pondéré_USD.py",
        "Dynamique": "portefeuille_dynamique_USD.py"
    },
    "100% Europe": {
        "Prudent": "portefeuille_prudent.py",
        "Pondéré": "portefeuille_pondéré_EUR.py",
        "Dynamique": "portefeuille_dynamique_EUR.py"
    },
    "Mixte": {
        "Prudent": "portefeuille_prudent.py",
        "Pondéré": "portefeuille_pondéré_MIXTE.py",
        "Dynamique": "portefeuille_dynamique_MIXTE.py"
    },
    "Mixte Asie": {
        "Prudent": "portefeuille_prudent.py",
        "Pondéré": "portefeuille_pondéré_MIXTE_ASIE.py",
        "Dynamique": "portefeuille_dynamique_MIXTE.py"
    }
}

# Interface utilisateur
st.sidebar.header("Configurer votre simulation")
portfolio_type = st.sidebar.selectbox(
    "Type de portefeuille",
    options=list(portfolio_options.keys())
)
strategy = st.sidebar.radio(
    "Profil de risque",
    options=list(portfolio_options[portfolio_type].keys())
)

# Affichage du profil et script correspondant
st.sidebar.markdown(f"**Profil sélectionné :** {strategy}")
script_name = portfolio_options[portfolio_type][strategy]
script_url = f"{GITHUB_BASE_URL}{script_name}"
st.sidebar.write(f"🗂️ Script sélectionné : `{script_name}`")

# Saisie du montant d'investissement mensuel
monthly_investment = st.sidebar.number_input(
    "Montant mensuel investi (€)",
    min_value=1,
    max_value=10000,
    value=100,
    step=1
)
st.sidebar.markdown(f"**Montant sélectionné :** {monthly_investment}€")

# Base complète pour les supports
base_supports = {
    "Euro Gov Bond 7-10 EUR (Acc) Amundi": {"ISIN": "LU1287023185", "VL": "VL_Gov_Bond", "Fee": 0.0015},
    "Euro Short-Term High Yield Corp Bond EUR (Acc) PIMCO": {"ISIN": "IE00BD8D5G25", "VL": "VL_PIMCO", "Fee": 0.005},
    "Euro STOXX 50 EUR (Acc) Xtrackers": {"ISIN": "LU0380865021", "VL": "VL_Stoxx50", "Fee": 0.0009},
    "MSCI EMU Small Cap EUR (Acc) iShares": {"ISIN": "IE00B3VWMM18", "VL": "VL_Small_Cap", "Fee": 0.0058},
    "MSCI Europe Mid Cap Unhedged EUR (Acc) iShares": {"ISIN": "IE00BF20LF40", "VL": "VL_Mid_Cap", "Fee": 0.0015}
}

# Télécharger le script Python pour récupérer les données dynamiques
def download_script(script_url):
    """Télécharge le script depuis GitHub."""
    try:
        response = requests.get(script_url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur lors du téléchargement du script : {str(e)}")
        return None

script_content = download_script(script_url)

if script_content:
    exec_globals = {}
    try:
        exec(script_content, exec_globals)

        # Renommer les colonnes dynamiquement en utilisant les noms complets
        if "df_combined" in exec_globals:
            df_combined = exec_globals["df_combined"]
            for full_name, details in base_supports.items():
                vl_column = details["VL"]
                if vl_column in df_combined.columns:
                    df_combined.rename(columns={vl_column: full_name}, inplace=True)

        # Récupérer les pondérations et frais dynamiques
        weights = exec_globals.get("weights", {})
        filtered_weights = {full_name: weights.get(details["VL"], 0) * 100 for full_name, details in base_supports.items() if details["VL"] in weights and weights[details["VL"]] > 0}

        # Afficher les pondérations avec sliders
        st.sidebar.header("Pondérations des supports (%)")
        for support, weight in filtered_weights.items():
            filtered_weights[support] = st.sidebar.slider(
                f"{support}",
                min_value=0.0,
                max_value=100.0,
                value=weight,
                step=1.0
            )

        # Afficher les résultats de simulation
        simulation_results = exec_globals["simulate_monthly_investment"](df_combined, [monthly_investment])
        performance_df = exec_globals["calculate_performance"](df_combined, simulation_results)

        # Séparer les données en deux tableaux
        table1 = performance_df[["Investissement Mensuel", "Rendement Annualisé", "Rendement Cumulé", "Valeur Finale"]]
        table2 = performance_df[["Investissement Mensuel", "Valeur Finale Après Impôt", "Durée de l'Investissement"]]

        st.header("Résultats de la simulation 📊")
        st.subheader("Performance avant impôts")
        st.dataframe(table1, use_container_width=True)

        st.subheader("Performance après impôts")
        st.dataframe(table2, use_container_width=True)
        st.caption("*Imposition au Prélèvement Forfaitaire Unique")

        # Graphique de la performance
        st.header("Graphique de la croissance du portefeuille")
        plt.figure(figsize=(10, 6))
        for investment, data in simulation_results.items():
            plt.plot(df_combined["Date"], data["Portfolio"], label=f"{investment}€ par mois")

        plt.xlabel("Date")
        plt.ylabel("Valeur du portefeuille (€)")
        plt.title(f"Croissance du portefeuille avec un investissement mensuel de {monthly_investment}€")
        plt.legend()
        plt.grid(True)
        st.pyplot(plt)

        # Graphique en camembert pour la répartition
        st.header("Répartition du portefeuille")
        fig, ax = plt.subplots()
        labels = [support for support, weight in filtered_weights.items() if weight > 0]
        sizes = [weight for weight in filtered_weights.values() if weight > 0]
        ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)

        # Afficher les informations sur les supports
        st.header("Informations sur les supports")
        filtered_support_data = {
            "Nom": [],
            "ISIN": [],
            "Frais courants (%)": []
        }
        for support, details in base_supports.items():
            vl_column = details["VL"]
            if vl_column in weights and weights[vl_column] > 0:
                filtered_support_data["Nom"].append(support)
                filtered_support_data["ISIN"].append(details["ISIN"])
                filtered_support_data["Frais courants (%)"].append(details["Fee"] * 100)  # Conversion en %

        filtered_support_df = pd.DataFrame(filtered_support_data)
        st.dataframe(filtered_support_df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Une erreur est survenue lors de l'exécution du script : {str(e)}")
else:
    st.error("Impossible de récupérer le script sélectionné.")

# Message par défaut
st.sidebar.write("💡 Utilisez les options pour configurer votre portefeuille.")
