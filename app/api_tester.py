"""Streamlit API Tester - Test de OnSpectAI API zoals Laravel dat zou doen."""

import streamlit as st
import requests

st.set_page_config(
    page_title="OnSpectAI API Tester",
    page_icon="🔌",
    layout="wide",
)

st.title("🔌 OnSpectAI API Tester")
st.markdown("*Test de API zoals Laravel (of elke andere client) dat zou doen*")

# Sidebar: API configuratie
with st.sidebar:
    st.header("API Configuratie")
    api_url = st.text_input("API URL", value="http://localhost:8000")
    api_key = st.text_input(
        "API Key",
        value="",
        type="password",
        help="Leeg laten voor development mode (als ONSPECTAI_API_KEY niet gezet is)"
    )

    st.divider()

    # Health check
    if st.button("🏥 Health Check"):
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "ok":
                    st.success(f"✅ API online\n\nModel: {data['model']}")
                else:
                    st.warning(f"⚠️ API degraded\n\n{data['message']}")
            else:
                st.error(f"❌ Status {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Kan niet verbinden met API")
        except Exception as e:
            st.error(f"❌ Fout: {e}")

# Headers voor API calls
headers = {"Content-Type": "application/json"}
if api_key:
    headers["X-API-Key"] = api_key

# Tabs voor verschillende functionaliteiten
tab_chat, tab_eisen, tab_raw = st.tabs(["💬 Chat", "📋 Eisen", "🔧 Raw Request"])

