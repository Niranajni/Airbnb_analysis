import io

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Airbnb Market Dashboard",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- CUSTOM STYLE --------------------
st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e8edf5;
        padding: 16px;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    h1, h2, h3 {
        color: #172554;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏡 Airbnb Market Insights")
st.caption(
    "Explore listing locations, prices, hosts, availability, reviews, and price outliers."
)


# -------------------- DATA LOADING AND CLEANING --------------------
@st.cache_data(show_spinner="Reading and preparing your dataset...")
def load_data(file_bytes):
    df = pd.read_csv(io.BytesIO(file_bytes), low_memory=False)

    # Standardize column names
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )

    # Standardize common alternative column names
    df = df.rename(columns={
        "name": "listing_name",
        "neighborhood_group": "neighbourhood_group",
        "neighborhood": "neighbourhood",
        "host_identity_verified": "host_identity_verified"
    })

    # Convert price and service fee to numeric
    for col in ["price", "service_fee"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[$,]", "", regex=True)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convert other numeric columns
    numeric_cols = [
        "number_of_reviews",
        "minimum_nights",
        "availability_365",
        "reviews_per_month",
        "review_rate_number",
        "calculated_host_listings_count",
        "construction_year"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convert review date
    if "last_review" in df.columns:
        df["last_review"] = pd.to_datetime(
            df["last_review"],
            errors="coerce"
        )
        df["review_year"] = df["last_review"].dt.year
        df["review_month"] = df["last_review"].dt.month_name()
    else:
        df["last_review"] = pd.NaT
        df["review_year"] = np.nan
        df["review_month"] = "Unknown"

    # Fill missing text values
    text_defaults = {
        "listing_name": "Unknown Listing",
        "host_name": "Unknown Host",
        "neighbourhood_group": "Unknown",
        "neighbourhood": "Unknown",
        "room_type": "Unknown",
        "country": "Unknown",
        "host_identity_verified": "Unknown",
        "instant_bookable": "Unknown",
        "cancellation_policy": "Unknown"
    }

    for col, default in text_defaults.items():
        if col in df.columns:
            df[col] = (
                df[col]
                .fillna(default)
                .astype(str)
                .str.strip()
            )

    # Add optional columns if missing
    optional_defaults = {
        "host_id": np.nan,
        "number_of_reviews": 0,
        "minimum_nights": np.nan,
        "availability_365": np.nan,
        "review_rate_number": np.nan,
        "service_fee": np.nan,
        "calculated_host_listings_count": np.nan
    }

    for col, default in optional_defaults.items():
        if col not in df.columns:
            df[col] = default

    # Remove duplicate rows
    duplicate_count = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()

    return df, duplicate_count


# -------------------- UPLOAD DATA --------------------
st.sidebar.header("📁 Upload Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Choose Airbnb_Open_Data.csv",
    type=["csv"],
    help="Upload the CSV from your computer. It does not need to be stored on GitHub."
)

if uploaded_file is None:
    st.info(
        "Upload your Airbnb CSV using the button in the left sidebar to open the dashboard."
    )
    st.stop()

try:
    df, duplicate_count = load_data(uploaded_file.getvalue())
except Exception as error:
    st.error(f"Could not read the CSV file: {error}")
    st.stop()

if df.empty:
    st.warning("The uploaded CSV contains no rows.")
    st.stop()

# Required columns for the dashboard
required_columns = ["price", "neighbourhood", "room_type"]
missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error("Missing required columns: " + ", ".join(missing_columns))
    st.write("Columns found in your file:", list(df.columns))
    st.stop()

if df["price"].notna().sum() == 0:
    st.error("The price column contains no valid numeric values.")
    st.stop()

# Ensure optional columns exist
optional_defaults = {
    "neighbourhood_group": "Unknown",
    "host_name": "Unknown Host",
    "host_id": np.nan,
    "listing_name": "Unknown Listing",
    "number_of_reviews": 0,
    "minimum_nights": np.nan,
    "availability_365": np.nan,
    "review_rate_number": np.nan,
    "service_fee": np.nan,
    "calculated_host_listings_count": np.nan,
    "host_identity_verified": "Unknown",
    "review_month": "Unknown"
}

for col, default in optional_defaults.items():
    if col not in df.columns:
        df[col] = default


# -------------------- SIDEBAR FILTERS --------------------
st.sidebar.divider()
st.sidebar.header("🔎 Dashboard Filters")

groups = sorted(
    df["neighbourhood_group"].dropna().astype(str).unique().tolist()
)

selected_groups = st.sidebar.multiselect(
    "Neighbourhood group",
    options=groups,
    default=groups
)

room_types = sorted(
    df["room_type"].dropna().astype(str).unique().tolist()
)

selected_rooms = st.sidebar.multiselect(
    "Room type",
    options=room_types,
    default=room_types
)

price_max = float(df["price"].max())
price_max = max(price_max, 1.0)

price_range = st.sidebar.slider(
    "Price range",
    min_value=0.0,
    max_value=price_max,
    value=(0.0, price_max),
    step=max(price_max / 100, 1.0),
    format="$%.0f"
)

filtered = df[
    df["neighbourhood_group"].astype(str).isin(selected_groups)
    & df["room_type"].astype(str).isin(selected_rooms)
    & df["price"].between(
        price_range[0],
        price_range[1],
        inclusive="both"
    )
].copy()

st.sidebar.caption(f"Showing {len(filtered):,} of {len(df):,} listings")

if filtered.empty:
    st.warning("No listings match the selected filters. Change the sidebar filters.")
    st.stop()


# -------------------- HELPER FUNCTIONS --------------------
def money(value):
    if pd.isna(value):
        return "N/A"
    return f"${value:,.0f}"


def chart_layout(fig, height=420):
    fig.update_layout(
        height=height,
        margin=dict(l=15, r=15, t=55, b=15),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial", size=12, color="#25324b"),
        title_font=dict(size=17, color="#172554"),
        legend_title_text=""
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#edf1f7")
    return fig


# -------------------- KPI ROW --------------------
st.subheader("📌 Market Overview")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Listings", f"{len(filtered):,}")
k2.metric("Unique Hosts", f"{filtered['host_name'].nunique():,}")
k3.metric("Average Price", money(filtered["price"].mean()))

average_availability = filtered["availability_365"].mean()
k4.metric(
    "Average Availability",
    f"{average_availability:.0f} days"
    if pd.notna(average_availability)
    else "N/A"
)

k5.metric(
    "Total Reviews",
    f"{filtered['number_of_reviews'].sum():,.0f}"
)

st.divider()


# -------------------- DASHBOARD TABS --------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📍 Location",
    "💵 Pricing",
    "👤 Hosts",
    "⭐ Reviews",
    "📅 Availability",
    "🧹 Data & Outliers"
])


# ==================== LOCATION ====================
with tab1:
    st.subheader("Location and Listing Analysis")

    left, right = st.columns(2)

    with left:
        top_neighbourhoods = (
            filtered["neighbourhood"]
            .value_counts()
            .head(10)
            .rename_axis("Neighbourhood")
            .reset_index(name="Listings")
        )

        fig = px.bar(
            top_neighbourhoods,
            x="Listings",
            y="Neighbourhood",
            orientation="h",
            title="Top 10 Neighbourhoods by Listings",
            color="Listings",
            color_continuous_scale="Teal"
        )

        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            coloraxis_showscale=False
        )

        st.plotly_chart(
            chart_layout(fig),
            use_container_width=True
        )

    with right:
        room_group = (
            filtered.groupby(
                ["neighbourhood_group", "room_type"]
            )
            .size()
            .reset_index(name="Listings")
        )

        fig = px.bar(
            room_group,
            x="neighbourhood_group",
            y="Listings",
            color="room_type",
            barmode="group",
            title="Room Types Across Neighbourhood Groups",
            labels={
                "neighbourhood_group": "Neighbourhood Group",
                "room_type": "Room Type"
            }
        )

        st.plotly_chart(
            chart_layout(fig),
            use_container_width=True
        )

    st.markdown("#### Neighbourhood Summary")

    location_table = (
        filtered.groupby("neighbourhood")
        .agg(
            Listings=("neighbourhood", "size"),
            Average_Price=("price", "mean"),
            Total_Reviews=("number_of_reviews", "sum")
        )
        .sort_values("Listings", ascending=False)
        .head(15)
        .reset_index()
    )

    st.dataframe(
        location_table.style.format({
            "Average_Price": "${:,.2f}",
            "Total_Reviews": "{:,.0f}"
        }),
        use_container_width=True,
        hide_index=True
    )


