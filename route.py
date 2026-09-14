import math

# --------------------------------
# SmartBin Locations
# --------------------------------

locations = {
    "Collection Center": (0, 0),
    "BIN1": (2, 3),
    "BIN2": (5, 2),
    "BIN3": (1, 6)
}

# Current fill levels
fill_levels = {
    "BIN1": 74,
    "BIN2": 88,
    "BIN3": 67
}

# Collection threshold
COLLECTION_THRESHOLD = 70


# --------------------------------
# Calculate Distance
# --------------------------------

def distance(point1, point2):

    x1, y1 = point1
    x2, y2 = point2

    return math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )


# --------------------------------
# Select Bins for Collection
# --------------------------------

bins_to_collect = []

for bin_name in ["BIN1", "BIN2", "BIN3"]:

    if fill_levels[bin_name] >= COLLECTION_THRESHOLD:
        bins_to_collect.append(bin_name)


# --------------------------------
# Nearest Neighbor Route
# --------------------------------

current_location = "Collection Center"

route = ["Collection Center"]

total_distance = 0

remaining_bins = bins_to_collect.copy()


while remaining_bins:

    nearest_bin = min(
        remaining_bins,
        key=lambda bin_name:
        distance(
            locations[current_location],
            locations[bin_name]
        )
    )

    travel_distance = distance(
        locations[current_location],
        locations[nearest_bin]
    )

    total_distance += travel_distance

    route.append(nearest_bin)

    current_location = nearest_bin

    remaining_bins.remove(nearest_bin)


# Return to Collection Center
return_distance = distance(
    locations[current_location],
    locations["Collection Center"]
)

total_distance += return_distance

route.append("Collection Center")


# --------------------------------
# Display Results
# --------------------------------

print("\n================================")
print("🚚 SMARTBIN ROUTE OPTIMIZATION")
print("================================\n")

print("Bins selected for collection:")

for bin_name in bins_to_collect:
    print(
        f"  {bin_name} → "
        f"{fill_levels[bin_name]}%"
    )

print("\nRecommended Route:")

print(" → ".join(route))

print(
    f"\nTotal Distance: "
    f"{total_distance:.2f} units"
)

print("\n================================")