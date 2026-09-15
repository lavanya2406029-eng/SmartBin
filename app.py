import streamlit as st
import pandas as pd
import math
import requests
import folium
from streamlit_folium import st_folium
import firebase_admin
from firebase_admin import credentials, db
from sklearn.linear_model import LinearRegression


# ==================================================
# PAGE SETTINGS
# ==================================================

st.set_page_config(
    page_title="SmartBin Dashboard",
    page_icon="🚮",
    layout="wide"
)

st.title("🚮 SmartBin Dashboard")
st.caption("IoT and AI Based Predictive Waste Collection System")


# ==================================================
# FIREBASE CONNECTION
# ==================================================

if not firebase_admin._apps:

    firebase_config = dict(st.secrets["firebase"])

    cred = credentials.Certificate(
        firebase_config
    )

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL":
            "https://smartbin-cd872-default-rtdb.firebaseio.com"
        }
    )


# ==================================================
# GET FIREBASE DATA
# ==================================================

def get_firebase_data():

    latest_data = db.reference(
        "smartbin/latest"
    ).get()

    readings_data = db.reference(
        "smartbin/readings"
    ).get()

    return latest_data, readings_data


# ==================================================
# ROAD ROUTE USING OSRM
# ==================================================

def get_road_route(route_locations):

    try:

        # OSRM expects longitude,latitude

        coordinates = ";".join(
            [
                f"{lon},{lat}"
                for lat, lon in route_locations
            ]
        )


        url = (
            "https://router.project-osrm.org/"
            "route/v1/driving/"
            + coordinates
            + "?overview=full&geometries=geojson"
        )


        response = requests.get(
            url,
            timeout=10
        )


        if response.status_code != 200:

            return None


        result = response.json()


        if result.get("code") != "Ok":

            return None


        route = result[
            "routes"
        ][0]


        distance_km = (
            route["distance"] / 1000
        )


        duration_min = (
            route["duration"] / 60
        )


        geometry = route[
            "geometry"
        ]["coordinates"]


        # OSRM gives [longitude, latitude]
        # Folium needs [latitude, longitude]

        route_points = [
            [point[1], point[0]]
            for point in geometry
        ]


        return (
            route_points,
            distance_km,
            duration_min
        )


    except Exception:

        return None


# ==================================================
# DASHBOARD
# ==================================================

