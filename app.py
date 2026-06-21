import datetime
import gspread
import streamlit as st

# Postavke stranice optimizirane za mobitel
st.set_page_config(page_title="75 Hard Pro", page_icon="⚡", layout="centered")

# --- SPAJANJE NA GOOGLE SHEETS ---
try:
    SHEET_URL = "https://docs.google.com/spreadsheets/d/19un_RxpTOEhzbhaTch9uA85ZljCXyKFewpwLotx1-fs/edit?usp=sharing"
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_url(SHEET_URL)
    worksheet = sh.get_worksheet(0)
except Exception as e:
    st.error(f"Problem sa spajanjem na Google Sheets: {e}")
    st.stop()
    
# --- LOGIKA DATUMA ---
# Budući da je izazov počeo u petak 19.6.2026.
START_DATE = datetime.date(2026, 6, 19)
today = datetime.date.today()
current_day = (today - START_DATE).days + 1

st.markdown(f"<h1 style='text-align: center;'>⚡ 75 HARD PRO — DAN {current_day}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: gray;'>Datum: {today.strftime('%d.%m.%Y.')}</p>", unsafe_allow_html=True)
st.write("---")

# --- DOHVAĆANJE POSTOJEĆIH PODATAKA ZA DANAS ---
all_records = worksheet.get_all_records()
today_str = today.strftime("%Y-%m-%d")
existing_row = None
current_data = {}

for idx, record in enumerate(all_records):
    if record.get("datum") == today_str:
        existing_row = idx + 2
        current_data = record
        break

# Ako nema podataka za danas, postavi zadane vrijednosti
if not current_data:
    current_data = {
        "voda_l": 0.0, "cardio_tip": "Hodanje", "cardio_vrijeme": 0, "cardio_avg_brzina": 0.0, "cardio_max_brzina": 0.0,
        "snaga_teretana_min": 0, "snaga_sklekovi_kom": 0, "snaga_plank_min": 0.0,
        "hrana_kcal": 0, "hrana_secer": 0, "hrana_protein": 0, "hrana_kreatin": 0,
        "citanje": 0, "slika": 0
    }

# --- FORMULAR ZA UPIS ---

# 1. VODA
st.subheader("💧 1. Hidratacija")
trenutna_voda = float(current_data.get("voda_l", 0.0))
voda_status = "✅ Ispunjeno" if trenutna_voda >= 3.8 else "❌ Nedovoljno (Cilj: 3.8L)"
st.metric(label=f"Status: {voda_status}", value=f"{trenutna_voda} L")
dodaj_vodu = st.number_input("Dodaj vodu (L):", min_value=0.0, max_value=4.0, step=0.1, value=0.0, key="voda_input")
if st.button("Upiši vodu 💧"):
    trenutna_voda = round(trenutna_voda + dodaj_vodu, 2)
    st.rerun()

st.write("---")

# 2. CARDIO TRENING
st.subheader("🏃‍♂️ 2. Kardio Trening (Min. 45 min)")
c_tip = st.selectbox("Način vježbe:", ["Hodanje", "Trčanje", "Bicikl", "Košarka"], index=["Hodanje", "Trčanje", "Bicikl", "Košarka"].index(current_data.get("cardio_tip", "Hodanje")))
c_vrijeme = st.number_input("Vrijeme (min):", min_value=0, max_value=300, value=int(current_data.get("cardio_vrijeme", 0)))

if c_tip == "Košarka":
    c_avg = st.number_input("Tempo (npr. lagan, jak, intenzivan):", value=0.0, description="Ovdje upiši subjektivni tempo ako želiš, ili ostavi 0")
    c_max = 0.0
else:
    c_avg = st.number_input("Srednja brzina (km/h):", min_value=0.0, max_value=100.0, value=float(current_data.get("cardio_avg_brzina", 0.0)))
    c_max = st.number_input("Maksimalna brzina (km/h):", min_value=0.0, max_value=100.0, value=float(current_data.get("cardio_max_brzina", 0.0)))

