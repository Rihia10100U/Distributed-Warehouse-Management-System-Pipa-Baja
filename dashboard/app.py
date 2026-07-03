import streamlit as st
import pandas as pd
import psycopg2
import json
import redis
from datetime import datetime

CACHE_TTL = 60

st.set_page_config(page_title="Dashboard PPIC 3 Segmen", layout="wide")

# ── Koneksi & Cache ──

def get_connection():
    return psycopg2.connect(
        host="pg-hub",
        database="db_hub_pusat",
        user="admin",
        password="secretpassword",
        port="5432"
    )

def get_redis():
    try:
        return redis.Redis(host="redis-cache", port=6379, decode_responses=True, socket_connect_timeout=2)
    except Exception:
        return None

def get_cached_dataframe(cache_key, query, ttl=CACHE_TTL):
    r = get_redis()
    if r is not None:
        try:
            cached = r.get(cache_key)
            if cached is not None:
                return pd.read_json(cached, orient="records")
        except Exception:
            pass

    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()

    if r is not None:
        try:
            r.setex(cache_key, ttl, df.to_json(orient="records"))
        except Exception:
            pass

    return df

def invalidate_cache():
    r = get_redis()
    if r is not None:
        try:
            r.delete("cache:raw_material", "cache:produksi_wip", "cache:finish_good")
        except Exception:
            pass

def load_all_data():
    df_rm = get_cached_dataframe(
        "cache:raw_material",
        "SELECT pabrik, kode_barcode_rm, jenis_material, berat_ton, lokasi_rm_sloc, status FROM v_global_raw_material;"
    )
    df_wip = get_cached_dataframe(
        "cache:produksi_wip",
        "SELECT pabrik, no_seri_barcode, jenis_pipa, status FROM v_global_produksi_wip;"
    )
    df_fg = get_cached_dataframe(
        "cache:finish_good",
        "SELECT pabrik, no_seri_barcode, jenis_pipa, id_rak_sloc, status FROM v_global_finish_good;"
    )
    return df_rm, df_wip, df_fg

# ── Sidebar ──

st.sidebar.markdown("Dashboard PPIC")
st.sidebar.markdown("**Pemantauan 3 Segmen Terintegrasi**")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navigasi",
    ["📦 Raw Material", "⚙️ Produksi (WIP)", "✅ Finish Good", "📊 Ringkasan"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Kontrol")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 Segarkan"):
        invalidate_cache()
        st.rerun()
with col2:
    if st.button("🧹 Hapus Cache"):
        r = get_redis()
        if r is not None:
            r.flushdb()
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### Info Sistem")
st.sidebar.markdown(f"⏱️ **Cache TTL:** {CACHE_TTL}s")
redis_ok = get_redis() is not None
st.sidebar.markdown(f"💾 **Redis:** {'✅ Aktif' if redis_ok else '❌ Tidak terhubung'}")
st.sidebar.markdown(f"🕐 **Terakhir diperbarui:** {datetime.now().strftime('%H:%M:%S')}")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<small style='color: gray;'>DWMS Pipa Baja — "
    "Sistem Database Terdistribusi<br>"
    "Plant 1 (Semarang) · Plant 2 (Surabaya) · Hub Pusat</small>",
    unsafe_allow_html=True
)

# ── Muat Data ──

try:
    df_rm, df_wip, df_fg = load_all_data()
except Exception as e:
    st.error(f"Gagal menghubungi database hub: {e}")
    df_rm = df_wip = df_fg = pd.DataFrame()

# ── Halaman ──

def show_metrics(df, label_pabrik):
    total = len(df)
    if total == 0:
        return st.metric(label_pabrik, 0)
    return st.metric(label_pabrik, total)

