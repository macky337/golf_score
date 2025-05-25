from setuptools import setup, find_packages

setup(
    name="streamlit_extras",
    version="0.1.0",
    packages=find_packages(include=["streamlit_extras", "streamlit_extras.*"]),
    author="Local Override",
    description="Local implementation of streamlit_extras utilities",
)
