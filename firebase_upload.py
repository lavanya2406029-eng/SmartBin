import pandas as pd
import firebase_admin
from firebase_admin import credentials, db

# Connect to Firebase
cred = credentials.Certificate("firebase-key.json")

firebase_admin.initialize_app(
    cred,
    {
        "databaseURL": "https://smartbin-cd872-default-rtdb.firebaseio.com"
    }
)

# Read latest data
data = pd.read_csv("data.csv")
latest = data.iloc[-1]

# Send latest bin data to Firebase
firebase_data = {
    "time": latest["time"],
    "bin1": int(latest["bin1"]),
    "bin2": int(latest["bin2"]),
    "bin3": int(latest["bin3"])
}

db.reference("smartbin").set(firebase_data)

print("Data uploaded to Firebase successfully!")
print(firebase_data)