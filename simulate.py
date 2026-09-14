import time
import random
import firebase_admin
from firebase_admin import credentials, db


# --------------------------------------------------
# FIREBASE CONNECTION
# --------------------------------------------------

if not firebase_admin._apps:

    cred = credentials.Certificate(
        "firebase-key.json"
    )

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL":
            "https://smartbin-cd872-default-rtdb.firebaseio.com"
        }
    )


# --------------------------------------------------
# INITIAL VALUES
# --------------------------------------------------

bin2 = 40
bin3 = 60

simulated_time = "04:00"


# --------------------------------------------------
# SIMULATION
# --------------------------------------------------

while True:

    # ----------------------------------------------
    # Increase BIN2 and BIN3
    # ----------------------------------------------

    bin2 += random.randint(1, 3)
    bin3 += random.randint(1, 3)


    # ----------------------------------------------
    # Reset after collection
    # ----------------------------------------------

    if bin2 >= 100:

        bin2 = 10

        print("🗑️ BIN2 reached 100% → Collected → Reset to 10%")


    if bin3 >= 100:

        bin3 = 10

        print("🗑️ BIN3 reached 100% → Collected → Reset to 10%")


    # ----------------------------------------------
    # Get current BIN1 from Firebase
    # ----------------------------------------------

    latest = db.reference(
        "smartbin/latest"
    ).get()


    if latest:

        bin1 = latest.get(
            "bin1",
            30
        )

    else:

        bin1 = 30


    # ----------------------------------------------
    # Update latest data
    # ----------------------------------------------

    latest_data = {

        "time":
            simulated_time,

        "bin1":
            bin1,

        "bin2":
            bin2,

        "bin3":
            bin3
    }


    db.reference(
        "smartbin/latest"
    ).set(
        latest_data
    )


    # ----------------------------------------------
    # Store historical reading
    # ----------------------------------------------

    db.reference(
        "smartbin/readings"
    ).push(
        latest_data
    )


    # ----------------------------------------------
    # Display
    # ----------------------------------------------

    print(
        f"Time: {simulated_time} | "
        f"BIN1: {bin1:.0f}% | "
        f"BIN2: {bin2}% | "
        f"BIN3: {bin3}%"
    )


    # ----------------------------------------------
    # Advance simulated time by 5 minutes
    # ----------------------------------------------

    hour, minute = map(
        int,
        simulated_time.split(":")
    )


    minute += 5


    if minute >= 60:

        minute -= 60
        hour += 1


    if hour >= 24:

        hour = 0


    simulated_time = (
        f"{hour:02d}:{minute:02d}"
    )


    # ----------------------------------------------
    # Wait 5 seconds
    # ----------------------------------------------

    time.sleep(5)