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
    
    # Memastikan kolom 'hour' dan 'month' ada untuk visualisasi tren
    if 'hour' not in df.columns:
        df['hour'] = df['datetime'].dt.hour
    if 'month' not in df.columns:
        df['month'] = df['datetime'].dt.month
        
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

# Filter dataset berdasarkan rentang waktu di sidebar
main_df = df[(df["datetime"].dt.date >= start_date) & (df["datetime"].dt.date <= end_date)]

# ----------------------------------------
# MAIN PAGE
# ----------------------------------------
st.title("☁️ Beijing Air Quality Dashboard (2013-2017)")
st.markdown("Visualisasi data kualitas udara berdasarkan 12 stasiun pemantauan di Beijing untuk menjawab pertanyaan bisnis inti.")

# Menampilkan Metrik Utama
col1, col2, col3 = st.columns(3)
with col1:
    avg_pm25 = round(main_df['PM2.5'].mean(), 2)
    st.metric("Rata-rata PM2.5 Keseluruhan", value=f"{avg_pm25} µg/m³")
with col2:
    avg_pm10 = round(main_df['PM10'].mean(), 2)
    st.metric("Rata-rata PM10 Keseluruhan", value=f"{avg_pm10} µg/m³")
with col3:
    worst_station = main_df.groupby('station')['PM2.5'].mean().idxmax()
    st.metric("Stasiun Paling Berpolusi (PM2.5)", value=worst_station)

st.markdown("---")

# ----------------------------------------
# VISUALISASI 1: Menjawab Pertanyaan Bisnis 1
# ----------------------------------------
st.subheader("1. Konsentrasi Polutan Tertinggi dan Terendah per Stasiun")
st.markdown("Grafik ini menjawab stasiun mana yang harus menjadi prioritas pengendalian polusi berdasarkan batas aman WHO.")

col_bar1, col_bar2 = st.columns(2)

# Menghitung rata-rata
station_pm = main_df.groupby('station')[['PM2.5', 'PM10']].mean().reset_index()
station_pm25 = station_pm.sort_values(by='PM2.5', ascending=False).reset_index(drop=True)
station_pm10 = station_pm.sort_values(by='PM10', ascending=False).reset_index(drop=True)

with col_bar1:
    fig, ax = plt.subplots(figsize=(8, 6))
    colors_pm25 = ['#d95f02' if i < 3 else ('#1b9e77' if i == len(station_pm25)-1 else '#b3cde3') for i in range(len(station_pm25))]
    sns.barplot(data=station_pm25, x='PM2.5', y='station', palette=colors_pm25, ax=ax)
    ax.axvline(15, color='red', linestyle='--', linewidth=1.5, label='Batas Aman Tahunan WHO (15 µg/m³)')
    ax.set_title("Rata-Rata PM2.5 per Stasiun")
    ax.set_xlabel("PM2.5 (µg/m³)")
    ax.set_ylabel("Stasiun")
    ax.legend(loc="lower right")
    plt.tight_layout()
    st.pyplot(fig)

with col_bar2:
    fig, ax = plt.subplots(figsize=(8, 6))
    colors_pm10 = ['#d95f02' if i < 3 else ('#1b9e77' if i == len(station_pm10)-1 else '#b3cde3') for i in range(len(station_pm10))]
    sns.barplot(data=station_pm10, x='PM10', y='station', palette=colors_pm10, ax=ax)
    ax.axvline(45, color='red', linestyle='--', linewidth=1.5, label='Batas Aman Tahunan WHO (45 µg/m³)')
    ax.set_title("Rata-Rata PM10 per Stasiun")
    ax.set_xlabel("PM10 (µg/m³)")
    ax.set_ylabel("")
    ax.legend(loc="lower right")
    plt.tight_layout()
    st.pyplot(fig)

with st.expander("Lihat Penjelasan Grafik 1"):
    st.write("Berdasarkan grafik di atas, **Dongsi** dan **Wanshouxigong** adalah stasiun dengan rata-rata polusi tertinggi, sedangkan **Dingling** adalah yang terendah. Hampir seluruh stasiun melampaui batas aman tahunan yang ditetapkan oleh WHO.")

