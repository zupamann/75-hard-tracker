import datetime
import gspread
import streamlit as st

# Postavke stranice optimizirane za mobitel
st.set_page_config(page_title="75 Hard Pro", page_icon="⚡", layout="centered")

# --- SPAJANJE NA GOOGLE SHEETS ---
try:
    SHEET_URL = "https://docs.google.com/spreadsheets/d/19un_RxpT0EhzbhaTch9uA85Z1jCXyKFewpwLotx1-fs/edit?usp=sharing"
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_url(SHEET_URL)
    worksheet = sh.get_worksheet(0)
except Exception as e:
    st.error(f"Problem sa spajanjem na Google Sheets: {e}")
    st.stop()

# --- OPTIMIZACIJA: DOHVAĆANJE PODATAKA S CACHEOM ---
@st.cache_data(ttl=60)
def get_cached_records():
    return worksheet.get_all_records()

# --- LOGIKA DATUMA ---
START_DATE = datetime.date(2026, 6, 19)
today = datetime.date.today()
current_day = (today - START_DATE).days + 1

# --- TABS ZA NAVIGACIJU ---
tab_danas, tab_povijest = st.tabs(["📝 Danas", "📊 Povijest & Analitika"])

# Učitavanje podataka iz baze
all_records = get_cached_records()
today_str = today.strftime("%Y-%m-%d")
existing_row = None
current_data = {}

for idx, record in enumerate(all_records):
    if record.get("datum") == today_str:
        existing_row = idx + 2
        current_data = record
        break

if not current_data:
    current_data = {
        "voda_l": 0.0, "cardio_tip": "Hodanje", "cardio_vrijeme": 0, "cardio_avg_brzina": 0.0, "cardio_max_brzina": 0.0,
        "snaga_teretana_min": 0, "snaga_sklekovi_kom": 0, "snaga_plank_min": 0.0,
        "hrana_kcal": 0, "hrana_secer": 0, "hrana_protein": 0, "hrana_kreatin": 0,
        "citanje": 0, "slika": 0, "biljeske": ""
    }

# Zaključavanje početne vrijednosti vode u Session State
if "voda_session" not in st.session_state:
    st.session_state["voda_session"] = float(current_data.get("voda_l", 0.0))


