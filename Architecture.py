import streamlit as st
import importlib.util
import os
import subprocess

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

# Définir la branche Git correspondante pour les simulations DCA
branch_name = "DCA"

# Fonction pour changer de branche dans Git
def switch_git_branch(branch):
    try:
        subprocess.run(["git", "checkout", branch], check=True)
        st.sidebar.write(f"✅ Branche Git active : `{branch}`")
    except subprocess.CalledProcessError as e:
        st.sidebar.error(f"❌ Erreur lors du changement de branche : {str(e)}")

# Changer vers la branche DCA
switch_git_branch(branch_name)

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

st.sidebar.write(f"🗂️ Script sélectionné : `{selected_script}.py`")

# Essayer de charger et exécuter le script correspondant
try:
    # Vérifier si le fichier Python existe dans le répertoire
    script_path = os.path.join(os.getcwd(), f"{selected_script}.py")
    if not os.path.exists(script_path):
        st.error(f"Le fichier `{selected_script}.py` est introuvable. Assurez-vous qu'il est dans la branche `{branch_name}`.")
    else:
        # Charger dynamiquement le module Python depuis le chemin
        spec = importlib.util.spec_from_file_location("portfolio_module", script_path)
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
            st.error(f"Le fichier `{selected_script}.py` ne contient pas de fonction `simulate_portfolio`.")
except Exception as e:
    st.error(f"Une erreur est survenue : {str(e)}")

# Indication pour éviter la page blanche
st.sidebar.write("💡 Utilisez le menu pour configurer votre portefeuille.")


