import streamlit as st
import requests

# Titre de l'application
st.title("Simulateur de portefeuilles InvestSmart 🚀")

# URL de base pour accéder aux fichiers sur GitHub
GITHUB_BASE_URL = "https://raw.githubusercontent.com/InvestSmartFR/InvestSmartFR-Portfolio/Portefeuilles/"

# Options pour les portefeuilles et stratégies
portfolio_options = {
    "100% US": {
        "Pondéré": "portefeuille_pondéré_USD.py",
        "Dynamique": "portefeuille_dynamique_USD.py"
    },
    "100% Europe": {
        "Prudent": "portefeuille_prudent.py",
        "Pondéré": "portefeuille_pondéré_EUR.py",
        "Dynamique": "portefeuille_dynamique_EUR.py"
    },
    "Mixte": {
        "Pondéré": "portefeuille_pondéré_MIXTE.py",
        "Dynamique": "portefeuille_dynamique_MIXTE.py"
    }
}

# Menu déroulant pour sélectionner le type de portefeuille
st.sidebar.header("Sélectionnez votre portefeuille")
portfolio_type = st.sidebar.selectbox(
    "Type de portefeuille",
    options=list(portfolio_options.keys())
)

# Menu déroulant pour sélectionner la stratégie
strategy = st.sidebar.selectbox(
    "Stratégie",
    options=list(portfolio_options[portfolio_type].keys())
)

# Récupération du script correspondant depuis GitHub
script_name = portfolio_options[portfolio_type][strategy]
script_url = f"{GITHUB_BASE_URL}{script_name}"
st.sidebar.write(f"🗂️ Script sélectionné : `{script_name}`")

def download_script(script_url):
    try:
        response = requests.get(script_url)
        response.raise_for_status()  # Vérifie les erreurs HTTP
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

        # Vérifier si la fonction simulate_portfolio est définie
        if "simulate_portfolio" in exec_globals:
            simulate_portfolio = exec_globals["simulate_portfolio"]

            # Appeler la fonction simulate_portfolio
            results, df_combined = simulate_portfolio()

            # Afficher les résultats
            st.header("Résultats de la simulation 📊")
            st.write(f"**Montant total investi :** {results['Montant total investi']}")
            st.write(f"**Valeur finale :** {results['Valeur finale']}")
            st.write(f"**Rendement cumulatif :** {results['Rendement cumulatif']}")
            st.write(f"**Rendement annualisé :** {results['Rendement annualisé']}")

            # Graphique de la performance
            st.line_chart(data=df_combined.set_index('Date')['Portfolio_Value'])

        else:
            st.error(f"Le script `{script_name}` ne contient pas de fonction `simulate_portfolio`.")
    except Exception as e:
        st.error(f"❌ Une erreur est survenue lors de l'exécution du script : {str(e)}")
else:
    st.error("Impossible de récupérer le script sélectionné.")

# Indication pour éviter la page blanche
st.sidebar.write("💡 Utilisez le menu pour configurer votre portefeuille.")