if menu == "📦 Raw Material":
    st.title("📦 Raw Material")
    st.markdown("Lokasi & Stok Bahan Baku Baja Gulung (Coil)")

    if df_rm.empty:
        st.info("Tidak ada stok bahan baku.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Semua Plant", len(df_rm))
        with col2:
            p1 = len(df_rm[df_rm['pabrik'] == 'Gudang / Plant 1'])
            st.metric("Plant 1 (Semarang)", p1)
        with col3:
            p2 = len(df_rm[df_rm['pabrik'] == 'Gudang / Plant 2'])
            st.metric("Plant 2 (Surabaya)", p2)
        with col4:
            total_berat = df_rm['berat_ton'].sum()
            st.metric("Total Berat (Ton)", f"{total_berat:.2f}")

        st.markdown("---")
        st.dataframe(df_rm, use_container_width=True, hide_index=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### Berat per Material")
            chart = df_rm.groupby('jenis_material')['berat_ton'].sum().reset_index(name='berat_ton')
            st.bar_chart(data=chart, x='jenis_material', y='berat_ton', color='#1f77b4')
        with col_b:
            st.markdown("### Distribusi per Plant")
            dist = df_rm.groupby('pabrik').size().reset_index(name='jumlah')
            st.bar_chart(data=dist, x='pabrik', y='jumlah', color='#ff7f0e')

elif menu == "⚙️ Produksi (WIP)":
    st.title("⚙️ Produksi — Work In Progress")
    st.markdown("Antrean Jenis Pipa yang Sedang dalam Proses Produksi")

    if df_wip.empty:
        st.success("Semua antrean produksi selesai! Lantai produksi kosong.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total WIP", len(df_wip))
        with col2:
            p1 = len(df_wip[df_wip['pabrik'] == 'Gudang / Plant 1'])
            st.metric("Plant 1 (Semarang)", p1)
        with col3:
            p2 = len(df_wip[df_wip['pabrik'] == 'Gudang / Plant 2'])
            st.metric("Plant 2 (Surabaya)", p2)

        st.markdown("---")
        col_chart, col_table = st.columns([1, 1.5])
        with col_table:
            st.dataframe(df_wip, use_container_width=True, hide_index=True)
        with col_chart:
            st.markdown("### Jumlah per Jenis Pipa")
            summary_wip = df_wip.groupby('jenis_pipa').size().reset_index(name='Jumlah Batang')
            st.bar_chart(data=summary_wip, x='jenis_pipa', y='Jumlah Batang', color='#dd5500')

elif menu == "✅ Finish Good":
    st.title("✅ Finish Good")
    st.markdown("Stok Jenis Pipa Siap Jual Lengkap dengan Lokasi Sloc Rak")

    if df_fg.empty:
        st.warning("Gudang barang jadi kosong. Belum ada produk siap jual.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total FG", len(df_fg))
        with col2:
            p1 = len(df_fg[df_fg['pabrik'] == 'Gudang / Plant 1'])
            st.metric("Plant 1 (Semarang)", p1)
        with col3:
            p2 = len(df_fg[df_fg['pabrik'] == 'Gudang / Plant 2'])
            st.metric("Plant 2 (Surabaya)", p2)

        st.markdown("---")
        st.dataframe(df_fg, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### Sebaran Jenis Pipa per Plant")
        summary_fg = df_fg.groupby(['jenis_pipa', 'pabrik']).size().reset_index(name='jumlah')
        st.bar_chart(data=summary_fg, x='jenis_pipa', y='jumlah', color='pabrik', use_container_width=True)

elif menu == "📊 Ringkasan":
    st.title("📊 Ringkasan Seluruh Segmen")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("📦 Total Raw Material", len(df_rm) if not df_rm.empty else 0,
                  help="Bahan baku coil di semua plant")
    with col_b:
        st.metric("⚙️ Total WIP", len(df_wip) if not df_wip.empty else 0,
                  help="Pipa dalam proses produksi")
    with col_c:
        st.metric("✅ Total Finish Good", len(df_fg) if not df_fg.empty else 0,
                  help="Pipa siap jual di rak")

    st.markdown("---")
    st.markdown("### Data Tabel Lengkap")

    tab1, tab2, tab3 = st.tabs(["📦 Raw Material", "⚙️ WIP", "✅ Finish Good"])
    with tab1:
        if not df_rm.empty:
            st.dataframe(df_rm, use_container_width=True, hide_index=True)
        else:
            st.info("Kosong")
    with tab2:
        if not df_wip.empty:
            st.dataframe(df_wip, use_container_width=True, hide_index=True)
        else:
            st.info("Kosong")
    with tab3:
        if not df_fg.empty:
            st.dataframe(df_fg, use_container_width=True, hide_index=True)
        else:
            st.info("Kosong")

    if not df_rm.empty and not df_wip.empty and not df_fg.empty:
        st.markdown("---")
        st.markdown("### Perbandingan Antar Plant")
        ringkasan = pd.DataFrame({
            'Segmen': ['Raw Material', 'Produksi (WIP)', 'Finish Good'],
            'Plant 1': [
                len(df_rm[df_rm['pabrik'] == 'Gudang / Plant 1']),
                len(df_wip[df_wip['pabrik'] == 'Gudang / Plant 1']),
                len(df_fg[df_fg['pabrik'] == 'Gudang / Plant 1'])
            ],
            'Plant 2': [
                len(df_rm[df_rm['pabrik'] == 'Gudang / Plant 2']),
                len(df_wip[df_wip['pabrik'] == 'Gudang / Plant 2']),
                len(df_fg[df_fg['pabrik'] == 'Gudang / Plant 2'])
            ]
        })
        st.dataframe(ringkasan, use_container_width=True, hide_index=True)
