import importlib

import pandas as pd
import pytest

from global_macro_data import (
    VALID_VARIABLES,
    GMDCommandError,
    get_available_versions,
    get_current_version,
    gmd,
    list_countries,
    list_variables,
)

gmd_module = importlib.import_module("global_macro_data.gmd")


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

class TestTokens:
    def test_none_returns_empty(self):
        assert gmd_module._tokens(None) == []

    def test_string_splits_on_spaces(self):
        assert gmd_module._tokens("a b c") == ["a", "b", "c"]

    def test_string_splits_on_commas(self):
        assert gmd_module._tokens("a,b,c") == ["a", "b", "c"]

    def test_list_of_strings(self):
        assert gmd_module._tokens(["a", "b c"]) == ["a", "b", "c"]

    def test_nested_sequences(self):
        assert gmd_module._tokens(["a b", "c,d"]) == ["a", "b", "c", "d"]

    def test_numeric_in_list(self):
        assert gmd_module._tokens([1, 2]) == ["1", "2"]


class TestIsFastYes:
    def test_true(self):
        assert gmd_module._is_fast_yes(True) is True

    def test_false(self):
        assert gmd_module._is_fast_yes(False) is False

    def test_string_yes(self):
        assert gmd_module._is_fast_yes("yes") is True

    def test_string_YES(self):
        assert gmd_module._is_fast_yes("YES") is True

    def test_string_no(self):
        assert gmd_module._is_fast_yes("no") is False

    def test_none(self):
        assert gmd_module._is_fast_yes(None) is False


class TestCoerceFlag:
    def test_bool_passthrough(self):
        assert gmd_module._coerce_flag(True, "raw") is True
        assert gmd_module._coerce_flag(False, "raw") is False

    def test_none_is_false(self):
        assert gmd_module._coerce_flag(None, "raw") is False

    def test_truthy_strings(self):
        for token in ("yes", "Y", "TRUE", "1", "on", " On "):
            assert gmd_module._coerce_flag(token, "fast") is True

    def test_falsey_strings(self):
        for token in ("no", "N", "false", "0", "off", ""):
            assert gmd_module._coerce_flag(token, "raw") is False

    def test_invalid_string_raises(self):
        with pytest.raises(GMDCommandError):
            gmd_module._coerce_flag("maybe", "raw")

    def test_invalid_type_raises(self):
        with pytest.raises(GMDCommandError):
            gmd_module._coerce_flag(2.5, "raw")


class TestFlagCoercionInGmd:
    def test_raw_no_does_not_load_raw(self, capsys):
        df = gmd(variables="rGDP", raw="no", version="2025_12")
        out = capsys.readouterr().out
        assert isinstance(df, pd.DataFrame)
        assert "Loaded raw data on rGDP" not in out

    def test_raw_yes_loads_raw(self, capsys):
        df = gmd(variables="rGDP", raw="yes", version="2025_12")
        out = capsys.readouterr().out
        assert isinstance(df, pd.DataFrame)
        assert "Loaded raw data on rGDP" in out

    def test_iso_no_does_not_alias_country_list(self, capsys):
        result = gmd(iso="no", version="2025_12")
        out = capsys.readouterr().out
        assert isinstance(result, pd.DataFrame)
        assert "Available countries:" not in out

    def test_raw_invalid_string_raises(self):
        with pytest.raises(GMDCommandError):
            gmd(variables="rGDP", raw="maybe", version="2025_12")

    def test_iso_invalid_string_raises(self):
        with pytest.raises(GMDCommandError):
            gmd(iso="maybe", version="2025_12")

    def test_fast_numeric_string_now_caches(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gmd_module, "_CACHE_DIR", tmp_path / "gmd_cache")
        gmd(version="2025_12", fast="1")
        assert (gmd_module._CACHE_DIR / "GMD_2025_12.dta").exists()

    def test_fast_no_does_not_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gmd_module, "_CACHE_DIR", tmp_path / "gmd_cache")
        gmd(version="2025_12", fast="no")
        assert not (gmd_module._CACHE_DIR / "GMD_2025_12.dta").exists()

    def test_fast_invalid_string_raises(self):
        with pytest.raises(GMDCommandError):
            gmd(version="2025_12", fast="sometimes")


