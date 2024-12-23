from connect import db
import pandas as pd

sdgs_collection = db['data_kemiskinan']

csv_file = "dataset_bps.csv"  # Ganti dengan path file Anda
df = pd.read_csv(csv_file)

documents = []

for _, row in df.iterrows():

    documents.append({
        "_id": f"{row['nama_kabupaten_kota']}_{row['tahun']}",  # Unique identifier
        "nama_kabupaten_kota": row['nama_kabupaten_kota'],
        "tahun": row['tahun'],
        "indeks_keparahan_kemiskinan": row['indeks_keparahan_kemiskinan'] if not pd.isnull(row['indeks_keparahan_kemiskinan']) else None,
        "persentase_penduduk_miskin": row['persentase_penduduk_miskin'] if not pd.isnull(row['persentase_penduduk_miskin']) else None,
        "tingkat_pengangguran_terbuka": row['tingkat_pengangguran_terbuka'] if not pd.isnull(row['tingkat_pengangguran_terbuka']) else None,
    })

result = sdgs_collection.insert_many(documents)
print(f"Inserted {len(result.inserted_ids)} product documents.")
