import streamlit as st
import pandas as pd
import psycopg2
import json
import redis

CACHE_TTL = 60

st.set_page_config(page_title="Dashboard PPIC 3 Segmen", layout="wide", page_icon="🏭")
st.title("Dashboard PPIC - Pemantauan 3 Segmen Terintegrasi")
st.markdown("Sistem Monitoring Terdistribusi: **Raw Material**, **Lantai Produksi (WIP)**, dan **Finish Good (Sloc Rak)**.")
st.markdown("---")

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

tab1, tab2, tab3 = st.tabs(["1. Segmen Raw Material", "2. Segmen Produksi (WIP)", "3. Segmen Finish Good (Siap Jual)"])

with tab1:
    st.subheader("Lokasi & Stok Bahan Baku Baja Gulung (Coil)")
    try:
        df_rm = get_cached_dataframe(
            "cache:raw_material",
            "SELECT pabrik, kode_barcode_rm, jenis_material, berat_ton, lokasi_rm_sloc, status FROM v_global_raw_material;"
        )
        if df_rm.empty:
            st.info("Tidak ada stok bahan baku.")
        else:
            st.dataframe(df_rm, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Gagal mengambil data RM: {e}")

with tab2:
    st.subheader("Antrean Jenis Pipa yang SEDANG dalam Proses Produksi (WIP)")
    try:
        df_wip = get_cached_dataframe(
            "cache:produksi_wip",
            "SELECT pabrik, no_seri_barcode, jenis_pipa, status FROM v_global_produksi_wip;"
        )
        if df_wip.empty:
            st.success("Semua antrean produksi selesai! Lantai produksi kosong.")
        else:
            col_chart, col_table = st.columns([1, 1])
            with col_table:
                st.dataframe(df_wip, use_container_width=True, hide_index=True)
            with col_chart:
                summary_wip = df_wip.groupby('jenis_pipa').size().reset_index(name='Jumlah Batang')
                st.bar_chart(data=summary_wip, x='jenis_pipa', y='Jumlah Batang', color='#dd5500')
    except Exception as e:
        st.error(f"Gagal mengambil data Produksi: {e}")

with tab3:
    st.subheader("Stok Jenis Pipa SIAP JUAL Lengkap dengan Lokasi Sloc Rak")
    try:
        df_fg = get_cached_dataframe(
            "cache:finish_good",
            "SELECT pabrik, no_seri_barcode, jenis_pipa, id_rak_sloc, status FROM v_global_finish_good;"
        )
        if df_fg.empty:
            st.warning("Gudang barang jadi kosong. Belum ada produk siap jual.")
        else:
            st.markdown("### Daftar Posisi Barang Siap Angkut")
            st.dataframe(df_fg, use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("### Sebaran Jenis Pipa Siap Jual di Rak Gudang")
            summary_fg = df_fg.groupby(['jenis_pipa', 'pabrik']).size().reset_index(name='jumlah')
            st.bar_chart(data=summary_fg, x='jenis_pipa', y='jumlah', color='pabrik', use_container_width=True)
    except Exception as e:
        st.error(f"Gagal mengambil data FG: {e}")

st.sidebar.header("Kontrol Panel")
if st.sidebar.button("Segarkan Seluruh Segmen"):
    invalidate_cache()
    st.rerun()
