import streamlit as st
import pandas as pd
import altair as alt
from connect import *

# Koneksi ke MongoDB

# Fungsi untuk memuat data dari MongoDB
def load_data():
    cursor = sdgs_collection.find().sort([("nama_kabupaten_kota", 1), ("tahun", 1)])
    data = list(cursor)
    return pd.DataFrame(data)

# Fungsi untuk menangani data null
def handle_nulls(data):
    data = data.fillna(0)  # Ganti nilai null dengan 0
    return data

# Sidebar filter untuk kota dan rentang tahun
def sidebar_filters(data):
    st.sidebar.title("Filter")
    kota_selected = "Semua"
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

#fungsi untuk menambahkan data
def create_data(new_data):

    existing_data = sdgs_collection.find_one({"_id": new_data["_id"]})
    
    if existing_data:
        st.error(f"Data {new_data['nama_kabupaten_kota']} pada tahun {new_data['tahun']} sudah ada!")
    else:
        # Jika ID belum ada, lakukan penyisipan data baru
        sdgs_collection.insert_one(new_data)
        st.success("Data berhasil ditambahkan!")
        st.session_state.data = load_data()  # Refresh data setelah insert
        #st.session_state.page_num = 0  # Reset page number to show the first page
        st.rerun()


# Fungsi untuk mengupdate data
def update_data(doc_id, new_data):
    result = sdgs_collection.update_one({"_id": doc_id}, {"$set": new_data})
    if result.modified_count > 0:
        st.success("Data berhasil diperbarui!")
    else:
        st.error("Gagal memperbarui data.")

# Fungsi untuk menghapus data
def delete_data(doc_id):
    result = sdgs_collection.delete_one({"_id": doc_id})
    if result.deleted_count > 0:
        st.success("Data berhasil dihapus!")
    else:
        st.error("Gagal menghapus data.")

# Top navigation bar
st.set_page_config(layout="wide")  # Perlebar ukuran konten
st.title("SDGs Dashboard and CRUD")
page = st.selectbox("Pilih Halaman", ["CRUD", "Dashboard"])

# Load data awal
data = load_data()
data = handle_nulls(data)  # Tangani data null

# Manage pagination
def get_paginated_data(data, page_num, page_size):
    start = page_num * page_size
    end = start + page_size
    return data.iloc[start:end]

if page == "CRUD":
    st.header("CRUD Operations")

    # Sidebar filters
    filtered_data, kota_selected = sidebar_filters(data)

    if kota_selected != "Semua":
        filtered_data = filtered_data[filtered_data['nama_kabupaten_kota'] == kota_selected]

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
            create_data(new_data)

    # Tabel data dengan filter dan pagination
    st.subheader("Data Tabel")
    page_size = 15  # Show 15 records per page
    if "page_num" not in st.session_state:
        st.session_state.page_num = 0

    paginated_data = get_paginated_data(filtered_data, st.session_state.page_num, page_size)

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    col1.write("Nama Kabupaten/Kota")
    col2.write("Tahun")
    col3.write("Indeks Keparahan Kemiskinan")
    col4.write("Persentase Penduduk Miskin")
    col5.write("Tingkat Pengangguran Terbuka")
    col6.write("Update")
    col7.write("Delete")

    for _, row in paginated_data.iterrows():
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
                st.success(f"{row['_id']}")
                new_ikk = st.number_input("Indeks Keparahan Kemiskinan", value=row['indeks_keparahan_kemiskinan'])
                new_ppm = st.number_input("Persentase Penduduk Miskin", value=row['persentase_penduduk_miskin'])
                new_tpt = st.number_input("Tingkat Pengangguran Terbuka", value=row['tingkat_pengangguran_terbuka'])
                submitted_update = st.form_submit_button("Update")
                if submitted_update:
                    update_data(row['_id'], {
                        "indeks_keparahan_kemiskinan": new_ikk,
                        "persentase_penduduk_miskin": new_ppm,
                        "tingkat_pengangguran_terbuka": new_tpt
                    })
                    st.session_state.data = load_data()  # Refresh data setelah update
                    #st.session_state.page_num = 0  # Reset page number
                    st.rerun()

        if delete_btn:
            delete_data(row["_id"])
            st.session_state.data = load_data()  # Refresh data setelah delete
            #st.session_state.page_num = 0  # Reset page number
            st.rerun() 

    # Pagination Controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:

        if st.session_state.page_num == 0:
            #prev_button = st.button("Previous", key="prev")
            next_button = st.button("Next", key="next")

            if next_button and (st.session_state.page_num + 1) * page_size <= len(filtered_data):
                st.session_state.page_num += 1
                st.rerun() 
        else:
            prev_button = st.button("Previous", key="prev")
            next_button = st.button("Next", key="next")

            if prev_button and st.session_state.page_num > 0:
                st.session_state.page_num -= 1
                st.rerun() 
            if next_button and (st.session_state.page_num + 1) * page_size <= len(filtered_data):
                st.session_state.page_num += 1
                st.rerun()


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
