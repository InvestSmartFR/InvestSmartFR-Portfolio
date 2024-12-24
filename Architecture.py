import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Base URL GitHub pour accéder aux scripts et au fichier des frais
GITHUB_BASE_URL = "https://raw.githubusercontent.com/InvestSmartFR/InvestSmartFR-Portfolio/Portefeuilles/"
FRAIS_FILE_URL = f"{GITHUB_BASE_URL}Frais%20par%20support.xlsx"

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

# Télécharger le fichier des frais
def download_fees_file():
    try:
        response = requests.get(FRAIS_FILE_URL)
        response.raise_for_status()
        fees_data = pd.read_excel(response.content)
        return fees_data
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur lors du téléchargement du fichier des frais : {str(e)}")
        return None

fees_data = download_fees_file()

# Télécharger le script Python pour récupérer les données dynamiques
def download_script(script_url):
    try:
        response = requests.get(script_url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur lors du téléchargement du script : {str(e)}")
        return None

script_content = download_script(script_url)

if script_content and fees_data is not None:
    exec_globals = {}
    try:
        exec(script_content, exec_globals)

        # Renommer les colonnes dynamiquement en utilisant les noms complets
        if "df_combined" in exec_globals:
            df_combined = exec_globals["df_combined"]

        # Récupérer les pondérations dynamiques
        weights = exec_globals.get("weights", {})
        filtered_weights = {support: weight for support, weight in weights.items() if weight > 0}

        # Filtrer les frais pour les supports dans le portefeuille
        filtered_fees_data = fees_data[fees_data["Nom"].isin(filtered_weights.keys())]

        # Ajouter une colonne pondération en %
        filtered_fees_data["Pondération (%)"] = filtered_fees_data["Nom"].map(lambda x: filtered_weights.get(x, 0) * 100)

        # Afficher le tableau des supports avec frais
        st.header("Informations sur les supports")
        st.dataframe(filtered_fees_data[["Nom", "ISIN", "Frais courants", "Pondération (%)"]], use_container_width=True)

    except Exception as e:
        st.error(f"❌ Une erreur est survenue lors de l'exécution du script : {str(e)}")
else:
    st.error("Impossible de récupérer le fichier des frais ou le script sélectionné.")

# Message par défaut
st.sidebar.write("💡 Utilisez les options pour configurer votre portefeuille.")
