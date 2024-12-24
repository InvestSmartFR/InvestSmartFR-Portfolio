import streamlit as st
import requests
import matplotlib.pyplot as plt

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

# Configuration des pondérations
default_weights = None
weights = {}

# Télécharger le script Python pour récupérer les pondérations par défaut
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

        # Vérifier si des pondérations spécifiques sont définies dans le script
        if "weights" in exec_globals:
            default_weights = {k: v * 100 for k, v in exec_globals["weights"].items()}  # Convertir en pourcentages
        else:
            st.warning("Le script ne contient pas de pondérations spécifiques. Utilisation des valeurs génériques.")
            default_weights = {
                'Support 1': 25.0,
                'Support 2': 25.0,
                'Support 3': 25.0,
                'Support 4': 25.0
            }

        # Créer des sliders pour ajuster les pondérations dynamiquement
        st.sidebar.header("Pondérations des supports (%)")
        for support, default_weight in default_weights.items():
            weights[support] = st.sidebar.slider(
                f"{support}",
                min_value=0.0,
                max_value=100.0,
                value=default_weight,
                step=1.0
            )

        # Normaliser les pondérations si nécessaire
        total_weight = sum(weights.values())
        if total_weight != 100.0:
            st.sidebar.warning("Les pondérations ne totalisent pas 100%. Elles seront normalisées.")
            weights = {k: (v / total_weight) * 100 for k, v in weights.items()}

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
            plt.title("Croissance du portefeuille avec investissement mensuel")
            plt.legend()
            plt.grid(True)
            st.pyplot(plt)

            # Ajouter un graphique en camembert pour la répartition
            st.header("Répartition du portefeuille")
            fig, ax = plt.subplots()
            ax.pie(weights.values(), labels=weights.keys(), autopct="%1.1f%%", startangle=90)
            ax.axis('equal')  # Assure que le graphique est un cercle
            plt.title("Répartition du portefeuille (%)")
            st.pyplot(fig)

        else:
            st.error(f"Le script `{script_name}` ne contient pas les fonctions nécessaires ou les données requises.")
    except Exception as e:
        st.error(f"❌ Une erreur est survenue lors de l'exécution du script : {str(e)}")
else:
    st.error("Impossible de récupérer le script sélectionné.")

# Message par défaut
st.sidebar.write("💡 Utilisez les options pour configurer votre portefeuille.")
