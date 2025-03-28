from setuptools import setup, find_packages

setup(
    name="company_officers_from_web",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-dotenv==1.0.0",
        "psycopg2==2.9.9",
        "openai==1.3.5",
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "python-dateutil==2.8.2",
    ],
) 