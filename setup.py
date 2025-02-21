"""Setup file for the Magnetic package."""

from setuptools import setup, find_packages

setup(
    name="magnetic",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "autogen-agentchat",
        "autogen-ext[magentic-one,openai]",
        "python-dotenv",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "black",
            "pylint",
            "mypy",
        ],
    },
    python_requires=">=3.9",
) 