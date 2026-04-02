"""Quick local smoke test for the global-macro-data package."""

from global_macro_data import gmd, get_available_versions, get_current_version


def main() -> None:
    print("=== Version Info ===")
    print("Current version:", get_current_version())
    print("Available versions:", get_available_versions())

    print("\n=== Load full dataset ===")
    df = gmd()
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns[:10])}...")

    print("\n=== Filter by country and variables ===")
    subset = gmd(variables=["rGDP", "infl"], country="USA")
    print(subset.head(10))

    print("\n=== Variable list ===")
    varlist = gmd(vars="load")
    print(f"{len(varlist)} variables available")

    print("\n=== Country list ===")
    countries = gmd(country="load")
    print(f"{len(countries)} countries available")

    print("\n=== Raw data ===")
    raw = gmd(variables="rGDP", raw=True)
    print(f"Raw rGDP shape: {raw.shape}")

    print("\n=== Sources ===")
    sources = gmd(sources="load")
    print(f"{len(sources)} sources available")

    print("\n=== Citation ===")
    gmd(cite="GMD")

    print("\nAll checks passed!")


if __name__ == "__main__":
    main()
