import io
import re

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Airbnb Business Intelligence",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# PROFESSIONAL THEME
# =========================================================

st.markdown(
    """
    <style>
    :root {
        --navy: #14243A;
        --blue: #1F4E79;
        --teal: #0F9D9A;
        --light-bg: #F4F7FB;
        --text: #25364A;
    }

    .stApp {
        background: #F4F7FB;
        color: #25364A;
    }

    [data-testid="stSidebar"] {
        background: #14243A;
    }

    [data-testid="stSidebar"] * {
        color: #F5F8FC !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #25364A !important;
    }

    [data-testid="stSidebar"] input {
        color: #25364A !important;
    }

    .dashboard-header {
        background: linear-gradient(110deg, #14243A 0%, #1F4E79 65%, #0F9D9A 100%);
        padding: 28px 32px;
        border-radius: 16px;
        margin-bottom: 22px;
        color: white;
        box-shadow: 0 6px 18px rgba(20, 36, 58, 0.12);
    }

    .dashboard-header h1 {
        color: white;
        font-size: 2rem;
        font-weight: 750;
        margin: 0;
    }

    .dashboard-header p {
        color: #DCE8F3;
        margin: 8px 0 0 0;
        font-size: 1rem;
    }

    .section-heading {
        color: #14243A;
        font-size: 1.25rem;
        font-weight: 750;
        margin: 8px 0 12px 0;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #E1E8F0;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 3px 12px rgba(20, 36, 58, 0.05);
    }

    div[data-testid="stMetric"] label {
        color: #60758A !important;
        font-weight: 600;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #14243A !important;
        font-weight: 750;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        background: #1F4E79;
        color: white;
        border: 1px solid #1F4E79;
        border-radius: 9px;
        font-weight: 650;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background: #0F9D9A;
        border-color: #0F9D9A;
        color: white;
    }

    [data-testid="stPlotlyChart"] {
        background: white;
        border: 1px solid #E1E8F0;
        border-radius: 14px;
        padding: 8px;
        box-shadow: 0 3px 12px rgba(20, 36, 58, 0.04);
    }

    h2, h3 {
        color: #14243A;
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
    <div class="dashboard-header">
        <h1>Airbnb Business Intelligence</h1>
        <p>Listing performance, pricing, host activity, and guest engagement</p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# DATA LOADING AND CLEANING
# =========================================================

@st.cache_data
def load_data(file_bytes):
    df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")

    # Standardize column names
    df.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower()).strip("_")
        for col in df.columns
    ]

    # Standardize common spelling variations
    rename_map = {
        "name": "listing_name",
        "neighborhood": "neighbourhood",
        "neighborhood_group": "neighbourhood_group"
    }
    df = df.rename(columns=rename_map)

    # Clean numeric fields
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

    if "last_review" in df.columns:
        df["last_review"] = pd.to_datetime(
            df["last_review"], errors="coerce"
        )

    return df.drop_duplicates()


uploaded_file = st.file_uploader(
    "Upload Airbnb CSV dataset",
    type=["csv"],
    help="Select your Airbnb Open Data CSV file."
)

if uploaded_file is None:
    st.info("Upload your Airbnb CSV file to view the dashboard.")
    st.stop()

try:
    df = load_data(uploaded_file.getvalue())
except Exception as error:
    st.error(f"Could not read the uploaded file: {error}")
    st.stop()

if df.empty:
    st.error("The uploaded dataset is empty.")
    st.stop()


# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.title("Dashboard Filters")
st.sidebar.caption("Choose values to update the dashboard.")

filtered_df = df.copy()


def dropdown_filter(data, column, label):
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
    filtered_df, "neighbourhood_group", "Neighbourhood Group"
)

filtered_df = dropdown_filter(
    filtered_df, "neighbourhood", "Neighbourhood"
)

filtered_df = dropdown_filter(
    filtered_df, "room_type", "Room Type"
)

filtered_df = dropdown_filter(
    filtered_df, "host_identity_verified", "Host Verification"
)

filtered_df = dropdown_filter(
    filtered_df, "instant_bookable", "Instant Bookable"
)

if "price" in filtered_df.columns and filtered_df["price"].notna().any():
    min_price = float(filtered_df["price"].min())
    max_price = float(filtered_df["price"].max())

    if min_price < max_price:
        price_range = st.sidebar.slider(
            "Price Range",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price)
        )

        filtered_df = filtered_df[
            filtered_df["price"].between(price_range[0], price_range[1])
        ]

st.sidebar.markdown("---")
st.sidebar.caption(f"Listings in current view: {len(filtered_df):,}")


# =========================================================
# KPI METRICS
# =========================================================

st.markdown(
    '<div class="section-heading">Executive Overview</div>',
    unsafe_allow_html=True
)

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "Total Listings",
    f"{len(filtered_df):,}"
)

if "price" in filtered_df.columns and filtered_df["price"].notna().any():
    metric2.metric(
        "Average Price",
        f"${filtered_df['price'].mean():,.0f}"
    )
else:
    metric2.metric("Average Price", "N/A")

if "number_of_reviews" in filtered_df.columns:
    metric3.metric(
        "Total Reviews",
        f"{filtered_df['number_of_reviews'].sum():,.0f}"
    )
else:
    metric3.metric("Total Reviews", "N/A")

if (
    "availability_365" in filtered_df.columns
    and filtered_df["availability_365"].notna().any()
):
    metric4.metric(
        "Average Availability",
        f"{filtered_df['availability_365'].mean():.1f} days"
    )
else:
    metric4.metric("Average Availability", "N/A")


# =========================================================
# ANALYSIS SELECTOR
# =========================================================

st.markdown("---")

analysis = st.selectbox(
    "Select Analysis",
    [
        "Location Analysis",
        "Pricing Analysis",
        "Host Analysis",
        "Review Analysis",
        "Availability Analysis",
        "Dataset Explorer"
    ]
)

st.markdown(
    f'<div class="section-heading">{analysis}</div>',
    unsafe_allow_html=True
)


# =========================================================
# LOCATION ANALYSIS
# =========================================================

if analysis == "Location Analysis":

    col1, col2 = st.columns(2)

    with col1:
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
                color_continuous_scale="Teal",
                title="Top Neighbourhoods by Listing Count"
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)

    with col2:
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
                color_discrete_sequence=px.colors.qualitative.Set2,
                title="Listing Share by Room Type"
            )
            st.plotly_chart(fig, use_container_width=True)

    if "neighbourhood_group" in filtered_df.columns:
        group_counts = (
            filtered_df["neighbourhood_group"]
            .dropna()
            .astype(str)
            .value_counts()
            .reset_index()
        )
        group_counts.columns = ["Neighbourhood Group", "Listings"]

        fig = px.bar(
            group_counts,
            x="Neighbourhood Group",
            y="Listings",
            color="Listings",
            color_continuous_scale="Blues",
            title="Listings by Neighbourhood Group"
        )
        st.plotly_chart(fig, use_container_width=True)


# =========================================================
# PRICING ANALYSIS
# =========================================================

elif analysis == "Pricing Analysis":

    if "price" not in filtered_df.columns:
        st.warning("The uploaded dataset does not contain a price column.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            price_data = filtered_df.dropna(subset=["price"])

            fig = px.histogram(
                price_data,
                x="price",
                nbins=40,
                color_discrete_sequence=["#0F9D9A"],
                title="Listing Price Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
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
                    title="Average Price by Room Type"
                )
                st.plotly_chart(fig, use_container_width=True)

        if "neighbourhood_group" in filtered_df.columns:
            group_price = (
                filtered_df.groupby("neighbourhood_group", dropna=True)["price"]
                .mean()
                .reset_index()
                .sort_values("price", ascending=False)
            )
            group_price.columns = ["Neighbourhood Group", "Average Price"]

            fig = px.bar(
                group_price,
                x="Neighbourhood Group",
                y="Average Price",
                color="Average Price",
                color_continuous_scale="Blues",
                title="Average Price by Neighbourhood Group"
            )
            st.plotly_chart(fig, use_container_width=True)


# =========================================================
# HOST ANALYSIS
# =========================================================

elif analysis == "Host Analysis":

    col1, col2 = st.columns(2)

    with col1:
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
                color_continuous_scale="Blues",
                title="Top 10 Hosts by Listing Count"
            )
            fig.update_layout(xaxis_title="Host ID")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
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
                color_continuous_scale="Teal",
                title="Average Price by Host Verification"
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
            color_continuous_scale="Blues",
            title="Average Reviews by Host Verification"
        )
        st.plotly_chart(fig, use_container_width=True)


# =========================================================
# REVIEW ANALYSIS
# =========================================================

elif analysis == "Review Analysis":

    col1, col2 = st.columns(2)

    with col1:
        if "number_of_reviews" in filtered_df.columns:
            review_data = filtered_df.dropna(subset=["number_of_reviews"])

            fig = px.histogram(
                review_data,
                x="number_of_reviews",
                nbins=40,
                color_discrete_sequence=["#1F4E79"],
                title="Distribution of Review Counts"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
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
                color_continuous_scale="Teal",
                title="Average Reviews by Room Type"
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
            color_continuous_scale="Blues",
            title="Neighbourhoods with the Most Reviews"
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)


# =========================================================
# AVAILABILITY ANALYSIS
# =========================================================

elif analysis == "Availability Analysis":

    if "availability_365" not in filtered_df.columns:
        st.warning("The uploaded dataset does not contain an availability column.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            availability_data = filtered_df.dropna(subset=["availability_365"])

            fig = px.histogram(
                availability_data,
                x="availability_365",
                nbins=30,
                color_discrete_sequence=["#0F9D9A"],
                title="Availability Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
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
                    color_continuous_scale="Teal",
                    title="Average Availability by Room Type"
                )
                st.plotly_chart(fig, use_container_width=True)


# =========================================================
# DATASET EXPLORER
# =========================================================

elif analysis == "Dataset Explorer":

    st.markdown("### Search and inspect filtered listings")

    search_text = st.text_input(
        "Search listings",
        placeholder="Search by listing name, neighbourhood, room type, or host"
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

    st.caption(f"Records displayed: {len(display_df):,}")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    csv_data = display_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Filtered Data as CSV",
        data=csv_data,
        file_name="filtered_airbnb_data.csv",
        mime="text/csv",
        use_container_width=True
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Airbnb Business Intelligence Dashboard | Built with Streamlit and Plotly"
)
