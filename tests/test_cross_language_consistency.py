"""Cross-language consistency tests for ``gmd()``.

These exercise the input-normalization behaviors that align the Python package
with the R / Stata packages while reading the same S3 dataset:

* case-insensitive keyword arguments (``list`` / ``current`` / ``load``),
* case-insensitive variable names normalized to the dataset's canonical casing
  (``"rgdp"`` -> ``"rGDP"``), on both the main dataset and ``sources=`` paths,
* case-insensitive country codes and citation / print keys,
* whitespace trimming on the ``version`` argument.

Everything runs fully offline against the bundled fixtures (see conftest.py),
which provide version ``2025_12``, sources ``IMF_IFS`` / ``ARG_1`` and the raw
``rGDP`` series.
"""
import pandas as pd
import pytest

from global_macro_data import gmd, GMDCommandError

_ID_COLS = {"ISO3", "year", "id", "countryname"}


def _data_cols(df: pd.DataFrame) -> list:
    """Return the non-identifier columns of a returned dataset."""
    return [c for c in df.columns if c not in _ID_COLS]


# ---------------------------------------------------------------------------
# Keyword case-insensitivity  (list / current / load)
# ---------------------------------------------------------------------------

class TestKeywordCaseInsensitivity:
    @pytest.mark.parametrize("kw", ["list", "LIST", "List", "lIsT"])
    def test_version_list_any_case(self, kw, capsys):
        result = gmd(version=kw)
        out = capsys.readouterr().out
        assert result is None
        assert "2025_12" in out

    @pytest.mark.parametrize("kw", ["current", "CURRENT", "Current"])
    def test_version_current_any_case(self, kw, capsys):
        # "current" announces the latest version and loads that dataset.
        result = gmd(version=kw)
        out = capsys.readouterr().out
        assert isinstance(result, pd.DataFrame)
        assert "Current version:" in out

    @pytest.mark.parametrize("kw", ["load", "LOAD", "Load"])
    def test_sources_load_any_case(self, kw):
        df = gmd(sources=kw)
        assert isinstance(df, pd.DataFrame)
        assert "source_name" in df.columns

    @pytest.mark.parametrize("kw", ["list", "LIST"])
    def test_sources_list_any_case(self, kw, capsys):
        result = gmd(sources=kw)
        out = capsys.readouterr().out
        assert result is None
        assert "IMF_IFS" in out

    @pytest.mark.parametrize("kw", ["load", "LOAD", "Load"])
    def test_cite_load_any_case(self, kw):
        df = gmd(cite=kw)
        assert isinstance(df, pd.DataFrame)
        assert "citation" in df.columns

    @pytest.mark.parametrize("kw", ["list", "LIST"])
    def test_vars_list_any_case(self, kw, capsys):
        result = gmd(vars=kw)
        out = capsys.readouterr().out
        assert result is None
        assert "Available variables:" in out

    @pytest.mark.parametrize("kw", ["load", "LOAD"])
    def test_vars_load_any_case(self, kw):
        df = gmd(vars=kw)
        assert isinstance(df, pd.DataFrame)
        assert "variables" in df.columns


# ---------------------------------------------------------------------------
# Whitespace trimming on the version argument
# ---------------------------------------------------------------------------

class TestVersionWhitespace:
    def test_padded_specific_version(self):
        df = gmd(version=" 2025_12 ")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_padded_list_keyword(self, capsys):
        result = gmd(version=" list ")
        out = capsys.readouterr().out
        assert result is None
        assert "2025_12" in out

    def test_padded_current_keyword(self, capsys):
        result = gmd(version=" current ")
        out = capsys.readouterr().out
        assert isinstance(result, pd.DataFrame)
        assert "Current version:" in out


# ---------------------------------------------------------------------------
# Variable-name case-insensitivity + canonical casing (main dataset path)
# ---------------------------------------------------------------------------

