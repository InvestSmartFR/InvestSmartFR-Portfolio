import streamlit as st
import importlib
import os

# Title of the application
st.title("Simulateur de portefeuilles InvestSmart 🚀")

# Portfolio options
portfolio_options = {
    "100% US": {
        "Prudent": "portefeuille_prudent_US",
        "Pondéré": "portefeuille_pondéré_USD",
        "Dynamique": "portefeuille_dynamique_USD"
    },
    "100% Europe": {
        "Prudent": "portefeuille_prudent",
        "Pondéré": "portefeuille_pondéré_EUR",
        "Dynamique": "portefeuille_dynamique_EUR"
    },
    "Mixte": {
        "Prudent": "portefeuille_prudent",
        "Pondéré": "portefeuille_pondéré_MIXTE",
        "Dynamique": "portefeuille_dynamique_MIXTE"
    }
}

# User selects portfolio type
portfolio_type = st.sidebar.selectbox(
    "Choisissez le type de portefeuille",
    options=list(portfolio_options.keys())
)

# User selects portfolio strategy
strategy = st.sidebar.selectbox(
    "Choisissez la stratégie",
    options=list(portfolio_options[portfolio_type].keys())
)

# User selects monthly investment
monthly_investment = st.sidebar.number_input(
    "Montant mensuel investi (€)", min_value=50, max_value=5000, value=250, step=50
)

# Get the corresponding script name
selected_script = portfolio_options[portfolio_type][strategy]

# Dynamically import the selected portfolio script
try:
    module_path = f"{selected_script}"
    portfolio_module = importlib.import_module(module_path)

    # Call the main function of the imported script to execute simulation
    if hasattr(portfolio_module, "simulate_portfolio"):
        portfolio_module.simulate_portfolio(monthly_investment)
    else:
        st.error(f"Le fichier {selected_script}.py ne contient pas de fonction 'simulate_portfolio'.")
except ModuleNotFoundError as e:
    st.error(f"Le module {selected_script} n'a pas été trouvé. Assurez-vous qu'il est dans le répertoire correct.")
except Exception as e:
    st.error(f"Une erreur est survenue : {e}")

