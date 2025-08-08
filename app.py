# Import library yang dibutuhkan
import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
from googlesearch import search # Library baru untuk Google Search
import time

# --- KONFIGURASI AI ---
# Mengambil API key dari file rahasia (secrets.toml)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except (KeyError, AttributeError):
    st.error("🚨 Kunci API Google tidak ditemukan! Harap pastikan file .streamlit/secrets.toml sudah benar.")
    st.stop()

# --- FUNGSI-FUNGSI PENCARIAN ---

def cari_dengan_duckduckgo(keyword):
    """Fungsi untuk mencari menggunakan DuckDuckGo, mengambil rangkuman teks DAN link sumber."""
    st.write("🔎 Mencari hasil **Riset** (mengambil rangkuman teks)...")
    query = f'"{keyword_lokal}" site:docrida.go.id OR site:repository.unsoed.ac.id OR site:jatengprov.go.id OR site:undip.ac.id OR site:uns.ac.id OR site:unnes.ac.id OR site:walisongo.ac.id OR site:sinta.kemdikbud.go.id'
        try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=7)]
        if not results:
            return None, None
        
        # Mengambil rangkuman teks untuk konteks AI
        snippets = [result['body'] for result in results]
        konteks = "\n\n".join(snippets)
        
        # BARU: Mengambil link sumber untuk daftar referensi
        source_urls = [result['href'] for result in results]
        
        return konteks, source_urls # Mengembalikan DUA nilai
    except Exception as e:
        st.error(f"Terjadi kesalahan saat pencarian DuckDuckGo: {e}")
        return None, None

def cari_dengan_google(keyword):
    """Fungsi untuk mencari menggunakan Google, mengambil konteks berupa daftar link."""
    st.write("🔎 Mencari hasil **Riset** (mengambil daftar sumber/link)...")
    query = f'"{keyword_lokal}" site:docrida.go.id OR site:repository.unsoed.ac.id OR site:jatengprov.go.id OR site:undip.ac.id OR site:uns.ac.id OR site:unnes.ac.id OR site:walisongo.ac.id OR site:sinta.kemdikbud.go.id'
    try:
        search_results_urls = [url for url in search(query, num_results=10, sleep_interval=2)]
        if not search_results_urls:
            return None, None
        
        konteks = "Berikut adalah daftar sumber relevan yang ditemukan:\n" + "\n".join(f"- {url}" for url in search_results_urls)
        
        # Mengembalikan DUA nilai (konteks dan link sumber)
        return konteks, search_results_urls
    except Exception as e:
        st.error(f"Terjadi kesalahan saat pencarian Google: {e}")
        return None, None

# --- FUNGSI GENERATOR AI ---
def generate_brief_dengan_ai(keyword, konteks, search_engine):
    """Fungsi untuk memanggil AI Gemini dan membuat draf policy brief (TANPA referensi)."""
    st.write("🤖 AI sedang membaca konteks dan menyusun draf... Mohon tunggu.")
    prompt = f"""
    Anda adalah seorang analis kebijakan publik yang ahli dan bertugas untuk Gubernur Jawa Tengah.
    Tugas Anda adalah membuat draf *policy brief* berdasarkan rangkuman informasi yang diberikan.
    Gunakan HANYA informasi dari 'KONTEKS' yang saya berikan.
    Jangan membuat bagian referensi, karena itu akan ditambahkan nanti.

    Topik Utama: "{keyword}"
    Mesin Pencari yang Digunakan: "{search_engine}"

    KONTEKS:
    ---
    {konteks}
    ---

    Sekarang, berdasarkan konteks di atas, buatkan draf *policy brief* dengan format Markdown yang ketat sebagai berikut (HANYA 4 bagian ini):

    **Judul:** [Buatkan judul yang menarik dan relevan dengan topik]

    ### 1. Ringkasan Eksekutif
    [Tulis ringkasan singkat (1-2 paragraf) yang mencakup masalah utama dan rekomendasi kunci]

    ### 2. Pendahuluan
    [Jelaskan latar belakang dan signifikansi masalah berdasarkan konteks]

    ### 3. Temuan dan Pembahasan
    [Sajikan poin-poin temuan utama dari konteks. Gunakan bullet points jika perlu.]

    ### 4. Rekomendasi Kebijakan
    [Berikan 2-4 rekomendasi kebijakan yang konkret, logis, dan dapat ditindaklanjuti berdasarkan temuan]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Terjadi kesalahan saat menghubungi AI: {e}")
        return None

# --- ANTARMUKA APLIKASI STREAMLIT ---
st.title("📄 Policy Brief Generator Jawa Tengah (AI-Powered)")
st.write("Masukkan topik, dan biarkan AI menyusun draf *policy brief* lengkap dengan referensi.")
st.write("---")

with st.form("input_form"):
    keyword_input = st.text_input("Masukkan Topik atau Kata Kunci:", placeholder="Contoh: digitalisasi umkm di solo")
    search_engine = st.radio(
        "Pilih Mesin Pencari:",
        ('DuckDuckGo', 'Google'),
        horizontal=True,
        help="DuckDuckGo memberikan rangkuman teks, Google memberikan daftar link sumber."
    )
    submitted = st.form_submit_button("🚀 Buat Draf Policy Brief Sekarang")

if submitted:
    if keyword_input:
        with st.spinner("Harap tunggu, proses sedang berjalan..."):
            konteks = None
            sumber_referensi = None # Variabel baru untuk menyimpan link

            if search_engine == 'DuckDuckGo':
                konteks, sumber_referensi = cari_dengan_duckduckgo(keyword_input)
            elif search_engine == 'Google':
                konteks, sumber_referensi = cari_dengan_google(keyword_input)

            if konteks and sumber_referensi:
                st.success(f"Berhasil mengumpulkan konteks & sumber menggunakan {search_engine}!")
                hasil_brief = generate_brief_dengan_ai(keyword_input, konteks, search_engine)
                
                if hasil_brief:
                    st.success("Draf berhasil dibuat!")
                    st.write("---")
                    
                    # Menampilkan hasil dari AI (Judul s/d Rekomendasi)
                    st.markdown(hasil_brief)
                    
                    # BARU: Menambahkan bagian Referensi secara otomatis
                    st.markdown("### 5. Referensi")
                    for url in sumber_referensi:
                        st.markdown(f"- {url}")
            else:
                st.warning("Tidak ditemukan informasi yang cukup relevan dari pencarian. Coba kata kunci atau mesin pencari lain.")
    else:

        st.error("Mohon masukkan topik atau kata kunci terlebih dahulu.")


