import streamlit as st
import sqlite3
import pandas as pd
import datetime
import matplotlib.pyplot as plt

# --- SAYFA VE SEKME AYARLARI ---
st.set_page_config(page_title="ABB Afet Lojistik Portalı", layout="wide")

DB_YOLU = 'afet_lojistik_web.db'

# --- VERİTABANI BAŞLATMA (Örnek veri ekleme kaldırıldı) ---
def init_db():
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS malzemeler (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        malzeme_adi TEXT UNIQUE NOT NULL,
                        kategori TEXT NOT NULL,
                        birim TEXT NOT NULL,
                        toplam_stok REAL DEFAULT 0,
                        sahadaki_stok REAL DEFAULT 0,
                        zayi_stok REAL DEFAULT 0)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS hareketler (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        malzeme_adi TEXT NOT NULL,
                        islem_tipi TEXT NOT NULL,
                        miktar REAL NOT NULL,
                        tarih TEXT NOT NULL,
                        yer TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

# --- VERİ ÇEKME YARDIMCILARI ---
def get_data(query, params=()):
    conn = sqlite3.connect(DB_YOLU)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def run_query(query, params=()):
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

# --- KURUMSAL BAŞLIK VE LOGOLAR ---
col_logo1, col_baslik, col_logo2 = st.columns([1, 4, 1])

with col_logo1:
    try:
        st.image("abb logo.jpg", use_column_width=True)
    except FileNotFoundError:
        st.warning("abb logo.jpg bulunamadı")

with col_baslik:
    st.markdown("<h3 style='text-align: center; color: #555;'>Afet İşleri ve Risk Yönetimi Dairesi Başkanlığı</h3>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #2C3E50; font-weight: bold;'>Afet Eğitim ve Lojistik Merkezi</h2>", unsafe_allow_html=True)

with col_logo2:
    try:
        st.image("daire başkanlığı logo.jpg", use_column_width=True)
    except FileNotFoundError:
        st.warning("daire başkanlığı logo.jpg bulunamadı")

st.markdown("---")

# Sekmeler
tab1, tab2, tab3 = st.tabs(["📦 1. Malzeme Tanımlama & Düzenleme", "🚚 2. Depo İşlemleri (Sevk/Zayi)", "📊 3. Analiz ve Raporlar"])

# ================= SEKME 1: MALZEME TANIMLAMA =================
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("### Yeni Malzeme Ekle")
        with st.form("malzeme_ekle_form", clear_on_submit=True):
            kategori = st.selectbox("Kategori", ["Çadır & Barınma", "Konteyner", "Isıtıcı & Jeneratör", "Mobil Araçlar", "Hijyen & Tuvalet", "Arama Kurtarma Ekipmanı", "Diğer"])
            malzeme_adi = st.text_input("Malzeme Adı")
            birim = st.selectbox("Birim", ["Adet", "Litre", "Kg", "Ton", "Kutu", "Koli"])
            submit = st.form_submit_button("Sisteme Kaydet")
            
            if submit:
                if malzeme_adi:
                    try:
                        run_query("INSERT INTO malzemeler (malzeme_adi, kategori, birim, toplam_stok, sahadaki_stok, zayi_stok) VALUES (?, ?, ?, 0, 0, 0)", (malzeme_adi, kategori, birim))
                        st.success(f"{malzeme_adi} başarıyla eklendi!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Bu malzeme zaten sistemde var!")
                else:
                    st.warning("Malzeme adı boş olamaz!")
                    
        st.write("### Malzeme Güncelle / Sil")
        malzemeler_df = get_data("SELECT id, malzeme_adi FROM malzemeler ORDER BY malzeme_adi")
        
        if not malzemeler_df.empty:
            islem_turu = st.radio("Yapmak İstediğiniz İşlem:", ["Malzeme Adını Güncelle", "Sistemden Tamamen Sil"])
            secilen_malzeme = st.selectbox("İşlem Yapılacak Malzemeyi Seçin:", malzemeler_df['malzeme_adi'].tolist())
            
            if islem_turu == "Sistemden Tamamen Sil":
                st.warning("DİKKAT: Bu işlem, malzemenin geçmiş tüm kayıtlarını da silecektir!")
                if st.button("Seçili Malzemeyi Kalıcı Olarak Sil", type="primary"):
                    run_query("DELETE FROM malzemeler WHERE malzeme_adi = ?", (secilen_malzeme,))
                    run_query("DELETE FROM hareketler WHERE malzeme_adi = ?", (secilen_malzeme,))
                    st.success(f"{secilen_malzeme} sistemden silindi.")
                    st.rerun()
            else:
                yeni_ad = st.text_input("Yeni Malzeme Adı:", value=secilen_malzeme)
                if st.button("Güncelle", type="primary"):
                    if yeni_ad and yeni_ad != secilen_malzeme:
                        try:
                            run_query("UPDATE malzemeler SET malzeme_adi = ? WHERE malzeme_adi = ?", (yeni_ad, secilen_malzeme))
                            run_query("UPDATE hareketler SET malzeme_adi = ? WHERE malzeme_adi = ?", (yeni_ad, secilen_malzeme))
                            st.success("Malzeme adı güncellendi.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Bu isimde başka bir malzeme zaten var!")

    with col2:
        st.write("### Sistemde Tanımlı Malzemeler")
        df_tanimli = get_data("SELECT id as ID, malzeme_adi as 'Malzeme Adı', kategori as Kategori, birim as Birim FROM malzemeler ORDER BY malzeme_adi")
        st.dataframe(df_tanimli, use_container_width=True, hide_index=True)

# ================= SEKME 2: GİRİŞ / ÇIKIŞ / ZAYİ =================
with tab2:
    col_islem, col_gecmis = st.columns([1, 2])
    
    with col_islem:
        st.write("### Yeni Depo İşlemi")
        with st.form("islem_form", clear_on_submit=True):
            islemler = ["Sahaya Gönder (Depodan Çıkış)", "Sahadan Döndü (Depoya Sağlam Giriş)", "Yeni Alım (Depoya Ekle)", "Sahada Hurda/Zayi Oldu", "Depoda Hurda/Zayi Oldu"]
            islem_tipi = st.selectbox("İşlem Tipi", islemler)
            
            malzemeler_list = get_data("SELECT malzeme_adi FROM malzemeler ORDER BY malzeme_adi")['malzeme_adi'].tolist()
            malzeme_secim = st.selectbox("Malzeme Seç", malzemeler_list if malzemeler_list else ["Önce malzeme tanımlayın"])
            
            miktar = st.number_input("Miktar", min_value=0.1, step=1.0)
            tarih = st.date_input("Tarih", datetime.date.today())
            yer = st.text_input("İlgili Yer / Etkinlik")
            
            islem_kaydet = st.form_submit_button("İşlemi Kaydet ve Stok Güncelle")
            
            if islem_kaydet and malzeme_secim != "Önce malzeme tanımlayın" and yer:
                durum_df = get_data("SELECT toplam_stok, sahadaki_stok, zayi_stok FROM malzemeler WHERE malzeme_adi=?", (malzeme_secim,))
                toplam, sahada, zayi = durum_df.iloc[0]['toplam_stok'], durum_df.iloc[0]['sahadaki_stok'], durum_df.iloc[0]['zayi_stok']
                depoda = toplam - sahada - zayi
                
                hata = False
                if islem_tipi == "Sahaya Gönder (Depodan Çıkış)" and miktar > depoda:
                    st.error(f"Stok yetersiz! Depoda: {depoda}"); hata = True
                elif islem_tipi == "Sahadan Döndü (Depoya Sağlam Giriş)" and miktar > sahada:
                    st.warning(f"Sahada bu kadar görünmüyor! Saha stok: {sahada}"); hata = True
                elif islem_tipi == "Sahada Hurda/Zayi Oldu" and miktar > sahada:
                    st.error(f"Sahada bu kadar miktar yok! Saha stok: {sahada}"); hata = True
                elif islem_tipi == "Depoda Hurda/Zayi Oldu" and miktar > depoda:
                    st.error(f"Depoda bu kadar miktar yok! Depo stok: {depoda}"); hata = True
                
                if not hata:
                    if islem_tipi == "Sahaya Gönder (Depodan Çıkış)":
                        run_query("UPDATE malzemeler SET sahadaki_stok = sahadaki_stok + ? WHERE malzeme_adi = ?", (miktar, malzeme_secim))
                    elif islem_tipi == "Sahadan Döndü (Depoya Sağlam Giriş)":
                        run_query("UPDATE malzemeler SET sahadaki_stok = sahadaki_stok - ? WHERE malzeme_adi = ?", (miktar, malzeme_secim))
                    elif islem_tipi == "Yeni Alım (Depoya Ekle)":
                        run_query("UPDATE malzemeler SET toplam_stok = toplam_stok + ? WHERE malzeme_adi = ?", (miktar, malzeme_secim))
                    elif islem_tipi == "Sahada Hurda/Zayi Oldu":
                        run_query("UPDATE malzemeler SET sahadaki_stok = sahadaki_stok - ?, zayi_stok = zayi_stok + ? WHERE malzeme_adi = ?", (miktar, miktar, malzeme_secim))
                    elif islem_tipi == "Depoda Hurda/Zayi Oldu":
                        run_query("UPDATE malzemeler SET zayi_stok = zayi_stok + ? WHERE malzeme_adi = ?", (miktar, malzeme_secim))
                    
                    run_query("INSERT INTO hareketler (malzeme_adi, islem_tipi, miktar, tarih, yer) VALUES (?, ?, ?, ?, ?)", (malzeme_secim, islem_tipi, miktar, tarih.strftime("%d.%m.%Y"), yer))
                    st.success("İşlem başarıyla kaydedildi!")
                    st.rerun()

    with col_gecmis:
        st.write("### İşlem Defteri ve Geri Alma (Silme)")
        df_hareket = get_data("SELECT id as ID, tarih as Tarih, malzeme_adi as Malzeme, islem_tipi as 'İşlem Tipi', miktar as Miktar, yer as 'Görev Yeri' FROM hareketler ORDER BY id DESC")
        st.dataframe(df_hareket, use_container_width=True, hide_index=True)
        
        if not df_hareket.empty:
            with st.expander("⚠️ Hatalı İşlemi Geri Al (Sil ve Stok Düzelt)"):
                silinecek_islem_id = st.selectbox("Geri Alınacak İşlem (ID Seçin):", df_hareket['ID'].tolist())
                secili_kayit = df_hareket[df_hareket['ID'] == silinecek_islem_id].iloc[0]
                st.info(f"Seçilen İşlem: {secili_kayit['Malzeme']} | {secili_kayit['İşlem Tipi']} | Miktar: {secili_kayit['Miktar']}")
                
                if st.button("Bu İşlemi Geri Al", type="primary"):
                    islem_id = int(silinecek_islem_id)
                    malzeme = secili_kayit['Malzeme']
                    islem = secili_kayit['İşlem Tipi']
                    miktar = float(secili_kayit['Miktar'])

                    # Stokları geriye sarma matematiği
                    if islem == "Sahaya Gönder (Depodan Çıkış)":
                        run_query("UPDATE malzemeler SET sahadaki_stok = sahadaki_stok - ? WHERE malzeme_adi = ?", (miktar, malzeme))
                    elif islem == "Sahadan Döndü (Depoya Sağlam Giriş)":
                        run_query("UPDATE malzemeler SET sahadaki_stok = sahadaki_stok + ? WHERE malzeme_adi = ?", (miktar, malzeme))
                    elif islem == "Yeni Alım (Depoya Ekle)":
                        run_query("UPDATE malzemeler SET toplam_stok = toplam_stok - ? WHERE malzeme_adi = ?", (miktar, malzeme))
                    elif islem == "Sahada Hurda/Zayi Oldu":
                        run_query("UPDATE malzemeler SET sahadaki_stok = sahadaki_stok + ?, zayi_stok = zayi_stok - ? WHERE malzeme_adi = ?", (miktar, miktar, malzeme))
                    elif islem == "Depoda Hurda/Zayi Oldu":
                        run_query("UPDATE malzemeler SET zayi_stok = zayi_stok - ? WHERE malzeme_adi = ?", (miktar, malzeme))

                    run_query("DELETE FROM hareketler WHERE id = ?", (islem_id,))
                    st.success("İşlem başarıyla geri alındı ve stok düzeltildi!")
                    st.rerun()

            csv = df_hareket.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 İşlem Defterini Excel (CSV) Olarak İndir", data=csv, file_name='islem_defteri.csv', mime='text/csv')

# ================= SEKME 3: RAPOR VE ANALİZ =================
with tab3:
    st.write("### 🏢 Depolardaki Anlık Genel Durum (Kullanıma Hazır Miktara Göre Sıralı)")
    
    df_stok = get_data("SELECT malzeme_adi as Malzeme, kategori as Kategori, toplam_stok, sahadaki_stok, zayi_stok, birim as Birim FROM malzemeler")
    df_stok['Depoda (Mevcut)'] = df_stok['toplam_stok'] - df_stok['sahadaki_stok'] - df_stok['zayi_stok']
    
    df_stok = df_stok.rename(columns={'toplam_stok': 'Toplam Alınan', 'sahadaki_stok': 'Görevde (Sahada)', 'zayi_stok': 'Zayi / Hurda'})
    df_stok = df_stok[['Malzeme', 'Kategori', 'Toplam Alınan', 'Görevde (Sahada)', 'Zayi / Hurda', 'Depoda (Mevcut)', 'Birim']]
    df_stok = df_stok.sort_values(by='Depoda (Mevcut)', ascending=False)
    
    st.dataframe(df_stok, use_container_width=True, hide_index=True)
    
    csv_stok = df_stok.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Güncel Envanter Raporunu İndir", data=csv_stok, file_name='guncel_envanter.csv', mime='text/csv')
    
    st.markdown("---")
    
    col_grafik, col_analiz = st.columns(2)
    
    with col_grafik:
        st.write("### 📈 Kullanıma Hazır Malzeme Grafiği")
        df_grafik = df_stok[df_stok['Depoda (Mevcut)'] > 0]
        if not df_grafik.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.bar(df_grafik['Malzeme'], df_grafik['Depoda (Mevcut)'], color='#3498DB')
            plt.xticks(rotation=45, ha='right')
            plt.ylabel('Depo Mevcudu')
            st.pyplot(fig)
        else:
            st.info("Grafik çizilecek mevcut stok bulunamadı.")
            
    with col_analiz:
        st.write("### 🎯 Saha Operasyon Analizi")
        df_analiz = get_data("SELECT malzeme_adi as Malzeme, SUM(miktar) as 'Toplam Giden Miktar', COUNT(id) as 'Sevkiyat Sayısı' FROM hareketler WHERE islem_tipi='Sahaya Gönder (Depodan Çıkış)' GROUP BY malzeme_adi ORDER BY SUM(miktar) DESC")
        st.write("**En Çok Sahaya Gönderilen Malzemeler**")
        st.dataframe(df_analiz, use_container_width=True, hide_index=True)
        
        df_yer = get_data("SELECT yer as 'Görev Yeri', COUNT(id) as 'Operasyon Sayısı' FROM hareketler WHERE islem_tipi='Sahaya Gönder (Depodan Çıkış)' GROUP BY yer ORDER BY COUNT(id) DESC")
        st.write("**En Çok Sevkiyat Yapılan Bölgeler**")
        st.dataframe(df_yer, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: right; color: gray; font-style: italic;'>Tüm hakları saklıdır © Erdem KUŞÇU - 2026</p>", unsafe_allow_html=True)