# ==================== PRICING ====================
with tab2:
    st.subheader("Pricing Analysis")

    left, right = st.columns(2)

    with left:
        average_room_price = (
            filtered.groupby("room_type", as_index=False)["price"]
            .mean()
            .sort_values("price", ascending=False)
        )

        fig = px.bar(
            average_room_price,
            x="room_type",
            y="price",
            title="Average Price by Room Type",
            color="price",
            color_continuous_scale="Sunset",
            labels={
                "room_type": "Room Type",
                "price": "Average Price"
            }
        )

        fig.update_layout(coloraxis_showscale=False)

        st.plotly_chart(
            chart_layout(fig),
            use_container_width=True
        )

    with right:
        fig = px.histogram(
            filtered.dropna(subset=["price"]),
            x="price",
            nbins=40,
            title="Listing Price Distribution",
            labels={"price": "Price"},
            color_discrete_sequence=["#0f766e"]
        )

        st.plotly_chart(
            chart_layout(fig),
            use_container_width=True
        )

    top_price = (
        filtered.groupby("neighbourhood", as_index=False)["price"]
        .mean()
        .nlargest(10, "price")
    )

    fig = px.bar(
        top_price,
        x="price",
        y="neighbourhood",
        orientation="h",
        title="10 Neighbourhoods with Highest Average Price",
        labels={
            "price": "Average Price",
            "neighbourhood": "Neighbourhood"
        },
        color="price",
        color_continuous_scale="Oranges"
    )

    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=False
    )

    st.plotly_chart(
        chart_layout(fig, 460),
        use_container_width=True
    )

    st.markdown("#### Numeric Correlation")

    correlation_columns = [
        "price",
        "number_of_reviews",
        "minimum_nights",
        "availability_365"
    ]

    correlation = filtered[correlation_columns].corr(numeric_only=True)

    fig = px.imshow(
        correlation,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Correlation Between Price, Reviews, Minimum Nights and Availability"
    )

    st.plotly_chart(
        chart_layout(fig, 430),
        use_container_width=True
    )


