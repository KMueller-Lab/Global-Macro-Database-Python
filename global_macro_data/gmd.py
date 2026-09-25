
from __future__ import annotations

import io
import re
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Sequence, Union

import pandas as pd
import requests

PACKAGE_VERSION = "2.0.0"

_DATA_BASES = (
    "https://gmd-releases.s3.ap-southeast-2.amazonaws.com/data",
    "https://raw.githubusercontent.com/KMueller-Lab/Global-Macro-Database/refs/heads/main/data",
)
_TIMEOUT_SECONDS = 60
_CACHE_DIR = Path.home() / ".global_macro_data"
_ID_COLS = ("ISO3", "year", "id", "countryname")

_APA_GMD = (
    "Müller, K., Xu, C., Lehbib, M., & Chen, Z. (2025). "
    "The Global Macro Database: A New International Macroeconomic Dataset "
    "(NBER Working Paper No. 33714)."
)
_APA_PACKAGE = (
    "Lehbib, M. & Müller, K. (2025). gmd: The Easy Way to Access the "
    "World's Most Comprehensive Macroeconomic Database. Working Paper."
)

_ISSUES_URL = "https://github.com/KMueller-Lab/Global-Macro-Database"
_UPGRADE_MSG = "There is a new version of the package. Run: pip install --upgrade global-macro-data"
_NETWORK_HINT = 'If you have active internet access, specify the option: gmd(network="yes")'
_VARS_HINTS = (
    'To print the list of variables: gmd(vars="list")',
    'To load the list of variables: gmd(vars="load")',
)
_COUNTRY_HINTS = (
    'To print the list of countries: gmd(country="list")',
    'To load the list of countries: gmd(country="load")',
)

VALID_VARIABLES = [
    "CA","CA_USD","CA_GDP","cbrate","cons_USD","cons","cons_GDP","CPI","deflator",
    "exports","exports_GDP","exports_USD","finv_USD","finv","finv_GDP","HPI","imports_GDP",
    "imports","imports_USD","infl","inv_GDP","inv","inv_USD","ltrate","M0","M1","M2",
    "M3","M4","nGDP_USD","nGDP","pop","REER","rGDP","rGDP_pc_USD","rGDP_pc","rGDP_USD",
    "strate","unemp","USDfx","BankingCrisis","SovDebtCrisis","CurrencyCrisis","cgovdebt",
    "cgovdebt_GDP","cgovdef","cgovdef_GDP","cgovexp","cgovexp_GDP","cgovrev","cgovrev_GDP",
    "cgovtax","cgovtax_GDP","gen_govdebt","gen_govdebt_GDP","gen_govdef","gen_govdef_GDP",
    "gen_govexp","gen_govexp_GDP","gen_govrev","gen_govrev_GDP","gen_govtax","gen_govtax_GDP",
    "govrev_GDP","govexp_GDP","govtax_GDP","govdef_GDP","govdebt_GDP","govrev","govexp",
    "govtax","govdef","govdebt",
]


class GMDCommandError(RuntimeError):
    def __init__(self, message: str, code: int = 498, data: Optional[pd.DataFrame] = None):
        super().__init__(message)
        self.code = code
        self.data = data


def _emit(*lines: str) -> None:
    for line in lines:
        print(line)


def _fail(*lines: str, code: int = 498) -> None:
    if lines:
        _emit(*lines)
        raise GMDCommandError(lines[-1], code=code)
    raise GMDCommandError("gmd failed", code=code)


def _fail_with_issue(resource: str, code: int = 498) -> None:
    _fail(f"Unable to access {resource}. Please raise an issue at {_ISSUES_URL}", code=code)


def _fail_needs_internet(action: str) -> None:
    _fail(f"You need access to the internet in order to {action}", _NETWORK_HINT, code=498)


