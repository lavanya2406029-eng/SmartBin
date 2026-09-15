import firebase_admin
import streamlit as st
from firebase_admin import credentials, db

if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])

    cred = credentials.Certificate(firebase_config)

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://smartbin-cd872-default-rtdb.firebaseio.com"
        }
    )

print("Firebase connected successfully!")