# ==================== HOSTS ====================
with tab3:
    st.subheader("Host Analysis")

    left, right = st.columns(2)

    with left:
        top_hosts = (
            filtered.groupby("host_name", as_index=False)
            .agg(
                Listings=("host_name", "size"),
                Average_Price=("price", "mean")
            )
            .nlargest(10, "Listings")
        )

        fig = px.bar(
            top_hosts,
            x="Listings",
            y="host_name",
            orientation="h",
            title="Top 10 Hosts by Number of Listings",
            color="Listings",
            color_continuous_scale="Teal"
        )

        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            coloraxis_showscale=False
        )

        st.plotly_chart(
            chart_layout(fig),
            use_container_width=True
        )

    with right:
        verified_hosts = (
            filtered.groupby("host_identity_verified", dropna=False)
            .agg(
                Average_Price=("price", "mean"),
                Average_Rating=("review_rate_number", "mean"),
                Listings=("host_name", "size")
            )
            .reset_index()
        )

        fig = px.bar(
            verified_hosts,
            x="host_identity_verified",
            y="Average_Price",
            title="Average Price by Host Verification",
            color="host_identity_verified",
            labels={
                "host_identity_verified": "Host Verification",
                "Average_Price": "Average Price"
            }
        )

        st.plotly_chart(
            chart_layout(fig),
            use_container_width=True
        )

    host_reviews = (
        filtered.groupby("host_name", as_index=False)["number_of_reviews"]
        .sum()
        .nlargest(10, "number_of_reviews")
    )

    fig = px.bar(
        host_reviews,
        x="number_of_reviews",
        y="host_name",
        orientation="h",
        title="Top 10 Hosts by Total Reviews",
        labels={
            "number_of_reviews": "Total Reviews",
            "host_name": "Host"
        }
    )

    fig.update_layout(yaxis=dict(autorange="reversed"))

    st.plotly_chart(
        chart_layout(fig, 460),
        use_container_width=True
    )


