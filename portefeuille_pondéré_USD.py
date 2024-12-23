def simulate_portfolio(initial_investment=0, monthly_investment=0, start_date="2017-10-09"):
    """
    Simule l'évolution d'un portefeuille basé sur un investissement initial et un DCA (Dollar Cost Averaging).
    """
    # Chemins locaux des fichiers
    files = {
        "US Treasury Bond": "Us Treasury Bond 3-7Y.xlsx",
        "US Short Duration": "Short duration USD Corp.xlsx",
        "S&P 500": "IShares Core SP500.xlsx",
        "Nasdaq": "AMUNDI NASDAQ.xlsx",
        "Small Cap": "S&P SmallCap 600.xlsx",
    }

    fees = {
        "US Treasury Bond": 0.0007,
        "US Short Duration": 0.0045,
        "S&P 500": 0.0007,
        "Nasdaq": 0.0022,
        "Small Cap": 0.0014,
    }

    def preprocess_data(filepath, column_name, start_date, fee_rate):
        """
        Prépare les données : format datetime, trie par date croissante, limite à start_date, applique les frais courants.
        """
        df = pd.read_excel(filepath)  # Chargement depuis un fichier local
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['Date']).sort_values(by='Date', ascending=True).reset_index(drop=True)
        df = df[df['Date'] >= pd.to_datetime(start_date)]
        df.rename(columns={'NAV': column_name}, inplace=True)
        daily_fee_rate = (1 - fee_rate) ** (1 / 252)
        df[column_name] *= daily_fee_rate ** np.arange(len(df))
        return df

    # Charger et prétraiter les fichiers
    dfs = []
    for name, file in files.items():
        dfs.append(preprocess_data(file, f"VL_{name.replace(' ', '_')}", start_date, fees[name]))

    # Fusionner les données sur les dates
    df_combined = dfs[0]
    for df in dfs[1:]:
        df_combined = pd.merge(df_combined, df[['Date', df.columns[-1]]], on='Date', how='outer')

    df_combined = df_combined.sort_values(by='Date', ascending=True).reset_index(drop=True)
    df_combined.iloc[:, 1:] = df_combined.iloc[:, 1:].interpolate(method='linear', axis=0).ffill().bfill()

    # Pondérations par défaut
    weights = {
        'VL_US_Treasury_Bond': 0.30,
        'VL_US_Short_Duration': 0.20,
        'VL_S&P_500': 0.20,
        'VL_Nasdaq': 0.20,
        'VL_Small_Cap': 0.10,
    }

    # Normalisation des pondérations
    total_weight = sum(weights.values())
    weights = {k: v / total_weight for k, v in weights.items()}

    # Calculer la valeur du portefeuille
    portfolio_value = []
    cumulative_capital = initial_investment
    total_invested = initial_investment

    for i, row in df_combined.iterrows():
        if i % 21 == 0 and i != 0:  # Simulation des investissements mensuels
            total_invested += monthly_investment
            cumulative_capital += monthly_investment

        value = sum(weights[col] * row[col] / df_combined[col].iloc[0] for col in weights)
        portfolio_value.append(value * total_invested)

    df_combined['Portfolio_Value'] = portfolio_value
    df_combined['Cumulative_Capital'] = cumulative_capital

    # Calcul des performances
    final_value = df_combined['Portfolio_Value'].iloc[-1]
    total_return = (final_value / total_invested) - 1
    annualized_return = (1 + total_return) ** (1 / ((df_combined['Date'].iloc[-1] - df_combined['Date'].iloc[0]).days / 365.25)) - 1

    performance = {
        "Montant total investi": f"{total_invested:,.2f} €",
        "Valeur finale": f"{final_value:,.2f} €",
        "Rendement cumulatif": f"{total_return * 100:.2f} %",
        "Rendement annualisé": f"{annualized_return * 100:.2f} %",
    }

    return performance, df_combined

