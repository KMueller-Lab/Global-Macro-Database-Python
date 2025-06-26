import pytest
import pandas as pd
import global_macro_data as gmd
from global_macro_data.exceptions import (
    InvalidVersionError,
    InvalidCountryError,
    InvalidVariableError,
    RawModeError,
)


def test_get_available_versions():
    """Test getting available versions"""
    versions = gmd.list_versions()
    assert isinstance(versions, list)
    assert len(versions) > 0
    assert all(isinstance(v, str) for v in versions)
    assert all(len(v.split('_')) == 2 for v in versions)


def test_get_current_version():
    """Test getting current version"""
    version = gmd.get_current_version()
    assert isinstance(version, str)
    assert len(version.split('_')) == 2


def test_list_variables():
    df = gmd.list_variables()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    for var in gmd.VALID_VARIABLES:
        assert var in df['Variable'].values


def test_list_countries():
    df = gmd.list_countries()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_gmd_default():
    """Test default gmd call"""
    df = gmd.get_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert all(col in df.columns for col in ["ISO3", "countryname", "year"])


def test_gmd_version():
    """Test gmd with specific version"""
    version = gmd.get_current_version()
    df = gmd.get_data(version=version)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


def test_gmd_country():
    """Test gmd with specific country"""
    df = gmd.get_data(country="USA")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert all(df["ISO3"] == "USA")


def test_gmd_countries():
    """Test gmd with multiple countries"""
    df = gmd.get_data(country=["USA", "CHN"])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert set(df["ISO3"].unique()) == {"USA", "CHN"}


def test_gmd_variables():
    """Test gmd with specific variables"""
    df = gmd.get_data(variables=["rGDP", "infl"])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert all(col in df.columns for col in ["rGDP", "infl"])


def test_gmd_raw():
    """Test gmd with raw data option"""
    df = gmd.get_data(variables="rGDP", raw=True)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "rGDP" in df.columns


def test_gmd_combinations():
    """Test gmd with multiple parameters"""
    df = gmd.get_data(
        version=gmd.get_current_version(),
        country=["USA", "CHN"],
        variables=["rGDP", "infl"]
    )
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert set(df["ISO3"].unique()) == {"USA", "CHN"}
    assert all(col in df.columns for col in ["rGDP", "infl"])


def test_gmd_invalid_version():
    """Test gmd with invalid version"""
    with pytest.raises(InvalidVersionError):
        gmd.get_data(version="invalid_version")


def test_gmd_invalid_country():
    """Test gmd with invalid country"""
    with pytest.raises(InvalidCountryError):
        gmd.get_data(country="INVALID")


def test_gmd_invalid_variable():
    """Test gmd with invalid variable"""
    with pytest.raises(InvalidVariableError):
        gmd.get_data(variables="INVALID")


def test_gmd_raw_multiple_variables():
    """Test gmd raw option with multiple variables"""
    with pytest.raises(RawModeError):
        gmd.get_data(variables=["rGDP", "infl"], raw=True)


def test_gmd_raw_no_variable():
    """Test gmd raw option without variable"""
    with pytest.raises(RawModeError):
        gmd.get_data(raw=True)
