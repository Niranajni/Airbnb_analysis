import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re

st.set_page_config(
    page_title="Airbnb Data Analysis",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Airbnb Data Analysis Dashboard")
st.write("Explore Airbnb listings using dropdown filters and interactive charts.")


# -------------------- DATA LOADING --------------------

@st.cache_data
def load_data(file_bytes):
    df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")

    # Standardize column names
    df.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower()).strip("_")
        for col in df.columns
    ]

    # Rename common Airbnb dataset columns
    rename_columns = {
        "name": "listing_name",
        "host_name": "host_name",
        "host_id": "host_id",
        "neighbourhood_group": "neighbourhood_group",
        "neighborhood_group": "neighbourhood_group",
        "neighbourhood": "neighbourhood",
        "neighborhood": "neighbourhood",
        "room_type": "room_type",
        "price": "price",
        "service_fee": "service_fee",
        "number_of_reviews": "number_of_reviews",
        "reviews_per_month": "reviews_per_month",
        "review_rate_number": "review_rate_number",
        "availability_365": "availability_365",
        "calculated_host_listings_count": "calculated_host_listings_count",
        "minimum_nights": "minimum_nights",
        "host_identity_verified": "host_identity_verified",
        "instant_bookable": "instant_bookable",
        "last_review": "last_review",
        "country": "country"
    }

    df = df.rename(columns=rename_columns)

    # Clean common numeric columns
    numeric_columns = [
        "price",
        "service_fee",
        "number_of_reviews",
        "reviews_per_month",
        "review_rate_number",
        "availability_365",
        "calculated_host_listings_count",
        "minimum_nights",
        "host_id"
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

    # Clean date column
    if "last_review" in df.columns:
        df["last_review"] = pd.to_datetime(
            df["last_review"], errors="coerce"
        )

    # Remove duplicate rows
    df = df.drop_duplicates()

    return df


uploaded_file = st.file_uploader(
    "Upload your Airbnb CSV file",
    type=["csv"]
)

if uploaded_file is None:
    st.info("Upload your Airbnb CSV file to start the dashboard.")
    st.stop()

try:
    df = load_data(uploaded_file.getvalue())
except Exception as e:
    st.error(f"Unable to read the file: {e}")
    st.stop()

if df.empty:
    st.error("The uploaded file is empty.")
    st.stop()


# -------------------- SIDEBAR FILTERS --------------------

st.sidebar.header("🔎 Filter Listings")

filtered_df = df.copy()


def add_all_dropdown(data, column, label):
    """Show a dropdown with an All option when the column exists."""
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

    choice = st.sidebar.selectbox(label, ["All"] + values)

    if choice != "All":
        data = data[data[column].astype(str) == choice]

    return data


filtered_df = add_all_dropdown(
    filtered_df, "neighbourhood_group", "Select City / Neighbourhood Group"
)

filtered_df = add_all_dropdown(
    filtered_df, "neighbourhood", "Select Neighbourhood"
)

filtered_df = add_all_dropdown(
    filtered_df, "room_type", "Select Room Type"
)

filtered_df = add_all_dropdown(
    filtered_df, "host_identity_verified", "Host Identity Verified"
)

filtered_df = add_all_dropdown(
    filtered_df, "instant_bookable", "Instant Bookable"
)


# Price range dropdown/slider
if "price" in filtered_df.columns and filtered_df["price"].notna().any():
    min_price = float(filtered_df["price"].min())
    max_price = float(filtered_df["price"].max())

    if min_price < max_price:
        price_range = st.sidebar.slider(
            "Select Price Range",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price)
        )

        filtered_df = filtered_df[
            filtered_df["price"].between(price_range[0], price_range[1])
        ]


# -------------------- TOP METRICS --------------------

st.subheader("📊 Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Listings", f"{len(filtered_df):,}")

if "price" in filtered_df.columns:
    col2.metric(
        "Average Price",
        f"${filtered_df['price'].mean():,.2f}"
        if filtered_df["price"].notna().any()
        else "N/A"
    )
else:
    col2.metric("Average Price", "N/A")

if "number_of_reviews" in filtered_df.columns:
    col3.metric(
        "Total Reviews",
        f"{filtered_df['number_of_reviews'].sum():,.0f}"
    )
else:
    col3.metric("Total Reviews", "N/A")

if "availability_365" in filtered_df.columns:
    col4.metric(
        "Average Availability",
        f"{filtered_df['availability_365'].mean():.1f} days"
        if filtered_df["availability_365"].notna().any()
        else "N/A"
    )
else:
    col4.metric("Average Availability", "N/A")


# -------------------- ANALYSIS DROPDOWN --------------------

st.divider()

analysis = st.selectbox(
    "Choose an Analysis",
    [
        "Location Analysis",
        "Pricing Analysis",
        "Host Analysis",
        "Reviews Analysis",
        "Availability Analysis",
        "View Dataset"
    ]
)

st.subheader(analysis)


# -------------------- LOCATION ANALYSIS --------------------

if analysis == "Location Analysis":

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

        if not location_counts.empty:
            fig = px.bar(
                location_counts,
                x="Neighbourhood",
                y="Listings",
                title="Top 15 Neighbourhoods by Number of Listings",
                color="Listings"
            )
            st.plotly_chart(fig, use_container_width=True)

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
            title="Listings by Room Type"
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
            title="Listings by Neighbourhood Group",
            color="Listings"
        )
        st.plotly_chart(fig, use_container_width=True)