class TestNormalizeSourceName:
    def test_cs_alias_rewrite(self):
        assert gmd_module._normalize_source_name("CS1_ARG") == "ARG_1"

    def test_cs_alias_preserves_case(self):
        assert gmd_module._normalize_source_name("CS1_arg") == "arg_1"

    def test_non_cs_passthrough(self):
        assert gmd_module._normalize_source_name("IMF_IFS") == "IMF_IFS"

    def test_short_cs_passthrough(self):
        assert gmd_module._normalize_source_name("CS1") == "CS1"

    def test_whitespace_stripped(self):
        assert gmd_module._normalize_source_name("  IMF_IFS  ") == "IMF_IFS"


class TestFormatBibtex:
    def test_splits_fields_onto_newlines(self):
        raw = '@misc{foo, author={A}, year={2025}}'
        result = gmd_module._format_bibtex_for_print(raw)
        assert "\n" in result
        assert "author=" in result

    def test_closing_brace_on_own_line(self):
        raw = '@misc{foo, title={T}}'
        result = gmd_module._format_bibtex_for_print(raw)
        assert result.strip().endswith("}")


class TestStripSourcePrefixCols:
    def test_strips_prefix(self):
        df = pd.DataFrame(columns=["ISO3", "year", "SRC_a", "SRC_b", "other"])
        result = gmd_module._strip_source_prefix_cols(df, "SRC")
        assert result == ["a", "b", "other"]

    def test_skips_id_cols(self):
        df = pd.DataFrame(columns=["ISO3", "year", "SRC_x"])
        result = gmd_module._strip_source_prefix_cols(df, "SRC")
        assert "ISO3" not in result
        assert "year" not in result


class TestSortVersionsDf:
    def test_sorts_descending(self):
        df = pd.DataFrame({"versions": ["2025_01", "2025_12", "2025_06"]})
        result = gmd_module._sort_versions_df(df)
        assert result["versions"].tolist() == ["2025_12", "2025_06", "2025_01"]


# ---------------------------------------------------------------------------
# Version functions
# ---------------------------------------------------------------------------

class TestVersions:
    def test_get_available_versions_returns_nonempty_list(self):
        versions = get_available_versions()
        assert isinstance(versions, list)
        assert len(versions) > 0

    def test_get_available_versions_contains_known_version(self):
        assert "2025_12" in get_available_versions()

    def test_get_current_version_is_first(self):
        assert get_current_version() == get_available_versions()[0]

    def test_version_list_output(self, capsys):
        result = gmd(version="list")
        out = capsys.readouterr().out
        assert result is None
        assert "2025_12" in out

    def test_version_list_is_sorted(self, capsys):
        gmd(version="list")
        out = capsys.readouterr().out
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        assert lines == sorted(lines)

    def test_version_current_prints_latest(self, capsys):
        gmd(version="current")
        out = capsys.readouterr().out
        assert f"Current version: {get_current_version()}" in out

    def test_invalid_version_raises(self, capsys):
        with pytest.raises(GMDCommandError) as exc:
            gmd(version="invalid_version")
        out = capsys.readouterr().out
        assert "Error: Version invalid_version does not exist" in out
        assert "Available versions:" in str(exc.value)

    def test_multi_token_version_returns_none(self, capsys):
        result = gmd(version="2025_12 current")
        out = capsys.readouterr().out
        assert result is None
        assert "Version must either be one specific version" in out

    def test_specific_version_loads_data(self):
        df = gmd(version="2025_12")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_listed_version_with_missing_file_gives_clear_error(self, capsys, monkeypatch):
        """A version listed in versions.csv whose .dta is unreachable must yield a
        clear 'data file ... could not be retrieved' message, not a bare
        'raise an issue' nor a raw RuntimeError."""
        original = gmd_module._read_dta_primary

        def _fake_read_dta_primary(path):
            if path.startswith("distribute/GMD_"):
                raise RuntimeError("404 Not Found")
            return original(path)

        monkeypatch.setattr(gmd_module, "_read_dta_primary", _fake_read_dta_primary)

        with pytest.raises(GMDCommandError) as exc:
            gmd(version="2025_12")
        out = capsys.readouterr().out
        assert "could not be retrieved" in out
        assert "2025_12" in out
        assert exc.value.code == 498

    def test_get_available_versions_offline_no_cache_raises_command_error(self, tmp_path, monkeypatch):
        """When the metadata cannot be loaded and no local fallback exists, the
        failure must surface as GMDCommandError, not a raw RuntimeError."""
        def _boom():
            raise RuntimeError("forced offline")

        monkeypatch.setattr(gmd_module, "_CACHE_DIR", tmp_path / "empty")
        monkeypatch.setattr(gmd_module, "_versions_df", _boom)
        monkeypatch.setattr(gmd_module, "_default_local_gmd_path", lambda: None)

        with pytest.raises(GMDCommandError):
            get_available_versions()


