import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import folium
from streamlit_folium import st_folium

# Konfigurasi Halaman
st.set_page_config(page_title="Beijing Air Quality Dashboard", page_icon="☁️", layout="wide")
sns.set_theme(style="whitegrid")

# Helper function untuk memuat data
@st.cache_data
def load_data():
    # Mengambil direktori tempat file dashboard.py ini berada
    current_dir = os.path.dirname(__file__)
    
    # Menggabungkan path direktori dengan nama file CSV
    file_path = os.path.join(current_dir, "main_data.csv")
    
    df = pd.read_csv(file_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df

df = load_data()

# ----------------------------------------
# SIDEBAR
# ----------------------------------------
with st.sidebar:
    st.title("☁️ Air Quality Beijing")
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208977.png", width=150)
    st.write("Dashboard Analisis Kualitas Udara (2013-2017)")
    
    # Filter Rentang Waktu
    min_date = df["datetime"].min().date()
    max_date = df["datetime"].max().date()
    
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# Filter dataset berdasarkan sidebar
main_df = df[(df["datetime"].dt.date >= start_date) & (df["datetime"].dt.date <= end_date)]

# ----------------------------------------
# MAIN PAGE
# ----------------------------------------
st.title("☁️ Beijing Air Quality Dashboard (2013-2017)")
st.markdown("Visualisasi data kualitas udara berdasarkan 12 stasiun pemantauan di Beijing.")

# Menampilkan Metrik Utama
col1, col2, col3 = st.columns(3)
with col1:
    avg_pm25 = round(main_df['PM2.5'].mean(), 2)
    st.metric("Rata-rata PM2.5 (µg/m³)", value=avg_pm25)
with col2:
    avg_pm10 = round(main_df['PM10'].mean(), 2)
    st.metric("Rata-rata PM10 (µg/m³)", value=avg_pm10)
with col3:
    worst_station = main_df.groupby('station')['PM2.5'].mean().idxmax()
    st.metric("Stasiun Paling Berpolusi", value=worst_station)

st.markdown("---")

# ----------------------------------------
# VISUALISASI 1: Perbandingan Stasiun (Bar Chart)
# ----------------------------------------
st.subheader("1. Konsentrasi Polutan Tertinggi dan Terendah per Stasiun")

col_bar1, col_bar2 = st.columns(2)

station_pm = main_df.groupby('station')[['PM2.5', 'PM10']].mean().reset_index()
station_pm25 = station_pm.sort_values(by='PM2.5', ascending=False).reset_index(drop=True)
station_pm10 = station_pm.sort_values(by='PM10', ascending=False).reset_index(drop=True)

with col_bar1:
    fig, ax = plt.subplots(figsize=(8, 6))
    colors_pm25 = ['#d95f02' if i < 3 else ('#1b9e77' if i == len(station_pm25)-1 else '#b3cde3') for i in range(len(station_pm25))]
    sns.barplot(data=station_pm25, x='PM2.5', y='station', palette=colors_pm25, ax=ax)
    ax.axvline(15, color='red', linestyle='--', linewidth=1.5, label='Batas Aman WHO (15)')
    ax.set_title("Rata-Rata PM2.5 per Stasiun")
    ax.set_xlabel("PM2.5 (µg/m³)")
    ax.set_ylabel("")
    ax.legend(loc="lower right")
    st.pyplot(fig)

with col_bar2:
    fig, ax = plt.subplots(figsize=(8, 6))
    colors_pm10 = ['#d95f02' if i < 3 else ('#1b9e77' if i == len(station_pm10)-1 else '#b3cde3') for i in range(len(station_pm10))]
    sns.barplot(data=station_pm10, x='PM10', y='station', palette=colors_pm10, ax=ax)
    ax.axvline(45, color='red', linestyle='--', linewidth=1.5, label='Batas Aman WHO (45)')
    ax.set_title("Rata-Rata PM10 per Stasiun")
    ax.set_xlabel("PM10 (µg/m³)")
    ax.set_ylabel("")
    ax.legend(loc="lower right")
    st.pyplot(fig)

st.markdown("---")

# ----------------------------------------
# VISUALISASI 2: Tren Bulanan (Line Chart)
# ----------------------------------------
st.subheader("2. Pola Musiman PM2.5 vs Curah Hujan (RAIN)")

monthly_trend = main_df.groupby('month')[['PM2.5', 'RAIN']].mean().reset_index()

fig, ax1 = plt.subplots(figsize=(12, 5))
ax2 = ax1.twinx()

sns.lineplot(data=monthly_trend, x='month', y='PM2.5', marker='o', color='#d95f02', linewidth=2.5, ax=ax1, label='PM2.5')
sns.barplot(data=monthly_trend, x='month', y='RAIN', color='#b3cde3', alpha=0.6, ax=ax2, label='Curah Hujan (RAIN)')

ax1.set_xlabel('Bulan (1 = Jan, 12 = Des)')
ax1.set_ylabel('Rata-rata PM2.5 (µg/m³)', color='#d95f02')
ax2.set_ylabel('Rata-rata Curah Hujan (mm)', color='#377eb8')
ax1.set_xticks(range(1, 13))

st.pyplot(fig)

st.markdown("---")

# ----------------------------------------
# VISUALISASI 3: Analisis Lanjutan (Clustering & Geospatial)
# ----------------------------------------
st.subheader("3. Analisis Lanjutan: Clustering (Binning) & Geospatial")

col_adv1, col_adv2 = st.columns(2)

with col_adv1:
    st.markdown("**Distribusi Kategori Kualitas Udara (AQI Category)**")
    aqi_dist = main_df['AQI_Category'].value_counts(normalize=True).reset_index()
    aqi_dist.columns = ['Kategori', 'Persentase']
    aqi_dist['Persentase'] = aqi_dist['Persentase'] * 100
    
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.barplot(x='Persentase', y='Kategori', data=aqi_dist, palette='YlOrRd', ax=ax)
    ax.set_xlabel("Persentase (%)")
    ax.set_ylabel("")
    for i, v in enumerate(aqi_dist['Persentase']):
        ax.text(v + 0.5, i, f'{v:.1f}%', va='center', fontsize=10)
    st.pyplot(fig)

with col_adv2:
    st.markdown("**Peta Geospasial Stasiun Pemantauan di Beijing**")
    
    # Koordinat manual stasiun
    station_coords = {
        'Aotizhongxin': [39.982, 116.397], 'Changping': [40.217, 116.230],
        'Dingling': [40.292, 116.220], 'Dongsi': [39.929, 116.417],
        'Guanyuan': [39.929, 116.339], 'Gucheng': [39.914, 116.184],
        'Huairou': [40.328, 116.628], 'Nongzhanguan': [39.937, 116.461],
        'Shunyi': [40.127, 116.655], 'Tiantan': [39.886, 116.407],
        'Wanliu': [39.987, 116.287], 'Wanshouxigong': [39.878, 116.352]
    }
    
    # Inisialisasi Peta berpusat di Beijing
    m = folium.Map(location=[40.0, 116.4], zoom_start=9)
    
    for station, coords in station_coords.items():
        pm_val = station_pm25[station_pm25['station'] == station]['PM2.5'].values
        if len(pm_val) > 0:
            pm_val = pm_val[0]
            # Pewarnaan marker berdasarkan tingkat keparahan PM2.5
            color = 'darkred' if pm_val > 80 else 'orange' if pm_val > 70 else 'green'
            
            folium.CircleMarker(
                location=coords,
                radius=pm_val / 5,
                popup=f"{station}: {pm_val:.1f} µg/m³",
                tooltip=station,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7
            ).add_to(m)
            
    st_folium(m, width=500, height=400)

st.caption("Copyright © 2026 - Proyek Analisis Data Dicoding")