# =============================================================================
# Tab 1: Chat
# =============================================================================
with tab_chat:
    st.header("Chat met de AI")

    # Haal eisen op voor dropdown
    @st.cache_data(ttl=60)
    def fetch_eisen(url, key):
        try:
            req_headers = {}
            if key:
                req_headers["X-API-Key"] = key
            resp = requests.get(
                f"{url}/api/v1/eisen",
                headers=req_headers,
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json()["eisen"]
            return []
        except Exception:
            return []

    eisen = fetch_eisen(api_url, api_key)

    if not eisen:
        st.warning("Kon geen eisen ophalen. Is de API online en de API key correct?")
        eis_options = ["VS 1.5"]
    else:
        eis_options = [f"{e['id']} - {e['titel']}" for e in eisen]

    col1, col2 = st.columns(2)

    with col1:
        selected_eis = st.selectbox("Selecteer eis", eis_options)
        eis_id = selected_eis.split(" - ")[0] if " - " in selected_eis else selected_eis

        vraag_type = st.radio(
            "Vraag type",
            ["feedback", "uitleg", "suggestie", "algemeen"],
            horizontal=True,
        )

        vraag = st.text_area(
            "Vraag",
            value="Geef feedback op onze invulling" if vraag_type == "feedback" else "Leg deze eis uit",
            height=100,
        )

    with col2:
        st.markdown("**School invulling:**")
        ambitie = st.text_area("Ambitie", height=80)
        beoogd_resultaat = st.text_area("Beoogd resultaat", height=80)
        concrete_acties = st.text_area("Concrete acties", height=80)
        wijze_van_meten = st.text_area("Wijze van meten", height=80)

    if st.button("🚀 Verstuur naar API", type="primary", use_container_width=True):
        # Bouw request body
        request_body = {
            "eis_id": eis_id,
            "vraag": vraag,
            "vraag_type": vraag_type,
            "school_invulling": {
                "ambitie": ambitie,
                "beoogd_resultaat": beoogd_resultaat,
                "concrete_acties": concrete_acties,
                "wijze_van_meten": wijze_van_meten,
            },
        }

        # Toon wat we versturen
        with st.expander("📤 Request (wat we versturen)", expanded=False):
            st.code(f"POST {api_url}/api/v1/chat", language="http")
            st.json(request_body)

        # Verstuur request
        with st.spinner("Wachten op AI response..."):
            try:
                response = requests.post(
                    f"{api_url}/api/v1/chat",
                    headers=headers,
                    json=request_body,
                    timeout=180,  # AI kan even duren
                )

                # Toon response
                st.divider()

                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ Response ontvangen (status {response.status_code})")

                    with st.expander("📥 Raw JSON Response", expanded=False):
                        st.json(data)

                    st.markdown("### Antwoord:")
                    st.markdown(data["antwoord"])
                else:
                    st.error(f"❌ Fout (status {response.status_code})")
                    st.json(response.json())

            except requests.exceptions.ConnectionError:
                st.error("❌ Kan niet verbinden met API. Draait de server?")
            except requests.exceptions.Timeout:
                st.error("❌ Request timeout - de AI deed er te lang over")
            except Exception as e:
                st.error(f"❌ Fout: {e}")

# =============================================================================
# Tab 2: Eisen bekijken
# =============================================================================
with tab_eisen:
    st.header("Deugdelijkheidseisen ophalen")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Alle eisen (GET /api/v1/eisen)")
        if st.button("📋 Haal alle eisen op"):
            try:
                response = requests.get(
                    f"{api_url}/api/v1/eisen",
                    headers=headers,
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ {data['totaal']} eisen gevonden")
                    for eis in data["eisen"]:
                        st.markdown(f"- **{eis['id']}**: {eis['titel']}")
                else:
                    st.error(f"❌ Status {response.status_code}")
                    st.json(response.json())
            except Exception as e:
                st.error(f"❌ Fout: {e}")

    with col2:
        st.subheader("Eis details (GET /api/v1/eisen/{id})")
        eis_id_input = st.text_input("Eis ID", value="VS 1.5")
        if st.button("🔍 Haal eis details op"):
            try:
                response = requests.get(
                    f"{api_url}/api/v1/eisen/{eis_id_input}",
                    headers=headers,
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ {data['id']} - {data['titel']}")
                    st.markdown(f"**Standaard:** {data['standaard']}")
                    st.markdown(f"**Eisomschrijving:** {data['eisomschrijving'][:500]}...")
                    with st.expander("Volledige JSON"):
                        st.json(data)
                else:
                    st.error(f"❌ Status {response.status_code}")
                    st.json(response.json())
            except Exception as e:
                st.error(f"❌ Fout: {e}")

# =============================================================================
# Tab 3: Raw Request
# =============================================================================
with tab_raw:
    st.header("Raw HTTP Request")
    st.markdown("Voer een handmatige request uit - zoals curl of Postman")

    col1, col2 = st.columns(2)

    with col1:
        method = st.selectbox("Method", ["GET", "POST"])
        endpoint = st.text_input("Endpoint", value="/api/v1/eisen")

        if method == "POST":
            body = st.text_area(
                "Request Body (JSON)",
                value='{\n  "eis_id": "VS 1.5",\n  "vraag": "Test",\n  "vraag_type": "uitleg",\n  "school_invulling": {}\n}',
                height=200,
            )

    with col2:
        st.markdown("**Headers:**")
        st.code(f"X-API-Key: {api_key}\nContent-Type: application/json", language="http")

        st.markdown("**Volledige URL:**")
        st.code(f"{api_url}{endpoint}", language="http")

    if st.button("🚀 Execute Request", use_container_width=True):
        try:
            if method == "GET":
                response = requests.get(
                    f"{api_url}{endpoint}",
                    headers=headers,
                    timeout=180,
                )
            else:
                import json
                response = requests.post(
                    f"{api_url}{endpoint}",
                    headers=headers,
                    json=json.loads(body),
                    timeout=180,
                )

            st.divider()
            st.markdown(f"**Status:** {response.status_code}")
            st.markdown("**Response:**")
            try:
                st.json(response.json())
            except:
                st.code(response.text)

        except Exception as e:
            st.error(f"❌ Fout: {e}")

# Footer
st.divider()
st.caption("Deze app simuleert hoe een externe client (zoals Laravel) de OnSpectAI API zou aanroepen.")
