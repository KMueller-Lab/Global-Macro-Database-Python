<h1 align="center">The Global Macro Database</h1>
<p align="center"><strong>Python Package</strong></p>

<p align="center">
  <a href="https://www.globalmacrodata.com" target="_blank" rel="noopener noreferrer">
    <img src="https://img.shields.io/badge/%F0%9F%8C%8D%20Explore%20the%20Database-globalmacrodata.com-2563EB?style=for-the-badge&labelColor=0B1F3A&color=2563EB" alt="Explore the Global Macro Database" height="46">
  </a>
</p>

<p align="center">
  <a href="https://www.globalmacrodata.com/research-paper.html" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Paper-Read-1E3A8A?style=flat-square&logo=readthedocs&logoColor=white" alt="Read the paper"></a>
  <a href="https://www.globalmacrodata.com/data.html" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Data-Download-0EA5E9?style=flat-square&logo=databricks&logoColor=white" alt="Download the data"></a>
  <a href="https://pypi.org/project/global-macro-data/" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/pypi/v/global-macro-data?style=flat-square&logo=pypi&logoColor=white&label=PyPI&color=3776AB" alt="PyPI version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Non--Commercial-DC2626?style=flat-square" alt="License: Non-Commercial"></a>
</p>

<p align="center"><a href="https://www.globalmacrodata.com/research-paper.html" target="_blank" rel="noopener noreferrer">Link to paper</a></p>

This repository complements the paper, **Müller, Xu, Lehbib, and Chen (2025)**, which introduces a panel dataset of **79 macroeconomic variables across 243 countries** from historical records beginning in the year **1086** until **2025**, including projections through the year **2030**.

## Features

- **Unparalleled Coverage**: Combines data from more than **121 contemporary and historical sources** (e.g., IMF, World Bank, OECD).
- **Extensive Variables**: GDP, inflation, government finance, trade, employment, interest rates, and more.
- **Harmonized Data**: Resolves inconsistencies and splices all available data together.
- **Scheduled Updates**: Regular releases ensure data reliability.
- **Full Transparency**: All code is open source and available in this repository.
- **Accessible Formats**: Provided in `.dta`, `.csv` and as **<a href="https://github.com/KMueller-Lab/Global-Macro-Database-Stata" target="_blank" rel="noopener noreferrer">Stata</a>/<a href="https://github.com/KMueller-Lab/Global-Macro-Database-Python" target="_blank" rel="noopener noreferrer">Python</a>/<a href="https://github.com/KMueller-Lab/Global-Macro-Database-R" target="_blank" rel="noopener noreferrer">R</a> package**.

## Installation

<a href="https://www.globalmacrodata.com/data.html" target="_blank" rel="noopener noreferrer">Download via website</a>

**Python package:**
```bash
# Install the latest published release from PyPI
pip install global-macro-data

# Or install the latest code directly from GitHub
pip install git+https://github.com/KMueller-Lab/Global-Macro-Database-Python.git
```

Upgrade an existing install:
```bash
pip install --upgrade global-macro-data
```

## Usage

