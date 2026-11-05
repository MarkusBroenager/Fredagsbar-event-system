import os

import httpx
import streamlit as st

API_URL = os.environ.get("API_URL", "http://127.0.0.1:5000")

TIMEOUT = 2

st.set_page_config(page_title="Fredagsbaren", page_icon=":beers:")
st.title("Fredagsbarens events")


if "besked" in st.session_state:
    st.success(st.session_state.pop("besked"))


def vis_statusfejl(fejl):
    try:
        besked = fejl.response.json().get("error", "Ukendt fejl")
    except ValueError:
        besked = fejl.response.text or "Ukendt fejl"
    st.error(f"{fejl.response.status_code}: {besked}")


def kald(metode, sti, **kw):
    try:
        with httpx.Client(base_url=API_URL, timeout=TIMEOUT) as klient:
            svar = klient.request(metode, sti, **kw)
            svar.raise_for_status()

            if svar.status_code == 204:
                return True, None
            return True, svar.json()

    except httpx.HTTPStatusError as fejl:
        vis_statusfejl(fejl)

    except (httpx.ConnectError, httpx.ConnectTimeout):
        st.error(f"Kan ikke få forbindelse til API'en på {API_URL}. Kører den?")

    except httpx.TimeoutException:
        st.error(f"API'en svarede ikke inden for {TIMEOUT} sekunder.")

    return False, None


with st.sidebar:
    st.header("Dig")
    st.text_input("Dit navn", key="navn")

    st.divider()
    st.caption(f"API: {API_URL}")

    if st.button("Test timeout"):
        kald("GET", "/debug/slow")

navn = st.session_state.get("navn", "").strip()

ok, events = kald("GET", "/events")

if not ok:
    st.stop()


# --- 1. Oversigt --------------------------------------------------------
st.subheader("Oversigt")

if not events:
    st.info("Der er ingen events endnu.")
else:
    st.dataframe(
        [
            {
                "Titel": e["title"],
                "Dato": e["date"],
                "Tilmeldte": len(e["participants"]),
                "Ledige pladser": e["capacity"] - len(e["participants"]),
            }
            for e in events
        ],
        hide_index=True,
    )


# --- 2. Tilmeld og afmeld ----------------------------------------------
if events:
    st.divider()
    st.subheader("Tilmelding")

    efter_id = {e["id"]: e for e in events}

    valgt_id = st.selectbox(
        "Vælg event",
        list(efter_id),
        format_func=lambda i: f"{efter_id[i]['title']} ({efter_id[i]['date']})",
    )
    valgt = efter_id[valgt_id]

    tilmeldte = valgt["participants"]
    ledige = valgt["capacity"] - len(tilmeldte)
    fuldt = ledige <= 0

    st.write(f"**Deltagere ({len(tilmeldte)}/{valgt['capacity']}):** "
             + (", ".join(tilmeldte) if tilmeldte else "ingen endnu"))

    if fuldt:
        st.warning("Eventet er fuldt.")

    kol_til, kol_af = st.columns(2)

    if kol_til.button("Tilmeld mig", disabled=fuldt):
        ok, _ = kald("POST", f"/events/{valgt['id']}/signups", json={"name": navn})
        if ok:
            st.session_state.besked = f"{navn} er tilmeldt {valgt['title']}."
            st.rerun()

    if kol_af.button("Afmeld mig"):
        ok, _ = kald("DELETE", f"/events/{valgt['id']}/signups/{navn}")
        if ok:
            st.session_state.besked = f"{navn} er afmeldt {valgt['title']}."
            st.rerun()


# --- 3. Opret event -----------------------------------------------------
st.divider()
st.subheader("Opret event")

with st.form("nyt_event"):
    titel = st.text_input("Titel")
    dato = st.date_input("Dato")
    pladser = st.number_input("Antal pladser", min_value=1, value=10, step=1)

    if st.form_submit_button("Opret"):
        ok, nyt = kald(
            "POST",
            "/events",
            json={"title": titel, "date": str(dato), "capacity": int(pladser)},
        )
        if ok:
            st.session_state.besked = f"{nyt['title']} er oprettet."
            st.rerun()
