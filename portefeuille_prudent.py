# -*- coding: utf-8 -*-
"""Portefeuille Prudent - Simulation avec DCA et investissement initial"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def simulate_portfolio(monthly_investment):
    """
    Simule le portefeuille prudent avec un investissement initial et/ou mensuel (DCA).
    :param monthly_investment: Montant investi chaque mois (€).
    :return: Tuple contenant le DataFrame combiné et les résultats DCA.
    """

    # Charger les fichiers
    df_gov_bond = pd.read_excel("Historique VL Euro Gov Bond.xlsx")
    df_stoxx50 = pd.read_excel("HistoricalData EuroStoxx 50.xlsx")
    df_pimco = pd.read_excel("PIMCO Euro Short-Term High Yield Corporate Bond Index UCITS ETF.xlsx")

    # Convertir les colonnes de dates au format datetime
    df_gov_bond['Date'] = pd.to_datetime(df_gov_bond['Date'], errors='coerce', dayfirst=True)
    df_stoxx50['Date'] = pd.to_datetime(df_stoxx50['Date'], errors='coerce', dayfirst=True)
    df_pimco['Date'] = pd.to_datetime(df_pimco['Date'], errors='coerce', dayfirst=True)

    # Supprimer les lignes avec des dates invalides
    df_gov_bond = df_gov_bond.dropna(subset=['Date'])
    df_stoxx50 = df_stoxx50.dropna(subset=['Date'])
    df_pimco = df_pimco.dropna(subset=['Date'])

    # Renommer les colonnes de valeur liquidative
    df_gov_bond.rename(columns={'NAV': 'VL_Gov_Bond'}, inplace=True)
    df_stoxx50.rename(columns={'NAV': 'VL_Stoxx50'}, inplace=True)
    df_pimco.rename(columns={'NAV': 'VL_PIMCO_Short_Term'}, inplace=True)

    # Trier les fichiers par ordre chronologique
    start_date = pd.to_datetime("2017-10-09")
    df_gov_bond = df_gov_bond[df_gov_bond['Date'] >= start_date].sort_values(by='Date', ascending=True).reset_index(drop=True)
    df_stoxx50 = df_stoxx50[df_stoxx50['Date'] >= start_date].sort_values(by='Date', ascending=True).reset_index(drop=True)
    df_pimco = df_pimco[df_pimco['Date'] >= start_date].sort_values(by='Date', ascending=True).reset_index(drop=True)

    # Fusionner les DataFrames sur la colonne 'Date'
    df_combined = pd.merge(df_gov_bond[['Date', 'VL_Gov_Bond']],
                           df_stoxx50[['Date', 'VL_Stoxx50']],
                           on='Date', how='outer')

    df_combined = pd.merge(df_combined,
                           df_pimco[['Date', 'VL_PIMCO_Short_Term']],
                           on='Date', how='outer').sort_values(by='Date', ascending=True).reset_index(drop=True)

    # Interpolation pour combler les valeurs manquantes
    numeric_cols = df_combined.select_dtypes(include=[np.number]).columns
    df_combined[numeric_cols] = df_combined[numeric_cols].interpolate(method='linear', axis=0)

    # Frais courants (exprimés en pourcentage annuel)
    frais = {
        'VL_Gov_Bond': 0.15,
        'VL_Stoxx50': 0.09,
        'VL_PIMCO_Short_Term': 0.50
    }

    # Appliquer les frais sur les VL
    def apply_fees(df, frais):
        """
        Ajuste les VL pour prendre en compte les frais courants.
        """
        days_in_year = 365.25
        for col, fee in frais.items():
            if col in df.columns:
                daily_fee = (1 - fee / 100) ** (1 / days_in_year)
                df[col] = df[col] * (daily_fee ** np.arange(len(df)))
        return df

    df_combined = apply_fees(df_combined, frais)

    # Poids du portefeuille
    weights = {
        'VL_Gov_Bond': 0.50,
        'VL_Stoxx50': 0.30,
        'VL_PIMCO_Short_Term': 0.20
    }

    # Calculer la valeur du portefeuille
    def calculate_portfolio_value(df, weights):
        """
        Calcule la valeur totale du portefeuille.
        """
        df['Portfolio_Value'] = (
            weights['VL_Gov_Bond'] * df['VL_Gov_Bond'] / df['VL_Gov_Bond'].iloc[0] +
            weights['VL_Stoxx50'] * df['VL_Stoxx50'] / df['VL_Stoxx50'].iloc[0] +
            weights['VL_PIMCO_Short_Term'] * df['VL_PIMCO_Short_Term'] / df['VL_PIMCO_Short_Term'].iloc[0]
        ) * 100  # Base initiale
        return df

    df_combined = calculate_portfolio_value(df_combined, weights)

    # Simulation d'investissement mensuel
    def simulate_dca(df, monthly_investment):
        """
        Simule un investissement mensuel (DCA).
        """
        portfolio_value = []
        total_invested = 0

        for i, row in df.iterrows():
            if i % 21 == 0:  # Approximation : un mois (21 jours ouvrés)
                total_invested += monthly_investment
            portfolio_value.append(row['Portfolio_Value'] * (total_invested / 100))

        return portfolio_value, total_invested

    # Simuler le DCA
    portfolio_dca, total_invested = simulate_dca(df_combined, monthly_investment)

    # Vérifier les résultats
    if not portfolio_dca or not total_invested:
        raise ValueError("Erreur lors de la simulation DCA. Aucune donnée générée.")

    # Ajouter les résultats au DataFrame
    df_combined['Portfolio_DCA'] = portfolio_dca

    # Retourner les résultats et le DataFrame
    return df_combined, total_invested