# ---------------------------------------------------------------------------
# Print / citation
# ---------------------------------------------------------------------------

class TestPrintOption:
    def test_print_gmd(self, capsys):
        result = gmd(print_option="GMD")
        out = capsys.readouterr().out
        assert result is None
        assert "Müller, K., Xu, C., Lehbib, M., & Chen, Z. (2025)." in out

    def test_print_stata(self, capsys):
        result = gmd(print_option="Stata")
        out = capsys.readouterr().out
        assert result is None
        assert "Lehbib, M. & Müller, K. (2025)." in out

    def test_print_keyword_alias(self, capsys):
        result = gmd(**{"print": "Stata"})
        out = capsys.readouterr().out
        assert result is None
        assert "Lehbib, M. & Müller, K. (2025)." in out

    def test_invalid_print_option_raises_198(self):
        with pytest.raises(GMDCommandError) as exc:
            gmd(print_option="bad")
        assert exc.value.code == 198

    def test_print_and_print_option_both_raises_type_error(self):
        with pytest.raises(TypeError, match="Specify either"):
            gmd(print_option="GMD", **{"print": "Stata"})

    def test_unexpected_kwarg_raises_type_error(self):
        with pytest.raises(TypeError, match="Unexpected keyword"):
            gmd(foo="bar")


# ---------------------------------------------------------------------------
# Citation
# ---------------------------------------------------------------------------

class TestCite:
    def test_cite_load_returns_dataframe(self):
        bib_df = gmd(cite="load")
        assert isinstance(bib_df, pd.DataFrame)
        assert "citation" in bib_df.columns
        assert "source_name" in bib_df.columns

    def test_cite_specific_key_prints_bibtex(self, capsys):
        result = gmd(cite="GMD")
        out = capsys.readouterr().out
        assert result is None
        assert "@techreport" in out

    def test_cite_nonexistent_source_raises(self, capsys):
        with pytest.raises(GMDCommandError):
            gmd(cite="NONEXISTENT_SOURCE_XYZ")
        out = capsys.readouterr().out
        assert "does not exist" in out

    def test_cite_multiple_tokens_raises(self):
        with pytest.raises(GMDCommandError, match="Only one citation"):
            gmd(cite="A B")


# ---------------------------------------------------------------------------
# Default load and variable filtering
# ---------------------------------------------------------------------------

