import os
import requests
import pandas as pd
import io
import re

# Allowed quarters
VALID_QUARTERS = ["01", "03", "06", "09", "12"]

def gmd(version=None, country=None, variables=None, show_preview=True):
    """
    Download and filter Global Macro Data.
    
    Parameters:
    - version (str): Dataset version in format 'YYYY_MM' (e.g., '2025_01').
                   If None, the latest available version is used.
                   Note: '01' quarter is only valid for year 2025.
    - country (str or list): ISO3 country code(s) (e.g., "SGP" or ["MRT", "SGP"]).
                          If None, returns all countries.
    - variables (list): List of variable codes to include (e.g., ["rGDP", "unemp"]).
                      If None, all variables are included.
    - show_preview (bool): If True and no other parameters are provided, shows a preview.
    
    Returns:
    - pd.DataFrame: The requested data.
    """
    # Check if this is a default call (no specific parameters)
    default_call = (version is None and country is None and variables is None and show_preview)
    
    base_url = "https://www.globalmacrodata.com"

    # Process version parameter or find latest
    if version is None:
        # Automatically select the latest available dataset
        year, quarter = find_latest_data(base_url)
        version = f"{year}_{quarter:02d}"
    else:
        # Validate the version format
        if not re.match(r'^\d{4}_(01|03|06|09|12)$', version):
            raise ValueError("Version must be in format 'YYYY_MM' where MM is one of: 01, 03, 06, 09, 12")
        
        # Parse the version
        year_str, quarter = version.split('_')
        year = int(year_str)
        
        # Special validation for quarter 01
        if quarter == "01" and year != 2025:
            raise ValueError("Quarter '01' is only valid for year 2025")

    # Construct URL
    data_url = f"{base_url}/GMD_{version}.csv"
    print(f"Downloading: {data_url}")

    # Download data
    response = requests.get(data_url)
    if response.status_code != 200:
        raise FileNotFoundError(f"Error: Data file not found at {data_url}")

    # Read the data
    df = pd.read_csv(io.StringIO(response.text))

    # Filter by country if specified
    if country:
        # Convert single country to list for consistent handling
        if isinstance(country, str):
            country = [country]
        
        # Convert all country codes to uppercase
        country = [c.upper() for c in country]
        
        # Check if all specified countries exist in the dataset
        invalid_countries = [c for c in country if c not in df["ISO3"].unique()]
        if invalid_countries:
            # Load isomapping for better error handling
            try:
                # Try to load isomapping from the expected location
                script_dir = os.path.dirname(os.path.abspath(__file__))
                isomapping_path = os.path.join(script_dir, 'isomapping.csv')
                isomapping = pd.read_csv(isomapping_path)
                
                # Display helpful error message with available countries
                print(f"Error: Invalid country code(s): {', '.join(invalid_countries)}. Available country codes are:")
                for i, row in isomapping.iterrows():
                    print(f"{row['ISO3']}: {row['countryname']}")
            except Exception:
                # If isomapping.csv can't be loaded, use the country list from the dataset
                print(f"Error: Invalid country code(s): {', '.join(invalid_countries)}. Available country codes are:")
                country_list = sorted(set(zip(df["ISO3"], df["countryname"])))
                for iso3, name in country_list:
                    if pd.notna(iso3) and pd.notna(name):
                        print(f"{iso3}: {name}")
            
            raise ValueError(f"Invalid country code(s): {', '.join(invalid_countries)}")
        
        # Filter for multiple countries
        df = df[df["ISO3"].isin(country)]
        print(f"Filtered data for countries: {', '.join(country)}")
    
    # Filter by variables if specified
    if variables:
        # Always include identifier columns
        required_cols = ["ISO3", "countryname", "year"]
        all_cols = required_cols + [var for var in variables if var not in required_cols]
        
        # Check if all requested variables exist in the dataset
        missing_vars = [var for var in variables if var not in df.columns]
        if missing_vars:
            print(f"Warning: The following requested variables are not in the dataset: {missing_vars}")
            print("Available variables are:")
            for i, col in enumerate(sorted(df.columns)):
                if i > 0 and i % 4 == 0:
                    print("")  # Line break every 4 columns
                print(f"- {col}", end="  ")
            print("\n")
        
        # Filter to only include requested variables (plus identifiers)
        existing_vars = [var for var in all_cols if var in df.columns]
        df = df[existing_vars]
        print(f"Selected {len(existing_vars)} variables")
    
    # Only show the preview for default calls (no specific parameters)
    if default_call:
        # Get Singapore data from 2000-2020
        sample_df = df[(df["ISO3"] == "SGP") & (df["year"] >= 2000) & (df["year"] <= 2020)]
        
        if len(sample_df) > 0:
            print(f"Singapore (SGP) data, 2000-2020")
            print(f"{len(sample_df)} rows out of {len(df)} total rows in the dataset")
            
            # Display the data with specified columns, sorted by year
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
            
            # Define the preview columns in the exact order requested
            preview_cols = ["year", "ISO3", "countryname", "nGDP", "rGDP", "pop", "unemp", "infl", 
                            "exports", "imports", "govdebt_GDP", "ltrate"]
            
            # Check which columns exist in the dataset
            available_cols = [col for col in preview_cols if col in sample_df.columns]
            
            # Sort by year and display with available columns
            print(sample_df[available_cols].sort_values(by="year"))
        else:
            print("No data available for Singapore (SGP) between 2000-2020")

    print(f"Final dataset: {len(df)} observations of {len(df.columns)} variables")
    return df

def find_latest_data(base_url):
    """ Attempt to find the most recent available dataset """
    import datetime

    current_year = datetime.datetime.now().year
    for year in range(current_year, 2019, -1):  # Iterate backward by year
        for quarter in ["12", "09", "06", "03", "01"]:
            url = f"{base_url}/GMD_{year}_{quarter}.csv"
            try:
                response = requests.head(url, timeout=5)
                if response.status_code == 200:
                    return year, int(quarter)
            except:
                continue
    
    raise FileNotFoundError("No available dataset found on the server.")