# ==========================================
# 🟢 TAB 1: DANAS (FORMULAR & POBOLJŠANI STATUSI)
# ==========================================
with tab_danas:
    st.markdown(f"<h1 style='text-align: center;'>⚡ 75 HARD PRO — DAN {current_day}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: gray;'>Datum: {today.strftime('%d.%m.%Y.')}</p>", unsafe_allow_html=True)
    st.write("---")

    # --- EVALUACIJA STATUSA (Za bolji prikaz) ---
    voda_ok = st.session_state["voda_session"] >= 3.8
    
    # Privremeni dohvat inputa za brzu evaluaciju na vrhu
    # (Streamlit renderira elemente redom, ali možemo koristiti logiku za indikatore pokraj podnaslova)
    
    # 1. VODA SEKCIJA
    if voda_ok:
        st.markdown("### 🟢 1. Hidratacija — **GOTOVO**")
    else:
        st.markdown("### 🔴 1. Hidratacija — **U TIJEKU** (Cilj: 3.8L)")
        
    trenutna_voda = st.session_state["voda_session"]
    st.metric(label="Trenutno popijeno", value=f"{trenutna_voda} L / 3.8 L")
    dodaj_vodu = st.number_input("Dodaj vodu (L):", min_value=0.0, max_value=4.0, step=0.1, value=0.0, key="voda_input")
    if st.button("Upiši vodu 💧"):
        if dodaj_vodu > 0.0:
            st.session_state["voda_session"] = round(trenutna_voda + dodaj_vodu, 2)
            st.cache_data.clear()
            st.rerun()

    st.write("---")

    # 2. CARDIO SEKCIJA
    st.markdown("### 🏃‍♂️ 2. Kardio Trening (Min. 45 min)")
    c_tip = st.selectbox("Način vježbe:", ["Hodanje", "Trčanje", "Bicikl", "Košarka"], index=["Hodanje", "Trčanje", "Bicikl", "Košarka"].index(current_data.get("cardio_tip", "Hodanje")))
    c_vrijeme = st.number_input("Vrijeme (min):", min_value=0, max_value=300, value=int(current_data.get("cardio_vrijeme", 0)))

    if c_tip == "Košarka":
        c_avg = st.number_input("Tempo / Intenzitet košarke (npr. 1-lagan, 2-jak, 3-intenzivan):", min_value=0.0, value=float(current_data.get("cardio_avg_brzina", 0.0)))
        c_max = 0.0
    else:
        c_avg = st.number_input("Srednja brzina (km/h):", min_value=0.0, max_value=100.0, value=float(current_data.get("cardio_avg_brzina", 0.0)))
        c_max = st.number_input("Maksimalna brzina (km/h):", min_value=0.0, max_value=100.0, value=float(current_data.get("cardio_max_brzina", 0.0)))

    kardio_ok = c_vrijeme >= 45
    if kardio_ok:
        st.markdown("<span style='color:#28a745; font-weight:bold;'>🟢 Kardio status: GOTOVO</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span style='color:#dc3545; font-weight:bold;'>🔴 Kardio status: U TIJEKU (Fali ti još {45 - c_vrijeme} min)</span>", unsafe_allow_html=True)

    st.write("---")

    # 3. SNAGA SEKCIJA
    st.markdown("### 🏋️‍♂️ 3. Trening Snage (2 od 3 za prolaz)")
    s_teretana = st.number_input("Teretana - Vrijeme (min):", min_value=0, max_value=180, value=int(current_data.get("snaga_teretana_min", 0)))
    s_sklekovi = st.number_input("Sklekovi - Količina (kom):", min_value=0, max_value=500, value=int(current_data.get("snaga_sklekovi_kom", 0)))
    s_plank = st.number_input("Plank - Vrijeme (min):", min_value=0.0, max_value=60.0, step=0.5, value=float(current_data.get("snaga_plank_min", 0.0)))

    uvjeti_snage = sum([1 for x in [s_teretana, s_sklekovi, s_plank] if x > 0])
    snaga_ok = uvjeti_snage >= 2
    if snaga_ok:
        st.markdown(f"<span style='color:#28a745; font-weight:bold;'>🟢 Snaga status: GOTOVO ({uvjeti_snage}/3 ispunjeno)</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span style='color:#dc3545; font-weight:bold;'>🔴 Snaga status: U TIJEKU (Ispunio si {uvjeti_snage}/3, trebaju ti barem 2)</span>", unsafe_allow_html=True)

    st.write("---")

    # 4. PREHRANA SEKCIJA
    st.markdown("### 🥩 4. Prehrana & Suplementacija")
    p_kcal = st.number_input("Kalorije (kcal):", min_value=0, max_value=10000, value=int(current_data.get("hrana_kcal", 0)))
    p_secer = st.number_input("Šećer (g):", min_value=0, max_value=500, value=int(current_data.get("hrana_secer", 0)))
    p_protein = st.number_input("Protein (g):", min_value=0, max_value=500, value=int(current_data.get("hrana_protein", 0)))
    p_kreatin = st.number_input("Kreatin (g):", min_value=0, max_value=50, value=int(current_data.get("hrana_kreatin", 0)))

    prehrana_ok = p_kcal > 0 or p_protein > 0
    if prehrana_ok:
        st.markdown("<span style='color:#28a745; font-weight:bold;'>🟢 Prehrana status: UPISANO</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#dc3545; font-weight:bold;'>🔴 Prehrana status: U TIJEKU (Upiši kalorije ili proteine)</span>", unsafe_allow_html=True)

    st.write("---")

    # 5. & 6. NAVIKE
    st.markdown("### 📚 5. & 📸 6. Dnevne Navike")
    citanje = st.checkbox("Pročitao 10 stranica knjige", value=bool(current_data.get("citanje", 0)))
    slika = st.checkbox("Napravio fotografiju napretka", value=bool(current_data.get("slika", 0)))

    if citanje: st.markdown("<span style='color:#28a745;'>📚 Čitanje: GOTOVO</span>", unsafe_allow_html=True)
    if slika: st.markdown("<span style='color:#28a745;'>📸 Slika: GOTOVO</span>", unsafe_allow_html=True)

    st.write("---")

    # SPREMANJE STATUSANA
    izazov_prolaz = voda_ok and kardio_ok and snaga_ok and prehrana_ok and citanje and slika
    status_dana = "SUCCESS" if izazov_prolaz else "INCOMPLETE"

    if st.button("SPREMI DANAŠNJI NAPREDAK 🚀", use_container_width=True):
        row_data = [
            today_str, current_day, st.session_state["voda_session"],
            c_tip, c_vrijeme, c_avg, c_max,
            s_teretana, s_sklekovi, s_plank,
            p_kcal, p_secer, p_protein, p_kreatin,
            1 if citanje else 0, 1 if slika else 0,
            status_dana
        ]
        if existing_row:
            worksheet.update(range_name=f"A{existing_row}:Q{existing_row}", values=[row_data])
        else:
            worksheet.append_row(row_data)
            
        st.cache_data.clear()
        if izazov_prolaz:
            st.balloons()
            st.success("Dan je uspješno završen i spremljen! Čist kod, čist dan! 🔥")
        else:
            st.warning("Podaci spremljeni, ali nisu svi uvjeti za Hard 75 zadovoljeni za danas.")


