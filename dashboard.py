import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ---- Konfigurasi Tampilan ----
st.set_page_config(layout="wide", page_title="📊 Dashboard Analisis E-commerce")
sns.set(style="whitegrid")

# ---- Load Data ----
@st.cache_data
def load_data():
    df = pd.read_csv("all_data.csv")
    return df

df = load_data()

# ---- Sidebar ----
st.sidebar.header("🛠️ Pengaturan Filter")
selected_category = st.sidebar.multiselect(
    "Pilih Kategori Produk", 
    options=df["product_category_name_english"].unique(),
    default=df["product_category_name_english"].unique()
)

start_date = st.sidebar.date_input("📅 Rentang Waktu Mulai", df["order_purchase_timestamp"].min())
end_date = st.sidebar.date_input("📅 Rentang Waktu Akhir", df["order_purchase_timestamp"].max())

top_n = st.sidebar.slider("🔝 Jumlah Produk Terlaris", min_value=5, max_value=20, value=10)
least_n = st.sidebar.slider("🔽 Jumlah Produk Paling Jarang Terjual", min_value=5, max_value=20, value=10)

# ---- Filter Data ----
df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
df_filtered = df[(df["product_category_name_english"].isin(selected_category)) & 
                 (df["order_purchase_timestamp"].between(pd.Timestamp(start_date), pd.Timestamp(end_date)))]

# ---- Cek apakah kolom yang diperlukan ada ----
required_columns = ["product_id", "product_category_name_english", "order_item_id", "customer_unique_id", "order_purchase_timestamp"]
missing_columns = [col for col in required_columns if col not in df_filtered.columns]

if missing_columns:
    st.error(f"⚠️ Kolom berikut tidak ditemukan dalam dataset: {missing_columns}")
    st.stop()

# ---- Hitung Produk Terlaris dan Paling Jarang Terjual ----
product_sales = df_filtered.groupby(["product_id", "product_category_name_english"])["order_item_id"].count().reset_index()
product_sales = product_sales.rename(columns={"order_item_id": "total_sales"}).sort_values(by="total_sales", ascending=False)

top_selling = product_sales.head(top_n)  # Produk Terlaris
least_selling = product_sales.tail(least_n)  # Produk Paling Jarang Terjual

# ---- 1️⃣ Produk Terlaris (Bar Chart) ----
st.subheader(f"📈 {top_n} Produk Terlaris")
fig, ax = plt.subplots(figsize=(12, 5))
sns.barplot(y=top_selling['product_category_name_english'], x=top_selling['total_sales'], palette='viridis', ax=ax)
ax.set_xlabel("Jumlah Terjual")
ax.set_ylabel("Kategori Produk")
st.pyplot(fig)

# ---- 2️⃣ Produk Paling Jarang Terjual (Pie Chart) ----
st.subheader(f"📉 {least_n} Produk Paling Jarang Terjual")
fig, ax = plt.subplots(figsize=(8, 8))
ax.pie(least_selling['total_sales'], labels=least_selling['product_category_name_english'], autopct='%1.1f%%', 
       startangle=140, colors=sns.color_palette("magma", len(least_selling)))
ax.set_title("Distribusi Produk Paling Jarang Terjual")
st.pyplot(fig)

# ---- 3️⃣ Analisis Churn ----
st.subheader("📊 Analisis Churn Pelanggan")

# Hitung hari sejak pembelian terakhir untuk setiap pelanggan
df_filtered["days_since_last_purchase"] = (df_filtered["order_purchase_timestamp"].max() - df_filtered["order_purchase_timestamp"]).dt.days

# Tentukan pelanggan yang hampir churn (tidak membeli dalam 90 hari terakhir)
churn_customers = df_filtered[df_filtered["days_since_last_purchase"] > 90]

# ---- 3.1 Distribusi Waktu Pembelian Pelanggan (Histogram) ----
st.write("📌 **Distribusi Hari Sejak Pembelian Terakhir**")
fig, ax = plt.subplots(figsize=(12, 5))
sns.histplot(df_filtered["days_since_last_purchase"], bins=30, kde=True, color='blue', ax=ax)
ax.set_xlabel("Hari Sejak Pembelian Terakhir")
ax.set_ylabel("Jumlah Pelanggan")
ax.set_title("Distribusi Pelanggan Berdasarkan Hari Sejak Pembelian Terakhir")
st.pyplot(fig)

# ---- 3.2 Heatmap Pola Pembelian Pelanggan ----
st.subheader("📊 Heatmap Pola Pembelian Pelanggan")

# Konversi tanggal ke format bulanan
df_filtered["order_month"] = df_filtered["order_purchase_timestamp"].dt.to_period("M").astype(str)

# Hitung jumlah transaksi setiap pelanggan per bulan
customer_heatmap = df_filtered.pivot_table(index='customer_unique_id', columns='order_month', 
                                  values='order_item_id', aggfunc='count').fillna(0)

# Pilih hanya 20 pelanggan teratas berdasarkan total transaksi
top_customers = customer_heatmap.sum(axis=1).sort_values(ascending=False).head(20).index
customer_heatmap = customer_heatmap.loc[top_customers]

# Ganti Customer ID dengan label sederhana
customer_labels = [f"Pelanggan {i+1}" for i in range(len(top_customers))]
customer_heatmap.index = customer_labels

# Buat heatmap
fig, ax = plt.subplots(figsize=(14, 6))
sns.heatmap(customer_heatmap, cmap="coolwarm", cbar=True, ax=ax, linewidths=0.3, linecolor="gray")

# Konfigurasi tampilan
ax.set_xlabel("Bulan", fontsize=12)
ax.set_ylabel("Pelanggan", fontsize=12)
ax.set_title("Pola Pembelian Pelanggan (Top 20)", fontsize=14)
plt.xticks(rotation=45)

st.pyplot(fig)

# ---- 4️⃣ Ekspor Data ----
st.sidebar.subheader("📂 Ekspor Data")
if st.sidebar.button("Unduh Data Filtered (CSV)"):
    df_filtered.to_csv("filtered_data.csv", index=False)
    st.sidebar.success("✅ Data berhasil disimpan!")

# ---- Footer ----
st.write("© 2025 Dashboard by Streamlit")
