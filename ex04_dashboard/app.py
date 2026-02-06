import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from db import read_sql

# ─────────────────────────── Configuration ───────────────────────────
st.set_page_config(
    page_title="NYC Yellow Taxi — Dashboard",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Couleur thème taxi NYC
TAXI_YELLOW = "#F7C948"
TAXI_DARK = "#1B1B1B"
PALETTE = ["#F7C948", "#F2A900", "#E8871E", "#D9534F", "#5BC0DE", "#5CB85C", "#428BCA", "#8E44AD"]

# Css custom pour les metrics et titres
st.markdown("""
<style>
    .stMetric > div {border-left: 4px solid #F7C948; padding-left: 12px;}
    div[data-testid="stMetricValue"] {font-size: 1.6rem; font-weight: 700;}
    div[data-testid="stMetricLabel"] {font-size: 0.9rem; color: #888;}
    h1 {color: #F7C948 !important;}
</style>
""", unsafe_allow_html=True)

st.title("🚕 NYC Yellow Taxi — Dashboard Analytique")

# Sidebar : connexion + filtres
try:
    _ = read_sql("SELECT 1 AS ok;")
    st.sidebar.success("PostgreSQL connecté")
except Exception as e:
    st.sidebar.error("PostgreSQL indisponible")
    st.sidebar.exception(e)
    st.stop()

st.sidebar.header("🔍 Filtres")

# Charger les mois disponibles dynamiquement
months_df = read_sql("""
    SELECT DISTINCT to_char(tpep_pickup_datetime, 'YYYY-MM') AS m
    FROM fact_trips
    ORDER BY m;
""")
available_months = months_df["m"].tolist() if not months_df.empty else ["2025-01"]

selected_months = st.sidebar.multiselect(
    "Mois",
    options=available_months,
    default=available_months,
    help="Sélectionnez un ou plusieurs mois"
)

if not selected_months:
    st.warning("Sélectionnez au moins un mois.")
    st.stop()

# Build SQL filter
month_list = tuple(selected_months)
month_filter = "to_char(tpep_pickup_datetime, 'YYYY-MM') IN %(months)s"
params = {"months": month_list}

st.sidebar.markdown("---")
st.sidebar.caption(f"📊 {len(selected_months)} mois sélectionné(s)")

#  1. KPI principaux

kpi = read_sql(f"""
    SELECT
        COUNT(*)             AS nb_trips,
        SUM(total_amount)    AS sum_total,
        AVG(total_amount)    AS avg_total,
        AVG(trip_distance)   AS avg_distance,
        AVG(tip_amount)      AS avg_tip,
        SUM(tip_amount)      AS sum_tip,
        AVG(passenger_count) AS avg_passengers
    FROM fact_trips
    WHERE {month_filter};
""", params=params)

k = kpi.iloc[0]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🚖 Courses", f"{int(k['nb_trips']):,}".replace(",", " "))
c2.metric("💰 CA Total", f"${float(k['sum_total'] or 0):,.0f}".replace(",", " "))
c3.metric("🧾 Panier Moyen", f"${float(k['avg_total'] or 0):.2f}")
c4.metric("📏 Distance Moy.", f"{float(k['avg_distance'] or 0):.2f} mi")
c5.metric("💵 Tip Moyen", f"${float(k['avg_tip'] or 0):.2f}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
#  2) LIGNE 1 : CA par jour + Distribution horaire
# ═══════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📈 Chiffre d'affaires par jour")
    daily = read_sql(f"""
        SELECT
            date(tpep_pickup_datetime) AS day,
            SUM(total_amount)          AS revenue,
            COUNT(*)                   AS trips
        FROM fact_trips
        WHERE {month_filter}
        GROUP BY 1 ORDER BY 1;
    """, params=params)

    fig = px.area(
        daily, x="day", y="revenue",
        labels={"day": "Date", "revenue": "CA ($)"},
        color_discrete_sequence=[TAXI_YELLOW],
    )
    fig.update_traces(
        line=dict(width=2, color=TAXI_YELLOW),
        fillcolor="rgba(247,201,72,0.2)",
    )
    fig.update_layout(
        hovermode="x unified",
        xaxis_title="",
        yaxis_title="CA ($)",
        height=380,
        margin=dict(l=20, r=20, t=10, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🕐 Distribution horaire des courses")
    hourly = read_sql(f"""
        SELECT
            EXTRACT(HOUR FROM tpep_pickup_datetime)::int AS hour,
            COUNT(*)                                      AS trips
        FROM fact_trips
        WHERE {month_filter}
        GROUP BY 1 ORDER BY 1;
    """, params=params)

    fig = go.Figure(go.Bar(
        x=hourly["hour"],
        y=hourly["trips"],
        marker_color=[TAXI_YELLOW if 7 <= h <= 20 else "#555" for h in hourly["hour"]],
        hovertemplate="<b>%{x}h</b><br>%{y:,} courses<extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(title="Heure", dtick=2),
        yaxis=dict(title="Courses"),
        height=380,
        margin=dict(l=20, r=20, t=10, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


#  3. Ligne 2 : Top zones + Répartition paiements
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📍 Top 10 zones de pickup")
    top_pu = read_sql(f"""
        SELECT
            l.zone      AS pickup_zone,
            l.borough   AS borough,
            COUNT(*)    AS trips,
            SUM(f.total_amount) AS revenue
        FROM fact_trips f
        JOIN dim_location l ON l.location_id = f.pu_location_id
        WHERE {month_filter.replace('tpep_pickup_datetime', 'f.tpep_pickup_datetime')}
        GROUP BY 1, 2
        ORDER BY trips DESC
        LIMIT 10;
    """, params=params)

    fig = px.bar(
        top_pu, x="trips", y="pickup_zone",
        orientation="h",
        color="borough",
        color_discrete_sequence=PALETTE,
        labels={"trips": "Courses", "pickup_zone": "", "borough": "Borough"},
        hover_data={"revenue": ":,.0f"},
    )
    fig.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        height=420,
        margin=dict(l=20, r=20, t=10, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("💳 Répartition des paiements")
    pay = read_sql(f"""
        SELECT
            p.payment_name AS payment,
            COUNT(*)       AS trips,
            SUM(f.total_amount) AS revenue
        FROM fact_trips f
        JOIN dim_payment_type p ON p.payment_type_id = f.payment_type_id
        WHERE {month_filter.replace('tpep_pickup_datetime', 'f.tpep_pickup_datetime')}
        GROUP BY 1
        ORDER BY trips DESC;
    """, params=params)

    fig = px.pie(
        pay, values="trips", names="payment",
        color_discrete_sequence=PALETTE,
        hole=0.45,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>%{value:,} courses<br>%{percent}<extra></extra>",
    )
    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=10, b=20),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


#  4. Ligne 3 : CA par vendor + Distance vs Montant
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🏢 CA & Courses par Vendor")
    vendor = read_sql(f"""
        SELECT
            COALESCE(v.vendor_name, 'Unknown') AS vendor,
            SUM(f.total_amount) AS revenue,
            COUNT(*) AS trips,
            AVG(f.total_amount) AS avg_fare
        FROM fact_trips f
        LEFT JOIN dim_vendor v ON v.vendor_id = f.vendor_id
        WHERE {month_filter.replace('tpep_pickup_datetime', 'f.tpep_pickup_datetime')}
        GROUP BY 1 ORDER BY revenue DESC;
    """, params=params)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="CA ($)",
        x=vendor["vendor"], y=vendor["revenue"],
        marker_color=TAXI_YELLOW,
        yaxis="y",
        hovertemplate="<b>%{x}</b><br>CA: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        name="Courses",
        x=vendor["vendor"], y=vendor["trips"],
        mode="markers+text",
        marker=dict(size=14, color="#5BC0DE"),
        text=vendor["trips"].apply(lambda x: f"{x:,}"),
        textposition="top center",
        yaxis="y2",
        hovertemplate="<b>%{x}</b><br>Courses: %{y:,}<extra></extra>",
    ))
    fig.update_layout(
        yaxis=dict(title="CA ($)", side="left"),
        yaxis2=dict(title="Courses", side="right", overlaying="y"),
        height=380,
        margin=dict(l=20, r=20, t=10, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("📊 Tarif moyen par tranche de distance")
    dist_fare = read_sql(f"""
        SELECT
            CASE
                WHEN trip_distance < 1  THEN '0-1 mi'
                WHEN trip_distance < 3  THEN '1-3 mi'
                WHEN trip_distance < 5  THEN '3-5 mi'
                WHEN trip_distance < 10 THEN '5-10 mi'
                WHEN trip_distance < 20 THEN '10-20 mi'
                ELSE '20+ mi'
            END AS dist_bucket,
            CASE
                WHEN trip_distance < 1  THEN 1
                WHEN trip_distance < 3  THEN 2
                WHEN trip_distance < 5  THEN 3
                WHEN trip_distance < 10 THEN 4
                WHEN trip_distance < 20 THEN 5
                ELSE 6
            END AS sort_key,
            AVG(total_amount) AS avg_fare,
            COUNT(*)          AS trips
        FROM fact_trips
        WHERE {month_filter}
          AND trip_distance > 0 AND trip_distance < 100
          AND total_amount > 0  AND total_amount < 500
        GROUP BY 1, 2
        ORDER BY sort_key;
    """, params=params)

    fig = px.bar(
        dist_fare, x="dist_bucket", y="avg_fare",
        color="avg_fare",
        color_continuous_scale=["#5CB85C", TAXI_YELLOW, "#D9534F"],
        labels={"dist_bucket": "Distance", "avg_fare": "Tarif moy. ($)"},
        text_auto=".2f",
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Moy: $%{y:.2f}<br>%{customdata[0]:,} courses<extra></extra>",
        customdata=dist_fare[["trips"]].values,
    )
    fig.update_layout(
        coloraxis_showscale=False,
        height=380,
        margin=dict(l=20, r=20, t=10, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


#  5. Ligne 4 : Heatmap jour x heure + Top dropoff
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("🔥 Heatmap des courses (jour de la semaine × heure)")
    heatmap = read_sql(f"""
        SELECT
            EXTRACT(DOW FROM tpep_pickup_datetime)::int  AS dow,
            EXTRACT(HOUR FROM tpep_pickup_datetime)::int AS hour,
            COUNT(*)                                      AS trips
        FROM fact_trips
        WHERE {month_filter}
        GROUP BY 1, 2;
    """, params=params)

    day_names = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"]
    pivot = heatmap.pivot_table(index="dow", columns="hour", values="trips", fill_value=0)
    pivot = pivot.reindex(range(7), fill_value=0)
    pivot.index = [day_names[i] for i in pivot.index]
    # Reorder Lun->Dim
    order = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    pivot = pivot.reindex([d for d in order if d in pivot.index])

    fig = px.imshow(
        pivot,
        color_continuous_scale=["#1B1B1B", TAXI_YELLOW, "#D9534F"],
        labels={"x": "Heure", "y": "Jour", "color": "Courses"},
        aspect="auto",
    )
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=10, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🏁 Top 10 zones de dropoff")
    top_do = read_sql(f"""
        SELECT
            l.zone    AS dropoff_zone,
            l.borough AS borough,
            COUNT(*)  AS trips
        FROM fact_trips f
        JOIN dim_location l ON l.location_id = f.do_location_id
        WHERE {month_filter.replace('tpep_pickup_datetime', 'f.tpep_pickup_datetime')}
        GROUP BY 1, 2
        ORDER BY trips DESC
        LIMIT 10;
    """, params=params)

    fig = px.bar(
        top_do, x="trips", y="dropoff_zone",
        orientation="h",
        color="borough",
        color_discrete_sequence=PALETTE,
        labels={"trips": "Courses", "dropoff_zone": ""},
    )
    fig.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        height=350,
        margin=dict(l=20, r=20, t=10, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)


#  6. Ligne 5 : Comparaison mensuelle
if len(selected_months) > 1:
    st.subheader("📅 Comparaison mensuelle")
    monthly = read_sql(f"""
        SELECT
            to_char(tpep_pickup_datetime, 'YYYY-MM') AS month,
            COUNT(*)             AS trips,
            SUM(total_amount)    AS revenue,
            AVG(total_amount)    AS avg_fare,
            AVG(trip_distance)   AS avg_dist,
            AVG(tip_amount)      AS avg_tip
        FROM fact_trips
        WHERE {month_filter}
        GROUP BY 1 ORDER BY 1;
    """, params=params)

    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        fig = px.bar(
            monthly, x="month", y="trips",
            color_discrete_sequence=[TAXI_YELLOW],
            labels={"month": "Mois", "trips": "Courses"},
            text_auto=",",
        )
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20), title="Courses")
        st.plotly_chart(fig, use_container_width=True)

    with mc2:
        fig = px.bar(
            monthly, x="month", y="revenue",
            color_discrete_sequence=["#F2A900"],
            labels={"month": "Mois", "revenue": "CA ($)"},
            text_auto=",.0f",
        )
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20), title="Chiffre d'affaires")
        st.plotly_chart(fig, use_container_width=True)

    with mc3:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Tarif moy.", x=monthly["month"], y=monthly["avg_fare"], marker_color="#5BC0DE"))
        fig.add_trace(go.Bar(name="Tip moy.", x=monthly["month"], y=monthly["avg_tip"], marker_color="#5CB85C"))
        fig.update_layout(
            barmode="group", height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            title="Tarifs & Tips moyens",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)


#  7. Table échantillon
with st.expander("🔎 Voir un échantillon de trajets (50 lignes)"):
    sample = read_sql(f"""
        SELECT
            f.trip_id,
            f.tpep_pickup_datetime  AS pickup,
            f.tpep_dropoff_datetime AS dropoff,
            f.passenger_count       AS pax,
            f.trip_distance         AS distance,
            f.total_amount          AS total,
            f.tip_amount            AS tip,
            pu.zone                 AS pickup_zone,
            dz.zone                 AS dropoff_zone,
            p.payment_name          AS payment,
            v.vendor_name           AS vendor
        FROM fact_trips f
        LEFT JOIN dim_location pu ON pu.location_id = f.pu_location_id
        LEFT JOIN dim_location dz ON dz.location_id = f.do_location_id
        LEFT JOIN dim_payment_type p ON p.payment_type_id = f.payment_type_id
        LEFT JOIN dim_vendor v ON v.vendor_id = f.vendor_id
        WHERE {month_filter.replace('tpep_pickup_datetime', 'f.tpep_pickup_datetime')}
        ORDER BY f.tpep_pickup_datetime
        LIMIT 50;
    """, params=params)
    st.dataframe(sample, use_container_width=True, height=400)

# 8. Footer
st.markdown("---")
st.caption("🚕 NYC Yellow Taxi Analytics — Projet Big Data CY Tech 2025")