class TestDefaultLoad:
    def test_default_returns_dataframe_with_id_cols(self, capsys):
        df = gmd()
        out = capsys.readouterr().out
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert {"countryname", "ISO3", "id", "year"}.issubset(df.columns)
        assert "Global Macro Database by Müller, Xu, Lehbib, and Chen (2025)" in out
        assert "Website: https://www.globalmacrodata.com" in out

    def test_summary_contains_citation_instructions(self, capsys):
        gmd(variables="rGDP", version="2025_12")
        out = capsys.readouterr().out
        assert "When using these data, please cite:" in out
        assert 'gmd(cite="GMD")' in out
        assert "When using the gmd command, please further cite:" in out

    def test_summary_contains_fast_hint_when_not_cached(self, capsys):
        gmd(variables="rGDP", version="2025_12")
        out = capsys.readouterr().out
        assert 'gmd(version="2025_12", fast="yes")' in out

    def test_variables_keep_order(self):
        df = gmd(variables=["rGDP", "infl"], version="2025_12")
        assert list(df.columns) == ["ISO3", "year", "id", "countryname", "rGDP", "infl"]

    def test_single_variable_string(self):
        df = gmd(variables="rGDP", version="2025_12")
        assert "rGDP" in df.columns

    def test_identifying_var_as_variable_keeps_unique_columns(self):
        df = gmd(variables=["year", "rGDP"], version="2025_12")
        assert isinstance(df, pd.DataFrame)
        assert df.columns.tolist().count("year") == 1
        assert "rGDP" in df.columns

    def test_identifying_var_alone_raises(self, capsys):
        with pytest.raises(GMDCommandError):
            gmd(variables="ISO3", version="2025_12")
        out = capsys.readouterr().out
        assert "identifying variable" in out

    def test_invalid_variable_raises(self):
        with pytest.raises(GMDCommandError):
            gmd(variables="INVALID", version="2025_12")

    def test_all_columns_dropped_if_all_nan(self):
        df = gmd(variables="rGDP", version="2025_12", country="USA")
        for col in df.columns:
            assert df[col].notna().any()


# ---------------------------------------------------------------------------
# Country filtering
# ---------------------------------------------------------------------------

class TestYearRange:
    def test_start_year_filters_lower_bound(self):
        full = gmd(variables="rGDP", country="USA", version="2025_12")
        df = gmd(variables="rGDP", country="USA", version="2025_12", start_year=2022)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert df["year"].min() >= 2022
        assert len(df) < len(full)  # filtering actually removed rows

    def test_end_year_filters_upper_bound(self):
        df = gmd(variables="rGDP", country="USA", version="2025_12", end_year=2022)
        assert isinstance(df, pd.DataFrame)
        assert df["year"].max() <= 2022

    def test_year_window(self):
        df = gmd(variables="rGDP", country="USA", version="2025_12",
                 start_year=2020, end_year=2025)
        assert df["year"].min() >= 2020
        assert df["year"].max() <= 2025

    def test_string_years_accepted(self):
        df = gmd(variables="rGDP", country="USA", version="2025_12",
                 start_year="2020", end_year="2025")
        assert df["year"].min() >= 2020
        assert df["year"].max() <= 2025

    def test_start_after_end_raises(self):
        with pytest.raises(GMDCommandError, match="cannot be greater"):
            gmd(variables="rGDP", version="2025_12", start_year=2020, end_year=2000)

    def test_invalid_year_raises(self):
        with pytest.raises(GMDCommandError, match="integer year"):
            gmd(variables="rGDP", version="2025_12", start_year="not_a_year")

    def test_unknown_kwarg_still_type_error(self):
        # start_year/end_year are now real params; genuinely-unknown kwargs must
        # still raise TypeError (locked behavior, not GMDCommandError).
        with pytest.raises(TypeError, match="Unexpected keyword"):
            gmd(variables="rGDP", version="2025_12", totally_unknown=1)


