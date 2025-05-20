import streamlit as st
import pandas as pd
import numpy as np
from geopy.distance import geodesic
import pydeck as pdk
import os

# Protection par mot de passe
def check_password():
    def password_entered():
        if st.session_state["password"] == os.getenv("APP_PASSWORD"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Mot de passe", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Mot de passe", type="password", on_change=password_entered, key="password")
        st.error("Mot de passe incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# Titre personnalisé
st.markdown("""
<h1 style='color:#c82832;'>MAP MRKTG POLE PERF NXT</h1>
""", unsafe_allow_html=True)

# Chargement des données via Google Drive
@st.cache_data
def load_data():
    url = "https://drive.google.com/uc?export=download&id=1fykKU-wX6fNlq79qfdCya0JhV0wbblRs"
    df = pd.read_csv(url, dtype=str)
    # Conversion latitude et longitude en float pour traitement géographique
    df["Latitude"] = df["Latitude"].astype(float)
    df["Longitude"] = df["Longitude"].astype(float)
    return df

communes = load_data()

# Saisie utilisateur
ville_input = st.text_input("Entrez le nom de la ville ou son code postal :", "Aubervilliers")
rayon = st.slider("Rayon de recherche (km) :", 1, 50, 10)

# Recherche ville de référence
ville_ref = communes[
    (communes['Nom'].str.lower() == ville_input.lower()) | (communes['CP'] == ville_input)
]

if ville_ref.empty:
    st.warning("Ville non trouvée. Veuillez vérifier le nom ou le code postal.")
else:
    ref = ville_ref.iloc[0]
    ref_coords = (ref['Latitude'], ref['Longitude'])

    # Calcul des distances
    def calc_distance(row):
        return geodesic(ref_coords, (row['Latitude'], row['Longitude'])).km

    communes['distance_km'] = communes.apply(calc_distance, axis=1)
    communes_filtrees = communes[(communes['distance_km'] <= rayon) & (communes['Nom'] != ref['Nom'])]
    communes_filtrees = communes_filtrees.sort_values("distance_km")

    # Affichage du tableau
    st.subheader(f"Communes dans un rayon de {rayon} km autour de {ref['Nom']} ({ref['CP']})")
    st.dataframe(communes_filtrees[['Nom', 'CP', 'distance_km']])

    # Export CSV
    csv = communes_filtrees[['Nom', 'CP', 'distance_km']].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger les résultats en CSV",
        data=csv,
        file_name='communes_proches.csv',
        mime='text/csv')

    # Affichage carte
    st.subheader("Carte interactive des communes")

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=communes_filtrees,
        get_position='[Longitude, Latitude]',
        get_radius=2000,
        get_fill_color='[0, 100, 200, 160]',
        pickable=True,
    )

    center = {'latitude': ref['Latitude'], 'longitude': ref['Longitude']}
    view_state = pdk.ViewState(
        latitude=center['latitude'],
        longitude=center['longitude'],
        zoom=10,
        pitch=0
    )

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{Nom} ({CP})"}
    ))