def _sort_versions_df(df: pd.DataFrame) -> pd.DataFrame:
    parts = df["versions"].astype(str).str.extract(r"(?P<year>\d{4})_(?P<month>\d{2})")
    df = df.assign(
        _year=pd.to_numeric(parts["year"], errors="coerce"),
        _month=pd.to_numeric(parts["month"], errors="coerce"),
    ).sort_values(["_year", "_month"], ascending=[False, False])
    return df.drop(columns=["_year", "_month"]).reset_index(drop=True)


def _fetch_from(relative_path: str, bases: Sequence[str]) -> requests.Response:
    errors: List[str] = []
    for base in bases:
        url = f"{base}/{relative_path}"
        try:
            response = requests.get(url, timeout=_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            errors.append(f"{url}: {exc}")
    raise RuntimeError(f"Unable to load '{relative_path}'. {'; '.join(errors)}")


def _fetch_first(relative_path: str) -> requests.Response:
    return _fetch_from(relative_path, _DATA_BASES)


def _fetch_primary(relative_path: str) -> requests.Response:
    return _fetch_from(relative_path, (_DATA_BASES[0],))


def _fetch_secondary(relative_path: str) -> requests.Response:
    return _fetch_from(relative_path, (_DATA_BASES[1],))


def _read_csv(resp: requests.Response, **kwargs) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(resp.text), **kwargs)


def _read_dta(resp: requests.Response) -> pd.DataFrame:
    return pd.read_stata(io.BytesIO(resp.content), convert_categoricals=False)


def _read_csv_primary(relative_path: str, **kwargs) -> pd.DataFrame:
    return _read_csv(_fetch_primary(relative_path), **kwargs)


def _read_dta_primary(relative_path: str) -> pd.DataFrame:
    return _read_dta(_fetch_primary(relative_path))


def _tokens(value: Union[str, Sequence[str], None]) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        bits = value.replace(",", " ").split()
        return [bit.strip() for bit in bits if bit.strip()]
    out: List[str] = []
    for item in value:
        if isinstance(item, str):
            out.extend(_tokens(item))
        else:
            out.append(str(item))
    return out


def _is_fast_yes(fast: Optional[Union[str, bool]]) -> bool:
    if isinstance(fast, bool):
        return fast
    if isinstance(fast, str):
        return fast.strip().lower() == "yes"
    return False


def _ensure_cache_dir() -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_versions() -> List[str]:
    if not _CACHE_DIR.exists():
        return []
    out: List[str] = []
    pattern = re.compile(r"^GMD_(\d{4}_\d{2})\.dta$")
    for path in _CACHE_DIR.glob("GMD_*.dta"):
        match = pattern.match(path.name)
        if match:
            out.append(match.group(1))
    return sorted(set(out), reverse=True)


def _default_local_gmd_path() -> Optional[Path]:
    dta = _CACHE_DIR / "GMD.dta"
    if dta.exists():
        return dta
    return None