class TestCountryFilter:
    def test_single_country(self):
        df = gmd(version="2025_12", country="USA")
        assert set(df["ISO3"].unique()) == {"USA"}

    def test_multiple_countries(self):
        df = gmd(version="2025_12", country=["USA", "CHN"])
        assert set(df["ISO3"].unique()) == {"USA", "CHN"}

    def test_country_string_with_spaces(self):
        df = gmd(version="2025_12", country="USA CHN")
        assert set(df["ISO3"].unique()) == {"USA", "CHN"}

    def test_country_string_with_commas(self):
        df = gmd(version="2025_12", country="USA,CHN")
        assert set(df["ISO3"].unique()) == {"USA", "CHN"}

    def test_invalid_country_raises(self):
        with pytest.raises(GMDCommandError):
            gmd(country="INVALID", version="2025_12")

    def test_mixed_valid_invalid_returns_partial_in_exception(self):
        with pytest.raises(GMDCommandError) as exc:
            gmd(country=["USA", "INVALID"], version="2025_12")
        assert exc.value.code == 498
        assert isinstance(exc.value.data, pd.DataFrame)
        assert set(exc.value.data["ISO3"].unique()) == {"USA"}

    def test_country_load_returns_dataframe(self):
        cty_df = gmd(country="load")
        assert isinstance(cty_df, pd.DataFrame)
        assert "ISO3" in cty_df.columns
        assert "countryname" in cty_df.columns

    def test_country_list_always_prints_table(self, capsys):
        result = gmd(country="list")
        out = capsys.readouterr().out
        assert result is None
        assert "Available countries:" in out

    def test_iso_parameter_aliases_country_list(self, capsys):
        result = gmd(iso=True)
        out = capsys.readouterr().out
        assert result is None
        assert "Available countries:" in out

    def test_scalar_int_country_raises_command_error(self, capsys):
        with pytest.raises(GMDCommandError) as exc:
            gmd(country=840)
        assert "country must be a string or a list of strings" in str(exc.value)
        assert exc.value.code == 498

    def test_scalar_int_variables_raises_command_error(self):
        with pytest.raises(GMDCommandError):
            gmd(variables=1234, version="2025_12")

    def test_list_with_int_still_allowed(self):
        # Lists may contain non-strings (stringified by _tokens); only scalars are rejected.
        with pytest.raises(GMDCommandError, match="Invalid ISO3 code"):
            gmd(country=["USA", 840], version="2025_12")


# ---------------------------------------------------------------------------
# Variables listing
# ---------------------------------------------------------------------------

class TestVarsOption:
    def test_vars_load_returns_dataframe(self):
        var_df = gmd(vars="load")
        assert isinstance(var_df, pd.DataFrame)
        assert {"variables", "units", "definition"}.issubset(var_df.columns)

    def test_vars_list_prints_table(self, capsys):
        result = gmd(vars="list")
        out = capsys.readouterr().out
        assert result is None
        assert "Available variables:" in out
        assert "Definition" in out
        assert "nGDP" in out

    def test_vars_true_aliases_list(self, capsys):
        result = gmd(vars=True)
        out = capsys.readouterr().out
        assert result is None
        assert "Available variables:" in out

    def test_vars_false_is_noop(self, capsys):
        df = gmd(vars=False, version="2025_12")
        assert isinstance(df, pd.DataFrame)

    def test_list_variables_function(self, capsys):
        list_variables()
        out = capsys.readouterr().out
        assert "Available variables:" in out
        assert "nGDP" in out

    def test_list_countries_function(self, capsys):
        list_countries()
        out = capsys.readouterr().out
        assert "Available countries:" in out
        assert "ISO3 code" in out


# ---------------------------------------------------------------------------
# Raw data
# ---------------------------------------------------------------------------

class TestRaw:
    def test_raw_single_variable(self, capsys):
        df = gmd(variables="rGDP", raw=True, version="2025_12")
        out = capsys.readouterr().out
        assert isinstance(df, pd.DataFrame)
        assert "Loaded raw data on rGDP" in out
        assert "rGDP" in df.columns

    def test_raw_multiple_variables_raises(self):
        with pytest.raises(GMDCommandError):
            gmd(variables=["rGDP", "infl"], raw=True, version="2025_12")

    def test_raw_no_variable_raises(self):
        with pytest.raises(GMDCommandError):
            gmd(raw=True, version="2025_12")

    def test_raw_fallback_valid_variable_reports_no_raw_data(self, monkeypatch):
        """When raw CSV is missing but the variable exists in varlist, report 'no raw data'."""
        original_read_csv_primary = gmd_module._read_csv_primary

        def _fake_read_csv_primary(path, **kwargs):
            if path.startswith("distribute/"):
                raise RuntimeError("forced failure")
            return original_read_csv_primary(path, **kwargs)

        def _fake_varlist_df():
            return pd.DataFrame({
                "variables": ["rGDP", "infl"],
                "units": ["in LC", "in %"],
                "definition": ["Real GDP", "Inflation"],
            })

        monkeypatch.setattr(gmd_module, "_read_csv_primary", _fake_read_csv_primary)
        monkeypatch.setattr(gmd_module, "_varlist_df", _fake_varlist_df)

        with pytest.raises(GMDCommandError) as exc:
            gmd(variables="rGDP", raw=True, version="2025_12")
        assert str(exc.value) == "Variable does not have raw data."

    def test_raw_fallback_invalid_variable_reports_not_valid(self, monkeypatch):
        """When raw CSV is missing and the variable isn't in varlist, report 'not valid'."""
        original_read_csv_primary = gmd_module._read_csv_primary

        def _fake_read_csv_primary(path, **kwargs):
            if path.startswith("distribute/"):
                raise RuntimeError("forced failure")
            return original_read_csv_primary(path, **kwargs)

        def _fake_varlist_df():
            return pd.DataFrame({
                "variables": ["rGDP", "infl"],
                "units": ["in LC", "in %"],
                "definition": ["Real GDP", "Inflation"],
            })

        monkeypatch.setattr(gmd_module, "_read_csv_primary", _fake_read_csv_primary)
        monkeypatch.setattr(gmd_module, "_varlist_df", _fake_varlist_df)

        with pytest.raises(GMDCommandError) as exc:
            gmd(variables="FAKE_VAR", raw=True, version="2025_12")
        assert str(exc.value) == "Specified variable is not valid."


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

