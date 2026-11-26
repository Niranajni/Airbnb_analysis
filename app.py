import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Airbnb Market Analysis",
    page_icon="🏡",
    layout="wide"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background-color: #F5F7FA;
        border: 1px solid #E5E7EB;
        padding: 15px;
        border-radius: 12px;
    }
    div[data-testid="stMetric"] label {
        color: #475569;
    }
    h1, h2, h3 {
        color: #1E293B;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏡 Airbnb Market Intelligence")
st.caption(
    "Explore listing locations, prices, hosts, availability and customer reviews."
)

# ==========================================
# DATA UPLOAD
# ==========================================

st.sidebar.title("🏡 Airbnb Dashboard")

uploaded_file = st.sidebar.file_uploader(
    "Upload Airbnb_Open_Data.csv",
    type=["csv"]
)

if uploaded_file is None:
    st.info("Upload your Airbnb_Open_Data.csv file to begin.")
    st.stop()

# ==========================================
# DATA CLEANING
# ==========================================

@st.cache_data
def load_data(file):
    data = pd.read_csv(file)

    data.columns = data.columns.str.strip()

    # Standardize column names
    data = data.rename(columns={
        "host id": "host_id",
        "host name": "host_name",
        "neighbourhood group": "neighbourhood_group",
        "room type": "room_type",
        "Construction year": "Construction_year",
        "service fee": "service_fee",
        "minimum nights": "minimum_nights",
        "number of reviews": "number_of_reviews",
        "last review": "last_review",
        "reviews per month": "reviews_per_month",
        "calculated host listings count":
            "calculated_host_listings_count",
        "availability 365": "availability_365",
        "review rate number": "review_rate_number"
    })

    # Remove unnecessary columns
    data = data.drop(
        columns=["id", "lat", "long", "country code",
                 "house_rules"],
        errors="ignore"
    )

    # Convert price and service fee
    for col in ["price", "service_fee"]:
        if col in data.columns:
            data[col] = pd.to_numeric(
                data[col].astype(str)
                .str.replace(r"[$,]", "", regex=True),
                errors="coerce"
            )

    # Convert numeric columns
    numeric_cols = [
        "minimum_nights",
        "number_of_reviews",
        "reviews_per_month",
        "review_rate_number",
        "availability_365",
        "calculated_host_listings_count",
        "Construction_year"
    ]

    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(
                data[col], errors="coerce"
            )

    # Convert dates
    if "last_review" in data.columns:
        data["last_review"] = pd.to_datetime(
            data["last_review"], errors="coerce"
        )

    # Fill missing values
    if "price" in data.columns:
        data["price"] = data["price"].fillna(
            data["price"].median()
        )

    if "service_fee" in data.columns:
        data["service_fee"] = data["service_fee"].fillna(
            data["price"] * 0.20
        )

    for col in numeric_cols:
        if col in data.columns:
            data[col] = data[col].fillna(
                data[col].median()
            )

    text_cols = [
        "NAME", "host_name", "host_identity_verified",
        "neighbourhood_group", "neighbourhood",
        "country", "room_type", "instant_bookable",
        "cancellation_policy", "license"
    ]

    for col in text_cols:
        if col in data.columns:
            data[col] = data[col].fillna("Unknown")

    if "neighbourhood_group" in data.columns:
        data["neighbourhood_group"] = (
            data["neighbourhood_group"]
            .replace({
                "manhatan": "Manhattan",
                "brookln": "Brooklyn"
            })
        )

    # Create date-based columns
    if "last_review" in data.columns:
        data["year"] = data["last_review"].dt.year
        data["month"] = data["last_review"].dt.month_name()

    return data


df = load_data(uploaded_file)

required_columns = [
    "price", "room_type", "neighbourhood",
    "neighbourhood_group", "host_name",
    "number_of_reviews", "availability_365"
]

missing = [col for col in required_columns if col not in df.columns]

if missing:
    st.error(f"Required columns missing: {missing}")
    st.stop()

# ==========================================
# SIDEBAR FILTERS
# ==========================================

st.sidebar.header("🔎 Dashboard Filters")

groups = sorted(
    df["neighbourhood_group"].dropna().unique()
)

selected_groups = st.sidebar.multiselect(
    "Neighborhood Group",
    groups,
    default=groups
)

room_types = sorted(
    df["room_type"].dropna().unique()
)

selected_rooms = st.sidebar.multiselect(
    "Room Type",
    room_types,
    default=room_types
)

price_min = float(df["price"].min())
price_max = float(df["price"].max())

price_range = st.sidebar.slider(
    "Price Range",
    min_value=price_min,
    max_value=price_max,
    value=(price_min, price_max)
)

rating_range = st.sidebar.slider(
    "Minimum Review Rating",
    min_value=0.0,
    max_value=5.0,
    value=0.0,
    step=0.5
)

# Apply filters
filtered_df = df[
    df["neighbourhood_group"].isin(selected_groups)
    & df["room_type"].isin(selected_rooms)
    & df["price"].between(price_range[0], price_range[1])
]

if "review_rate_number" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["review_rate_number"] >= rating_range
    ]

