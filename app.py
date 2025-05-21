!pip install geopy requests

import pandas as pd
import streamlit as st
from geopy.distance import geodesic
import requests
import os

# Fonction de chargement des données depuis l'API
@st.cache_data
def load_communes():
    url = "https://geo.api.gouv.fr/communes?fields=nom,code,codesPostaux,centre&format=json&geometry=centre"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    rows = []
    for commune in data:
        nom = commune['nom']
        codes_postaux = commune['codesPostaux']
        centre = commune['centre']
        latitude = centre['coordinates'][1]
        longitude = centre['coordinates'][0]

        for code_postal in codes_postaux:
            rows.append({
                'nom': nom,
                'code_postal': code_postal,
                'latitude': latitude,
                'longitude': longitude
            })

    return pd.DataFrame(rows)

# Interface utilisateur
st.title("🗺️ Carte des communes à proximité")

# Saisie utilisateur
ville_input = st.text_input("Entrez le nom de la ville ou son code postal :", "Aubervilliers")
rayon = st.slider("Rayon de recherche (km) :", 1, 50, 10)

# Chargement des données
try:
    communes = load_communes()
except Exception as e:
    st.error(f"Erreur lors du chargement des données : {e}")
    st.stop()

# Recherche de la ville de référence
ville_ref = communes[
    (communes["nom"].str.lower() == ville_input.lower()) |
    (communes["code_postal"] == ville_input)
]

if ville_ref.empty:
    st.warning("Ville non trouvée. Veuillez vérifier le nom ou le code postal.")
    st.stop()

ref = ville_ref.iloc[0]
ref_coords = (ref["latitude"], ref["longitude"])

# Calcul des distances
def calc_distance(row):
    return geodesic(ref_coords, (row["latitude"], row["longitude"])).km

communes["distance_km"] = communes.apply(calc_distance, axis=1)
communes_filtrees = communes[
    (communes["distance_km"] <= rayon) &
    (communes["nom"] != ref["nom"])
].sort_values("distance_km")

# Affichage tableau
st.subheader(f"Communes dans un rayon de {rayon} km autour de {ref['nom']} ({ref['code_postal']}) :")
st.dataframe(communes_filtrees[["nom", "code_postal", "distance_km"]])

# 📥 Export CSV personnalisé avec codes postaux uniquement
codes_postaux = communes_filtrees["code_postal"].dropna().astype(str).unique()
csv_codes = ", ".join(codes_postaux)
csv_bytes = csv_codes.encode("utf-8")

# 🏷️ Nom dynamique du fichier
nom_fichier_ville = ref["nom"].replace(" ", "_").replace("-", "_")
fichier_csv = f"{nom_fichier_ville}_code_postal.csv"

st.download_button(
    label="📥 Télécharger les codes postaux",
    data=csv_bytes,
    file_name=fichier_csv,
    mime="text/csv"
)