# -------------------- PRICING ANALYSIS --------------------

elif analysis == "Pricing Analysis":

    if "price" in filtered_df.columns:
        price_data = filtered_df.dropna(subset=["price"])

        if not price_data.empty:
            fig = px.histogram(
                price_data,
                x="price",
                nbins=40,
                title="Distribution of Listing Prices",
                labels={"price": "Price"}
            )
            st.plotly_chart(fig, use_container_width=True)

        if "neighbourhood_group" in filtered_df.columns:
            avg_price = (
                filtered_df.groupby("neighbourhood_group", dropna=True)["price"]
                .mean()
                .reset_index()
                .sort_values("price", ascending=False)
            )
            avg_price.columns = ["Neighbourhood Group", "Average Price"]

            fig = px.bar(
                avg_price,
                x="Neighbourhood Group",
                y="Average Price",
                title="Average Price by Neighbourhood Group",
                color="Average Price"
            )
            st.plotly_chart(fig, use_container_width=True)

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
                title="Average Price by Room Type",
                color="Average Price"
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("The uploaded file does not contain a price column.")


# -------------------- HOST ANALYSIS --------------------

elif analysis == "Host Analysis":

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
            title="Top 10 Hosts by Number of Listings",
            labels={"host_id": "Host ID"},
            color="Listings"
        )
        st.plotly_chart(fig, use_container_width=True)

    if (
        "host_identity_verified" in filtered_df.columns
        and "price" in filtered_df.columns
    ):
        verified_price = (
            filtered_df.groupby("host_identity_verified", dropna=True)["price"]
            .mean()
            .reset_index()
        )
        verified_price.columns = ["Host Identity Verified", "Average Price"]

        fig = px.bar(
            verified_price,
            x="Host Identity Verified",
            y="Average Price",
            title="Average Price by Host Verification",
            color="Average Price"
        )
        st.plotly_chart(fig, use_container_width=True)

    if (
        "host_identity_verified" in filtered_df.columns
        and "number_of_reviews" in filtered_df.columns
    ):
        verified_reviews = (
            filtered_df.groupby("host_identity_verified", dropna=True)[
                "number_of_reviews"
            ]
            .mean()
            .reset_index()
        )
        verified_reviews.columns = [
            "Host Identity Verified",
            "Average Number of Reviews"
        ]

        fig = px.bar(
            verified_reviews,
            x="Host Identity Verified",
            y="Average Number of Reviews",
            title="Average Reviews by Host Verification",
            color="Average Number of Reviews"
        )
        st.plotly_chart(fig, use_container_width=True)


# -------------------- REVIEWS ANALYSIS --------------------

elif analysis == "Reviews Analysis":

    if "number_of_reviews" in filtered_df.columns:
        review_data = filtered_df.dropna(subset=["number_of_reviews"])

        fig = px.histogram(
            review_data,
            x="number_of_reviews",
            nbins=40,
            title="Distribution of Number of Reviews"
        )
        st.plotly_chart(fig, use_container_width=True)

    if (
        "room_type" in filtered_df.columns
        and "number_of_reviews" in filtered_df.columns
    ):
        room_reviews = (
            filtered_df.groupby("room_type", dropna=True)["number_of_reviews"]
            .mean()
            .reset_index()
        )
        room_reviews.columns = ["Room Type", "Average Number of Reviews"]

        fig = px.bar(
            room_reviews,
            x="Room Type",
            y="Average Number of Reviews",
            title="Average Reviews by Room Type",
            color="Average Number of Reviews"
        )
        st.plotly_chart(fig, use_container_width=True)

    if (
        "neighbourhood" in filtered_df.columns
        and "number_of_reviews" in filtered_df.columns
    ):
        neighbourhood_reviews = (
            filtered_df.groupby("neighbourhood", dropna=True)["number_of_reviews"]
            .sum()
            .sort_values(ascending=False)
            .head(15)
            .reset_index()
        )
        neighbourhood_reviews.columns = ["Neighbourhood", "Total Reviews"]

        fig = px.bar(
            neighbourhood_reviews,
            x="Neighbourhood",
            y="Total Reviews",
            title="Top 15 Neighbourhoods by Total Reviews",
            color="Total Reviews"
        )
        st.plotly_chart(fig, use_container_width=True)


# -------------------- AVAILABILITY ANALYSIS --------------------

elif analysis == "Availability Analysis":

    if "availability_365" in filtered_df.columns:
        availability_data = filtered_df.dropna(subset=["availability_365"])

        fig = px.histogram(
            availability_data,
            x="availability_365",
            nbins=30,
            title="Distribution of Availability (Days per Year)"
        )
        st.plotly_chart(fig, use_container_width=True)

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
                title="Average Availability by Room Type",
                color="Average Availability"
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("The uploaded file does not contain an availability column.")


# -------------------- VIEW DATASET --------------------

elif analysis == "View Dataset":

    st.write("Filtered dataset")
    st.dataframe(filtered_df, use_container_width=True)

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv_data,
        file_name="filtered_airbnb_data.csv",
        mime="text/csv"
    )


# -------------------- FOOTER --------------------

st.caption(
    "Airbnb Data Analysis Dashboard | Use the sidebar dropdowns to filter listings."
)
