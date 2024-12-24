import streamlit as st
import requests
import matplotlib.pyplot as plt

# Base URL GitHub pour accéder aux scripts
GITHUB_BASE_URL = "https://raw.githubusercontent.com/InvestSmartFR/InvestSmartFR-Portfolio/Portefeuilles/"

# Titre de l'application
st.title("Simulateur de portefeuilles InvestSmart 🚀")

# Options pour les portefeuilles et stratégies
portfolio_options = {
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

# Télécharger le script Python pour récupérer les pondérations, frais, et autres paramètres
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

        # Vérifier si les pondérations et frais sont définis dans le script
        if "weights" in exec_globals:
            default_weights = exec_globals["weights"]
        else:
            st.error("Le script ne contient pas de pondérations définies.")
            default_weights = {}

        if "fees" in exec_globals:
            portfolio_fees = exec_globals["fees"]
        else:
            st.error("Le script ne contient pas de frais définis.")
            portfolio_fees = {}

        # Créer des sliders pour ajuster les pondérations dynamiquement
        st.sidebar.header("Pondérations des supports (%)")
        filtered_weights = {}
        for support, weight in default_weights.items():
            filtered_weights[support] = st.sidebar.slider(
                support,
                min_value=0.0,
                max_value=100.0,
                value=weight * 100,  # Conversion en pourcentage
                step=1.0
            )

        # Normaliser les pondérations si nécessaire
        total_weight = sum(filtered_weights.values())
        if total_weight != 100.0:
            st.sidebar.warning("Les pondérations ne totalisent pas 100%. Elles seront normalisées.")
            filtered_weights = {k: (v / total_weight) * 100 for k, v in filtered_weights.items()}

        # Récupérer les informations sur les supports
        st.header("Informations sur les supports")
        support_data = []
        for support, weight in filtered_weights.items():
            if weight > 0 and support in portfolio_fees:
                support_data.append({
                    "Nom": support,
                    "Frais courants": f"{portfolio_fees[support] * 100:.2f}%"
                })
        st.table(support_data)

        # Appeler la fonction de simulation
        simulation_results = exec_globals["simulate_monthly_investment"](exec_globals["df_combined"], [monthly_investment])
        performance_df = exec_globals["calculate_performance"](exec_globals["df_combined"], simulation_results)

        # Afficher les tableaux des résultats
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
            plt.plot(exec_globals["df_combined"]["Date"], data["Portfolio"], label=f"{investment}€ par mois")

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

    except Exception as e:
        st.error(f"❌ Une erreur est survenue lors de l'exécution du script : {str(e)}")
else:
    st.error("Impossible de récupérer le script sélectionné.")