st.markdown("---")

# ----------------------------------------
# VISUALISASI 2: Menjawab Pertanyaan Bisnis 2
# ----------------------------------------
st.subheader("2. Tren Fluktuasi PM2.5: Bulanan dan Per Jam (Hourly)")
st.markdown("Grafik ini menjadi acuan waktu peringatan dini untuk pembatasan aktivitas luar ruangan bagi masyarakat.")

col_trend1, col_trend2 = st.columns(2)

with col_trend1:
    monthly_trend = main_df.groupby('month')['PM2.5'].mean().reset_index()
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.lineplot(data=monthly_trend, x='month', y='PM2.5', marker='o', color='#d95f02', linewidth=2.5, ax=ax)
    ax.set_title("Tren Rata-rata PM2.5 Bulanan", fontsize=14)
    ax.set_xlabel("Bulan (1 = Jan, 12 = Des)")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_xticks(range(1, 13))
    ax.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    st.pyplot(fig)

with col_trend2:
    hourly_trend = main_df.groupby('hour')['PM2.5'].mean().reset_index()
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.lineplot(data=hourly_trend, x='hour', y='PM2.5', marker='o', color='#377eb8', linewidth=2.5, ax=ax)
    ax.set_title("Tren Rata-rata PM2.5 Per Jam (Hourly)", fontsize=14)
    ax.set_xlabel("Jam (00:00 - 23:00)")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_xticks(range(0, 24, 2))
    ax.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    st.pyplot(fig)

with st.expander("Lihat Penjelasan Grafik 2"):
    st.write("- **Tren Bulanan**: Konsentrasi polusi memburuk pada musim dingin (Desember - Maret) dan paling rendah di bulan Agustus.\n- **Tren Per Jam**: Polusi mulai meningkat tajam setelah pukul 18:00 dan mencapai puncaknya di malam hari (pukul 21:00 - 23:00). Masyarakat disarankan membatasi aktivitas luar ruangan pada jam-jam tersebut.")

st.markdown("---")

# ----------------------------------------
# VISUALISASI 3: Analisis Lanjutan (Geospatial & Clustering)
# ----------------------------------------
st.subheader("3. Analisis Lanjutan: Peta Geospasial & Kategori AQI")

col_adv1, col_adv2 = st.columns(2)

with col_adv1:
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
    
    # Inisialisasi Peta
    m = folium.Map(location=[40.0, 116.4], zoom_start=9)
    
    for station, coords in station_coords.items():
        pm_val = station_pm25[station_pm25['station'] == station]['PM2.5'].values
        if len(pm_val) > 0:
            pm_val = pm_val[0]
            # Pewarnaan marker
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
            
    st_folium(m, width=500, height=350)

with col_adv2:
    st.markdown("**Distribusi Kategori Kualitas Udara (Binning)**")
    
    # Pastikan kolom AQI_Category ada, jika belum, kita buat secara dinamis
    if 'AQI_Category' not in main_df.columns:
        bins = [0, 15, 35, 75, 500, 1000]
        labels = ['Good', 'Moderate', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
        main_df['AQI_Category'] = pd.cut(main_df['PM2.5'], bins=bins, labels=labels)
        
    aqi_dist = main_df['AQI_Category'].value_counts(normalize=True).reset_index()
    aqi_dist.columns = ['Kategori', 'Persentase']
    aqi_dist['Persentase'] = aqi_dist['Persentase'] * 100
    
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.barplot(x='Persentase', y='Kategori', data=aqi_dist, palette='YlOrRd', ax=ax)
    ax.set_xlabel("Persentase (%)")
    ax.set_ylabel("")
    for i, v in enumerate(aqi_dist['Persentase']):
        ax.text(v + 0.5, i, f'{v:.1f}%', va='center', fontsize=10)
    plt.tight_layout()
    st.pyplot(fig)

st.caption("Copyright © 2026 - Aulia Ulina Simamora - Proyek Analisis Data Dicoding")
