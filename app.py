import streamlit as st
import requests
from geopy.distance import geodesic
import pandas as pd
import pydeck as pdk

# Titre
st.markdown("<h1 style='color:#c82832;'>MAP MRKTG POLE PERF NXT</h1>", unsafe_allow_html=True)

# Fonction pour obtenir les coordonnées d’une ville
def get_commune_info(ville_input):
    url = f"https://geo.api.gouv.fr/communes?nom={ville_input}&fields=nom,code,codePostal,centre&format=json&geometry=centre"
    r = requests.get(url)
    data = r.json()
    if not data:
        return None
    commune = data[0]
    return {
        "nom": commune["nom"],
        "code_postal": commune.get("codePostal", ""),
        "latitude": commune["centre"]["coordinates"][1],
        "longitude": commune["centre"]["coordinates"][0]
    }

# Fonction pour obtenir toutes les communes de France (coordonnées)
@st.cache_data
def get_all_communes():
    url = "https://geo.api.gouv.fr/communes?fields=nom,code,codePostal,centre&format=json&geometry=centre"
    r = requests.get(url)
    data = r.json()
    cleaned = []
    for c in data:
        try:
            lat = c["centre"]["coordinates"][1]
            lon = c["centre"]["coordinates"][0]
            cleaned.append({
                "nom": c["nom"],
                "code_postal": c.get("codePostal", ""),
                "latitude": lat,
                "longitude": lon
            })
        except:
            continue
    return pd.DataFrame(cleaned)

# Interface
ville_input = st.text_input("Entrez le nom de la ville ou son code postal :", "Aubervilliers")
rayon = st.slider("Rayon de recherche (km) :", 1, 50, 10)

# Recherche
if ville_input:
    ref = get_commune_info(ville_input)

    if not ref:
        st.warning("Ville non trouvée via l'API. Vérifiez l'orthographe.")
        st.stop()

    ref_coords = (ref['latitude'], ref['longitude'])
    df = get_all_communes()

    # Calcul des distances
    def calc_distance(row):
        return geodesic(ref_coords, (row["latitude"], row["longitude"])).km

    df["distance_km"] = df.apply(calc_distance, axis=1)
    communes_filtrees = df[(df["distance_km"] <= rayon) & (df["nom"] != ref["nom"])]
    communes_filtrees = communes_filtrees.sort_values("distance_km")

    # Résultat
    st.subheader(f"Communes dans un rayon de {rayon} km autour de {ref['nom']} ({ref['code_postal']})")
    st.dataframe(communes_filtrees[["nom", "code_postal", "distance_km"]])

    # Export CSV
    csv = communes_filtrees[["nom", "code_postal", "distance_km"]].to_csv(index=False).encode("utf-8")
    st.download_button("📥 Télécharger en CSV", data=csv, file_name="communes_proches.csv", mime="text/csv")

    # Carte
    st.subheader("Carte interactive")
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=communes_filtrees,
        get_position='[longitude, latitude]',
        get_radius=2000,
        get_fill_color='[0, 100, 200, 160]',
        pickable=True,
    )
    view_state = pdk.ViewState(
        latitude=ref["latitude"],
        longitude=ref["longitude"],
        zoom=9,
        pitch=0
    )
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{nom} ({code_postal})"}
    ))