@st.fragment(run_every="5s")
def dashboard():

    latest_data, readings_data = (
        get_firebase_data()
    )


    bins = [
        "bin1",
        "bin2",
        "bin3"
    ]


    # ==================================================
    # LOAD DATA
    # ==================================================

    if readings_data:

        data = pd.DataFrame(
            list(
                readings_data.values()
            )
        )

    else:

        data = pd.read_csv(
            "data.csv"
        )


    data = data[
        [
            "time",
            "bin1",
            "bin2",
            "bin3"
        ]
    ]


    for bin_name in bins:

        data[bin_name] = pd.to_numeric(
            data[bin_name],
            errors="coerce"
        )


    data = data.dropna(
        subset=bins
    ).reset_index(
        drop=True
    )


    for bin_name in bins:

        data[bin_name] = (
            data[bin_name]
            .clip(0, 100)
        )


    # ==================================================
    # LATEST DATA
    # ==================================================

    if latest_data:

        latest = pd.Series(
            {
                "time":
                    latest_data.get("time"),

                "bin1":
                    latest_data.get("bin1"),

                "bin2":
                    latest_data.get("bin2"),

                "bin3":
                    latest_data.get("bin3")
            }
        )

    else:

        latest = data.iloc[-1]


    for bin_name in bins:

        latest[bin_name] = float(
            latest[bin_name]
        )

        latest[bin_name] = max(
            0,
            min(
                100,
                latest[bin_name]
            )
        )


    # ==================================================
    # OVERALL STATUS
    # ==================================================

    levels = [
        latest[bin_name]
        for bin_name in bins
    ]


    average_level = (
        sum(levels)
        /
        len(levels)
    )


    bins_to_collect = sum(
        level >= 90
        for level in levels
    )


    bins_soon = sum(
        70 <= level < 90
        for level in levels
    )


    st.subheader(
        "📊 Overall Status"
    )


    col1, col2, col3, col4 = (
        st.columns(4)
    )


    with col1:

        st.metric(
            "Total Bins",
            "3"
        )


    with col2:

        st.metric(
            "Average Fill Level",
            f"{average_level:.1f}%"
        )


    with col3:

        st.metric(
            "🔴 Collection Required",
            bins_to_collect
        )


    with col4:

        st.metric(
            "🟡 Collection Soon",
            bins_soon
        )


    # ==================================================
    # CURRENT BIN STATUS
    # ==================================================

    st.subheader(
        "🗑️ Current Bin Status"
    )


    col1, col2, col3 = (
        st.columns(3)
    )


    for col, bin_name in zip(
        [col1, col2, col3],
        bins
    ):

        level = latest[bin_name]


        with col:

            st.metric(
                bin_name.upper(),
                f"{level:.0f}%"
            )


            if level >= 90:

                st.error(
                    "🔴 Collection Required"
                )

            elif level >= 70:

                st.warning(
                    "🟡 Collection Soon"
                )

            else:

                st.success(
                    "🟢 Normal"
                )


    # ==================================================
    # AI PREDICTION
    # ==================================================

    st.subheader(
        "🤖 AI Future Prediction"
    )


    st.caption(
        "AI Model: Linear Regression using recent continuous fill-level data"
    )


    predictions = {}

    filling_rates = {}

    time_to_90 = {}


    prediction_cols = (
        st.columns(3)
    )


    for col, bin_name in zip(
        prediction_cols,
        bins
    ):

        current_level = latest[
            bin_name
        ]


        bin_series = (
            data[bin_name]
            .reset_index(drop=True)
        )


        differences = (
            bin_series.diff()
        )


        reset_points = (
            differences[
                differences < 0
            ].index
        )


        if len(reset_points) > 0:

            start_index = (
                reset_points[-1]
            )

            model_data = (
                data.iloc[
                    start_index + 1:
                ].copy()
            )

        else:

            model_data = data.copy()


        model_data = (
            model_data
            .tail(20)
            .copy()
        )


        model_data[
            "time_number"
        ] = range(
            len(model_data)
        )


        if len(model_data) >= 2:

            X = model_data[
                ["time_number"]
            ]

            y = model_data[
                bin_name
            ]


            model = (
                LinearRegression()
            )


            model.fit(
                X,
                y
            )


            rate = model.coef_[0]


            if rate <= 0:

                changes = y.diff()


                positive_changes = (
                    changes[
                        changes > 0
                    ]
                )


                if len(
                    positive_changes
                ) > 0:

                    rate = (
                        positive_changes.mean()
                    )

                else:

                    rate = 0

        else:

            rate = 0


        filling_rates[
            bin_name
        ] = rate


        # 5 minutes = 1 reading

        prediction_15 = (
            current_level
            +
            rate * 3
        )


        prediction_30 = (
            current_level
            +
            rate * 6
        )


        prediction_60 = (
            current_level
            +
            rate * 12
        )


        prediction_15 = max(
            0,
            min(
                100,
                prediction_15
            )
        )


        prediction_30 = max(
            0,
            min(
                100,
                prediction_30
            )
        )


        prediction_60 = max(
            0,
            min(
                100,
                prediction_60
            )
        )


        predictions[
            bin_name
        ] = prediction_30


        if current_level >= 90:

            minutes_to_90 = 0

        elif rate > 0:

            remaining = (
                90
                -
                current_level
            )


            readings_needed = (
                remaining
                /
                rate
            )


            minutes_to_90 = (
                readings_needed * 5
            )

        else:

            minutes_to_90 = 999


        time_to_90[
            bin_name
        ] = minutes_to_90


        with col:

            st.metric(
                bin_name.upper(),
                f"{current_level:.0f}%"
            )


            st.write(
                f"📈 Filling Rate: "
                f"**{rate:.2f}% / 5 min**"
            )


            st.write(
                f"⏱️ 15 min: "
                f"**{prediction_15:.1f}%**"
            )


            st.write(
                f"⏱️ 30 min: "
                f"**{prediction_30:.1f}%**"
            )


            st.write(
                f"⏱️ 60 min: "
                f"**{prediction_60:.1f}%**"
            )


            if prediction_30 >= 90:

                st.error(
                    "🔴 AI: Collection Required"
                )

            elif prediction_30 >= 70:

                st.warning(
                    "🟡 AI: Collection Soon"
                )

            else:

                st.success(
                    "🟢 AI: Normal"
                )


    # ==================================================
    # TIME TO 90%
    # ==================================================

    st.subheader(
        "⏱️ Estimated Time to 90%"
    )


    time_cols = st.columns(3)


    for col, bin_name in zip(
        time_cols,
        bins
    ):

        minutes = time_to_90[
            bin_name
        ]


        with col:

            if minutes == 0:

                st.error(
                    f"{bin_name.upper()} "
                    f"→ 90% already reached"
                )

            elif minutes == 999:

                st.info(
                    f"{bin_name.upper()} "
                    f"→ Not increasing"
                )

            else:

                st.metric(
                    f"{bin_name.upper()} "
                    f"Time to 90%",
                    f"{minutes:.1f} min"
                )


    # ==================================================
    # COLLECTION PRIORITY
    # ==================================================

    st.subheader(
        "🚚 Collection Priority"
    )


    priority_data = []


    for bin_name in bins:

        current = latest[
            bin_name
        ]

        predicted = predictions[
            bin_name
        ]

        minutes = time_to_90[
            bin_name
        ]


        if minutes == 0:

            urgency = 100

        elif minutes <= 10:

            urgency = 100

        elif minutes <= 30:

            urgency = 80

        elif minutes <= 60:

            urgency = 50

        else:

            urgency = 20


        score = (
            current * 0.35
            +
            predicted * 0.35
            +
            urgency * 0.30
        )


        priority_data.append(
            {
                "Bin":
                    bin_name.upper(),

                "Current Level":
                    f"{current:.0f}%",

                "30 Min Prediction":
                    f"{predicted:.1f}%",

                "Time to 90%":
                    (
                        "Reached"
                        if minutes == 0
                        else
                        "Not increasing"
                        if minutes == 999
                        else
                        f"{minutes:.1f} min"
                    ),

                "Filling Rate":
                    f"{filling_rates[bin_name]:.2f}% / 5 min",

                "Priority Score":
                    f"{score:.1f}",

                "_score":
                    score
            }
        )


    priority_df = pd.DataFrame(
        priority_data
    )


    priority_df = (
        priority_df
        .sort_values(
            "_score",
            ascending=False
        )
        .reset_index(drop=True)
    )


    priority_df.insert(
        0,
        "Priority",
        range(
            1,
            len(priority_df) + 1
        )
    )


    priority_df = (
        priority_df
        .drop(
            columns=["_score"]
        )
    )


    st.table(
        priority_df
    )


    # ==================================================
    # COLLECTION ORDER
    # ==================================================

    st.subheader(
        "📋 Recommended Collection Order"
    )


    order = priority_df[
        "Bin"
    ].tolist()


    for i, bin_name in enumerate(
        order,
        start=1
    ):

        score = float(
            priority_df.loc[
                priority_df["Bin"]
                == bin_name,
                "Priority Score"
            ].iloc[0]
        )


        if i == 1:

            st.error(
                f"🔴 {i}. {bin_name} "
                f"→ Highest Priority "
                f"(Score: {score:.1f})"
            )

        elif i == 2:

            st.warning(
                f"🟡 {i}. {bin_name} "
                f"→ Medium Priority "
                f"(Score: {score:.1f})"
            )

        else:

            st.success(
                f"🟢 {i}. {bin_name} "
                f"→ Lower Priority "
                f"(Score: {score:.1f})"
            )


    # ==================================================
    # FILL LEVEL TREND
    # ==================================================

    st.subheader(
        "📈 Fill Level Trend"
    )


    chart_data = data[
        [
            "time",
            "bin1",
            "bin2",
            "bin3"
        ]
    ].copy()


    chart_data = (
        chart_data
        .tail(30)
    )


    st.line_chart(
        chart_data.set_index(
            "time"
        )[bins]
    )


    # ==================================================
    # COLLECTION RECOMMENDATION
    # ==================================================

    st.subheader(
        "📋 Collection Recommendation"
    )


    for bin_name in bins:

        current = latest[
            bin_name
        ]

        predicted = predictions[
            bin_name
        ]


        if current >= 90:

            st.error(
                f"🔴 {bin_name.upper()} "
                f"→ Collect immediately"
            )

        elif predicted >= 90:

            st.error(
                f"🔴 {bin_name.upper()} "
                f"→ AI predicts collection required"
            )

        elif current >= 70:

            st.warning(
                f"🟡 {bin_name.upper()} "
                f"→ Collection soon"
            )

        else:

            st.success(
                f"🟢 {bin_name.upper()} "
                f"→ No collection required"
            )


    # ==================================================
    # ROUTE OPTIMIZATION
    # ==================================================

    st.subheader(
        "🚚 Recommended Collection Route"
    )


    # Prototype sample GPS coordinates
    # Replace these later with actual bin GPS locations.

    locations = {

        "Collection Center":
            (11.0168, 76.9558),

        "BIN1":
            (11.0195, 76.9610),

        "BIN2":
            (11.0225, 76.9680),

        "BIN3":
            (11.0250, 76.9580)
    }


    bins_for_route = []


    for bin_name in bins:

        current = latest[
            bin_name
        ]

        predicted = predictions[
            bin_name
        ]

        minutes = time_to_90[
            bin_name
        ]


        if (
            current >= 90
            or predicted >= 90
            or minutes <= 10
        ):

            bins_for_route.append(
                bin_name.upper()
            )


    # ==================================================
    # NEAREST-BIN ROUTE
    # ==================================================

    def distance(
        point1,
        point2
    ):

        lat1, lon1 = point1

        lat2, lon2 = point2


        x = (
            lat2 - lat1
        ) * 111


        y = (
            lon2 - lon1
        ) * 111


        return math.sqrt(
            x ** 2
            +
            y ** 2
        )


    current_location = (
        "Collection Center"
    )


    route = [
        "Collection Center"
    ]


    remaining_bins = (
        bins_for_route.copy()
    )


    while remaining_bins:

        nearest_bin = min(
            remaining_bins,
            key=lambda bin_name:
                distance(
                    locations[
                        current_location
                    ],
                    locations[
                        bin_name
                    ]
                )
        )


        route.append(
            nearest_bin
        )


        current_location = (
            nearest_bin
        )


        remaining_bins.remove(
            nearest_bin
        )


    if bins_for_route:

        route.append(
            "Collection Center"
        )


        st.success(
            " → ".join(route)
        )


    else:

        st.info(
            "No bins require collection currently."
        )


    # ==================================================
    # MAP
    # ==================================================

    st.subheader(
        "🗺️ Smart Collection Route Map"
    )


    center_lat, center_lon = (
        locations[
            "Collection Center"
        ]
    )


    smartbin_map = folium.Map(
        location=[
            center_lat,
            center_lon
        ],
        zoom_start=14,
        tiles="OpenStreetMap"
    )


    # ==================================================
    # COLLECTION CENTER
    # ==================================================

    folium.Marker(

        location=[
            center_lat,
            center_lon
        ],

        popup="Collection Center",

        tooltip="📍 Collection Center",

        icon=folium.Icon(
            color="blue",
            icon="home"
        )

    ).add_to(
        smartbin_map
    )


    # ==================================================
    # BIN MARKERS
    # ==================================================

    for bin_name in bins:

        level = latest[
            bin_name
        ]


        if level >= 90:

            marker_color = "red"

            status = (
                "🔴 Collection Required"
            )

        elif level >= 70:

            marker_color = "orange"

            status = (
                "🟡 Collection Soon"
            )

        else:

            marker_color = "green"

            status = (
                "🟢 Normal"
            )


        latitude, longitude = (
            locations[
                bin_name.upper()
            ]
        )


        popup_text = (
            f"<b>{bin_name.upper()}</b><br>"
            f"Fill Level: {level:.0f}%<br>"
            f"Status: {status}"
        )


        folium.Marker(

            location=[
                latitude,
                longitude
            ],

            popup=folium.Popup(
                popup_text,
                max_width=250
            ),

            tooltip=(
                f"{bin_name.upper()} "
                f"({level:.0f}%)"
            ),

            icon=folium.Icon(
                color=marker_color,
                icon="trash"
            )

        ).add_to(
            smartbin_map
        )


    # ==================================================
    # ROAD-FOLLOWING ROUTE
    # ==================================================

    road_route_available = False


    if len(route) > 1:

        route_locations = [
            locations[
                location_name
            ]
            for location_name in route
        ]


        road_result = (
            get_road_route(
                route_locations
            )
        )


        if road_result:

            (
                road_points,
                road_distance,
                road_time
            ) = road_result


            folium.PolyLine(

                locations=road_points,

                weight=6,

                opacity=0.9,

                tooltip=(
                    "🚚 Fastest Road Route"
                )

            ).add_to(
                smartbin_map
            )


            road_route_available = True


            st.success(
                "🛣️ Road-following route calculated"
            )


            route_col1, route_col2 = (
                st.columns(2)
            )


            with route_col1:

                st.metric(
                    "📏 Road Distance",
                    f"{road_distance:.2f} km"
                )


            with route_col2:

                st.metric(
                    "⏱️ Estimated Travel Time",
                    f"{road_time:.0f} min"
                )


        else:

            # Fallback to straight line

            straight_points = [
                locations[
                    location_name
                ]
                for location_name in route
            ]


            folium.PolyLine(

                locations=straight_points,

                weight=5,

                opacity=0.8,

                tooltip=(
                    "Recommended Route"
                )

            ).add_to(
                smartbin_map
            )


            st.warning(
                "⚠️ Road routing unavailable. "
                "Showing prototype route."
            )


    # ==================================================
    # DISPLAY MAP
    # ==================================================

    st_folium(
        smartbin_map,
        width=1200,
        height=550
    )


    st.caption(
        "Prototype GPS locations are simulated. "
        "Actual deployment can use GPS coordinates of each bin."
    )


# ==================================================
# RUN
# ==================================================

dashboard()
