# Import library yang dibutuhkan
import streamlit as st
import pandas as pd
import altair as alt
import google.generativeai as genai
from duckduckgo_search import DDGS
from googlesearch import search
import time

# TAMBAHKAN BARIS INI TEPAT DI BAWAH IMPORT
st.set_page_config(
    page_title="Policy Brief Generator Jateng",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="auto"
)
# --- KONFIGURASI AI ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except (KeyError, AttributeError):
    st.error("🚨 Kunci API Google tidak ditemukan! Harap pastikan file .streamlit/secrets.toml sudah benar.")
    st.stop()

# --- FUNGSI-FUNGSI PENCARIAN (Tidak ada perubahan di sini) ---
def cari_dengan_duckduckgo(keyword):
    st.write("🔎 Mencari dengan **DuckDuckGo**...")
    keyword_lokal = f'"{keyword} jawa tengah"'
    query = f'{keyword_lokal} (site:docrida.id OR site:ejournal.jatengprov.go.id ORD site:jatengprov.go.id OR site:undip.ac.id OR site:uns.ac.id OR site:unnes.ac.id OR site:walisongo.ac.id OR site:sinta.kemdikbud.go.id OR site:rama.kemdikbud.go.id OR site:go.id OR site:ac.id)'
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=7)]
        if not results: return None, None
        snippets = [result['body'] for result in results]
        konteks = "\n\n".join(snippets)
        source_urls = [result['href'] for result in results]
        return konteks, source_urls
    except Exception as e:
        st.error(f"Error DuckDuckGo: {e}")
        return None, None

def cari_dengan_google(keyword):
    st.write("🔎 Mencari dengan **Google**...")
    keyword_lokal = f'"{keyword} jawa tengah"'
    query = f'{keyword_lokal} (site:docrida.id OR site:ejournal.jatengprov.go.id ORD site:jatengprov.go.id OR site:undip.ac.id OR site:uns.ac.id OR site:unnes.ac.id OR site:walisongo.ac.id OR site:sinta.kemdikbud.go.id OR site:rama.kemdikbud.go.id OR site:go.id OR site:ac.id)'
    try:
        search_results_urls = [url for url in search(query, num_results=10, sleep_interval=2)]
        if not search_results_urls: return None, None
        konteks = "Daftar sumber relevan:\n" + "\n".join(f"- {url}" for url in search_results_urls)
        return konteks, search_results_urls
    except Exception as e:
        st.error(f"Error Google: {e}")
        return None, None

