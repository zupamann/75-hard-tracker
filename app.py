import datetime
import gspread
import streamlit as st

# Postavke stranice optimizirane za mobitel
st.set_page_config(page_title="75 Hard Pro", page_icon="⚡", layout="centered")

# --- SPAJANJE NA GOOGLE SHEETS ---
try:
    # ⚠️ Ovdje ponovo stavi link SVOJE tablice!
    SHEET_URL = "https://docs.google.com/spreadsheets/d/19un_RxpTOEhzbhaTch9uA85ZljCXyKFewpwLotx1-fs/edit?usp=sharing"
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_url(SHEET_URL)
    worksheet = sh.get_worksheet(0)
except Exception as e:
    st.error(f"Problem sa spajanjem na Google Sheets: {e}")
    st.stop()

# --- OPTIMIZACIJA: DOHVAĆANJE PODATAKA S CACHEOM ---
@st.cache_data(ttl=30)
def get_cached_records():
    return worksheet.get_all_records()

# --- LOGIKA RESTARTA I DATUMA ---
if "start_date_env" not in st.session_state:
    st.session_state["start_date_env"] = datetime.date(2026, 6, 29)

today = datetime.date.today()
current_day = (today - st.session_state["start_date_env"]).days + 1

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
        "voda_l": 0.0, "cardio_tip": "", "cardio_vrijeme": "", "cardio_avg_brzina": "", "cardio_max_brzina": "",
        "snaga_teretana_min": 0, "snaga_sklekovi_kom": 0, "snaga_plank_min": 0.0,
        "hrana_kcal": 0, "hrana_secer": 0, "hrana_protein": 0, "hrana_kreatin": 0,
        "citanje": 0, "slika": 0
    }

# --- INICIJALIZACIJA SESSION STATE-A ---
if "voda_session" not in st.session_state:
    st.session_state["voda_session"] = float(current_data.get("voda_l", 0.0))

if "cardio_list" not in st.session_state:
    c_tips = str(current_data.get("cardio_tip", "")).split(" | ") if current_data.get("cardio_tip") else []
    c_mins = str(current_data.get("cardio_vrijeme", "")).split(" | ") if current_data.get("cardio_vrijeme") else []
    c_avgs = str(current_data.get("cardio_avg_brzina", "")).split(" | ") if current_data.get("cardio_avg_brzina") else []
    c_maxs = str(current_data.get("cardio_max_brzina", "")).split(" | ") if current_data.get("cardio_max_brzina") else []
    
    st.session_state["cardio_list"] = []
    for i in range(max(len(c_tips), len(c_mins))):
        try:
            t = c_tips[i] if i < len(c_tips) else "Hodanje"
            m = int(c_mins[i]) if i < len(c_mins) and c_mins[i] else 0
            a = float(c_avgs[i]) if i < len(c_avgs) and c_avgs[i] else 0.0
            mx = float(c_maxs[i]) if i < len(c_maxs) and c_maxs[i] else 0.0
            if t or m > 0:
                st.session_state["cardio_list"].append({"tip": t, "min": m, "avg": a, "max": mx})
        except:
            pass

