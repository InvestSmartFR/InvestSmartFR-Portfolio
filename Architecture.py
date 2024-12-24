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

        # Vérifier la présence de la fonction calculate_portfolio_value
        if "calculate_portfolio_value" in exec_globals:
            calculate_portfolio_value = exec_globals["calculate_portfolio_value"]

            # Définir les pondérations du portefeuille
            weights = {
                'VL_Gov_Bond': 0.225,
                'VL_PIMCO': 0.075,  # Correspond à PIMCO Euro Short-Term
                'VL_Stoxx50': 0.40,
                'VL_Small_Cap': 0.15,
                'VL_Mid_Cap': 0.15,
            }

            # Calculer les résultats
            df_combined = exec_globals["df_combined"]
            df_combined['Portfolio_Value'] = calculate_portfolio_value(df_combined, weights)

            # Afficher les résultats
            st.header("Résultats de la simulation 📊")
            st.write(f"**Montant total investi :** {10000}")
            st.write(f"**Valeur finale :** {df_combined['Portfolio_Value'].iloc[-1]:,.2f}€")

            # Graphique de la performance
            st.line_chart(data=df_combined.set_index('Date')['Portfolio_Value'])
        else:
            st.error(f"Le script `{script_name}` ne contient pas de fonction `calculate_portfolio_value`.")
    except Exception as e:
        st.error(f"❌ Une erreur est survenue lors de l'exécution du script : {str(e)}")
else:
    st.error("Impossible de récupérer le script sélectionné.")

# Message par défaut
st.sidebar.write("💡 Utilisez les options pour configurer votre portefeuille.")

