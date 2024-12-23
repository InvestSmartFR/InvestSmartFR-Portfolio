import streamlit as st
import importlib.util
import os
import requests

# Titre de l'application
st.title("Simulateur de portefeuilles InvestSmart 🚀")

# Options pour les portefeuilles et stratégies
portfolio_options = {
    "100% US": {
        "Pondéré": "portefeuille_pondéré_USD",
        "Dynamique": "portefeuille_dynamique_USD"
    },
    "100% Europe": {
        "Prudent": "portefeuille_prudent",
        "Pondéré": "portefeuille_pondéré_EUR",
        "Dynamique": "portefeuille_dynamique_EUR"
    },
    "Mixte": {
        "Pondéré": "portefeuille_pondéré_MIXTE",
        "Dynamique": "portefeuille_dynamique_MIXTE"
    }
}

# Définir le dépôt GitHub
GITHUB_BASE_URL = "https://raw.githubusercontent.com/InvestSmartFR/InvestSmartFR-Portfolio/DCA/"

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

# Entrée pour le montant investi mensuellement
monthly_investment = st.sidebar.number_input(
    "Montant investi chaque mois (€)",
    min_value=50, max_value=5000, value=250, step=50
)

# Déterminer le fichier Python correspondant
selected_script = portfolio_options[portfolio_type][strategy]
script_filename = f"{selected_script}.py"
script_url = f"{GITHUB_BASE_URL}{script_filename}"

st.sidebar.write(f"🗂️ Script sélectionné : `{script_filename}`")

# Fonction pour télécharger un fichier depuis GitHub
def download_script_from_github(url, local_path):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Vérifie les erreurs HTTP
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur lors du téléchargement du fichier : {str(e)}")
        return False

# Vérifier si le fichier existe localement ou le télécharger
local_script_path = os.path.join(os.getcwd(), script_filename)
if not os.path.exists(local_script_path):
    st.sidebar.write(f"Téléchargement de `{script_filename}` depuis GitHub...")
    if not download_script_from_github(script_url, local_script_path):
        st.stop()

# Charger et exécuter le script correspondant
try:
    # Charger dynamiquement le module Python depuis le chemin
    spec = importlib.util.spec_from_file_location("portfolio_module", local_script_path)
    portfolio_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(portfolio_module)

    # Vérifier si la fonction simulate_portfolio existe
    if hasattr(portfolio_module, "simulate_portfolio"):
        # Appeler la fonction simulate_portfolio avec le montant investi
        results, df_combined = portfolio_module.simulate_portfolio(monthly_investment)

        # Afficher les résultats dans l'application Streamlit
        st.header("Résultats de la simulation 📊")
        st.write(f"**Montant total investi :** {results['Montant total investi']}")
        st.write(f"**Valeur finale :** {results['Valeur finale']}")
        st.write(f"**Rendement cumulatif :** {results['Rendement cumulatif']}")
        st.write(f"**Rendement annualisé :** {results['Rendement annualisé']}")

        # Graphique d'évolution du portefeuille
        st.line_chart(data=df_combined.set_index('Date')['Portfolio_DCA'])
    else:
        st.error(f"Le fichier `{script_filename}` ne contient pas de fonction `simulate_portfolio`.")
except Exception as e:
    st.error(f"❌ Une erreur est survenue : {str(e)}")

# Indication pour éviter la page blanche
st.sidebar.write("💡 Utilisez le menu pour configurer votre portefeuille.")


