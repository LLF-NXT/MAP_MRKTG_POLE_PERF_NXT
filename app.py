import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import pydeck as pdk
import os

# ---------------------
# Protection par mot de passe
# ---------------------
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

# ---------------------
# Titre personnalisé
# ---------------------
st.markdown("""
<h1 style='color:#c82832;'>MAP MRKTG POLE PERF NXT</h1>
""", unsafe_allow_html=True)

# ---------------------
# Chargement des données
# ---------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("communes.csv", dtype=str)
        df["latitude"] = df["latitude"].astype(float)
        df["longitude"] = df["longitude"].astype(float)
        return df
    except Exception as e:
        st.error("Erreur lors du chargement du fichier CSV : " + str(e))
        return pd.DataFrame(columns=["nom", "code_postal", "latitude", "longitude"])

communes = load_data()

# ---------------------
# Saisie utilisateur
# ---------------------
ville_input = st.text_input("Entrez le nom de la ville ou son code postal :", "Aubervilliers").strip()
rayon = st.slider("Rayon de recherche (km) :", 1, 50, 10)

# ---------------------
# Recherche ville de référence
# ---------------------
ville_ref = communes[
    (communes['nom'].str.strip().str.lower() == ville_input.lower()) |
    (communes['code_postal'].str.strip() == ville_input)
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
    communes_filtrees = communes[
        (communes['distance_km'] <= rayon) & (communes['nom'] != ref['nom'])
    ].sort_values("distance_km")

    # ---------------------
    # Affichage tableau
    # ---------------------
    st.subheader(f"Communes dans un rayon de {rayon} km autour de {ref['nom']} ({ref['code_postal']}):")
    st.dataframe(communes_filtrees[['nom', 'code_postal', 'distance_km']])

    # ---------------------
    # Export CSV
    # ---------------------
    csv = communes_filtrees[['nom', 'code_postal', 'distance_km']].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger les résultats en CSV",
        data=csv,
        file_name='communes_proches.csv',
        mime='text/csv'
    )

    # ---------------------
    # Carte interactive
    # ---------------------
    st.subheader("Carte interactive des communes")

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=communes_filtrees,
        get_position='[longitude, latitude]',
        get_radius=2000,
        get_fill_color='[0, 100, 200, 160]',
        pickable=True,
    )

    # Point de référence (ville saisie)
    ref_layer = pdk.Layer(
        "ScatterplotLayer",
        data=pd.DataFrame([ref]),
        get_position='[longitude, latitude]',
        get_radius=3000,
        get_fill_color='[200, 30, 0, 160]',
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=ref['latitude'],
        longitude=ref['longitude'],
        zoom=10,
        pitch=0
    )

    st.pydeck_chart(pdk.Deck(
        layers=[layer, ref_layer],
        initial_view_state=view_state,
        tooltip={"text": "{nom} ({code_postal})"}
    ))
