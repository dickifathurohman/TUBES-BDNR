import streamlit as st
import pandas as pd
import altair as alt
from connect import *

# Koneksi ke MongoDB

# Fungsi untuk memuat data dari MongoDB
def load_data():
    cursor = sdgs_collection.find()
    data = list(cursor)
    return pd.DataFrame(data)

# Fungsi untuk menangani data null
def handle_nulls(data):
    data = data.fillna(0)  # Ganti nilai null dengan 0
    return data

# Sidebar filter untuk kota dan rentang tahun
def sidebar_filters(data):
    st.sidebar.title("Filter")
    kota_selected = st.sidebar.selectbox(
        "Pilih Kota (Opsional, untuk Highlight)", 
        options=["Semua"] + list(data['nama_kabupaten_kota'].unique())
    )
    tahun_min, tahun_max = st.sidebar.slider(
        "Filter Rentang Tahun", 
        int(data['tahun'].min()), 
        int(data['tahun'].max()), 
        (int(data['tahun'].min()), int(data['tahun'].max()))
    )
    filtered_data = data[
        (data['tahun'] >= tahun_min) & 
        (data['tahun'] <= tahun_max)
    ]
    return filtered_data, kota_selected

# Fungsi untuk mengupdate data
def update_data(doc_id, new_data):
    sdgs_collection.update_one({"_id": doc_id}, {"$set": new_data})

# Fungsi untuk menghapus data
def delete_data(doc_id):
    sdgs_collection.delete_one({"_id": doc_id})

# Top navigation bar
st.set_page_config(layout="wide")  # Perlebar ukuran konten
st.title("SDGs Dashboard and CRUD")
page = st.selectbox("Pilih Halaman", ["CRUD", "Dashboard"])

# Load data awal
data = load_data()
data = handle_nulls(data)  # Tangani data null

if page == "CRUD":
    st.header("CRUD Operations")

    # Sidebar filters
    filtered_data, _ = sidebar_filters(data)

    # Form untuk menambahkan data
    st.subheader("Tambah Data Baru")
    with st.form("add_data_form"):
        kota = st.selectbox("Pilih Kota", options=data['nama_kabupaten_kota'].unique())
        tahun = st.number_input("Tahun", min_value=2000, max_value=2100, step=1)
        ikk = st.number_input("Indeks Keparahan Kemiskinan")
        ppm = st.number_input("Persentase Penduduk Miskin")
        tpt = st.number_input("Tingkat Pengangguran Terbuka")
        submitted = st.form_submit_button("Tambahkan Data")
        if submitted:
            new_data = {
                "_id": f"{kota}_{tahun}",
                "nama_kabupaten_kota": kota,
                "tahun": tahun,
                "indeks_keparahan_kemiskinan": ikk,
                "persentase_penduduk_miskin": ppm,
                "tingkat_pengangguran_terbuka": tpt
            }
            sdgs_collection.insert_one(new_data)
            st.success("Data berhasil ditambahkan!")
            
            # Tambahkan data baru ke dalam session_state untuk update langsung
            if "data" in st.session_state:
                st.session_state["data"] = pd.concat([st.session_state["data"], pd.DataFrame([new_data])])
            else:
                st.session_state["data"] = load_data()  # Memuat ulang seluruh data


    # Tabel data dengan filter
    st.subheader("Data Tabel")
    sorted_data = filtered_data.sort_values(by=["nama_kabupaten_kota", "tahun"])
    for _, row in sorted_data.iterrows():
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        col1.write(row['nama_kabupaten_kota'])
        col2.write(row['tahun'])
        col3.write(row['indeks_keparahan_kemiskinan'])
        col4.write(row['persentase_penduduk_miskin'])
        col5.write(row['tingkat_pengangguran_terbuka'])
        update_btn = col6.button("Update", key=f"update_{row['_id']}")
        delete_btn = col7.button("Delete", key=f"delete_{row['_id']}")

        if update_btn:
            with st.form(f"update_form_{row['_id']}"):
                new_ikk = st.number_input("Indeks Keparahan Kemiskinan", value=row['indeks_keparahan_kemiskinan'])
                new_ppm = st.number_input("Persentase Penduduk Miskin", value=row['persentase_penduduk_miskin'])
                new_tpt = st.number_input("Tingkat Pengangguran Terbuka", value=row['tingkat_pengangguran_terbuka'])
                submitted_update = st.form_submit_button("Update")
                if submitted_update:
                    update_data(row["_id"], {
                        "indeks_keparahan_kemiskinan": new_ikk,
                        "persentase_penduduk_miskin": new_ppm,
                        "tingkat_pengangguran_terbuka": new_tpt
                    })
                    st.success("Data berhasil diperbarui!")
                    st.experimental_rerun()

        if delete_btn:
            delete_data(row["_id"])
            st.success("Data berhasil dihapus!")
            st.experimental_rerun()