st.write("---")

# 3. TRENING SNAGE
st.subheader("🏋️‍♂️ 3. Trening Snage (Uspjeh ako su 2 od 3 ispunjena)")
s_teretana = st.number_input("Teretana - Vrijeme (min):", min_value=0, max_value=180, value=int(current_data.get("snaga_teretana_min", 0)))
s_sklekovi = st.number_input("Sklekovi - Količina (kom):", min_value=0, max_value=500, value=int(current_data.get("snaga_sklekovi_kom", 0)))
s_plank = st.number_input("Plank - Vrijeme (min):", min_value=0.0, max_value=60.0, step=0.5, value=float(current_data.get("snaga_plank_min", 0.0)))

# Provjera uvjeta za snagu
uvjeti_snage = 0
if s_teretana > 0: uvjeti_snage += 1
if s_sklekovi > 0: uvjeti_snage += 1
if s_plank > 0: uvjeti_snage += 1
snaga_ok = uvjeti_snage >= 2

if snaga_ok:
    st.success(f"💪 Trening snage: PROLAZ ({uvjeti_snage}/3 ispunjeno)")
else:
    st.warning(f"⚠️ Trening snage: Trebaš ispuniti barem 2 od 3 stavke (Trenutno: {uvjeti_snage}/3)")

st.write("---")

# 4. PREHRANA
st.subheader("🥩 4. Prehrana & Suplementacija")
p_kcal = st.number_input("Kalorije (kcal):", min_value=0, max_value=10000, value=int(current_data.get("hrana_kcal", 0)))
p_secer = st.number_input("Šećer (g):", min_value=0, max_value=500, value=int(current_data.get("hrana_secer", 0)))
p_protein = st.number_input("Protein (g):", min_value=0, max_value=500, value=int(current_data.get("hrana_protein", 0)))
p_kreatin = st.number_input("Kreatin (g):", min_value=0, max_value=50, value=int(current_data.get("hrana_kreatin", 0)))

# Bilo kakav unos (npr. ako su unesene kalorije ili proteini) znači da je praćeno
prehrana_ok = p_kcal > 0 or p_protein > 0

st.write("---")

# 5. & 6. ČITANJE I SLIKA
st.subheader("📚 5. & 📸 6. Dnevne Navike")
citanje = st.checkbox("Pročitao 10 stranica knjige", value=bool(current_data.get("citanje", 0)))
slika = st.checkbox("Napravio fotografiju napretka", value=bool(current_data.get("slika", 0)))

st.write("---")

# --- PROVJERA KONAČNOG STATUSA DANA ---
kardio_ok = c_vrijeme >= 45
voda_ok = trenutna_voda >= 3.8

izazov_prolaz = voda_ok and kardio_ok and snaga_ok and prehrana_ok and citanje and slika
status_dana = "SUCCESS" if izazov_prolaz else "INCOMPLETE"

if st.button("SPREMI DANAŠNJI NAPREDAK 🚀", use_container_width=True):
    row_data = [
        today_str,
        current_day,
        trenutna_voda,
        header_frame_fix_type := c_tip,
        c_vrijeme,
        c_avg,
        c_max,
        s_teretana,
        s_sklekovi,
        s_plank,
        p_kcal,
        p_secer,
        p_protein,
        p_kreatin,
        1 if citanje else 0,
        1 if slika else 0,
        status_dana
    ]
    
    if existing_row:
        worksheet.update(range_name=f"A{existing_row}:Q{existing_row}", values=[row_data])
    else:
        worksheet.append_row(row_data)
        
    if izazov_prolaz:
        st.balloons()
        st.success("Dan je uspješno završen i spremljen! Čist kod, čist dan! 🔥")
    else:
        st.warning("Podaci spremljeni, ali nisu svi uvjeti za Hard 75 zadovoljeni za danas.")