# --- FUNGSI-FUNGSI GENERATOR AI ---
def generate_brief_dengan_ai(keyword, konteks, search_engine):
    st.write("🤖 AI menganalisis & menyusun draf teks...")
    prompt = f"""
    Anda adalah seorang analis kebijakan publik senior yang sangat teliti dan analitis untuk Bappeda Provinsi Jawa Tengah.
    Tugas Anda adalah melakukan SINTESIS komprehensif dari potongan-potongan informasi dalam 'KONTEKS' untuk menyusun sebuah draf policy brief yang kaya data dan mendalam.

    INSTRUKSI PENTING:
    -   Gunakan HANYA informasi dari 'KONTEKS'.
    -   Jika Anda menemukan data perbandingan atau statistik kunci yang bisa ditabelkan, **formatlah dalam bentuk Tabel Markdown** agar mudah dibaca.
    -   Jangan membuat bagian referensi atau grafik, karena itu akan ditambahkan oleh sistem secara terpisah.

    Topik Utama: "{keyword}"
    KONTEKS:
    ---
    {konteks}
    ---

    Setelah menganalisis konteks, tuliskan draf *policy brief* dengan format dan instruksi ketat sebagai berikut (HANYA 4 bagian ini):

    **Judul:** [Judul yang tajam dan mencerminkan analisis]
    ### 1. Ringkasan Eksekutif
    [Ringkasan padat, sertakan 1-2 data kunci, dan sebutkan rekomendasi utama.]
    ### 2. Pendahuluan
    [Latar belakang masalah dengan data skala dan urgensi di Jawa Tengah.]
    ### 3. Temuan dan Pembahasan Mendalam
    [Susun pembahasan berdasarkan TEMA UTAMA. Untuk setiap tema, sajikan data yang Anda temukan (gunakan tabel markdown jika cocok), bandingkan informasi dari beberapa sumber, dan berikan analisis.]
    ### 4. Rekomendasi Kebijakan Berbasis Bukti (Evidence-Based)
    [Rekomendasi yang SPESIFIK, TERUKUR, dan dapat DILAKSANAKAN, dengan justifikasi kuat dari temuan.]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error saat generate brief: {e}")
        return None

def generate_chart_code(konteks):
    """Fungsi BARU untuk meminta AI membuat kode visualisasi data."""
    st.write("📊 AI merancang kode untuk visualisasi data...")
    prompt = f"""
    Anda adalah seorang spesialis visualisasi data menggunakan Python.
    Tugas Anda adalah menganalisis teks berikut dan membuat satu buah kode Python sederhana menggunakan library Altair untuk memvisualisasikan data paling menarik atau penting dari teks tersebut.

    KONTEKS:
    ---
    {konteks}
    ---

    INSTRUKSI KODE:
    1.  Baca konteks di atas, cari data numerik yang bisa dibandingkan (misalnya: perbandingan antar tahun, antar wilayah, persentase, dll).
    2.  Jika tidak ada data yang cocok untuk divisualisasikan, cukup kembalikan teks: #TIDAK_ADA_DATA
    3.  Jika ada, tulis kode Python untuk membuat sebuah chart Altair (misalnya: bar chart, line chart).
    4.  Kode harus lengkap, termasuk pembuatan `pandas.DataFrame`.
    5.  Variabel final yang berisi chart harus bernama `chart`.
    6.  Jangan menulis `st.altair_chart(chart)`. Hanya kode pembuatan chart-nya saja.

    Contoh output yang baik:
    ```python
    import pandas as pd
    import altair as alt

    data = pd.DataFrame({{
        'Tahun': [2022, 2023, 2024],
        'Jumlah Kasus': [120, 95, 78]
    }})

    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('Tahun:O', title='Tahun'),
        y=alt.Y('Jumlah Kasus:Q', title='Jumlah Kasus Stunting'),
        tooltip=['Tahun', 'Jumlah Kasus']
    ).properties(
        title='Penurunan Kasus Stunting'
    )
    ```
    """
    try:
        response = model.generate_content(prompt)
        # Membersihkan kode dari markdown code block
        clean_code = response.text.replace("```python", "").replace("```", "").strip()
        return clean_code
    except Exception as e:
        st.error(f"Error saat generate chart code: {e}")
        return None

# --- ANTARMUKA APLIKASI STREAMLIT ---
st.title("📄 Policy Brief Generator Jawa Tengah (AI-Powered)")
st.write("Masukkan topik, dan biarkan AI menyusun draf *policy brief*")
st.write("---")

with st.form("input_form"):
    keyword_input = st.text_input("Masukkan Topik atau Kata Kunci:", placeholder="Contoh: penurunan stunting di jawa tengah")
    search_engine = st.radio("Pilih Mesin Pencari:", ('Mesin 1', 'Mesin 2'), horizontal=True)
    submitted = st.form_submit_button("🚀 Buat Draf Lengkap")

if submitted:
    if keyword_input:
        with st.spinner("Harap tunggu, proses analisis komprehensif sedang berjalan..."):
            konteks, sumber_referensi = (None, None)
            if search_engine == 'DuckDuckGo':
                konteks, sumber_referensi = cari_dengan_duckduckgo(keyword_input)
            elif search_engine == 'Google':
                konteks, sumber_referensi = cari_dengan_google(keyword_input)

            if konteks and sumber_referensi:
                st.success("Berhasil mengumpulkan konteks & sumber!")
                
                # Menjalankan kedua generator secara paralel (konsep)
                hasil_brief = generate_brief_dengan_ai(keyword_input, konteks, search_engine)
                kode_grafik = generate_chart_code(konteks)
                
                if hasil_brief:
                    st.success("Draf berhasil dibuat!")
                    st.write("---")
                    
                    st.markdown(hasil_brief) # Menampilkan Judul, Ringkasan, Pembahasan (dengan tabel), Rekomendasi
                    
                    # BAGIAN BARU: Menampilkan Grafik
                    if kode_grafik and "#TIDAK_ADA_DATA" not in kode_grafik:
                        st.markdown("### Visualisasi Data Kunci")
                        try:
                            # PERINGATAN KEAMANAN: exec() menjalankan kode secara dinamis.
                            # Di lingkungan ini, risikonya terkendali karena kita yang merancang prompt-nya.
                            # Namun, berhati-hatilah saat menggunakan exec() pada kode dari sumber yang tidak dipercaya.
                            exec(kode_grafik, globals(), locals())
                            st.altair_chart(locals()['chart'], use_container_width=True)
                        except Exception as e:
                            st.warning(f"Gagal membuat grafik: {e}")
                            st.code(kode_grafik) # Tampilkan kode jika error agar bisa di-debug

                    # Menampilkan Referensi
                    st.markdown("### 5. Referensi")
                    for url in sumber_referensi:
                        st.markdown(f"- {url}")
            else:
                st.warning("Tidak ditemukan informasi yang cukup relevan dari pencarian.")
    else:
        st.error("Mohon masukkan topik atau kata kunci.")