class TestSources:
    def test_sources_load(self, capsys):
        source_df = gmd(sources="load")
        out = capsys.readouterr().out
        assert isinstance(source_df, pd.DataFrame)
        assert "source_name" in source_df.columns
        assert "Imported the list of sources." in out

    def test_sources_list(self, capsys):
        result = gmd(sources="list")
        out = capsys.readouterr().out
        assert result is None
        assert "IMF_IFS" in out

    def test_sources_list_is_sorted(self, capsys):
        gmd(sources="list")
        out = capsys.readouterr().out
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        assert lines == sorted(lines)

    def test_sources_specific_query(self):
        df = gmd(sources="IMF_IFS", variables="rGDP", country="USA", version="2025_12")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "IMF_IFS_rGDP" in df.columns

    def test_sources_specific_without_variable_returns_full(self):
        df = gmd(sources="IMF_IFS", version="2025_12")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_sources_invalid_variable_exits_gracefully(self, capsys):
        result = gmd(sources="IMF_IFS", variables="NOT_A_VAR", version="2025_12")
        out = capsys.readouterr().out
        assert result is None
        assert "This source doesn't have data on NOT_A_VAR." in out

    def test_sources_invalid_country_returns_empty(self):
        df = gmd(sources="IMF_IFS", variables="rGDP", country="XXX", version="2025_12")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_sources_cs_alias(self):
        df = gmd(sources="CS1_ARG", version="2025_12")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_sources_invalid_name_raises(self, capsys):
        with pytest.raises(GMDCommandError):
            gmd(sources="TOTALLY_FAKE_SOURCE", version="2025_12")
        out = capsys.readouterr().out
        assert "Invalid source name" in out

    def test_sources_with_raw_prints_note(self, capsys):
        gmd(sources="load", raw=True)
        out = capsys.readouterr().out
        assert "raw option is specified" in out


# ---------------------------------------------------------------------------
# Caching (fast option)
# ---------------------------------------------------------------------------

