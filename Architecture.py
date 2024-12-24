import streamlit as st
import requests

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
        "Dynamique": "portefeuille_dynamique_MIXTE.py"  # Utilise le mixte pour dynamique
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

def download_script(script_url):
    """Télécharge le script depuis GitHub."""
    try:
        response = requests.get(script_url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur lors du téléchargement du script : {str(e)}")
        return None

# Télécharger et exécuter le script Python correspondant
script_content = download_script(script_url)

if script_content:
    exec_globals = {}
    try:
        exec(script_content, exec_globals)

        # Vérifier la présence de la fonction simulate_monthly_investment
        if "simulate_monthly_investment" in exec_globals and "df_combined" in exec_globals:
            simulate_monthly_investment = exec_globals["simulate_monthly_investment"]
            df_combined = exec_globals["df_combined"]
            monthly_investments = [100, 250, 500, 750]

            # Appeler la fonction de simulation
            simulation_results = simulate_monthly_investment(df_combined, monthly_investments)

            # Afficher les résultats sous forme de tableau
            st.header("Résultats de la simulation 📊")
            for investment, data in simulation_results.items():
                st.write(f"**Investissement Mensuel : {investment}€**")
                st.write(f"Valeur Finale : {data['Portfolio'][-1]:,.2f}€")

            # Graphique de la performance
            st.line_chart({
                f"{investment}€": data['Portfolio'] for investment, data in simulation_results.items()
            })
        else:
            st.error(f"Le script `{script_name}` ne contient pas les fonctions nécessaires ou les données requises.")
    except Exception as e:
        st.error(f"❌ Une erreur est survenue lors de l'exécution du script : {str(e)}")
else:
    st.error("Impossible de récupérer le script sélectionné.")

# Message par défaut
st.sidebar.write("💡 Utilisez les options pour configurer votre portefeuille.")
