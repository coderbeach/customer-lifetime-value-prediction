from setuptools import setup, find_packages

setup(
    name="cltv_prediction",
    version="1.0.0",
    description="End-to-end Customer Lifetime Value (CLTV) Prediction and Segmentation System.",
    author="Nisarga N",
    author_email="nissymessy14@gmail.com",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "xgboost>=1.7.0",
        "lightgbm>=3.3.0",
        "shap>=0.42.0",
    ],
    python_requires=">=3.10",
)
