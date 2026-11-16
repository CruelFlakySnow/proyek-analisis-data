import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Konfigurasi Halaman
st.set_page_config(page_title="Beijing Air Quality Dashboard", page_icon="☁️", layout="wide")
sns.set_theme(style="whitegrid")

# Helper function untuk memuat data
@st.cache_data
def load_data():
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "main_data.csv.gz")
    df = pd.read_csv(file_path)
    
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    return df

df = load_data()

# ----------------------------------------
# SIDEBAR (FITUR INTERAKTIF)
# ----------------------------------------
with st.sidebar:
    st.title("☁️ Air Quality Beijing")
    st.write("Dashboard Analisis Kualitas Udara (2013-2017)")
    
    st.markdown("### Filter Data (Fitur Interaktif)")
    # Filter 1: Berdasarkan Stasiun
    station_list = df['station'].unique().tolist()
    selected_stations = st.multiselect(
        label="Pilih Stasiun Pemantauan",
        options=station_list,
        default=station_list
    )
    
    # Filter 2: Berdasarkan Rentang Waktu
    if 'datetime' in df.columns:
        min_date = df["datetime"].min().date()
        max_date = df["datetime"].max().date()
        start_date, end_date = st.date_input(
            label='Rentang Waktu',
            min_value=min_date, max_value=max_date,
            value=[min_date, max_date]
        )
    else:
        start_date, end_date = None, None

# Terapkan Filter
if start_date and end_date:
    main_df = df[(df["datetime"].dt.date >= start_date) & (df["datetime"].dt.date <= end_date)]
else:
    main_df = df

if selected_stations:
    main_df = main_df[main_df['station'].isin(selected_stations)]

# ----------------------------------------
# MAIN PAGE
# ----------------------------------------
st.title("☁️ Beijing Air Quality Dashboard")
st.markdown("Visualisasi data kualitas udara berdasarkan stasiun pemantauan di Beijing.")

# ----------------------------------------
# VISUALISASI 1: Perbandingan Stasiun
# ----------------------------------------
st.subheader("1. Rata-Rata PM2.5 & PM10 Tertinggi dan Terendah per Stasiun")
col_bar1, col_bar2 = st.columns(2)

station_pm = main_df.groupby('station')[['PM2.5', 'PM10']].mean().reset_index()
station_pm25 = station_pm.sort_values(by='PM2.5', ascending=False).reset_index(drop=True)
station_pm10 = station_pm.sort_values(by='PM10', ascending=False).reset_index(drop=True)

with col_bar1:
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(data=station_pm25, x='PM2.5', y='station', palette="OrRd_r", ax=ax)
    ax.axvline(15, color='red', linestyle='--', linewidth=2, label='Batas WHO (15 µg/m³)')
    ax.set_title("Rata-Rata PM2.5 per Stasiun")
    ax.set_xlabel("Konsentrasi PM2.5 (µg/m³)")
    ax.set_ylabel("Stasiun")
    ax.legend(loc="lower right")
    plt.tight_layout()
    st.pyplot(fig)

with col_bar2:
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(data=station_pm10, x='PM10', y='station', palette="OrRd_r", ax=ax)
    ax.axvline(45, color='red', linestyle='--', linewidth=2, label='Batas WHO (45 µg/m³)')
    ax.set_title("Rata-Rata PM10 per Stasiun")
    ax.set_xlabel("Konsentrasi PM10 (µg/m³)")
    ax.set_ylabel("")
    ax.legend(loc="lower right")
    plt.tight_layout()
    st.pyplot(fig)

# ----------------------------------------
# VISUALISASI 2: Tren Bulanan & Harian (Hourly)
# ----------------------------------------
st.markdown("---")
st.subheader("2. Tren Fluktuasi PM2.5: Bulanan dan Per Jam (Hourly)")
col_line1, col_line2 = st.columns(2)

with col_line1:
    if 'month' in main_df.columns:
        monthly_trend = main_df.groupby('month')['PM2.5'].mean().reset_index()
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.lineplot(data=monthly_trend, x='month', y='PM2.5', marker='o', color='#d95f02', linewidth=2.5, ax=ax)
        ax.set_title("Fluktuasi Bulanan Konsentrasi PM2.5", fontsize=14)
        ax.set_xlabel("Bulan (1 = Jan, 12 = Des)")
        ax.set_ylabel("Rata-Rata PM2.5 (µg/m³)")
        ax.set_xticks(range(1, 13))
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.error("Kolom 'month' tidak ada. Pastikan main_data.csv memiliki kolom bulan.")

with col_line2:
    if 'hour' in main_df.columns and main_df['hour'].nunique() > 1:
        hourly_trend = main_df.groupby('hour')[['PM2.5', 'PM10']].mean().reset_index()
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.lineplot(data=hourly_trend, x='hour', y='PM2.5', marker='o', color='#e7298a', linewidth=2.5, label='PM2.5', ax=ax)
        sns.lineplot(data=hourly_trend, x='hour', y='PM10', marker='s', color='#7570b3', linewidth=2.5, label='PM10', ax=ax)
        ax.set_title("Pola Harian (Per Jam) Konsentrasi PM2.5 & PM10", fontsize=14)
        ax.set_xlabel("Jam (00:00 - 23:00)")
        ax.set_ylabel("Konsentrasi (µg/m³)")
        ax.set_xticks(range(0, 24, 2))
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.error("Kolom 'hour' tidak valid (hanya berisi nilai 0). Ini terjadi karena data yang Anda ekspor sudah digabungkan menjadi rata-rata harian di notebook. HARAP RE-EXPORT main_data.csv (lihat instruksi langkah 1).")

# ----------------------------------------
# VISUALISASI 3: Matriks Korelasi 
# ----------------------------------------
st.markdown("---")
st.subheader("3. Matriks Korelasi antara Polutan Udara dan Parameter Cuaca")

corr_columns = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'TEMP', 'PRES', 'DEWP', 'RAIN', 'WSPM']
available_cols = [col for col in corr_columns if col in main_df.columns]

if available_cols:
    corr_matrix = main_df[available_cols].corr()
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax, linewidths=0.5)
    ax.set_title("Matriks Korelasi Polutan & Cuaca", fontsize=14)
    plt.tight_layout()
    st.pyplot(fig)
else:
    st.error("Kolom untuk matriks korelasi tidak ditemukan.")
    
st.caption("Copyright © 2026 - Proyek Analisis Data Dicoding")