df = filtered_df.copy()

if df.empty:
    st.warning("No listings match the selected filters.")
    st.stop()

# ==========================================
# DASHBOARD OVERVIEW
# ==========================================

st.header("Market Overview")

total_listings = len(df)
total_hosts = df["host_name"].nunique()
average_price = df["price"].mean()
average_rating = df["review_rate_number"].mean()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Listings", f"{total_listings:,}")
c2.metric("Total Hosts", f"{total_hosts:,}")
c3.metric("Average Price", f"${average_price:,.2f}")
c4.metric("Average Rating", f"{average_rating:.2f} / 5")

st.divider()

# ==========================================
# NAVIGATION TABS
# ==========================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📍 Location",
    "💰 Pricing",
    "👤 Hosts",
    "⭐ Reviews",
    "📅 Availability",
    "🧹 Data Cleaning"
])

# ==========================================
# LOCATION ANALYSIS
# ==========================================

with tab1:

    st.subheader("Location & Listings Analysis")

    col1, col2 = st.columns(2)

    # Top neighborhoods
    with col1:
        top_neighborhoods = (
            df["neighbourhood"]
            .value_counts()
            .head(10)
            .reset_index()
        )

        top_neighborhoods.columns = [
            "Neighborhood", "Listings"
        ]

        fig = px.bar(
            top_neighborhoods,
            x="Listings",
            y="Neighborhood",
            orientation="h",
            title="Top 10 Neighborhoods by Listings",
            color="Listings",
            color_continuous_scale="Teal"
        )

        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    # Room types across neighborhood groups
    with col2:
        fig = px.histogram(
            df,
            x="neighbourhood_group",
            color="room_type",
            barmode="group",
            title="Room Types Across Neighborhood Groups"
        )

        st.plotly_chart(fig, use_container_width=True)

    # Neighborhood map-style comparison
    st.subheader("Neighborhood Listing Distribution")

    location_data = (
        df.groupby("neighbourhood_group")
        .size()
        .reset_index(name="Listings")
    )

    fig = px.pie(
        location_data,
        names="neighbourhood_group",
        values="Listings",
        hole=0.45,
        title="Listings by Neighborhood Group"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Neighborhoods")

    st.dataframe(
        df["neighbourhood"].value_counts()
        .head(10)
        .rename("Number of Listings"),
        use_container_width=True
    )

# ==========================================
# PRICE ANALYSIS
# ==========================================

with tab2:

    st.subheader("Pricing Analysis")

    col1, col2 = st.columns(2)

    # Price distribution
    with col1:
        fig = px.histogram(
            df,
            x="price",
            nbins=40,
            title="Distribution of Listing Prices",
            color_discrete_sequence=["#0F766E"]
        )

        st.plotly_chart(fig, use_container_width=True)

    # Average price by room type
    with col2:
        room_price = (
            df.groupby("room_type")["price"]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            room_price,
            x="room_type",
            y="price",
            title="Average Price by Room Type",
            color="room_type"
        )

        st.plotly_chart(fig, use_container_width=True)

    # Top 10 expensive neighborhoods
    st.subheader("Top 10 Neighborhoods by Average Price")

    avg_price = (
        df.groupby("neighbourhood")["price"]
        .mean()
        .nlargest(10)
        .reset_index()
    )

    fig = px.bar(
        avg_price,
        x="price",
        y="neighbourhood",
        orientation="h",
        title="Highest Average Neighborhood Prices",
        color="price",
        color_continuous_scale="Sunset"
    )

    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    # Price correlation
    st.subheader("Price and Listing Correlations")

    corr_cols = [
        "price", "number_of_reviews",
        "minimum_nights", "availability_365"
    ]

    corr = df[corr_cols].corr()

    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        title="Correlation Between Price and Other Variables"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Price by host
    top_hosts = (
        df.groupby("host_name")["price"]
        .mean()
        .nlargest(10)
        .reset_index()
    )

    fig = px.bar(
        top_hosts,
        x="host_name",
        y="price",
        title="Average Price by Top 10 Hosts"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# HOST ANALYSIS
# ==========================================

with tab3:

    st.subheader("Host Performance Analysis")

    col1, col2 = st.columns(2)

    with col1:
        top_hosts = (
            df["host_id"].value_counts()
            .head(10)
            .reset_index()
        )

        top_hosts.columns = ["Host ID", "Listings"]

        fig = px.bar(
            top_hosts,
            x="Host ID",
            y="Listings",
            title="Top 10 Hosts by Listings"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        host_data = (
            df.groupby("host_identity_verified")
            [["review_rate_number", "price"]]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            host_data,
            x="host_identity_verified",
            y="review_rate_number",
            color="host_identity_verified",
            title="Average Rating by Verification Status"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Hosts with Most Reviews")

    host_reviews = (
        df.groupby("host_name")["number_of_reviews"]
        .sum()
        .nlargest(10)
        .reset_index()
    )

    fig = px.bar(
        host_reviews,
        x="host_name",
        y="number_of_reviews",
        title="Top 10 Hosts by Total Reviews"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Average Reviews by Room Type")

    room_reviews = (
        df.groupby("room_type")["number_of_reviews"]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        room_reviews,
        x="room_type",
        y="number_of_reviews",
        title="Average Reviews by Room Type"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# CUSTOMER PREFERENCES & REVIEWS
# ==========================================

with tab4:

    st.subheader("Customer Preferences & Reviews")

    col1, col2 = st.columns(2)

    with col1:
        room_counts = (
            df["room_type"].value_counts()
            .reset_index()
        )

        room_counts.columns = ["Room Type", "Listings"]

        fig = px.pie(
            room_counts,
            names="Room Type",
            values="Listings",
            hole=0.4,
            title="Popular Room Types"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        top_reviews = (
            df.groupby("neighbourhood")["number_of_reviews"]
            .sum()
            .nlargest(10)
            .reset_index()
        )

        fig = px.bar(
            top_reviews,
            x="number_of_reviews",
            y="neighbourhood",
            orientation="h",
            title="Top 10 Neighborhoods by Reviews"
        )

        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Price vs Review Rating")

    fig = px.scatter(
        df,
        x="price",
        y="review_rate_number",
        color="room_type",
        hover_data=["NAME", "neighbourhood"],
        title="Price vs Review Rating"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Highly Rated Listings")

    high_rated = df[
        df["review_rate_number"] >= 4.5
    ]

    st.dataframe(
        high_rated[
            ["host_name", "neighbourhood",
             "room_type", "review_rate_number", "price"]
        ].head(20),
        use_container_width=True
    )

# ==========================================
# AVAILABILITY ANALYSIS
# ==========================================

with tab5:

    st.subheader("Availability Trends")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.histogram(
            df,
            x="availability_365",
            nbins=30,
            title="Distribution of Airbnb Availability",
            color_discrete_sequence=["#E76F51"]
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        availability = (
            df.groupby("room_type")["availability_365"]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            availability,
            x="room_type",
            y="availability_365",
            title="Average Availability by Room Type"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Most Available Properties")

    st.dataframe(
        df.nlargest(10, "availability_365")[
            ["NAME", "neighbourhood", "availability_365"]
        ],
        use_container_width=True
    )

    st.subheader("Least Available Properties")

    st.dataframe(
        df.nsmallest(10, "availability_365")[
            ["NAME", "neighbourhood", "availability_365"]
        ],
        use_container_width=True
    )

    if "month" in df.columns:
        st.subheader("Monthly Review Trends")

        monthly = (
            df["month"].value_counts()
            .reindex([
                "January", "February", "March", "April",
                "May", "June", "July", "August",
                "September", "October", "November", "December"
            ])
            .dropna()
            .reset_index()
        )

        monthly.columns = ["Month", "Listings"]

        fig = px.bar(
            monthly,
            x="Month",
            y="Listings",
            title="Monthly Listing Review Counts"
        )

        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# DATA CLEANING & OUTLIERS
# ==========================================

with tab6:

    st.subheader("Data Cleaning & Quality")

    col1, col2, col3 = st.columns(3)

    col1.metric("Dataset Rows", len(df))
    col2.metric("Missing Values", int(df.isnull().sum().sum()))
    col3.metric("Duplicate Rows", int(df.duplicated().sum()))

    st.subheader("Missing Values by Column")

    missing_values = (
        df.isnull().sum()
        .reset_index()
    )

    missing_values.columns = ["Column", "Missing Values"]

    st.dataframe(
        missing_values,
        use_container_width=True
    )

    st.subheader("Price Outlier Detection")

    Q1 = df["price"].quantile(0.25)
    Q3 = df["price"].quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    outliers = df[
        (df["price"] < lower)
        | (df["price"] > upper)
    ]

    st.metric("Price Outliers", len(outliers))

    fig = px.box(
        df,
        y="price",
        title="Price Outlier Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Outlier Records")

    st.dataframe(
        outliers[
            ["neighbourhood", "room_type", "price"]
        ].head(50),
        use_container_width=True
    )

    remove_outliers = st.checkbox(
        "Exclude price outliers from downloaded dataset"
    )

    if remove_outliers:
        download_df = df[
            df["price"].between(lower, upper)
        ]
    else:
        download_df = df

    st.subheader("Download Cleaned Dataset")

    csv = download_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Airbnb CSV",
        data=csv,
        file_name="Airbnb_Cleaned_Data.csv",
        mime="text/csv"
    )

    st.subheader("Dataset Preview")

    st.dataframe(
        download_df.head(100),
        use_container_width=True
    )

# ==========================================
# CITY / NEIGHBORHOOD GROUP OVERVIEW
# ==========================================

st.divider()

st.header("📊 Airbnb Market Overview")

city = st.selectbox(
    "Select Neighborhood Group",
    sorted(df["neighbourhood_group"].dropna().unique())
)

ng = df[df["neighbourhood_group"] == city]

tl = ng["NAME"].nunique()
th = ng["host_name"].nunique()
ap = ng["price"].mean()
aa = ng["availability_365"].mean()
nr = ng["number_of_reviews"].sum()

st.subheader(f"Market Overview: {city}")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Total Listings", f"{tl:,}")
c2.metric("Total Hosts", f"{th:,}")
c3.metric("Average Price", f"${ap:,.2f}")
c4.metric("Average Availability", f"{aa:.1f} days")
c5.metric("Total Reviews", f"{nr:,.0f}")

# Top 10 neighborhoods in selected group
tnp = (
    ng.groupby("neighbourhood")["price"]
    .mean()
    .nlargest(10)
    .reset_index()
)

fig = px.bar(
    tnp,
    x="price",
    y="neighbourhood",
    orientation="h",
    title=f"Top 10 Neighborhoods by Average Price - {city}"
)

fig.update_layout(yaxis={"categoryorder": "total ascending"})

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "Airbnb Market Intelligence Dashboard | "
    "Created using Python, Pandas, Plotly and Streamlit"
)
