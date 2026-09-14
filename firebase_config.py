import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("firebase-key.json")

firebase_admin.initialize_app(
    cred,
    {
        "databaseURL": "https://smartbin-cd872-default-rtdb.firebaseio.com"
    }
)

print("Firebase connected successfully!")