from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="techcare-bot",
    version="0.1.0",
    description="IT-Wartungs-Assistent für Windows/macOS Systeme",
    author="TechCare Team",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "techcare=techcare.__main__:main",
        ],
    },
    python_requires=">=3.9",
)
