import pandas as pd
from sklearn.ensemble import RandomForestRegressor

# Read the SmartBin data
data = pd.read_csv("data.csv")

# Create a time-based feature
data["time_number"] = range(len(data))

bins = ["bin1", "bin2", "bin3"]

print("\n===== SMARTBIN AI PREDICTION =====\n")

for bin_name in bins:

    # Input and output
    X = data[["time_number"]]
    y = data[bin_name]

    # Create Random Forest model
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )

    # Train the model
    model.fit(X, y)

    # Predict next reading
    next_time = pd.DataFrame({
        "time_number": [len(data)]
    })

    prediction = model.predict(next_time)[0]

    # Keep prediction between 0 and 100
    prediction = max(0, min(100, prediction))

    print(
        f"{bin_name.upper()} "
        f"current level: {data[bin_name].iloc[-1]}%"
    )

    print(
        f"{bin_name.upper()} "
        f"predicted level: {prediction:.1f}%"
    )

    # Collection decision
    if prediction >= 90:
        print("Status: 🔴 Collection Required")

    elif prediction >= 70:
        print("Status: 🟡 Collection Soon")

    else:
        print("Status: 🟢 Normal")

    print()

print("==================================")