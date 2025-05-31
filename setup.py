from setuptools import setup, find_packages

setup(
    name="streamlit_extras",
    version="0.7.1",
    packages=find_packages(),
)

from setuptools import setup, find_packages

setup(
    name="golf_score",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'streamlit',
        'pandas',
        'supabase',
        'python-dotenv',
        'reportlab',
        'streamlit-extras'
    ],
)