class TestVariableCaseInsensitivity:
    @pytest.mark.parametrize("name", ["rgdp", "RGDP", "rGDP", "Rgdp"])
    def test_single_variable_any_case_normalizes_to_canonical(self, name):
        df = gmd(variables=name, version="2025_12")
        # The returned column always uses the dataset's canonical casing,
        # regardless of how the caller typed the name.
        assert _data_cols(df) == ["rGDP"]

    def test_multiple_variables_mixed_case_normalized_and_ordered(self):
        df = gmd(variables=["rgdp", "INFL"], version="2025_12")
        assert _data_cols(df) == ["rGDP", "infl"]

    def test_comma_separated_mixed_case(self):
        df = gmd(variables="rgdp,INFL", version="2025_12")
        assert set(_data_cols(df)) == {"rGDP", "infl"}

    def test_invalid_variable_still_raises(self, capsys):
        with pytest.raises(GMDCommandError):
            gmd(variables="totally_fake_var", version="2025_12")
        out = capsys.readouterr().out
        assert "not a valid variable code" in out

    def test_mixed_valid_invalid_reports_only_invalid(self, capsys):
        with pytest.raises(GMDCommandError):
            gmd(variables=["rgdp", "fakevar"], version="2025_12")
        out = capsys.readouterr().out
        assert "fakevar is not a valid variable code" in out
        # "rgdp" matched case-insensitively, so it must not be flagged invalid.
        assert "rgdp is not a valid" not in out


# ---------------------------------------------------------------------------
# Variable-name case-insensitivity on the sources= path
# ---------------------------------------------------------------------------

class TestSourceVariableCaseInsensitivity:
    @pytest.mark.parametrize("name", ["rgdp", "RGDP", "rGDP"])
    def test_source_variable_any_case_resolves_canonical_column(self, name):
        df = gmd(sources="IMF_IFS", variables=name, country="USA", version="2025_12")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        # The source-prefixed column keeps the dataset's canonical casing.
        assert "IMF_IFS_rGDP" in df.columns

    def test_source_missing_variable_raises(self, capsys):
        with pytest.raises(GMDCommandError):
            gmd(sources="IMF_IFS", variables="NOT_A_VAR", version="2025_12")
        out = capsys.readouterr().out
        assert "This source doesn't have data on NOT_A_VAR." in out


# ---------------------------------------------------------------------------
# Country-code case-insensitivity
# ---------------------------------------------------------------------------

class TestCountryCaseInsensitivity:
    @pytest.mark.parametrize("code", ["usa", "USA", "Usa"])
    def test_single_country_any_case(self, code):
        df = gmd(version="2025_12", country=code)
        assert set(df["ISO3"].unique()) == {"USA"}

    def test_multiple_countries_lowercase(self):
        df = gmd(version="2025_12", country="usa chn")
        assert set(df["ISO3"].unique()) == {"USA", "CHN"}


# ---------------------------------------------------------------------------
# Citation / print keys are case-insensitive
# ---------------------------------------------------------------------------

class TestCiteAndPrintCaseInsensitivity:
    @pytest.mark.parametrize("key", ["GMD", "gmd", "Gmd"])
    def test_cite_key_any_case(self, key, capsys):
        result = gmd(cite=key)
        out = capsys.readouterr().out
        assert result is None
        assert "@techreport" in out

    @pytest.mark.parametrize("opt", ["GMD", "gmd"])
    def test_print_gmd_any_case(self, opt, capsys):
        result = gmd(print_option=opt)
        out = capsys.readouterr().out
        assert result is None
        assert "Müller, K., Xu, C., Lehbib, M., & Chen, Z. (2025)." in out

    @pytest.mark.parametrize("opt", ["Stata", "stata", "STATA"])
    def test_print_stata_any_case(self, opt, capsys):
        result = gmd(print_option=opt)
        out = capsys.readouterr().out
        assert result is None
        assert "Lehbib, M. & Müller, K. (2025)." in out
