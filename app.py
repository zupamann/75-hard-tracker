import datetime
import gspread
import streamlit as st

# Postavke stranice optimizirane za mobitel
st.set_page_config(page_title="75 Hard Pro", page_icon="⚡", layout="centered")

# --- SPAJANJE NA GOOGLE SHEETS ---
try:
    # ⚠️ OVDJE ZALIJEPI LINK SVOJE GOOGLE TABLICE:
    SHEET_URL = "https://docs.google.com/spreadsheets/d/19un_RxpTOEhzbhaTch9uA85ZljCXyKFewpwLotx1-fs/edit?usp=sharing"
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_url(SHEET_URL)
    worksheet = sh.get_worksheet(0)
    
    try:
        nnn_worksheet = sh.worksheet("NNN_Log")
    except:
        nnn_worksheet = sh.add_worksheet(title="NNN_Log", rows="100", cols="3")
        nnn_worksheet.append_row(["relaps_datum", "relaps_vrijeme", "prethodni_streak"])
except Exception as e:
    st.error(f"Problem sa spajanjem na Google Sheets: {e}")
    st.stop()

# --- OPTIMIZACIJA: DOHVAĆANJE PODATAKA S CACHEOM ---
@st.cache_data(ttl=30)
def get_cached_records():
    return worksheet.get_all_records()

@st.cache_data(ttl=30)
def get_cached_nnn():
    try:
        return nnn_worksheet.get_all_records()
    except:
        return []

all_records = get_cached_records()
today = datetime.date.today()
now = datetime.datetime.now()

# --- AUTOMATSKI RESET NA DAN 1 AKO JE BILO NEUSPJEŠNIH DANA ---
BASE_START_DATE = datetime.date(2026, 10, 22)
latest_reset_date = BASE_START_DATE

for record in all_records:
    rec_status = str(record.get("dan_status", "")).upper()
    rec_datum_str = str(record.get("datum", ""))
    
    if "INCOMPLETE" in rec_status and rec_datum_str:
        try:
            rec_date = datetime.datetime.strptime(rec_datum_str, "%Y-%m-%d").date()
            if rec_date >= BASE_START_DATE:
                next_day = rec_date + datetime.timedelta(days=1)
                if next_day > latest_reset_date:
                    latest_reset_date = next_day
        except:
            pass

START_DATE = latest_reset_date
current_day = (today - START_DATE).days + 1
if current_day < 1:
    current_day = 1

# --- LOGIKA NNN STREAKA (SATI I DANI) ---
nnn_records = get_cached_nnn()

if "nnn_last_relapse" not in st.session_state:
    if nnn_records:
        last_entry_date = str(nnn_records[-1].get("relaps_datum", ""))
        last_entry_time = str(nnn_records[-1].get("relaps_vrijeme", "00:00:00"))
        try:
            full_dt_str = f"{last_entry_date} {last_entry_time}"
            st.session_state["nnn_last_relapse"] = datetime.datetime.strptime(full_dt_str, "%Y-%m-%d %H:%M:%S")
        except:
            st.session_state["nnn_last_relapse"] = now
    else:
        st.session_state["nnn_last_relapse"] = now

time_diff = now - st.session_state["nnn_last_relapse"]
total_hours = int(time_diff.total_seconds() // 3600)
days = total_hours // 24
remaining_hours = total_hours % 24

# --- TABS ZA NAVIGACIJU ---
tab_danas, tab_povijest = st.tabs(["📝 Danas", "📊 Povijest & Analitika"])

today_str = today.strftime("%Y-%m-%d")
existing_row = None
current_data = {}

for idx, record in enumerate(all_records):
    if str(record.get("datum")) == today_str:
        existing_row = idx + 2
        current_data = record
        break

if not current_data:
    current_data = {
        "voda_l": 0.0, "cardio_tip": "", "cardio_vrijeme": "", "cardio_avg_brzina": "", "cardio_max_brzina": "",
        "snaga_teretana_min": 0, "snaga_sklekovi_kom": 0, "snaga_plank_min": 0.0,
        "hrana_kcal": 0, "hrana_potroseno_kcal": 0, "hrana_secer": 0, "hrana_protein": 0, "hrana_kreatin": 0,
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
    
    if START_DATE > BASE_START_DATE:
        st.info(f"🔄 Izazov je automatski resetiran na Dan 1 dana {START_DATE.strftime('%d.%m.%Y.')} zbog neuspješnog dana u povijesti.")
        
    st.write("---")

    # 🔥 NNN / STREAK TRACKER SEKCIJA
    st.subheader("🔥 NNN Tracker")
    col_nnn1, col_nnn2 = st.columns([2, 1])
    
    with col_nnn1:
        st.metric(label="Čist od zadnjeg relapsa:", value=f"{total_hours} h", delta=f"{days}d {remaining_hours}h")
        st.caption(f"Zadnji relaps: {st.session_state['nnn_last_relapse'].strftime('%d.%m.%Y. u %H:%M')}")
        
    with col_nnn2:
        if st.button("🚨 RELAPS", type="primary", width='stretch'):
            now_relapse = datetime.datetime.now()
            st.session_state["nnn_last_relapse"] = now_relapse
            
            try:
                relapse_date_str = now_relapse.strftime("%Y-%m-%d")
                relapse_time_str = now_relapse.strftime("%H:%M:%S")
                nnn_worksheet.append_row([relapse_date_str, relapse_time_str, f"{total_hours}h ({days}d {remaining_hours}h)"])
                st.cache_data.clear()
            except Exception as ex:
                st.error(f"Greška kod spremanja NNN relapsa: {ex}")
                
            st.warning("Streak je resetiran. Glavu gore, idemo dalje!")
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
    
    if c_tip == "Košarka":
        c_avg = st.number_input("Tempo / Intenzitet košarke (npr. 1-lagan, 2-jak, 3-intenzivan):", min_value=0.0, value=0