def _read_local_df(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".dta":
        return pd.read_stata(path, convert_categoricals=False)
    return pd.read_csv(path)

@lru_cache(maxsize=1)
def _versions_df() -> pd.DataFrame:
    df = _read_csv_primary("helpers/versions.csv")
    if "versions" not in df.columns:
        raise RuntimeError("Malformed versions.csv")
    return _sort_versions_df(df)


@lru_cache(maxsize=1)
def _varlist_df() -> pd.DataFrame:
    return _read_csv_primary("helpers/varlist.csv")


@lru_cache(maxsize=1)
def _source_list_df() -> pd.DataFrame:
    return _read_csv_primary("helpers/source_list.csv")


@lru_cache(maxsize=1)
def _bib_df() -> pd.DataFrame:
    return _read_csv_primary("helpers/bib_dataframe.csv")


@lru_cache(maxsize=1)
def _country_df() -> pd.DataFrame:
    return _read_dta_primary("helpers/countrylist.dta")


def _format_bibtex_for_print(entry: str) -> str:
    text = re.sub(r",\s*([a-zA-Z0-9_]+\s*=)", r",\n  \1", entry.strip())
    return re.sub(r"\}\s*$", "\n}", text)


def _print_var_table(df: pd.DataFrame) -> None:
    table = df
    if "variable" not in table.columns and "variables" in table.columns:
        table = table.rename(columns={"variables": "variable"})  # rename returns a new DataFrame
    if not {"variable", "definition", "units"}.issubset(table.columns):
        _fail_with_issue("variable list")

    varlength = int(table["variable"].astype(str).str.len().max()) + 2
    deflength = int(table["definition"].astype(str).str.len().max()) + varlength + 2

    _emit("", "Available variables:", "")
    _emit("-" * 90)
    _emit(
        f"Variable{' ' * max(varlength - len('Variable'), 1)}"
        f"Definition{' ' * max(deflength - varlength - len('Definition'), 1)}Units"
    )
    _emit("-" * 90)
    for _, row in table.iterrows():
        vname = str(row["variable"])
        vdesc = str(row["definition"])
        vunits = str(row["units"])
        left = vname + (" " * max(varlength - len(vname), 1))
        mid = " " * max(deflength - len(left) - len(vdesc), 1)
        _emit(f"{left}{vdesc}{mid}{vunits}")
    _emit("-" * 90)


def _print_country_table(df: pd.DataFrame) -> None:
    if not {"countryname", "ISO3"}.issubset(df.columns):
        _fail_with_issue("country list")
    _emit("", "Available countries:", "")
    _emit("-" * 90)
    _emit("ISO3 code  Country name")
    _emit("-" * 90)
    for _, row in df[["ISO3", "countryname"]].iterrows():
        _emit(f"{str(row['ISO3']):<10}{row['countryname']}")
    _emit("-" * 90)


def _summary(
    df: pd.DataFrame,
    anything: str,
    country: str,
    selected_version: str,
    version_opt: Optional[str],
    raw: bool,
    sources: Optional[str],
    fast: Optional[Union[str, bool]],
    saved_gmd: bool,
) -> None:
    n_vars = len(df.columns)
    for ident in _ID_COLS:
        if ident in df.columns:
            n_vars -= 1
    if n_vars <= 0:
        _fail(f"The database has no data on {anything} for {country}", code=498)
    if len(df) <= 0:
        return

    _emit("Global Macro Database by Müller, Xu, Lehbib, and Chen (2025)")
    _emit("Website: https://www.globalmacrodata.com")
    _emit("")
    _emit("When using these data, please cite:")
    _emit('For BibTeX: gmd(cite="GMD")  |  For APA: gmd(print_option="GMD")')
    _emit("")
    _emit("When using the gmd command, please further cite:")
    _emit('For BibTeX: gmd(cite="lehbib2025gmd")  |  For APA: gmd(print_option="Stata")')
    _emit("")

    if (fast is None or str(fast).strip() == "") and (not saved_gmd) and (not raw):
        _emit(
            f"To save the data locally for faster reloading, use: "
            f'gmd(version="{selected_version}", fast="yes")'
        )

    if raw or (sources is not None and str(sources) != ""):
        _emit(f"Final dataset: {len(df)} observations of {n_vars} variables")
    else:
        if n_vars > 1:
            _emit(f"Final dataset: {len(df)} observations for {n_vars} variables")
        else:
            _emit(f"Final dataset: {len(df)} observations for {n_vars} variable")

    if version_opt is not None and str(version_opt) != "":
        _emit(f"Version: {version_opt}")
    else:
        _emit(f"Version: {selected_version}")


def _normalize_source_name(source: str) -> str:
    source = source.strip()
    if len(source) == 7 and source.startswith("CS"):
        # Convert CS-prefixed 7-char alias e.g. "CS1_ARG" → "ARG_1"
        return f"{source[-3:]}_{source[2]}"
    return source


def _strip_source_prefix_cols(df: pd.DataFrame, source: str) -> List[str]:
    pref = f"{source}_"
    out: List[str] = []
    for col in df.columns:
        if col in ("ISO3", "year"):
            continue
        if col.startswith(pref):
            out.append(col[len(pref):])
        else:
            out.append(col)
    return out


def get_available_versions() -> List[str]:
    try:
        return _versions_df()["versions"].astype(str).tolist()
    except RuntimeError:
        versions = _cache_versions()
        if versions:
            return versions
        if _default_local_gmd_path() is not None:
            return ["local"]
        raise


def get_current_version() -> str:
    return get_available_versions()[0]


def list_variables() -> None:
    _print_var_table(_varlist_df())


def list_countries() -> None:
    _print_country_table(_country_df())

def gmd(
    variables: Optional[Union[str, Sequence[str]]] = None,
    country: Optional[Union[str, Sequence[str]]] = None,
    version: Optional[str] = None,
    raw: bool = False,
    iso: bool = False,
    vars: Optional[Union[bool, str]] = None,
    sources: Optional[str] = None,
    cite: Optional[str] = None,
    print_option: Optional[str] = None,
    network: Optional[str] = None,
    fast: Optional[Union[str, bool]] = None,
    **kwargs,
) -> Optional[pd.DataFrame]:
    if "print" in kwargs:
        if print_option is not None:
            raise TypeError("Specify either print_option or print, not both.")
        print_option = kwargs.pop("print")
    if kwargs:
        raise TypeError(f"Unexpected keyword argument(s): {', '.join(kwargs.keys())}")

    if iso:
        country = "list"
    if vars is True:
        vars = "list"
    elif vars is False:
        vars = None

    # [#3] Treat the list/current/load keywords case-insensitively (consistent with R).
    # Only normalize a string arg when it *is* one of these keywords; real version
    # numbers / source names / cite keys are left unchanged.
    def _kw(v, words):
        return v.lower() if isinstance(v, str) and v.lower() in words else v
    # [#4] Trim surrounding whitespace on the version value so " 2026_03 " (and a
    # padded keyword like " list ") works. Country/variable tokens are already
    # trimmed via _tokens().
    if isinstance(version, str):
        version = version.strip()
    version = _kw(version, {"list", "current"})
    sources = _kw(sources, {"load", "list"})
    cite = _kw(cite, {"load"})
    vars = _kw(vars, {"load", "list"})

    anything_tokens = _tokens(variables)
    anything = " ".join(anything_tokens)
    word_count = len(anything_tokens)

    if isinstance(country, str):
        country_arg = country
    elif country is None:
        country_arg = ""
    else:
        country_arg = " ".join(_tokens(country))

    if print_option is not None:
        option = str(print_option).strip().lower()
        if option == "gmd":
            _emit(_APA_GMD)
            return None
        if option == "stata":
            _emit(_APA_PACKAGE)
            return None
        _fail("Invalid option for print(). valid arguments are 'GMD' or 'Stata'.", code=198)

    selected_version = ""
    available_versions: List[str] = []
    has_internet = True
    gmd_local_path: Optional[Path] = None
    saved_gmd = False

    try:
        versions_df = _versions_df()
        selected_version = str(versions_df.loc[0, "versions"])
        available_versions = sorted(set(versions_df["versions"].astype(str).tolist()))

        if "version_package" in versions_df.columns:
            package_remote = str(versions_df.loc[0, "version_package"])
            if package_remote != PACKAGE_VERSION:
                _emit(_UPGRADE_MSG)

        if version == "list":
            for ver in available_versions:
                _emit(ver)
            return None

        if version is not None and str(version) != "":
            if len(_tokens(str(version))) != 1:
                _emit(
                    f"Version must either be one specific version ({selected_version}) or current."
                )
                return None
            requested = str(version)
            if requested in available_versions:
                selected_version = requested
            elif requested == "current":
                _emit(f"Current version: {selected_version}")
            else:
                _fail(
                    f"Error: Version {requested} does not exist",
                    f"Available versions: {' '.join(available_versions)}",
                    code=498,
                )

    except RuntimeError as exc:
        if isinstance(exc, GMDCommandError):
            raise
        try:
            versions_gh = _read_csv(_fetch_secondary("helpers/versions.csv"))
            if "versions" in versions_gh.columns and "version_package" in versions_gh.columns:
                versions_gh = _sort_versions_df(versions_gh)
                package_remote = str(versions_gh.iloc[0]["version_package"])
                if package_remote != PACKAGE_VERSION:
                    _emit(_UPGRADE_MSG)
                    _emit(f"Please raise an issue if the update does not work at {_ISSUES_URL}")
        except RuntimeError:
            pass

        has_internet = network is not None and str(network) != ""
        _emit("Error: Unable to access version information. Check internet connection.")
        _emit("Loading local version")

        local_default = _default_local_gmd_path()
        if local_default is None:
            _fail("Local version not found", code=498)

        gmd_local_path = local_default
        saved_gmd = True
        selected_version = ""

    if not has_internet:
        if sources in ("load", "list"):
            _fail_needs_internet("fetch the sources list")
        elif sources is not None and str(sources) != "":
            _fail_needs_internet(f"fetch the {sources} data")

        if raw:
            _fail_needs_internet("fetch the raw data")

        if cite == "load":
            _fail_needs_internet("load the sources to cite")
        elif cite is not None and str(cite) != "":
            _fail_needs_internet(f"cite {cite}")

    if cite == "load":
        try:
            return _bib_df()
        except RuntimeError:
            _fail_with_issue("the list of sources to cite")

    if cite is not None and str(cite) != "":
        cite_tokens = _tokens(str(cite))
        if len(cite_tokens) != 1:
            _fail("Only one citation can be retrieved at a time", code=498)
        key = cite_tokens[0]

        bib = _bib_df()
        if "source_name" not in bib.columns:
            _fail("source_name not found", code=111)
        if "citation" not in bib.columns:
            _fail("citation not found", code=111)
        mask = bib["source_name"].astype(str).str.lower() == key.lower()
        if not mask.any():
            _fail(
                f"Source '{key}' does not exist.",
                'To load the list of sources to cite: gmd(cite="load")',
                code=498,
            )
        _emit(_format_bibtex_for_print(str(bib.loc[mask, "citation"].iloc[0])))
        return None

    if sources is not None and str(sources) != "" and raw:
        _emit("Note: raw option is specified, but this is implicit when using the sources option.")

    if sources in ("load", "list"):
        try:
            source_df = _source_list_df()
        except RuntimeError:
            _fail_with_issue("source list")
        if sources == "load":
            _emit("Imported the list of sources.")
            return source_df
        for src in sorted(set(source_df["source_name"].astype(str).tolist())):
            _emit(src)
        return None

    if sources is not None and str(sources) != "":

        src_name = str(sources).strip()
        cs_col_prefix = None
        if len(src_name) == 7 and src_name.startswith("CS"):
            # CS-aliased sources keep the ORIGINAL alias prefix on their data
            # columns (e.g. "CS1_M3_GDP"), while the .dta file/source name is
            # normalized (e.g. "ARG_1"). Remember the column prefix so variable
            # selection resolves against the real column names.
            cs_col_prefix = src_name.split("_")[0]
            src_name = _normalize_source_name(src_name)

        src_tokens = _tokens(src_name)
        if len(src_tokens) > 1:
            _fail("Warning: Please specify exactly one source.", code=498)
        src_name = src_tokens[0]

        try:
            src_df = _read_dta_primary(f"clean/combined/{src_name}.dta")
        except RuntimeError:
            # First load failed — try correcting the source name and retry
            try:
                source_list = _source_list_df()
            except RuntimeError:
                _emit(f"Unable to access source list. Please raise an issue at {_ISSUES_URL}")
                src_df = pd.DataFrame()
                return src_df
            mask = source_list["source_name"].astype(str).str.lower() == src_name.lower()
            if not mask.any():
                _fail(
                    "Invalid source name",
                    'To load the list of sources: gmd(sources="load")',
                    code=498,
                )
            src_name = str(source_list.loc[mask, "source_name"].iloc[0])
            try:
                src_df = _read_dta_primary(f"clean/combined/{src_name}.dta")
            except RuntimeError:
                _fail(
                    f"Unable to load data for source '{src_name}'.",
                    "Please check your internet connection or report this issue.",
                    code=498,
                )

        if anything != "":
            # Match the variable name case-insensitively against the source's
            # columns and resolve to the dataset's canonical casing (e.g.
            # "rgdp" -> "PWT_rGDP"), consistent with the main dataset path.
            _col_by_lower = {str(col).lower(): str(col) for col in src_df.columns}
            src_col = _col_by_lower.get(f"{cs_col_prefix or src_name}_{anything}".lower())
            if src_col is not None:
                keep_cols: List[str] = [col for col in ["ISO3", "year", src_col] if col in src_df.columns]
                if "countryname" in src_df.columns:
                    keep_cols.append("countryname")
                if "id" in src_df.columns:
                    keep_cols.append("id")
                out = src_df.loc[:, keep_cols]

                if country_arg != "":
                    target = country_arg.upper()
                    out = out.loc[out["ISO3"].astype(str).str.upper() == target]
                return out

            avail = _strip_source_prefix_cols(src_df, cs_col_prefix or src_name)
            _fail(f"This source doesn't have data on {anything}. It has data on {' '.join(avail)}.")

        return src_df

    if vars == "load":
        try:
            return _varlist_df().copy()
        except RuntimeError:
            _fail_with_issue("variable list")

    if vars == "list":
        try:
            var_df = _varlist_df()
        except RuntimeError:
            _fail_with_issue("variable list")
        _print_var_table(var_df)
        return None

    df: Optional[pd.DataFrame] = None
    if raw:
        if word_count != 1:
            _fail("Warning: Please specify exactly one variable.", code=498)
        try:
            df = _read_csv_primary(f"distribute/{anything}_{selected_version}.csv")
        except RuntimeError:
            try:
                var_df = _varlist_df()
                # Check if the variable is listed in the varlist values
                var_col = "variable" if "variable" in var_df.columns else "variables"
                is_valid = var_col in var_df.columns and anything in set(var_df[var_col].astype(str))
            except RuntimeError:
                is_valid = False
            if not is_valid:
                _fail("Specified variable is not valid.", code=498)
            _fail("Variable does not have raw data.", code=498)
        _emit(f"Loaded raw data on {anything}")

    if isinstance(country, str) and country.lower() in {"load", "list"}:
        mode = country.lower()
        _ensure_cache_dir()
        local_country = _CACHE_DIR / "countrylist.dta"
        if local_country.exists():
            cty_df = pd.read_stata(local_country, convert_categoricals=False)
        else:
            try:
                cty_df = _country_df().copy()
            except RuntimeError:
                _fail_with_issue("country list")
            if _is_fast_yes(fast):
                _emit("Saving countrylist dataframe locally")
                cty_df.to_stata(local_country, write_index=False)

        if mode == "load":
            return cty_df
        _print_country_table(cty_df)
        return None

    check_id = anything.lower()
    if check_id in {c.lower() for c in _ID_COLS}:
        _fail(
            f"{anything} is an identifying variable loaded in the dataset, specify common variables",
            *_VARS_HINTS,
            code=498,
        )

    if not raw:
        _ensure_cache_dir()
        if gmd_local_path is None:
            local_version = _CACHE_DIR / f"GMD_{selected_version}.dta"
            if local_version.exists():
                saved_gmd = True
                df = pd.read_stata(local_version, convert_categoricals=False)
            elif _is_fast_yes(fast):
                try:
                    df = _read_dta_primary(f"distribute/GMD_{selected_version}.dta")
                except RuntimeError:
                    _fail_with_issue("the data")
                df.to_stata(local_version, write_index=False)
                df.to_stata(_CACHE_DIR / "GMD.dta", write_index=False)
                _emit(f"GMD dataset loaded and saved locally in {_CACHE_DIR}.")
            else:
                try:
                    df = _read_dta_primary(f"distribute/GMD_{selected_version}.dta")
                except RuntimeError:
                    _fail_with_issue("the data")
        else:
            df = _read_local_df(gmd_local_path)

    if df is None:
        raise GMDCommandError("No data loaded", code=498)

    # Valid country codes come from the FULL loaded panel, captured BEFORE the
    # variable-missingness row filter below, so a valid country that merely lacks
    # the requested variable is not later misreported as an invalid ISO3 code.
    _valid_iso = set(df["ISO3"].astype(str).str.upper()) if "ISO3" in df.columns else set()

    if anything != "" and not raw:
        # Match variable names case-insensitively and normalize to the dataset's
        # canonical casing (e.g. "rgdp" -> "rGDP"), consistent with how country
        # codes and source names are already handled.
        _col_by_lower = {str(col).lower(): str(col) for col in df.columns}
        _canonical: List[str] = []
        invalid_vars = []
        for var in anything_tokens:
            actual = _col_by_lower.get(var.lower())
            if actual is None:
                invalid_vars.append(var)
            else:
                _canonical.append(actual)
        if invalid_vars:
            if len(invalid_vars) == 1:
                _emit(f"{invalid_vars[0]} is not a valid variable code")
            else:
                _emit(f"{' '.join(invalid_vars)} are not valid variable codes")
            _fail(*_VARS_HINTS, code=498)
        anything_tokens = _canonical

        keep_cols = list(dict.fromkeys(col for col in list(_ID_COLS) + anything_tokens if col in df.columns))
        df = df.loc[:, keep_cols].copy()
        valid_count = df[anything_tokens].notna().sum(axis=1)
        if {"ISO3", "year"}.issubset(df.columns):
            ordered = df.assign(_valid_count=valid_count).sort_values(["ISO3", "year"])
            mask = ordered.groupby("ISO3", sort=False)["_valid_count"].cumsum() > 0
            df = ordered.loc[mask].drop(columns=["_valid_count"])

    if country_arg != "":
        c_tokens = _tokens(country_arg.upper())
        if len(c_tokens) == 1:
            iso_code = c_tokens[0]
            iso_series = df["ISO3"].astype(str).str.upper() if "ISO3" in df.columns else pd.Series(dtype=str)
            if iso_series.empty or not (iso_series == iso_code).any():
                _fail(
                    "Country code is invalid or no data for this country in source.",
                    *_COUNTRY_HINTS,
                    code=498,
                )
            df = df.loc[iso_series == iso_code]
        elif len(c_tokens) > 1:
            if "ISO3" not in df.columns:
                _fail(
                    "Country code is invalid or no data for this country in source.",
                    *_COUNTRY_HINTS,
                    code=498,
                )
            iso_series = df["ISO3"].astype(str).str.upper()
            keep_mask = pd.Series(False, index=df.index)
            invalid: List[str] = []
            for iso_code in c_tokens:
                one = iso_series == iso_code
                if one.any():
                    keep_mask = keep_mask | one
                elif iso_code not in _valid_iso:
                    invalid.append(iso_code)
                # else: a valid country that has no rows left after the variable-
                # missingness filter above -> keep silently (contributes 0 rows)
                # instead of being falsely flagged as an invalid ISO3 code.

            if invalid:
                inv = " ".join(invalid)
                if len(invalid) == 1:
                    _emit(f"{inv} is not a valid ISO3 code")
                else:
                    _emit(f"{inv} are not valid ISO3 codes")
                _emit(*_COUNTRY_HINTS)
                df = df.loc[keep_mask]
                raise GMDCommandError("Invalid ISO3 code", code=498, data=df.dropna(axis=1, how="all"))

            df = df.loc[keep_mask]

    df = df.dropna(axis=1, how="all")

    _summary(
        df=df,
        anything=anything,
        country=country_arg,
        selected_version=selected_version,
        version_opt=version,
        raw=raw,
        sources=sources,
        fast=fast,
        saved_gmd=saved_gmd,
    )

    return df
