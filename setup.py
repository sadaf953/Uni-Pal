from setuptools import setup, find_packages

setup(
    name="unipal",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'python-dotenv',
        'requests',
        'beautifulsoup4',
        'google-generativeai==0.3.1',
        'langchain-google-genai==0.0.5',
        'streamlit',
        'tavily-python'
    ]
)