# ==================== REVIEWS ====================
with tab4:
    st.subheader("Reviews and Customer Preferences")

    left, right = st.columns(2)

    with left:
        room_reviews = (
            filtered.groupby("room_type", as_index=False)["number_of_reviews"]
            .mean()
            .sort_values("number_of_reviews", ascending=False)
        )

        fig = px.bar(
            room_reviews,
            x="room_type",
            y="number_of_reviews",
            title="Average Reviews by Room Type",
            labels={
                "room_type": "Room Type",
                "number_of_reviews": "Average Reviews"
            },
            color="number_of_reviews",
            color_continuous_scale="Blues"
        )

        fig.update_layout(coloraxis_showscale=False)

        st.plotly_chart(
            chart_layout(fig),
            use_container_width=True
        )

    with right:
        room_counts = (
            filtered["room_type"]
            .value_counts()
            .rename_axis("Room Type")
            .reset_index(name="Listings")
        )

        fig = px.pie(
            room_counts,
            names="Room Type",
            values="Listings",
            title="Room Type Share",
            hole=0.48
        )

        st.plotly_chart(
            chart_layout(fig),
            use_container_width=True
        )

    top_review_areas = (
        filtered.groupby("neighbourhood", as_index=False)["number_of_reviews"]
        .sum()
        .nlargest(10, "number_of_reviews")
    )

    fig = px.bar(
        top_review_areas,
        x="number_of_reviews",
        y="neighbourhood",
        orientation="h",
        title="Top 10 Neighbourhoods by Total Reviews",
        labels={
            "number_of_reviews": "Total Reviews",
            "neighbourhood": "Neighbourhood"
        },
        color="number_of_reviews",
        color_continuous_scale="Purples"
    )

    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=False
    )

    st.plotly_chart(
        chart_layout(fig, 460),
        use_container_width=True
    )

    if filtered["review_rate_number"].notna().any():
        high_rated = filtered[
            filtered["review_rate_number"] >= 4.5
        ][[
            "host_name",
            "neighbourhood",
            "room_type",
            "review_rate_number",
            "price"
        ]].head(15)

        st.markdown("#### Highly Rated Listings (4.5 and above)")

        st.dataframe(
            high_rated,
            use_container_width=True,
            hide_index=True
        )


