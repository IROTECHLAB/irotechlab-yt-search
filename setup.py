"""Setup configuration for irotechlab-yt-search"""

from setuptools import setup, find_packages

setup(
    name="irotechlab-yt-search",
    version="0.1.0",
    author="IrotechLab",
    description="YouTube search without official API - fast, reliable, and free",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/irotechlab/irotechlab-yt-search",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        "aiohttp>=3.8.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "sphinx>=5.0.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/irotechlab/irotechlab-yt-search/issues",
        "Source": "https://github.com/irotechlab/irotechlab-yt-search",
        "Documentation": "https://github.com/irotechlab/irotechlab-yt-search#readme",
    },
    keywords="youtube search video scraper innertube api",
    license="MIT",
    include_package_data=True,
    zip_safe=False,
)