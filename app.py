
import streamlit as st
import pandas as pd
import numpy as np
from geopy.distance import geodesic
import pydeck as pdk

# Titre personnalisé
st.markdown("""
<h1 style='color:#c82832;'>MAP MRKTG POLE PERF NXT</h1>
""", unsafe_allow_html=True)

# Chargement des données (à remplacer par la base complète communes.csv)
@st.cache_data
def load_data():
    df = pd.read_csv("communes.csv")  # Fichier avec colonnes: nom, code_postal, latitude, longitude
    return df

communes = load_data()

# Saisie utilisateur
ville_input = st.text_input("Entrez le nom de la ville ou son code postal :", "Aubervilliers")
rayon = st.slider("Rayon de recherche (km) :", 1, 50, 10)

# Recherche ville de référence
ville_ref = communes[
    (communes['nom'].str.lower() == ville_input.lower()) | (communes['code_postal'] == ville_input)
]

if ville_ref.empty:
    st.warning("Ville non trouvée. Veuillez vérifier le nom ou le code postal.")
else:
    ref = ville_ref.iloc[0]
    ref_coords = (ref['latitude'], ref['longitude'])

    # Calcul des distances
    def calc_distance(row):
        return geodesic(ref_coords, (row['latitude'], row['longitude'])).km

    communes['distance_km'] = communes.apply(calc_distance, axis=1)
    communes_filtrees = communes[(communes['distance_km'] <= rayon) & (communes['nom'] != ref['nom'])]
    communes_filtrees = communes_filtrees.sort_values("distance_km")

    # Affichage du tableau
    st.subheader("Communes dans un rayon de {} km autour de {} ({}):".format(
        rayon, ref['nom'], ref['code_postal']))
    st.dataframe(communes_filtrees[['nom', 'code_postal', 'distance_km']])

    # Export CSV
    csv = communes_filtrees[['nom', 'code_postal', 'distance_km']].to_csv(index=False).encode('utf-8')
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
        get_position='[longitude, latitude]',
        get_radius=2000,
        get_fill_color='[0, 100, 200, 160]',
        pickable=True,
    )

    center = {'latitude': ref['latitude'], 'longitude': ref['longitude']}
    view_state = pdk.ViewState(
        latitude=center['latitude'],
        longitude=center['longitude'],
        zoom=10,
        pitch=0
    )

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{nom} ({code_postal})"}
    ))