# ==================== AVAILABILITY ====================
with tab5:
    st.subheader("Availability Trends")

    left, right = st.columns(2)

    with left:
        fig = px.histogram(
            filtered.dropna(subset=["availability_365"]),
            x="availability_365",
            nbins=30,
            title="Availability Distribution",
            labels={"availability_365": "Available Days in a Year"},
            color_discrete_sequence=["#7c3aed"]
        )

        st.plotly_chart(
            chart_layout(fig),
            use_container_width=True
        )

    with right:
        availability_counts = (
            filtered["availability_365"]
            .value_counts()
            .sort_index()
            .reset_index()
        )

        availability_counts.columns = ["Available Days", "Listings"]

        fig = px.line(
            availability_counts,
            x="Available Days",
            y="Listings",
            title="Listings by Available Days",
            markers=True,
            color_discrete_sequence=["#e11d48"]
        )

        st.plotly_chart(
            chart_layout(fig),
            use_container_width=True
        )

    most_available = filtered.nlargest(
        10, "availability_365"
    )[[
        "listing_name",
        "neighbourhood",
        "room_type",
        "availability_365",
        "price"
    ]]

    least_available = filtered.nsmallest(
        10, "availability_365"
    )[[
        "listing_name",
        "neighbourhood",
        "room_type",
        "availability_365",
        "price"
    ]]

    left, right = st.columns(2)

    with left:
        st.markdown("#### Most Available Listings")
        st.dataframe(
            most_available,
            use_container_width=True,
            hide_index=True
        )

    with right:
        st.markdown("#### Least Available Listings")
        st.dataframe(
            least_available,
            use_container_width=True,
            hide_index=True
        )

    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    monthly = (
        filtered[filtered["review_month"] != "Unknown"]["review_month"]
        .value_counts()
        .reindex(month_order, fill_value=0)
        .rename_axis("Month")
        .reset_index(name="Records")
    )

    fig = px.bar(
        monthly,
        x="Month",
        y="Records",
        title="Records by Month of Last Review",
        labels={"Records": "Number of Records"},
        color="Records",
        color_continuous_scale="Teal"
    )

    fig.update_layout(coloraxis_showscale=False)

    st.plotly_chart(
        chart_layout(fig),
        use_container_width=True
    )

    st.caption(
        "This chart counts records by the month of their last review. "
        "It does not represent the number of newly created listings."
    )


# ==================== DATA AND OUTLIERS ====================
with tab6:
    st.subheader("Data Quality and Price Outliers")

    q1 = filtered["price"].quantile(0.25)
    q3 = filtered["price"].quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers = filtered[
        (filtered["price"] < lower_bound)
        | (filtered["price"] > upper_bound)
    ].copy()

    a, b, c, d = st.columns(4)

    a.metric("Rows After Filtering", f"{len(filtered):,}")
    b.metric("Duplicate Rows Removed", f"{duplicate_count:,}")
    c.metric("Missing Cells", f"{df.isna().sum().sum():,}")
    d.metric("Price Outliers", f"{len(outliers):,}")

    fig = px.box(
        filtered.dropna(subset=["price"]),
        x="price",
        title="Price Outliers (IQR Box Plot)",
        points="outliers",
        color_discrete_sequence=["#0f766e"]
    )

    st.plotly_chart(
        chart_layout(fig),
        use_container_width=True
    )

    st.markdown("#### Example Price Outliers")

    outlier_columns = [
        "listing_name",
        "neighbourhood",
        "room_type",
        "price"
    ]

    st.dataframe(
        outliers[outlier_columns]
        .sort_values("price", ascending=False)
        .head(20),
        use_container_width=True,
        hide_index=True
    )

    with st.expander("View missing values by column"):
        missing_values = (
            df.isna()
            .sum()
            .rename("Missing Values")
            .reset_index()
        )

        missing_values.columns = ["Column", "Missing Values"]

        st.dataframe(
            missing_values,
            use_container_width=True,
            hide_index=True
        )

    with st.expander("View cleaned dataset"):
        st.dataframe(
            filtered.head(500),
            use_container_width=True,
            hide_index=True
        )

        st.caption("Showing up to the first 500 rows for faster display.")

    csv_data = filtered.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download Filtered Data as CSV",
        data=csv_data,
        file_name="airbnb_filtered_data.csv",
        mime="text/csv"
    )


st.caption("Airbnb Market Insights Dashboard • Built with Streamlit and Plotly")