class TestFastCaching:
    def test_fast_yes_saves_gmd_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gmd_module, "_CACHE_DIR", tmp_path / "gmd_cache")
        df = gmd(version="2025_12", fast="yes")
        assert isinstance(df, pd.DataFrame)
        assert (gmd_module._CACHE_DIR / "GMD_2025_12.dta").exists()
        assert (gmd_module._CACHE_DIR / "GMD.dta").exists()

    def test_fast_true_saves_gmd_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gmd_module, "_CACHE_DIR", tmp_path / "gmd_cache")
        df = gmd(version="2025_12", fast=True)
        assert isinstance(df, pd.DataFrame)
        assert (gmd_module._CACHE_DIR / "GMD_2025_12.dta").exists()

    def test_country_list_fast_yes_saves_and_prints(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(gmd_module, "_CACHE_DIR", tmp_path / "gmd_cache")
        result = gmd(country="list", fast="yes")
        out = capsys.readouterr().out
        assert result is None
        assert "Saving countrylist dataframe locally" in out
        assert "Available countries:" in out

    def test_cached_version_is_reused(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gmd_module, "_CACHE_DIR", tmp_path / "gmd_cache")
        gmd(version="2025_12", fast="yes")
        # Second load should use cached file
        df2 = gmd(version="2025_12")
        assert isinstance(df2, pd.DataFrame)
        assert len(df2) > 0


# ---------------------------------------------------------------------------
# Network option
# ---------------------------------------------------------------------------

class TestNetwork:
    def test_network_yes_loads_data(self):
        df = gmd(version="2025_12", network="yes")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


# ---------------------------------------------------------------------------
# Offline fallback
# ---------------------------------------------------------------------------

class TestOfflineFallback:
    @pytest.fixture()
    def go_offline(self, tmp_path, monkeypatch):
        """Populate a local cache then cut off network access."""
        monkeypatch.setattr(gmd_module, "_CACHE_DIR", tmp_path / "gmd_cache")
        gmd(version="2025_12", fast="yes")
        gmd_module._versions_df.cache_clear()

        def _fail_fetch(path):
            raise RuntimeError("no internet")

        # "No internet" must fail every fetch entrypoint. Data reads now route
        # through _fetch_first (primary S3 -> GitHub mirror fallback), so it has
        # to be cut off too, alongside the primary/secondary wrappers.
        monkeypatch.setattr(gmd_module, "_fetch_first", _fail_fetch)
        monkeypatch.setattr(gmd_module, "_fetch_primary", _fail_fetch)
        monkeypatch.setattr(gmd_module, "_fetch_secondary", _fail_fetch)

    def test_offline_no_cache_raises(self, monkeypatch):
        def _fail_fetch(path):
            raise RuntimeError("no internet")

        monkeypatch.setattr(gmd_module, "_fetch_first", _fail_fetch)
        monkeypatch.setattr(gmd_module, "_fetch_primary", _fail_fetch)
        monkeypatch.setattr(gmd_module, "_fetch_secondary", _fail_fetch)
        monkeypatch.setattr(gmd_module, "_default_local_gmd_path", lambda: None)
        gmd_module._versions_df.cache_clear()

        with pytest.raises(GMDCommandError, match="Local version not found"):
            gmd(version="2025_12")

    def test_offline_with_local_cache(self, go_offline, capsys):
        df = gmd()
        out = capsys.readouterr().out
        assert isinstance(df, pd.DataFrame)
        assert "Loading local version" in out

    def test_offline_blocks_raw(self, go_offline):
        with pytest.raises(GMDCommandError, match="internet"):
            gmd(variables="rGDP", raw=True)

    def test_offline_blocks_cite(self, go_offline):
        with pytest.raises(GMDCommandError, match="internet"):
            gmd(cite="load")

    def test_offline_blocks_sources(self, go_offline):
        with pytest.raises(GMDCommandError, match="internet"):
            gmd(sources="load")


# ---------------------------------------------------------------------------
# VALID_VARIABLES constant
# ---------------------------------------------------------------------------

class TestValidVariables:
    def test_contains_core_variables(self):
        for var in ("rGDP", "infl", "pop", "unemp", "CPI"):
            assert var in VALID_VARIABLES

    def test_contains_fiscal_variables(self):
        assert "cgovdebt" in VALID_VARIABLES
        assert "gen_govtax_GDP" in VALID_VARIABLES

    def test_contains_crisis_variables(self):
        for var in ("BankingCrisis", "SovDebtCrisis", "CurrencyCrisis"):
            assert var in VALID_VARIABLES


# ---------------------------------------------------------------------------
# GMDCommandError
# ---------------------------------------------------------------------------

class TestGMDCommandError:
    def test_default_code(self):
        err = GMDCommandError("test")
        assert err.code == 498
        assert str(err) == "test"
        assert err.data is None

    def test_custom_code_and_data(self):
        df = pd.DataFrame({"a": [1]})
        err = GMDCommandError("msg", code=111, data=df)
        assert err.code == 111
        assert err.data is df

    def test_is_runtime_error(self):
        assert issubclass(GMDCommandError, RuntimeError)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

class TestCacheHelpers:
    def test_cache_versions_empty_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gmd_module, "_CACHE_DIR", tmp_path / "nonexistent")
        assert gmd_module._cache_versions() == []

    def test_cache_versions_finds_files(self, tmp_path, monkeypatch):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "GMD_2025_12.dta").touch()
        (cache_dir / "GMD_2025_06.dta").touch()
        (cache_dir / "other.dta").touch()
        monkeypatch.setattr(gmd_module, "_CACHE_DIR", cache_dir)
        versions = gmd_module._cache_versions()
        assert "2025_12" in versions
        assert "2025_06" in versions
        assert versions[0] == "2025_12"  # sorted descending

    def test_default_local_gmd_path_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gmd_module, "_CACHE_DIR", tmp_path / "empty")
        assert gmd_module._default_local_gmd_path() is None


