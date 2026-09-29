from pathlib import Path

from setuptools import find_packages, setup

README = Path("README.md")
long_description = README.read_text(encoding="utf-8") if README.exists() else "Global Macro Data package"

setup(
    name="global-macro-data",
    version="2.0.0",
    packages=find_packages(),
    package_data={},
    install_requires=["requests>=2.20.0", "pandas>=1.3.0"],
    author="Karsten Mueller, Chenzi Xu, Mohamed Lehbib, Ziliang Chen",
    author_email="kmueller@nus.edu.sg",
    license="MIT",
    description=(
        "Global Macro Database by Karsten Mueller, Chenzi Xu, "
        "Mohamed Lehbib and Ziliang Chen (2025)"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KMueller-Lab/Global-Macro-Database-Python",
    project_urls={
        "Source": "https://github.com/KMueller-Lab/Global-Macro-Database-Python",
        "Issues": "https://github.com/KMueller-Lab/Global-Macro-Database/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
