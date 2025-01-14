#!/bin/bash

# Création de l'environnement virtuel
python -m venv venv

# Activation de l'environnement virtuel
source venv/bin/activate  # Pour Linux/Mac
# ou
# .\venv\Scripts\activate  # Pour Windows

# Installation des dépendances
pip install -r requirements.txt 