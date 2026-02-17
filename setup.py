from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="techcare-bot",
    version="0.2.0",
    description="AI-powered IT-Wartungs-Assistent für Windows/macOS Systeme",
    author="Carsten Eckhardt / Eckhardt-Marketing",
    author_email="info@eckhardt-marketing.de",
    url="https://github.com/carsten-eckhardt/techcare-bot",
    license="MIT",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "techcare=techcare.__main__:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
