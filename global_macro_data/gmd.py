# Standard library
import os
import io
from typing import Optional, Union, List
import json

# Third-party
import pandas as pd
import requests

# Internal modules
from .logging import logger
from .exceptions import (
    InvalidVariableError, InvalidVersionError, RawModeError,
    DataDownloadError, InvalidCountryError
)


# Valid variables list
VALID_VARIABLES = [
    # GDP and related
    "nGDP", "rGDP", "rGDP_USD", "rGDP_pc", "deflator",
    # Consumption
    "cons", "cons_GDP", "rcons",
    # Investment
    "inv", "inv_GDP", "finv", "finv_GDP",
    # Trade
    "exports", "exports_GDP", "imports", "imports_GDP",
    # Current account and exchange rates
    "CA", "CA_GDP", "USDfx", "REER",
    # Government
    "govexp", "govexp_GDP", "govrev", "govrev_GDP",
    "govtax", "govtax_GDP", "govdef", "govdef_GDP",
    "govdebt", "govdebt_GDP",
    # Prices and inflation
    "HPI", "CPI", "infl",
    # Demographics and labor
    "pop", "unemp",
    # Interest rates
    "strate", "ltrate", "cbrate",
    # Money supply
    "M0", "M1", "M2", "M3", "M4",
    # Crises
    "CurrencyCrisis", "BankingCrisis", "SovDebtCrisis"
]


def list_versions() -> List[str]:
    """Get list of available versions from GitHub"""
    try:
        versions_url = (
            "https://raw.githubusercontent.com/KMueller-Lab/"
            "Global-Macro-Database/refs/heads/main/data/helpers/versions.csv"
        )
        response = requests.get(versions_url)
        if response.status_code != 200:
            raise Exception("Could not fetch versions")

        versions_df = pd.read_csv(io.StringIO(response.text))
        versions = versions_df['versions'].tolist()
        return sorted(versions, reverse=True)
    except Exception as e:
        raise Exception(f"Error fetching versions: {str(e)}")


def get_current_version() -> str:
    """Get the current version of the dataset"""
    versions = list_versions()
    return versions[0] if versions else None


def list_variables() -> pd.DataFrame:
    """Return list of available variables and their descriptions."""
    global VALID_VARIABLES
    descriptions = {
        'nGDP': 'Nominal Gross Domestic Product',
        'rGDP': 'Real Gross Domestic Product, in 2010 prices',
        'rGDP_pc': 'Real Gross Domestic Product per Capita',
        'rGDP_USD': 'Real Gross Domestic Product in USD',
        'deflator': 'GDP deflator',
        'cons': 'Total Consumption',
        'rcons': 'Real Total Consumption',
        'cons_GDP': 'Total Consumption as % of GDP',
        'inv': 'Total Investment',
        'inv_GDP': 'Total Investment as % of GDP',
        'finv': 'Fixed Investment',
        'finv_GDP': 'Fixed Investment as % of GDP',
        'exports': 'Total Exports',
        'exports_GDP': 'Total Exports as % of GDP',
        'imports': 'Total Imports',
        'imports_GDP': 'Total Imports as % of GDP',
        'CA': 'Current Account Balance',
        'CA_GDP': 'Current Account Balance as % of GDP',
        'USDfx': 'Exchange Rate against USD',
        'REER': 'Real Effective Exchange Rate, 2010 = 100',
        'govexp': 'Government Expenditure',
        'govexp_GDP': 'Government Expenditure as % of GDP',
        'govrev': 'Government Revenue',
        'govrev_GDP': 'Government Revenue as % of GDP',
        'govtax': 'Government Tax Revenue',
        'govtax_GDP': 'Government Tax Revenue as % of GDP',
        'govdef': 'Government Deficit',
        'govdef_GDP': 'Government Deficit as % of GDP',
        'govdebt': 'Government Debt',
        'govdebt_GDP': 'Government Debt as % of GDP',
        'HPI': 'House Price Index',
        'CPI': 'Consumer Price Index, 2010 = 100',
        'infl': 'Inflation Rate',
        'pop': 'Population',
        'unemp': 'Unemployment Rate',
        'strate': 'Short-term Interest Rate',
        'ltrate': 'Long-term Interest Rate',
        'cbrate': 'Central Bank Policy Rate',
        'M0': 'M0 Money Supply',
        'M1': 'M1 Money Supply',
        'M2': 'M2 Money Supply',
        'M3': 'M3 Money Supply',
        'M4': 'M4 Money Supply',
        'SovDebtCrisis': 'Sovereign Debt Crisis',
        'CurrencyCrisis': 'Currency Crisis',
        'BankingCrisis': 'Banking Crisis',
    }

    return pd.DataFrame({
        'Variable': VALID_VARIABLES,
        'Description': [descriptions.get(var, '') for var in VALID_VARIABLES]
    }).sort_values('Variable').reset_index(drop=True)