```python
from global_macro_data import gmd

# Get data from the latest available version
df = gmd()

# Get data from a specific version
df = gmd(version="2025_12")

# List all available versions
gmd(version="list")

# Get data for a specific country
df = gmd(country="USA")

# Get data for multiple countries
df = gmd(country=["USA", "CHN", "DEU"])

# Get specific variables
df = gmd(variables=["rGDP", "infl", "unemp"])

# Restrict the year range
df = gmd(variables="rGDP", start_year=1990, end_year=2020)

# Get raw data for a single variable
df = gmd(variables="rGDP", raw=True)

# Cache the download locally for faster reloads
df = gmd(variables="rGDP", fast=True)

# Print available variables, or load them as a dataframe
gmd(vars="list")
var_df = gmd(vars="load")

# Print available countries, or load them as a dataframe
gmd(country="list")
country_df = gmd(country="load")

# Access data from a specific source (e.g., IMF World Economic Outlook)
df = gmd(sources="IMF_WEO")

# Access specific variables from a source
df = gmd(sources="IMF_WEO", variables="nGDP")

# List all available sources, or load the full source list as a dataframe
gmd(sources="list")
source_df = gmd(sources="load")

# Get BibTeX citation for a specific source
gmd(cite="GMD")

# Load the full citation list as a dataframe
bib_df = gmd(cite="load")

# Combine parameters
df = gmd(
    version="2025_12",
    country=["USA", "CHN"],
    variables=["rGDP", "unemp", "CPI"],
)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| **variables** | str or list | Variable code(s) to include (e.g., `"rGDP"` or `["rGDP", "unemp"]`) |
| **country** | str or list | ISO3 country code(s) (e.g., `"SGP"` or `["MRT", "SGP"]`). Use `"list"` to print or `"load"` to return the country table |
| **version** | str | Dataset version in format `"YYYY_MM"` (e.g., `"2025_12"`). Use `"current"` for the latest version, `"list"` to see all available versions |
| **start_year** | int | Keep only rows with `year >= start_year` |
| **end_year** | int | Keep only rows with `year <= end_year` |
| **raw** | bool | If `True`, download raw source-level data for a single variable |
| **vars** | str | `"list"` to print available variables with definitions and units, `"load"` to return them as a dataframe |
| **sources** | str | `"load"` to load the source list, `"list"` to print sources, or a source name (e.g., `"IMF_IFS"`) to load that source's data. Combine with `variables` to load only specific variables from that source |
| **cite** | str | `"load"` to load the citation list, or a source key (e.g., `"GMD"`) to display its BibTeX |
| **fast** | bool | If `True`, cache the dataset locally for faster reloading |
| **iso** | bool | If `True`, alias for `country="list"` |
| **network** | str | Pass `"yes"` to force the fetch when network detection has failed |

`raw`, `fast`, and `iso` also accept the boolean-like strings `yes`/`no`/`true`/`false`/`on`/`off`/`1`/`0`; any other value raises `GMDCommandError` instead of being silently treated as truthy.

Helper functions are also available:

- `get_available_versions()` — list all data vintages
- `get_current_version()` — get the latest version string
- `list_variables()` — print the variable table
- `list_countries()` — print the country table

## Citation

When using the Global Macro Database, please cite the following NBER Working Paper:

**Müller, K., Xu, C., Lehbib, M., & Chen, Z. (2025). The Global Macro Database: A New International Macroeconomic Dataset (NBER Working Paper No. 33714).**

```bibtex
@techreport{mueller2025global,
    title = {{The Global Macro Database: A New International Macroeconomic Dataset}},
    author = {Müller, Karsten and Xu, Chenzi and Lehbib, Mohamed and Chen, Ziliang},
    institution = {National Bureau of Economic Research},
    type = "Working Paper",
    series = "Working Paper Series",
    number = "33714",
    year = "2025",
    month = "April",
    doi = {10.3386/w33714},
    URL = "http://www.nber.org/papers/w33714",
}
```

## Documentation

You can find the [Technical Appendix](https://gmd-releases.s3.ap-southeast-2.amazonaws.com/data/distribute/GMD_TA.pdf) on the official [website](https://www.globalmacrodata.com).

Please visit this [repository](https://github.com/KMueller-Lab/Global-Macro-Database) to access the project source code.

## Authors

*   **Mohamed Lehbib** (National University of Singapore) - [lehbib@u.nus.edu](mailto:lehbib@u.nus.edu)

## License & Terms of Use

This repository and the bundled metadata shipped with the package are available for **non-commercial use only**. By using this package, you agree to the terms in [`LICENSE`](LICENSE) and the terms of use outlined on the [GMD website](https://www.globalmacrodata.com).

For license enquiries, please email [kmueller@globalmacrodata.com](mailto:kmueller@globalmacrodata.com).
