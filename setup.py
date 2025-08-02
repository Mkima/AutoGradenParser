from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="garden-irrigation-analyzer",
    version="1.0.0",
    author="Garden Analysis Team",
    author_email="mkima@gmail.com",
    description="A comprehensive system for analyzing garden sensor data and providing irrigation recommendations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/garden-irrigation-analyzer",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Agriculture",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "matplotlib>=3.3.0",
        "seaborn>=0.11.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "test": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "garden-analyzer=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["data/*.json", "data/*.log"],
    },
    zip_safe=False,
    keywords="agriculture irrigation sensors garden analysis monitoring",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/garden-irrigation-analyzer/issues",
        "Source": "https://github.com/yourusername/garden-irrigation-analyzer",
        "Documentation": "https://github.com/yourusername/garden-irrigation-analyzer/wiki",
    },
)