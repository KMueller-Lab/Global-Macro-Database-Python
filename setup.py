import os

def read_readme():
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    return "Global Macro Data package"

from setuptools import setup, find_packages

setup(
    name="global_macro_data",
    version="0.3.1",
    packages=find_packages(),
    package_data={
        "global_macro_data": ["isomapping.csv"],
    },
    install_requires=[
        "requests",
        "pandas"
    ],
    author="Yangbo Wang",
    author_email="wangyangbo@ruc.edu.cn",
    description="Global Macro Database by Karsten Müller, Chenzi Xu, Mohamed Lehbib and Ziliang Chen (2025)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/KMueller-Lab/Global-Macro-Database-Python",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