# ==========================================
# 📊 TAB 2: POVIJEST & ANALITIKA
# ==========================================
with tab_povijest:
    st.header("📊 Pregled Povijesti i Statistike")
    
    if not all_records:
        st.info("Još nema spremljenih dana u bazi podataka.")
    else:
        # Pretvaramo podatke iz baze u format pogodan za prikaz
        import pandas as pd
        df = pd.DataFrame(all_records)
        
        # 1. UKUPNI PREGLED (Tablica svih dana)
        st.subheader("📋 Ukupni Pregled (Svi dani)")
        
        # Formatiranje prikaza tablice radi čitljivosti
        styled_df = df.copy()
        styled_df["dan_status"] = styled_df["dan_status"].apply(lambda x: "🟢 SUCCESS" if x == "SUCCESS" else "🔴 INCOMPLETE")
        st.dataframe(styled_df[["datum", "dan", "voda_l", "cardio_tip", "cardio_vrijeme", "dan_status"]], use_container_width=True)
        
        st.write("---")
        
        # 2. POJEDINAČNI PREGLED PO KATEGORIJAMA
        st.subheader("🔍 Povijest po kategorijama")
        kategorija = st.selectbox("Odaberi kategoriju za detaljan pregled:", 
                                  ["1. Hidratacija (Voda)", "2. Kardio", "3. Trening Snage", "4. Prehrana & Suplementi", "5. & 6. Navike"])
        
        if kategorija == "1. Hidratacija (Voda)":
            st.metric("Ukupno popijeno vode u izazovu:", f"{round(df['voda_l'].sum(), 1)} Litara")
            st.dataframe(df[["datum", "dan", "voda_l"]].rename(columns={"voda_l": "Voda (L)"}), use_container_width=True)
            
        elif kategorija == "2. Kardio":
            st.metric("Ukupno minuta kardija:", f"{df['cardio_vrijeme'].sum()} min")
            st.dataframe(df[["datum", "dan", "cardio_tip", "cardio_vrijeme", "cardio_avg_brzina", "cardio_max_brzina"]]\
                         .rename(columns={"cardio_tip": "Tip", "cardio_vrijeme": "Vrijeme (min)", "cardio_avg_brzina": "Avg km/h", "cardio_max_brzina": "Max km/h"}), use_container_width=True)
            
        elif kategorija == "3. Trening Snage":
            st.dataframe(df[["datum", "dan", "snaga_teretana_min", "snaga_sklekovi_kom", "snaga_plank_min"]]\
                         .rename(columns={"snaga_teretana_min": "Teretana (min)", "snaga_sklekovi_kom": "Sklekovi (kom)", "snaga_plank_min": "Plank (min)"}), use_container_width=True)
            
        elif kategorija == "4. Prehrana & Suplementi":
            avg_kcal = int(df['hrana_kcal'].mean()) if len(df) > 0 else 0
            st.metric("Prosječan dnevni unos kalorija:", f"{avg_kcal} kcal")
            st.dataframe(df[["datum", "dan", "hrana_kcal", "hrana_secer", "hrana_protein", "hrana_kreatin"]]\
                         .rename(columns={"hrana_kcal": "Kalorije", "hrana_secer": "Šećer (g)", "hrana_protein": "Protein (g)", "hrana_kreatin": "Kreatin (g)"}), use_container_width=True)
            
        elif kategorija == "5. & 6. Navike":
            procitano_dana = df['citanje'].sum()
            slikano_dana = df['slika'].sum()
            st.write(f"📚 Knjiga pročitana: **{procitano_dana} / {len(df)} dana**")
            st.write(f"📸 Napredak uslikan: **{slikano_dana} / {len(df)} dana**")
            st.dataframe(df[["datum", "dan", "citanje", "slika"]].replace({1: "✅ Da", 0: "❌ Ne"}), use_container_width=True)