# ==========================================
# 🟢 TAB 1: DANAS
# ==========================================
with tab_danas:
    st.markdown(f"<h1 style='text-align: center;'>⚡ 75 HARD PRO — DAN {current_day}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: gray;'>Datum: {today.strftime('%d.%m.%Y.')}</p>", unsafe_allow_html=True)
    
    if st.button("🔄 Restartaj izazov na Dan 1 (Danas)", type="secondary"):
        st.session_state["start_date_env"] = today
        st.success("Izazov uspješno restartan! Danas je Dan 1.")
        st.rerun()
        
    st.write("---")

    # 1. VODA SEKCIJA
    voda_ok = st.session_state["voda_session"] >= 3.8
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
            st.rerun()

    st.write("---")

    # 2. MULTI-CARDIO SEKCIJA S BRZINAMA
    st.markdown("### 🏃‍♂️ 2. Kardio Trening (Min. 45 min ukupno)")
    
    ukupno_cardio_min = sum([trening["min"] for trening in st.session_state["cardio_list"]])
    
    if st.session_state["cardio_list"]:
        st.write("**Dodani treninzi za danas:**")
        for t in st.session_state["cardio_list"]:
            if t['tip'] == "Košarka":
                st.info(f"🏀 {t['tip']}: **{t['min']} min** | Tempo/Intenzitet: {t['avg']}")
            else:
                st.info(f"🏃‍♂️ {t['tip']}: **{t['min']} min** | Srednja: {t['avg']} km/h | Max: {t['max']} km/h")
    else:
        st.write("*Nema dodanih kardio treninga za danas.*")
        
    kardio_ok = ukupno_cardio_min >= 45
    if kardio_ok:
        st.markdown(f"<span style='color:#28a745; font-weight:bold;'>🟢 Kardio status: GOTOVO ({ukupno_cardio_min} min ukupno)</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span style='color:#dc3545; font-weight:bold;'>🔴 Kardio status: U TIJEKU (Trenutno: {ukupno_cardio_min} min | Fali ti još {max(0, 45 - ukupno_cardio_min)} min)</span>", unsafe_allow_html=True)

    st.markdown("#### Dodaj novu sesiju:")
    c_tip = st.selectbox("Način vježbe:", ["Hodanje", "Trčanje", "Bicikl", "Košarka"])
    c_vrijeme = st.number_input("Vrijeme vježbe (min):", min_value=0, max_value=300, value=0, key="cardio_min_input")
    
    # Dinamička polja ovisno o odabranom sportu
    if c_tip == "Košarka":
        c_avg = st.number_input("Tempo / Intenzitet košarke (npr. 1-lagan, 2-jak, 3-intenzivan):", min_value=0.0, value=0.0, key="c_avg_input")
        c_max = 0.0
    else:
        c_avg = st.number_input("Srednja brzina (km/h):", min_value=0.0, max_value=100.0, value=0.0, key="c_avg_input")
        c_max = st.number_input("Maksimalna brzina (km/h):", min_value=0.0, max_value=100.0, value=0.0, key="c_max_input")
    
    col1, col2 = st.columns(2)
    with col1:
        btn_add_cardio = st.button("Dodaj ovaj kardio ➕")
    with col2:
        btn_clear_cardio = st.button("Očisti listu kardija 🗑️")

    if btn_add_cardio and c_vrijeme > 0:
        st.session_state["cardio_list"].append({"tip": c_tip, "min": c_vrijeme, "avg": c_avg, "max": c_max})
        st.success(f"Uspješno dodano: {c_tip}!")
        st.rerun()
        
    if btn_clear_cardio:
        st.session_state["cardio_list"] = []
        st.warning("Lista kardio treninga za danas je ispražnjena.")
        st.rerun()

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
        st.markdown(f"<span style='color:#dc3545; font-weight:bold;'>🔴 Snaga status: U TIJEKU ({uvjeti_snage}/3 ispunjeno, trebaju ti barem 2)</span>", unsafe_allow_html=True)

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
        st.markdown("<span style='color:#dc3545; font-weight:bold;'>🔴 Prehrana status: U TIJEKU</span>", unsafe_allow_html=True)

    st.write("---")

    # 5. & 6. NAVIKE
    st.markdown("### 📚 5. & 📸 6. Dnevne Navike")
    citanje = st.checkbox("Pročitao 10 stranica knjige", value=bool(current_data.get("citanje", 0)))
    slika = st.checkbox("Napravio fotografiju napretka", value=bool(current_data.get("slika", 0)))

    # SPREMANJE I KONAČNA EVALUACIJA
    izazov_prolaz = voda_ok and kardio_ok and snaga_ok and prehrana_ok and citanje and slika
    status_dana = "SUCCESS" if izazov_prolaz else "INCOMPLETE"

    if st.button("SPREMI DANAŠNJI NAPREDAK 🚀", use_container_width=True):
        cardio_tipovi_str = " | ".join([x["tip"] for x in st.session_state["cardio_list"]])
        cardio_minute_str = " | ".join([str(x["min"]) for x in st.session_state["cardio_list"]])
        cardio_avg_str = " | ".join([str(x["avg"]) for x in st.session_state["cardio_list"]])
        cardio_max_str = " | ".join([str(x["max"]) for x in st.session_state["cardio_list"]])
        
        row_data = [
            today_str, current_day, st.session_state["voda_session"],
            cardio_tipovi_str, cardio_minute_str, cardio_avg_str, cardio_max_str,
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
            st.success("Dan spremljen kao SUCCESS! 🔥")
        else:
            st.warning("Podaci spremljeni, ali dan ima status INCOMPLETE.")

# ==========================================
# 📊 TAB 2: POVIJEST & ANALITIKA
# ==========================================
with tab_povijest:
    st.header("📊 Pregled Povijesti")
    if not all_records:
        st.info("Još nema spremljenih podataka u tablici.")
    else:
        import pandas as pd
        df = pd.DataFrame(all_records)
        styled_df = df.copy()
        styled_df["dan_status"] = styled_df["dan_status"].apply(lambda x: "🟢 SUCCESS" if x == "SUCCESS" else "🔴 INCOMPLETE")
        st.dataframe(styled_df[["datum", "dan", "voda_l", "cardio_tip", "cardio_vrijeme", "dan_status"]], use_container_width=True)