def list_countries() -> dict:
    """Return dict of available countries and their ISO3 codes."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        isomapping_path = os.path.join(
            os.path.dirname(script_dir), 'isomapping.json'
        )
        return _load_json(isomapping_path)
    except Exception as e:
        raise RuntimeError(f'Error loading country list: {e}')


def get_data(
    variables: Optional[Union[str, List[str]]] = None,
    country: Optional[Union[str, List[str]]] = None,
    version: Optional[str] = None,
    raw: bool = False,
) -> pd.DataFrame:
    """
    Download and filter Global Macro Data.

    Parameters
    ----------
    variables : str or list of str, optional
        Variable code(s) to include (e.g., 'rGDP' or ['rGDP', 'unemp']).
    country : str or list of str, optional
        Country or ISO3 country code(s) to include (e.g., 'SGP' or
        ['MRT', 'SGP']).
    version : str, optional
        Dataset version in 'YYYY_MM' format (e.g., '2025_01').
    raw : bool, default=False
        If True, download raw data for a single variable only.

    Returns
    -------
    pd.DataFrame or None
        Filtered macroeconomic data as a DataFrame, or None if no data
        available.
    """
    global VALID_VARIABLES
    base_url = "https://www.globalmacrodata.com"

    # Validate variables before proceeding
    if variables:
        if isinstance(variables, str):
            variables = [variables]

        # Validate variables
        invalid_vars = [
            var for var in variables if var not in VALID_VARIABLES
        ]
        if invalid_vars:
            raise InvalidVariableError(invalid_vars)

    # Get current version if not specified
    if version is None:
        version = get_current_version()
    elif version.lower() == "current":
        version = get_current_version()
    else:
        # Check if version exists
        available_versions = list_versions()
        if version not in available_versions:
            raise InvalidVersionError(
                requested_version=version,
            )

    # Handle raw data option
    if raw:
        if not variables or \
                (isinstance(variables, list) and len(variables) > 1):
            raise RawModeError()

        if isinstance(variables, list):
            variables = variables[0]

        data_url = f"{base_url}/{variables}_{version}.csv"
        logger.info(f'Importing raw data for variable: {variables}')
    else:
        # Handle single variable case for efficiency
        if isinstance(variables, list) and len(variables) == 1:
            variables = variables[0]
            data_url = f"{base_url}/{variables}_{version}.csv"
            logger.info(f'Importing data for variable: {variables}')
        else:
            data_url = f"{base_url}/GMD_{version}.csv"
            logger.info('Importing data')

    # Download data
    try:
        response = requests.get(data_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise DataDownloadError(e)

    # Read the data
    df = pd.read_csv(io.StringIO(response.text))

    # Filter by country if specified
    if country:
        if isinstance(country, str):
            country = [country]

        # Load country name to ISO3 mapping
        country_to_ISO = {k.upper(): v for k, v in list_countries().items()}
        country = [country_to_ISO.get(c.upper(), c.upper()) for c in country]

        # Validate country codes
        invalid_countries = [
            c for c in country if c not in df["ISO3"].unique()
        ]
        if invalid_countries:
            raise InvalidCountryError(invalid_countries)

        df = df[df["ISO3"].isin(country)]
        logger.info(f"Filtered data for countries: {', '.join(country)}")

    # Filter by variables if specified
    if variables and not raw:
        if isinstance(variables, str):
            variables = [variables]

        # Always include identifier columns
        required_cols = ["ISO3", "countryname", "year"]
        all_cols = required_cols + [
            var for var in variables if var not in required_cols
        ]

        # Filter to only include requested variables
        existing_vars = [var for var in all_cols if var in df.columns]
        df = df[existing_vars]

    # Clean up missing variables
    df = df.dropna(axis=1, how='all')

    # Display dataset information
    if len(df) == 0:
        logger.warning("The database has no data on "
                       f"{variables} for {country}")
        return None

    if raw:
        n_sources = len(df.columns) - 7  # Subtract identifier columns
        logger.info(f"Final dataset: {len(df)} "
                    f"observations of {n_sources} sources")
    else:
        logger.info(
            f"Final dataset: {len(df)} observations of "
            f"{len(df.columns)} variables"
        )

    logger.info(f"Version: {version}")

    # Sort and order columns
    df = df.sort_values(['countryname', 'year'])
    id_cols = ['ISO3', 'countryname', 'year']
    other_cols = [col for col in df.columns
                  if (col not in id_cols)]
    df = df[id_cols + other_cols]

    return df.drop(columns=['id'], errors='ignore').reset_index(drop=True)


def _load_json(path: str) -> dict:
    """Load a JSON file as a Python dictionary."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