elif page == "Dashboard":
    st.header("Dashboard Visualizations")

    # Sidebar filters
    filtered_data, kota_selected = sidebar_filters(data)

    # Visualisasi
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    col5, col6 = st.columns(2)

    # Bar Chart: Indeks Keparahan Kemiskinan
    with col1:
        st.subheader("Indeks Keparahan Kemiskinan")
        bar_chart_ikk = filtered_data.groupby("nama_kabupaten_kota")["indeks_keparahan_kemiskinan"].mean().reset_index()
        bar_chart_ikk["highlight"] = bar_chart_ikk["nama_kabupaten_kota"] == kota_selected
        chart = alt.Chart(bar_chart_ikk).mark_bar().encode(
            x=alt.X("nama_kabupaten_kota:N", sort="-y", title="Kabupaten/Kota"),
            y=alt.Y("indeks_keparahan_kemiskinan:Q", title="Indeks Keparahan Kemiskinan"),
            color=alt.condition(
                alt.datum.highlight,
                alt.value("blue"),
                alt.value("lightblue")
            )
        ).properties(width=800, height=400)
        st.altair_chart(chart, use_container_width=True)
    
    # Line Chart: Indeks Kemiskinan dari Tahun ke Tahun
    with col2:
        st.subheader("Trend Indeks Kemiskinan")
        line_chart_ikk = filtered_data[filtered_data['nama_kabupaten_kota'] == kota_selected] if kota_selected != "Semua" else filtered_data
        line_chart_ikk = line_chart_ikk.groupby("tahun")["indeks_keparahan_kemiskinan"].mean().reset_index()
        line_chart = alt.Chart(line_chart_ikk).mark_line().encode(
            x="tahun:O",
            y="indeks_keparahan_kemiskinan:Q",
            tooltip=["tahun", "indeks_keparahan_kemiskinan"]
        ).properties(width=400, height=400)
        st.altair_chart(line_chart, use_container_width=True)

    # Bar Chart: Persentase Penduduk Miskin
    with col3:
        st.subheader("Persentase Penduduk Miskin")
        bar_chart_ppm = filtered_data.groupby("nama_kabupaten_kota")["persentase_penduduk_miskin"].mean().reset_index()
        bar_chart_ppm["highlight"] = bar_chart_ppm["nama_kabupaten_kota"] == kota_selected
        chart = alt.Chart(bar_chart_ppm).mark_bar().encode(
            x=alt.X("nama_kabupaten_kota:N", sort="-y", title="Kabupaten/Kota"),
            y=alt.Y("persentase_penduduk_miskin:Q", title="Persentase Penduduk Miskin"),
            color=alt.condition(
                alt.datum.highlight,
                alt.value("blue"),
                alt.value("lightblue")
            )
        ).properties(width=800, height=400)
        st.altair_chart(chart, use_container_width=True)
    
    # Line Chart: Persentase Penduduk Miskin dari Tahun ke Tahun
    with col4:
        st.subheader("Trend Persentase Penduduk Miskin")
        line_chart_ikk = filtered_data[filtered_data['nama_kabupaten_kota'] == kota_selected] if kota_selected != "Semua" else filtered_data
        line_chart_ikk = line_chart_ikk.groupby("tahun")["persentase_penduduk_miskin"].mean().reset_index()
        line_chart = alt.Chart(line_chart_ikk).mark_line().encode(
            x="tahun:O",
            y="persentase_penduduk_miskin:Q",
            tooltip=["tahun", "persentase_penduduk_miskin"]
        ).properties(width=400, height=400)
        st.altair_chart(line_chart, use_container_width=True)