from setuptools import setup, find_packages

setup(
    name='unipal',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'streamlit',
        'langchain',
        'pydantic',
        'python-dotenv',
        'serpapi',
        'langgraph'
    ],
)