class TestAtomicToStata:
    def test_writes_file_and_leaves_no_tmp(self, tmp_path):
        df = pd.DataFrame({"ISO3": ["USA"], "year": [2000], "rGDP": [1.0]})
        target = tmp_path / "GMD.dta"
        gmd_module._atomic_to_stata(df, target)
        assert target.exists()
        assert not (tmp_path / "GMD.dta.tmp").exists()
        roundtrip = pd.read_stata(target, convert_categoricals=False)
        assert list(roundtrip["ISO3"]) == ["USA"]

    def test_failed_write_does_not_clobber_existing(self, tmp_path, monkeypatch):
        target = tmp_path / "GMD.dta"
        good = pd.DataFrame({"ISO3": ["USA"], "year": [2000], "rGDP": [1.0]})
        gmd_module._atomic_to_stata(good, target)
        original_bytes = target.read_bytes()

        class _Boom:
            def to_stata(self, *a, **k):
                raise ValueError("simulated write failure")

        with pytest.raises(ValueError):
            gmd_module._atomic_to_stata(_Boom(), target)
        # Existing cache file is untouched, no leftover tmp.
        assert target.read_bytes() == original_bytes
        assert not (tmp_path / "GMD.dta.tmp").exists()


class TestFetchRobustness:
    def test_sends_user_agent_and_returns(self, monkeypatch):
        seen = {}

        class _Resp:
            def raise_for_status(self):
                return None

        def _fake_get(url, timeout=None, headers=None):
            seen["headers"] = headers
            seen["url"] = url
            return _Resp()

        monkeypatch.setattr(gmd_module.requests, "get", _fake_get)
        resp = gmd_module._fetch_from("helpers/versions.csv", ("https://example.test",))
        assert resp is not None
        assert "User-Agent" in seen["headers"]
        assert "global-macro-data" in seen["headers"]["User-Agent"]

    def test_retries_transient_then_succeeds(self, monkeypatch):
        calls = {"n": 0}

        class _Resp:
            def raise_for_status(self):
                return None

        def _flaky_get(url, timeout=None, headers=None):
            calls["n"] += 1
            if calls["n"] < 2:
                raise gmd_module.requests.ConnectionError("transient")
            return _Resp()

        monkeypatch.setattr(gmd_module.requests, "get", _flaky_get)
        monkeypatch.setattr(gmd_module.time, "sleep", lambda *_: None)
        resp = gmd_module._fetch_from("helpers/versions.csv", ("https://example.test",))
        assert resp is not None
        assert calls["n"] == 2

    def test_does_not_retry_on_404(self, monkeypatch):
        calls = {"n": 0}

        def _not_found_get(url, timeout=None, headers=None):
            calls["n"] += 1
            err = gmd_module.requests.HTTPError("404")
            err.response = type("R", (), {"status_code": 404})()
            raise err

        monkeypatch.setattr(gmd_module.requests, "get", _not_found_get)
        slept = {"n": 0}
        monkeypatch.setattr(gmd_module.time, "sleep", lambda *_: slept.__setitem__("n", slept["n"] + 1))
        with pytest.raises(RuntimeError, match="Unable to load"):
            gmd_module._fetch_from("distribute/GMD_2025_01.dta", ("https://example.test",))
        assert calls["n"] == 1  # no retries on a 4xx
        assert slept["n"] == 0
