import io
import re

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# PAGE SETUP
# =========================================================

st.set_page_config(
    page_title="Airbnb Explorer",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Colorful app styling
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f7ff 0%, #fff7fb 50%, #f2fffc 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #25145b 0%, #492b91 55%, #7148b8 100%);
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #222222 !important;
    }

    [data-testid="stSidebar"] input {
        color: #222222 !important;
    }

    .hero {
        padding: 28px 30px;
        border-radius: 22px;
        background: linear-gradient(110deg, #41228e, #8b3dba, #ed5b9f);
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 8px 24px rgba(65, 34, 142, 0.18);
    }

    .hero h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }

    .hero p {
        color: #f6edff;
        margin: 8px 0 0 0;
        font-size: 1.05rem;
    }

    .section-title {
        color: #41228e;
        font-weight: 800;
        font-size: 1.45rem;
        margin-top: 12px;
        margin-bottom: 10px;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff, #f2ecff);
        border: 1px solid #e5d8ff;
        padding: 18px 18px;
        border-radius: 18px;
        box-shadow: 0 5px 15px rgba(65, 34, 142, 0.08);
    }

    div[data-testid="stMetric"] label {
        color: #6040a0 !important;
        font-weight: 700;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #2f176d !important;
        font-weight: 800;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        border-radius: 12px;
        border: 0;
        color: white;
        background: linear-gradient(90deg, #6741d9, #df4fa2);
        font-weight: 700;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        color: white;
        border: 1px solid #ffffff;
        background: linear-gradient(90deg, #df4fa2, #6741d9);
    }

    h2, h3 {
        color: #41228e;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <h1>🏡 Airbnb Explorer</h1>
        <p>Discover listings, compare prices, explore reviews, and uncover insights — all in one interactive dashboard ✨</p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# DATA LOADING
# =========================================================

@st.cache_data
def load_data(file_bytes):
    df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")

    # Standardize column names
    df.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower()).strip("_")
        for col in df.columns
    ]

    # Handle common column-name variations
    rename_map = {
        "name": "listing_name",
        "neighborhood": "neighbourhood",
        "neighborhood_group": "neighbourhood_group",
        "host_identity_verified": "host_identity_verified",
        "number_of_reviews": "number_of_reviews",
        "reviews_per_month": "reviews_per_month",
        "review_rate_number": "review_rate_number",
        "availability_365": "availability_365",
        "calculated_host_listings_count": "calculated_host_listings_count",
        "minimum_nights": "minimum_nights",
        "service_fee": "service_fee",
        "last_review": "last_review",
        "room_type": "room_type",
        "host_id": "host_id",
        "price": "price"
    }

    df = df.rename(columns=rename_map)

    # Clean numeric columns
    numeric_columns = [
        "price",
        "service_fee",
        "number_of_reviews",
        "reviews_per_month",
        "review_rate_number",
        "availability_365",
        "calculated_host_listings_count",
        "minimum_nights",
        "host_id",
        "latitude",
        "longitude"
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[$,]", "", regex=True)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convert review date if available
    if "last_review" in df.columns:
        df["last_review"] = pd.to_datetime(
            df["last_review"], errors="coerce"
        )

    return df.drop_duplicates()


uploaded_file = st.file_uploader(
    "📂 Upload your Airbnb CSV file",
    type=["csv"],
    help="Choose your Airbnb dataset CSV file."
)

if uploaded_file is None:
    st.info("👆 Upload your Airbnb CSV file to open the dashboard.")
    st.stop()

try:
    df = load_data(uploaded_file.getvalue())
except Exception as error:
    st.error(f"Could not read the uploaded file: {error}")
    st.stop()

if df.empty:
    st.error("The uploaded file is empty.")
    st.stop()


# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.markdown("## 🎛️ Dashboard Controls")
st.sidebar.caption("Use these dropdowns to explore a specific group of listings.")

filtered_df = df.copy()


def dropdown_filter(data, column, label):
    """Add a dropdown filter when the requested column exists."""
    if column not in data.columns:
        return data

    values = (
        data[column]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )

    selected = st.sidebar.selectbox(
        label,
        ["All"] + values,
        key=f"filter_{column}"
    )

    if selected != "All":
        data = data[data[column].astype(str) == selected]

    return data


filtered_df = dropdown_filter(
    filtered_df, "neighbourhood_group", "📍 Neighbourhood Group"
)

filtered_df = dropdown_filter(
    filtered_df, "neighbourhood", "🏙️ Neighbourhood"
)

filtered_df = dropdown_filter(
    filtered_df, "room_type", "🛏️ Room Type"
)

filtered_df = dropdown_filter(
    filtered_df, "host_identity_verified", "🪪 Host Verified"
)

filtered_df = dropdown_filter(
    filtered_df, "instant_bookable", "⚡ Instant Bookable"
)

# Price range filter
if "price" in filtered_df.columns and filtered_df["price"].notna().any():
    min_price = float(filtered_df["price"].min())
    max_price = float(filtered_df["price"].max())

    if min_price < max_price:
        price_range = st.sidebar.slider(
            "💰 Price Range",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price)
        )

        filtered_df = filtered_df[
            filtered_df["price"].between(price_range[0], price_range[1])
        ]

# Reset filters
if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("💜 Explore. Compare. Discover.")


# =========================================================
# KPI CARDS
# =========================================================

st.markdown('<div class="section-title">📌 Dashboard Overview</div>', unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "🏠 Total Listings",
    f"{len(filtered_df):,}"
)

if "price" in filtered_df.columns and filtered_df["price"].notna().any():
    kpi2.metric(
        "💰 Average Price",
        f"${filtered_df['price'].mean():,.0f}"
    )
else:
    kpi2.metric("💰 Average Price", "N/A")

if "number_of_reviews" in filtered_df.columns:
    kpi3.metric(
        "⭐ Total Reviews",
        f"{filtered_df['number_of_reviews'].sum():,.0f}"
    )
else:
    kpi3.metric("⭐ Total Reviews", "N/A")

if "availability_365" in filtered_df.columns and filtered_df["availability_365"].notna().any():
    kpi4.metric(
        "📅 Avg. Availability",
        f"{filtered_df['availability_365'].mean():.1f} days"
    )
else:
    kpi4.metric("📅 Avg. Availability", "N/A")


# =========================================================
# ANALYSIS SELECTOR
# =========================================================

st.markdown("---")

analysis = st.selectbox(
    "🧭 Choose an Analysis",
    [
        "🌍 Location Insights",
        "💸 Pricing Insights",
        "👤 Host Insights",
        "⭐ Reviews Insights",
        "📅 Availability Insights",
        "📋 Explore Dataset"
    ]
)

st.markdown(f'<div class="section-title">{analysis}</div>', unsafe_allow_html=True)


# =========================================================
# LOCATION ANALYSIS
# =========================================================

if analysis == "🌍 Location Insights":

    left, right = st.columns(2)

    with left:
        if "neighbourhood" in filtered_df.columns:
            location_counts = (
                filtered_df["neighbourhood"]
                .dropna()
                .astype(str)
                .value_counts()
                .head(15)
                .reset_index()
            )
            location_counts.columns = ["Neighbourhood", "Listings"]

            fig = px.bar(
                location_counts,
                x="Listings",
                y="Neighbourhood",
                orientation="h",
                color="Listings",
                color_continuous_scale="Purples",
                title="🏙️ Top 15 Neighbourhoods by Listings"
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)

    with right:
        if "room_type" in filtered_df.columns:
            room_counts = (
                filtered_df["room_type"]
                .dropna()
                .astype(str)
                .value_counts()
                .reset_index()
            )
            room_counts.columns = ["Room Type", "Listings"]

            fig = px.pie(
                room_counts,
                names="Room Type",
                values="Listings",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel,
                title="🛏️ Listings by Room Type"
            )
            st.plotly_chart(fig, use_container_width=True)

    if "neighbourhood_group" in filtered_df.columns:
        city_counts = (
            filtered_df["neighbourhood_group"]
            .dropna()
            .astype(str)
            .value_counts()
            .reset_index()
        )
        city_counts.columns = ["Neighbourhood Group", "Listings"]

        fig = px.bar(
            city_counts,
            x="Neighbourhood Group",
            y="Listings",
            color="Listings",
            color_continuous_scale="Sunset",
            title="📍 Listings by Neighbourhood Group"
        )
        st.plotly_chart(fig, use_container_width=True)


# =========================================================
# PRICING ANALYSIS
# =========================================================

elif analysis == "💸 Pricing Insights":

    if "price" not in filtered_df.columns:
        st.warning("This dataset does not contain a price column.")
    else:
        left, right = st.columns(2)

        with left:
            price_data = filtered_df.dropna(subset=["price"])

            fig = px.histogram(
                price_data,
                x="price",
                nbins=40,
                color_discrete_sequence=["#8B5CF6"],
                title="💰 Price Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            if "room_type" in filtered_df.columns:
                room_price = (
                    filtered_df.groupby("room_type", dropna=True)["price"]
                    .mean()
                    .reset_index()
                    .sort_values("price", ascending=False)
                )
                room_price.columns = ["Room Type", "Average Price"]

                fig = px.bar(
                    room_price,
                    x="Room Type",
                    y="Average Price",
                    color="Average Price",
                    color_continuous_scale="Teal",
                    title="🛏️ Average Price by Room Type"
                )
                st.plotly_chart(fig, use_container_width=True)

        if "neighbourhood_group" in filtered_df.columns:
            area_price = (
                filtered_df.groupby("neighbourhood_group", dropna=True)["price"]
                .mean()
                .reset_index()
                .sort_values("price", ascending=False)
            )
            area_price.columns = ["Neighbourhood Group", "Average Price"]

            fig = px.bar(
                area_price,
                x="Neighbourhood Group",
                y="Average Price",
                color="Average Price",
                color_continuous_scale="Plasma",
                title="📍 Average Price by Neighbourhood Group"
            )
            st.plotly_chart(fig, use_container_width=True)


# =========================================================
# HOST ANALYSIS
# =========================================================

elif analysis == "👤 Host Insights":

    left, right = st.columns(2)

    with left:
        if "host_id" in filtered_df.columns:
            host_counts = (
                filtered_df.groupby("host_id")
                .size()
                .reset_index(name="Listings")
                .sort_values("Listings", ascending=False)
                .head(10)
            )

            fig = px.bar(
                host_counts,
                x="host_id",
                y="Listings",
                color="Listings",
                color_continuous_scale="Bluered",
                title="🏆 Top 10 Hosts by Listings"
            )
            fig.update_layout(xaxis_title="Host ID")
            st.plotly_chart(fig, use_container_width=True)

    with right:
        if (
            "host_identity_verified" in filtered_df.columns
            and "price" in filtered_df.columns
        ):
            verified_price = (
                filtered_df.groupby("host_identity_verified", dropna=True)["price"]
                .mean()
                .reset_index()
            )
            verified_price.columns = ["Host Verified", "Average Price"]

            fig = px.bar(
                verified_price,
                x="Host Verified",
                y="Average Price",
                color="Average Price",
                color_continuous_scale="Viridis",
                title="🪪 Average Price by Host Verification"
            )
            st.plotly_chart(fig, use_container_width=True)

    if (
        "host_identity_verified" in filtered_df.columns
        and "number_of_reviews" in filtered_df.columns
    ):
        verified_reviews = (
            filtered_df.groupby("host_identity_verified", dropna=True)["number_of_reviews"]
            .mean()
            .reset_index()
        )
        verified_reviews.columns = ["Host Verified", "Average Reviews"]

        fig = px.bar(
            verified_reviews,
            x="Host Verified",
            y="Average Reviews",
            color="Average Reviews",
            color_continuous_scale="Sunset",
            title="⭐ Average Reviews by Host Verification"
        )
        st.plotly_chart(fig, use_container_width=True)


# =========================================================
# REVIEWS ANALYSIS
# =========================================================

elif analysis == "⭐ Reviews Insights":

    left, right = st.columns(2)

    with left:
        if "number_of_reviews" in filtered_df.columns:
            review_data = filtered_df.dropna(subset=["number_of_reviews"])

            fig = px.histogram(
                review_data,
                x="number_of_reviews",
                nbins=40,
                color_discrete_sequence=["#EC4899"],
                title="💬 Distribution of Reviews"
            )
            st.plotly_chart(fig, use_container_width=True)

    with right:
        if (
            "room_type" in filtered_df.columns
            and "number_of_reviews" in filtered_df.columns
        ):
            room_reviews = (
                filtered_df.groupby("room_type", dropna=True)["number_of_reviews"]
                .mean()
                .reset_index()
            )
            room_reviews.columns = ["Room Type", "Average Reviews"]

            fig = px.bar(
                room_reviews,
                x="Room Type",
                y="Average Reviews",
                color="Average Reviews",
                color_continuous_scale="Magenta",
                title="🛏️ Average Reviews by Room Type"
            )
            st.plotly_chart(fig, use_container_width=True)

    if (
        "neighbourhood" in filtered_df.columns
        and "number_of_reviews" in filtered_df.columns
    ):
        area_reviews = (
            filtered_df.groupby("neighbourhood", dropna=True)["number_of_reviews"]
            .sum()
            .sort_values(ascending=False)
            .head(15)
            .reset_index()
        )
        area_reviews.columns = ["Neighbourhood", "Total Reviews"]

        fig = px.bar(
            area_reviews,
            x="Total Reviews",
            y="Neighbourhood",
            orientation="h",
            color="Total Reviews",
            color_continuous_scale="Teal",
            title="🔥 Top 15 Neighbourhoods by Total Reviews"
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)


# =========================================================
# AVAILABILITY ANALYSIS
# =========================================================

elif analysis == "📅 Availability Insights":

    if "availability_365" not in filtered_df.columns:
        st.warning("This dataset does not contain an availability column.")
    else:
        left, right = st.columns(2)

        with left:
            availability_data = filtered_df.dropna(subset=["availability_365"])

            fig = px.histogram(
                availability_data,
                x="availability_365",
                nbins=30,
                color_discrete_sequence=["#14B8A6"],
                title="📅 Availability Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            if "room_type" in filtered_df.columns:
                room_availability = (
                    filtered_df.groupby("room_type", dropna=True)["availability_365"]
                    .mean()
                    .reset_index()
                )
                room_availability.columns = ["Room Type", "Average Availability"]

                fig = px.bar(
                    room_availability,
                    x="Room Type",
                    y="Average Availability",
                    color="Average Availability",
                    color_continuous_scale="Viridis",
                    title="🛏️ Average Availability by Room Type"
                )
                st.plotly_chart(fig, use_container_width=True)


# =========================================================
# DATASET EXPLORER
# =========================================================

elif analysis == "📋 Explore Dataset":

    st.markdown("### 🔍 Search and explore the filtered listings")

    search_text = st.text_input(
        "Search listing name, neighbourhood, room type, or host",
        placeholder="Type a word to search..."
    )

    display_df = filtered_df.copy()

    if search_text:
        searchable_columns = [
            col for col in [
                "listing_name",
                "neighbourhood",
                "neighbourhood_group",
                "room_type",
                "host_name"
            ]
            if col in display_df.columns
        ]

        if searchable_columns:
            search_mask = pd.Series(False, index=display_df.index)

            for col in searchable_columns:
                search_mask = search_mask | display_df[col].astype(str).str.contains(
                    search_text,
                    case=False,
                    na=False
                )

            display_df = display_df[search_mask]

    st.caption(f"Showing {len(display_df):,} rows")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    csv_data = display_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Download Filtered Data as CSV",
        data=csv_data,
        file_name="filtered_airbnb_data.csv",
        mime="text/csv",
        use_container_width=True
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; color:#7656a8; padding:10px;">
        Made with 💜 using Streamlit and Plotly | Airbnb Explorer 🏡
    </div>
    """,
    unsafe_allow_html=True
)
