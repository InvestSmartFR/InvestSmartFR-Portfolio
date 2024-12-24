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

# Saisie du montant d'investissement mensuel
monthly_investment = st.sidebar.number_input(
    "Montant mensuel investi (€)",
    min_value=1,  # Montant minimal
    max_value=10000,  # Montant maximal
    value=100,  # Valeur par défaut
    step=1
)
st.sidebar.markdown(f"**Montant sélectionné :** {monthly_investment}€")

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

# Base générique pour les supports
base_supports = {
    "Euro Gov Bond 7-10 EUR (Acc) Amundi": "LU1287023185",
    "Euro Short-Term High Yield Corp Bond EUR (Acc) PIMCO": "IE00BD8D5G25",
    "Euro STOXX 50 EUR (Acc) Xtrackers": "LU0380865021",
    "MSCI EMU Small Cap EUR (Acc) iShares": "IE00B3VWMM18",
    "MSCI Europe Mid Cap Unhedged EUR (Acc) iShares": "IE00BF20LF40",
    "US Treasury Bond 3-7y USD (Acc) Shares": "IE00B3VWN393",
    "S&P SmallCap 600 (Acc) Invesco": "IE00BH3YZ803",
    "Core S&P 500 USD (Acc) iShares": "IE00B5BMR087",
    "USD Short Duration High Yield Corp Bond USD (Acc) iShares": "IE00BZ17CN18",
    "Nasdaq-100 EUR (Acc) Amundi": "LU1829221024",
    "S&P 400 US Mid Cap (Acc) SPDR": "SPDR"
}

if script_content:
    exec_globals = {}
    try:
        exec(script_content, exec_globals)

        # Récupérer les pondérations et frais dynamiques
        weights = exec_globals.get("weights", {})
        fees = exec_globals.get("fees", {})

        # Créer les pondérations par défaut si absentes
        if not weights:
            st.warning("Le script ne contient pas de pondérations spécifiques. Utilisation des valeurs génériques.")
            weights = {support: 0 for support in base_supports.keys()}

        # Créer les frais dynamiques si absents
        if not fees:
            st.warning("Le script ne contient pas de frais spécifiques. Utilisation des valeurs génériques à 0.0.")
            fees = {support: 0.0 for support in base_supports.keys()}

        # Filtrer les supports avec pondérations > 0%
        filtered_weights = {k: v for k, v in weights.items() if v > 0}

        # Afficher les pondérations avec sliders
        st.sidebar.header("Pondérations des supports (%)")
        for support in filtered_weights.keys():
            filtered_weights[support] = st.sidebar.slider(
                f"{support}",
                min_value=0.0,
                max_value=100.0,
                value=filtered_weights.get(support, 0) * 100,
                step=1.0
            )

        # Normaliser les pondérations si nécessaire
        total_weight = sum(filtered_weights.values())
        if total_weight != 100.0:
            st.sidebar.warning("Les pondérations ne totalisent pas 100%. Elles seront normalisées.")
            filtered_weights = {k: (v / total_weight) * 100 for k, v in filtered_weights.items()}

        # Vérifier la présence des fonctions nécessaires pour la simulation
        if "simulate_monthly_investment" in exec_globals and "df_combined" in exec_globals and "calculate_performance" in exec_globals:
            simulate_monthly_investment = exec_globals["simulate_monthly_investment"]
            df_combined = exec_globals["df_combined"]
            calculate_performance = exec_globals["calculate_performance"]

            # Appeler la fonction de simulation
            simulation_results = simulate_monthly_investment(df_combined, [monthly_investment])

            # Calculer les performances
            performance_df = calculate_performance(df_combined, simulation_results)

            # Séparer les données en deux tableaux
            table1 = performance_df[["Investissement Mensuel", "Rendement Annualisé", "Rendement Cumulé", "Valeur Finale"]]
            table2 = performance_df[["Investissement Mensuel", "Valeur Finale Après Impôt", "Durée de l'Investissement"]]

            # Afficher le premier tableau
            st.header("Résultats de la simulation 📊")
            st.subheader("Performance avant impôts")
            st.dataframe(table1, use_container_width=True)

            # Afficher le deuxième tableau
            st.subheader("Performance après impôts")
            st.dataframe(table2, use_container_width=True)
            st.caption("*Imposition au Prélèvement Forfaitaire Unique")

            # Graphique de la performance personnalisé
            st.header("Graphique de la croissance du portefeuille")
            plt.figure(figsize=(10, 6))
            for investment, data in simulation_results.items():
                plt.plot(df_combined['Date'], data['Portfolio'], label=f"{investment}€ par mois")

            plt.xlabel("Date")
            plt.ylabel("Valeur du portefeuille (€)")
            plt.title(f"Croissance du portefeuille avec un investissement mensuel de {monthly_investment}€")
            plt.legend()
            plt.grid(True)
            st.pyplot(plt)

            # Ajouter un graphique en camembert pour la répartition
            st.header("Répartition du portefeuille")
            fig, ax = plt.subplots()
            ax.pie(filtered_weights.values(), labels=filtered_weights.keys(), autopct="%1.1f%%", startangle=90)
            ax.axis('equal')  # Assure que le graphique est un cercle
            st.pyplot(fig)

            # Ajouter un tableau pour les supports filtrés
            st.header("Informations sur les supports")
            filtered_support_data = {
                "Nom": [support for support in filtered_weights.keys()],
                "ISIN": [base_supports[support] for support in filtered_weights.keys()],
                "Frais courants (%)": [fees.get(support, 0) for support in filtered_weights.keys()]
            }
            filtered_support_df = pd.DataFrame(filtered_support_data)
            st.dataframe(filtered_support_df, use_container_width=True)

        else:
            st.error(f"Le script `{script_name}` ne contient pas les fonctions nécessaires ou les données requises.")
    except Exception as e:
        st.error(f"❌ Une erreur est survenue lors de l'exécution du script : {str(e)}")
else:
    st.error("Impossible de récupérer le script sélectionné.")

# Message par défaut
st.sidebar.write("💡 Utilisez les options pour configurer votre portefeuille.")

