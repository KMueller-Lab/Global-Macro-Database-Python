# The Global Macro Database (Python Package)

<a href="https://www.globalmacrodata.com" target="_blank" rel="noopener noreferrer">
    <img src="https://img.shields.io/badge/Website-Visit-blue?style=flat&logo=google-chrome" alt="Website Badge">
</a>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This package provides Python access to the Global Macro Database (GMD).

## Installation

Install the latest published release from PyPI:

```bash
pip install global-macro-data
```

Install the latest code directly from GitHub:

```bash
pip install git+https://github.com/KMueller-Lab/Global-Macro-Database-Python.git
```

Install a specific Git ref from GitHub:

```bash
pip install git+https://github.com/KMueller-Lab/Global-Macro-Database-Python.git@<tag-or-commit>
```

## Updating

Upgrade an existing PyPI install:

```bash
pip install --upgrade global-macro-data
```

Upgrade an existing GitHub install:

```bash
pip install --upgrade --force-reinstall git+https://github.com/KMueller-Lab/Global-Macro-Database-Python.git
```

## Quick Start

```python
from global_macro_data import gmd

# Latest dataset
full_df = gmd()

# Specific vintage
df = gmd(version="2025_12")

# Filter countries and variables
subset = gmd(
    version="2025_12",
    country=["USA", "CHN"],
    variables=["rGDP", "infl", "unemp"],
)

# Raw source-level data for one variable
raw_rgdp = gmd(variables="rGDP", raw=True, version="2025_12")

# Load helper tables
varlist_df = gmd(vars="load")
country_df = gmd(country="load")
source_df = gmd(sources="load")
bib_df = gmd(cite="load")

# Print citations
gmd(cite="GMD")
gmd(print_option="GMD")
```

## API Reference

The `gmd()` function supports the following options:

| Parameter | Values | Description |
|-----------|--------|-------------|
| `version` | `"YYYY_MM"`, `"current"`, `"list"` | Select data vintage |
| `country` | ISO3 code(s), `"load"`, `"list"` | Filter by country |
| `variables` | Variable code(s) | Select specific variables |
| `raw` | `True` / `False` | Load raw source-level data |
| `vars` | `"load"`, `"list"` | Load or display variable definitions |
| `sources` | Source name, `"load"`, `"list"` | Query specific data sources |
| `cite` | Source key, `"load"` | Retrieve BibTeX citations |
| `print_option` | `"GMD"`, `"Stata"` | Print APA-style citations |
| `fast` | `"yes"` or `True` | Cache data locally for faster reloading |
| `network` | `"yes"` | Override network detection |

Input handling notes (consistent with the R and Stata packages):

- **Variable names are case-insensitive** and normalized to the dataset's
  canonical casing, e.g. `variables="rgdp"` returns the `rGDP` column. This
  applies to both the main dataset and the `sources=` path.
- **Country codes are case-insensitive**, e.g. `country="usa"` is treated as `USA`.
- **The `list` / `current` / `load` keywords are case-insensitive**, e.g.
  `version="LIST"`, `sources="LOAD"`, `vars="LIST"`, `cite="LOAD"`.
- **Citation and `print_option` keys are case-insensitive**, e.g. `cite="gmd"`,
  `print_option="stata"`.
- **Whitespace around `version` is trimmed**, e.g. `version=" 2025_12 "`.
- `version="current"` prints the latest version label *and* returns that dataset.

Helper functions are also available:

- `get_available_versions()` -- list all data vintages
- `get_current_version()` -- get the latest version string
- `list_variables()` -- print the variable table
- `list_countries()` -- print the country table

## Citation

When using the Global Macro Database, please cite:

```bibtex
@techreport{mueller2025global,
    title = {The Global Macro Database: A New International Macroeconomic Dataset},
    author = {M{\"u}ller, Karsten and Xu, Chenzi and Lehbib, Mohamed and Chen, Ziliang},
    year = {2025},
    institution = {National Bureau of Economic Research},
    type = {Working Paper},
    number = {33714}
}
```
