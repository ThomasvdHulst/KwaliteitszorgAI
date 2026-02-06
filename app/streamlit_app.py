"""
Kwaliteitszorg AI - Streamlit Web Interface

Multi-page app met home-overzicht en detail-pagina per deugdelijkheidseis.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from config import settings
from src.kwaliteitszorg import DeugdelijkheidseisAssistent, SchoolInvulling
from src.kwaliteitszorg.utils.database import load_database
from src.kwaliteitszorg.utils.pdf_processor import extract_text_from_pdf

# ============================================================================
# EXPERIMENTEEL: Suggestie feature import
# ============================================================================
try:
    from app.suggestie_ui import render_suggesties_tab
    SUGGESTIES_ENABLED = True
except ImportError:
    try:
        from suggestie_ui import render_suggesties_tab
        SUGGESTIES_ENABLED = True
    except ImportError:
        SUGGESTIES_ENABLED = False
# ============================================================================

# ============================================================================
# RAG (Document Databank) feature import
# ============================================================================
try:
    from app.rag_ui import (
        init_rag_state,
        render_rag_toggle,
        render_document_databank,
    )
    RAG_ENABLED = True
except ImportError:
    try:
        from rag_ui import (
            init_rag_state,
            render_rag_toggle,
            render_document_databank,
        )
        RAG_ENABLED = True
    except ImportError:
        RAG_ENABLED = False
# ============================================================================

# ============================================================================
# Invulling storage import
# ============================================================================
try:
    from app.invulling_storage import (
        load_invulling,
        save_invulling,
        get_invulling_status,
    )
    STORAGE_ENABLED = True
except ImportError:
    try:
        from invulling_storage import (
            load_invulling,
            save_invulling,
            get_invulling_status,
        )
        STORAGE_ENABLED = True
    except ImportError:
        STORAGE_ENABLED = False
# ============================================================================

# Thema kleuren
COLORS = {
    "primary": "#4599D5",
    "primary_dark": "#2C81C0",
    "bg_light": "#F8FAFD",
    "bg_card": "#DCEEFA",
    "bg_white": "#FFFFFF",
    "text_dark": "#14194A",
    "text_gray": "#496580",
    "border": "#E2E8F0",
    "user_bg": "#E8F4FD",
    "assistant_bg": "#F0F7ED",
}


def inject_css():
    """Custom CSS styling."""
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {COLORS["bg_light"]};
        }}

        /* Header */
        .main-header {{
            background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["primary_dark"]} 100%);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 1rem;
        }}
        .main-header h1 {{
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
        }}
        .main-header .subtitle {{
            margin-top: 0.25rem;
            opacity: 0.9;
            font-size: 0.9rem;
        }}

        /* Eis beschrijving */
        .eis-box {{
            background: {COLORS["bg_white"]};
            border-left: 4px solid {COLORS["primary"]};
            padding: 1rem 1.25rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-size: 0.95rem;
            color: {COLORS["text_gray"]};
            line-height: 1.5;
        }}

        /* Chat berichten */
        .chat-message {{
            padding: 1rem 1.25rem;
            border-radius: 12px;
            margin-bottom: 0.75rem;
            line-height: 1.6;
        }}
        .chat-message.user {{
            background: {COLORS["user_bg"]};
            margin-left: 2rem;
        }}
        .chat-message.assistant {{
            background: {COLORS["assistant_bg"]};
            margin-right: 2rem;
        }}
        .chat-message .role {{
            font-weight: 600;
            font-size: 0.8rem;
            margin-bottom: 0.5rem;
            color: {COLORS["text_gray"]};
        }}

        /* Input styling */
        .stTextArea textarea, .stTextInput input {{
            border-radius: 8px !important;
            border: 1px solid {COLORS["border"]} !important;
        }}
        .stTextArea textarea:focus, .stTextInput input:focus {{
            border-color: {COLORS["primary"]} !important;
            box-shadow: 0 0 0 2px rgba(69, 153, 213, 0.2) !important;
        }}

        /* Buttons */
        .stButton > button {{
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s;
        }}
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["primary_dark"]} 100%);
            color: white;
            border: none;
        }}
        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(69, 153, 213, 0.25);
        }}

        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        /* Expander */
        .streamlit-expanderHeader {{
            font-size: 0.9rem;
            font-weight: 500;
        }}

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        .stTabs [data-baseweb="tab"] {{
            padding: 8px 16px;
            border-radius: 8px 8px 0 0;
        }}

        /* ============================================ */
        /* Home page: eis kaartjes                      */
        /* ============================================ */
        .eis-card {{
            background: {COLORS["bg_white"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.75rem;
            transition: all 0.2s;
        }}
        .eis-card:hover {{
            border-color: {COLORS["primary"]};
            box-shadow: 0 2px 12px rgba(69, 153, 213, 0.15);
        }}
        .eis-card-id {{
            font-weight: 700;
            color: {COLORS["primary"]};
            font-size: 0.85rem;
            margin-bottom: 0.25rem;
        }}
        .eis-card-title {{
            font-weight: 600;
            color: {COLORS["text_dark"]};
            font-size: 0.95rem;
            margin-bottom: 0.5rem;
        }}
        .eis-card-status {{
            font-size: 0.8rem;
            color: {COLORS["text_gray"]};
        }}
        .eis-card-status.opgeslagen {{
            color: #16A34A;
        }}
    </style>
    """, unsafe_allow_html=True)


@st.cache_data
def get_database() -> dict:
    return load_database(str(settings.DATABASE_PATH))


@st.cache_data
def get_standaard_naslagwerk() -> dict:
    """Laad standaard-specifiek naslagwerk (blog, kenniskaart, etc.)."""
    path = settings.DATA_DIR / "standaarden_naslagwerk.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_assistent() -> DeugdelijkheidseisAssistent:
    """Haal assistent uit session state of maak nieuwe aan."""
    if "assistent" not in st.session_state:
        st.session_state.assistent = DeugdelijkheidseisAssistent()
    return st.session_state.assistent


def init_session_state():
    """Initialiseer session state variabelen."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_eis" not in st.session_state:
        st.session_state.current_eis = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    # Standaard chat state
    if "standaard_messages" not in st.session_state:
        st.session_state.standaard_messages = []
    if "standaard_chat_current" not in st.session_state:
        st.session_state.standaard_chat_current = None
    # Document upload state
    if "document_text" not in st.session_state:
        st.session_state.document_text = None
    if "document_filename" not in st.session_state:
        st.session_state.document_filename = None
    # RAG state
    if RAG_ENABLED:
        init_rag_state()


def reset_chat():
    """Reset de chat."""
    st.session_state.messages = []
    get_assistent().reset_chat()
    # Reset ook suggesties als die feature actief is
    if "suggestie_resultaat" in st.session_state:
        st.session_state.suggestie_resultaat = None
    # Reset behandeld-status van suggesties
    for veld in ["ambitie", "beoogd_resultaat", "concrete_acties", "wijze_van_meten"]:
        key = f"suggestie_behandeld_{veld}"
        if key in st.session_state:
            del st.session_state[key]
    # Reset input velden
    for key in ["input_ambitie", "input_resultaat", "input_acties", "input_meten"]:
        st.session_state[key] = ""


# ============================================================================
# Navigatie
# ============================================================================

def navigate_to_eis(eis_id: str):
    """Navigeer naar de detail-pagina voor een eis."""
    st.session_state.current_page = "eis_detail"
    st.session_state.current_eis = eis_id

    # Reset chat eerst (dit maakt ook input velden leeg)
    reset_chat()

    # Laad opgeslagen invulling NA reset_chat, zodat waarden niet overschreven worden
    if STORAGE_ENABLED:
        invulling = load_invulling(eis_id)
        if invulling:
            st.session_state.input_ambitie = invulling.get("ambitie", "")
            st.session_state.input_resultaat = invulling.get("beoogd_resultaat", "")
            st.session_state.input_acties = invulling.get("concrete_acties", "")
            st.session_state.input_meten = invulling.get("wijze_van_meten", "")

    # Increment widget version om widgets te forceren naar nieuwe waarden
    st.session_state.widget_version = st.session_state.get("widget_version", 0) + 1

    st.rerun()


def navigate_to_home():
    """Navigeer terug naar het overzicht."""
    st.session_state.current_page = "home"
    reset_chat()
    st.rerun()


# ============================================================================
# Chat rendering (ongewijzigd)
# ============================================================================

def render_chat_message(role: str, content: str, sources: list = None):
    """Render een chat bericht met optionele bronvermelding."""
    avatar = "\U0001f9d1" if role == "user" else "\U0001f916"
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)
        if sources and role == "assistant":
            st.markdown("---")
            st.markdown("**Onderbouwing:**")
            for source in sources:
                st.caption(f"\u2022 {source}")


def extract_onderbouwing_from_response(response: str) -> tuple:
    """Extraheer de ONDERBOUWING sectie uit het AI-antwoord."""
    if not response:
        return response, []

    import re
    pattern = r'\n*ONDERBOUWING:\s*(.*)$'
    match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)

    if not match:
        return response, []

    onderbouwing_start = match.start()
    cleaned_response = response[:onderbouwing_start].strip()

    onderbouwing_text = match.group(1).strip()

    if "geen" in onderbouwing_text.lower():
        return cleaned_response, []

    sources = []
    for line in onderbouwing_text.split('\n'):
        line = line.strip()
        if line.startswith('-') or line.startswith('*') or line.startswith('\u2022'):
            source = line.lstrip('-*\u2022 ').strip()
            if source:
                sources.append(source)
        elif line and not line.startswith('ONDERBOUWING'):
            sources.append(line)

    return cleaned_response, sources


def _process_chat_message(
    vraag: str,
    vraag_type: str,
    selected_id: str,
    school_invulling,
    document_text: str = None,
    document_filename: str = None,
    rag_context: str = None,
):
    """Verwerk een chat bericht en genereer een antwoord."""
    st.session_state.messages.append({"role": "user", "content": vraag})

    with st.spinner(""):
        response_placeholder = st.empty()
        response_buffer = ""

        def handle_chunk(chunk: str):
            nonlocal response_buffer
            response_buffer += chunk
            response_placeholder.markdown(response_buffer)

        try:
            assistent = get_assistent()
            antwoord = assistent.chat(
                eis_id=selected_id,
                school_invulling=school_invulling,
                vraag=vraag,
                vraag_type=vraag_type,
                stream_handler=handle_chunk,
                document_text=document_text,
                document_filename=document_filename,
                rag_context=rag_context,
            )
        except RuntimeError as e:
            st.error(str(e))
            st.session_state.messages.pop()
            return

    used_sources = []
    display_content = antwoord
    if rag_context:
        display_content, used_sources = extract_onderbouwing_from_response(antwoord)

    message_data = {"role": "assistant", "content": display_content}
    if used_sources:
        message_data["sources"] = used_sources
    st.session_state.messages.append(message_data)

    st.rerun()


def render_chat_tab(
    selected_id: str,
    school_invulling: SchoolInvulling,
    document_text: str = None,
    document_filename: str = None,
    rag_context: str = None,
):
    """Render de chat tab."""
    st.markdown("### Chat met Kwaliteitszorg AI")

    auto_trigger = st.session_state.get("auto_chat_trigger")
    if st.session_state.get("switch_to_chat"):
        st.info("\U0001f4a1 Vraag wordt automatisch verstuurd...")
        st.session_state.pop("auto_chat_trigger", None)
        st.session_state.pop("switch_to_chat", None)

    if rag_context:
        st.info("Documentdatabank actief - relevante passages worden meegestuurd")
    elif document_text:
        st.info(f"Document gekoppeld: **{document_filename}**")

    for msg in st.session_state.messages:
        render_chat_message(msg["role"], msg["content"], msg.get("sources"))

    if auto_trigger:
        _process_chat_message(
            vraag=auto_trigger["vraag"],
            vraag_type=auto_trigger["type"],
            selected_id=selected_id,
            school_invulling=school_invulling,
            document_text=document_text,
            document_filename=document_filename,
            rag_context=rag_context,
        )
        return

    col_input, col_type = st.columns([3, 1])

    with col_type:
        vraag_type = st.selectbox(
            "Type",
            ["feedback", "uitleg", "suggestie", "algemeen"],
            format_func=lambda x: {
                "feedback": "Feedback",
                "uitleg": "Uitleg",
                "suggestie": "Suggestie",
                "algemeen": "Algemeen",
            }.get(x, x),
            label_visibility="collapsed",
        )

    with col_input:
        if not st.session_state.messages:
            placeholder = {
                "feedback": "Kun je feedback geven op onze invulling?",
                "uitleg": "Kun je deze eis uitleggen?",
                "suggestie": "Heb je suggesties voor verbetering?",
                "algemeen": "Stel je vraag...",
            }.get(vraag_type, "Stel je vraag...")
        else:
            placeholder = "Stel een vervolgvraag..."

        vraag = st.text_input(
            "Vraag",
            placeholder=placeholder,
            key="chat_input",
            label_visibility="collapsed",
        )

    if st.button("Verstuur", type="primary", use_container_width=True):
        if not vraag.strip():
            st.warning("Typ eerst een vraag.")
        else:
            _process_chat_message(
                vraag=vraag,
                vraag_type=vraag_type,
                selected_id=selected_id,
                school_invulling=school_invulling,
                document_text=document_text,
                document_filename=document_filename,
                rag_context=rag_context,
            )


# ============================================================================
# Standaard-niveau chat
# ============================================================================

def _get_standaard_invullingen(eis_lijst: list) -> dict:
    """Laad opgeslagen invullingen voor alle eisen in een standaard."""
    invullingen = {}
    for eis_id, _eis_data in eis_lijst:
        if STORAGE_ENABLED:
            data = load_invulling(eis_id)
            if data:
                invullingen[eis_id] = SchoolInvulling(
                    ambitie=data.get("ambitie", ""),
                    beoogd_resultaat=data.get("beoogd_resultaat", ""),
                    concrete_acties=data.get("concrete_acties", ""),
                    wijze_van_meten=data.get("wijze_van_meten", ""),
                )
            else:
                invullingen[eis_id] = SchoolInvulling()
        else:
            invullingen[eis_id] = SchoolInvulling()
    return invullingen


def _process_standaard_chat_message(
    vraag: str,
    vraag_type: str,
    standaard_naam: str,
    eisen_met_invullingen: dict,
    naslagwerk: str = "",
    standaard_omschrijving: str = "",
    rag_context: str = None,
):
    """Verwerk een standaard-niveau chat bericht."""
    st.session_state.standaard_messages.append({"role": "user", "content": vraag})

    with st.spinner(""):
        response_placeholder = st.empty()
        response_buffer = ""

        def handle_chunk(chunk: str):
            nonlocal response_buffer
            response_buffer += chunk
            response_placeholder.markdown(response_buffer)

        try:
            assistent = get_assistent()
            antwoord = assistent.chat_standaard(
                standaard_naam=standaard_naam,
                eisen_met_invullingen=eisen_met_invullingen,
                vraag=vraag,
                vraag_type=vraag_type,
                stream_handler=handle_chunk,
                naslagwerk=naslagwerk,
                standaard_omschrijving=standaard_omschrijving,
                rag_context=rag_context,
            )
        except RuntimeError as e:
            st.error(str(e))
            st.session_state.standaard_messages.pop()
            return

    used_sources = []
    display_content = antwoord
    if rag_context:
        display_content, used_sources = extract_onderbouwing_from_response(antwoord)

    message_data = {"role": "assistant", "content": display_content}
    if used_sources:
        message_data["sources"] = used_sources
    st.session_state.standaard_messages.append(message_data)

    st.rerun()


def render_standaard_chat_tab(
    standaard_naam: str,
    eis_lijst: list,
    naslagwerk_data: dict,
    rag_context: str = None,
):
    """Render de chat tab voor standaard-niveau gesprekken."""
    naslagwerk = naslagwerk_data.get("naslagwerk", "")
    omschrijving = naslagwerk_data.get("omschrijving", "")

    # Laad invullingen voor deze standaard
    invullingen = _get_standaard_invullingen(eis_lijst)

    # Toon overzicht
    ingevuld = sum(1 for inv in invullingen.values() if not inv.is_leeg())
    totaal = len(eis_lijst)
    st.caption(f"Standaard: **{standaard_naam}** \u2014 {ingevuld}/{totaal} eisen ingevuld")

    if naslagwerk:
        st.caption("Naslagwerk beschikbaar als context")
    else:
        st.caption("Geen standaard-specifiek naslagwerk beschikbaar")

    if rag_context:
        st.info("Documentdatabank actief")

    # Toon berichten
    for msg in st.session_state.standaard_messages:
        render_chat_message(msg["role"], msg["content"], msg.get("sources"))

    # Input
    col_input, col_type = st.columns([3, 1])

    with col_type:
        vraag_type = st.selectbox(
            "Type",
            ["feedback", "uitleg", "suggestie", "algemeen"],
            format_func=lambda x: {
                "feedback": "Beoordeling",
                "uitleg": "Uitleg",
                "suggestie": "Suggestie",
                "algemeen": "Algemeen",
            }.get(x, x),
            label_visibility="collapsed",
            key="standaard_chat_type",
        )

    with col_input:
        if not st.session_state.standaard_messages:
            placeholder = {
                "feedback": "Beoordeel onze invullingen voor deze standaard",
                "uitleg": "Leg deze standaard uit en hoe de eisen samenhangen",
                "suggestie": "Geef suggesties voor verbetering van deze standaard",
                "algemeen": "Stel je vraag over deze standaard...",
            }.get(vraag_type, "Stel je vraag...")
        else:
            placeholder = "Stel een vervolgvraag..."

        vraag = st.text_input(
            "Vraag",
            placeholder=placeholder,
            key="standaard_chat_input",
            label_visibility="collapsed",
        )

    if st.button("Verstuur", type="primary", use_container_width=True, key="standaard_chat_send"):
        if not vraag.strip():
            st.warning("Typ eerst een vraag.")
        else:
            _process_standaard_chat_message(
                vraag=vraag,
                vraag_type=vraag_type,
                standaard_naam=standaard_naam,
                eisen_met_invullingen=invullingen,
                naslagwerk=naslagwerk,
                standaard_omschrijving=omschrijving,
                rag_context=rag_context,
            )


# ============================================================================
# Home page
# ============================================================================

def _group_eisen_by_standaard(eisen: dict) -> dict:
    """Groepeer eisen op standaard. Return dict van standaard -> [(eis_id, eis_data)]."""
    grouped = defaultdict(list)
    for eis_id in sorted(eisen.keys()):
        eis = eisen[eis_id]
        standaard = eis.get("standaard", "Overig")
        grouped[standaard].append((eis_id, eis))
    return dict(grouped)


def render_home_page():
    """Render de home-pagina met overzicht van alle eisen."""
    database = get_database()
    eisen = database.get("deugdelijkheidseisen", {})

    if not eisen:
        st.error("Geen deugdelijkheidseisen gevonden.")
        return

    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>Kwaliteitszorg AI</h1>
        <div class="subtitle">Overzicht deugdelijkheidseisen</div>
    </div>
    """, unsafe_allow_html=True)

    # Documentdatabank in expander
    if RAG_ENABLED:
        with st.expander("Documentdatabank beheren", expanded=False):
            render_document_databank()

    # Eisen per standaard
    grouped = _group_eisen_by_standaard(eisen)

    for standaard, eis_lijst in grouped.items():
        st.markdown(f"### {standaard}")

        # 3 kolommen
        cols = st.columns(3)
        for idx, (eis_id, eis) in enumerate(eis_lijst):
            col = cols[idx % 3]

            with col:
                # Status bepalen
                if STORAGE_ENABLED:
                    status = get_invulling_status(eis_id)
                else:
                    status = "niet_opgeslagen"

                if status == "opgeslagen":
                    status_html = '<div class="eis-card-status opgeslagen">\u2705 Opgeslagen</div>'
                else:
                    status_html = '<div class="eis-card-status">\u2014 Niet ingevuld</div>'

                st.markdown(f"""
                <div class="eis-card">
                    <div class="eis-card-id">{eis_id}</div>
                    <div class="eis-card-title">{eis.get("titel", "")}</div>
                    {status_html}
                </div>
                """, unsafe_allow_html=True)

                if st.button("Openen", key=f"open_{eis_id}", use_container_width=True):
                    navigate_to_eis(eis_id)

    # ========================================================================
    # Floating AI Chat voor standaard-niveau
    # ========================================================================
    naslagwerk_db = get_standaard_naslagwerk()
    standaard_options = list(grouped.keys())

    # Popover CSS
    st.markdown("""
    <style>
        div[data-testid="stPopover"] > div:first-child > button {
            position: fixed !important;
            bottom: 24px !important;
            right: 24px !important;
            width: 64px !important;
            height: 64px !important;
            border-radius: 50% !important;
            background: linear-gradient(135deg, #4599D5 0%, #2C81C0 100%) !important;
            box-shadow: 0 4px 16px rgba(69, 153, 213, 0.4) !important;
            z-index: 9999 !important;
            padding: 0 !important;
            min-height: unset !important;
            border: none !important;
        }
        div[data-testid="stPopover"] > div:first-child > button:hover {
            transform: scale(1.1) !important;
            box-shadow: 0 6px 24px rgba(69, 153, 213, 0.5) !important;
        }
        div[data-testid="stPopover"] > div:first-child > button p {
            font-size: 28px !important;
            margin: 0 !important;
            line-height: 1 !important;
        }
        div[data-testid="stPopoverBody"] {
            width: 900px !important;
            min-width: 900px !important;
            max-width: 900px !important;
            min-height: 600px !important;
            max-height: 85vh !important;
        }
        div[data-testid="stPopoverBody"] > div {
            width: 100% !important;
            min-height: 580px !important;
        }
        [data-baseweb="popover"] > div {
            width: 700px !important;
            min-width: 700px !important;
        }
        [data-baseweb="popover"] [data-testid="stVerticalBlockBorderWrapper"] {
            width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.popover("\U0001f916", use_container_width=False):
        st.markdown("### Standaard AI Assistent")

        selected_standaard = st.selectbox(
            "Kies een standaard",
            standaard_options,
            key="standaard_selector",
        )

        # Reset chat als standaard wijzigt
        if st.session_state.standaard_chat_current != selected_standaard:
            st.session_state.standaard_chat_current = selected_standaard
            st.session_state.standaard_messages = []
            get_assistent().reset_standaard_chat()

        # Naslagwerk voor deze standaard
        naslagwerk_item = naslagwerk_db.get(selected_standaard, {})

        if st.button("Nieuwe chat", use_container_width=True, key="standaard_new_chat"):
            st.session_state.standaard_messages = []
            get_assistent().reset_standaard_chat()
            st.rerun()

        st.markdown("---")

        render_standaard_chat_tab(
            standaard_naam=selected_standaard,
            eis_lijst=grouped[selected_standaard],
            naslagwerk_data=naslagwerk_item,
        )


# ============================================================================
# Eis detail page
# ============================================================================

def render_eis_detail_page():
    """Render de detail-pagina voor een enkele deugdelijkheidseis."""
    database = get_database()
    eisen = database.get("deugdelijkheidseisen", {})
    selected_id = st.session_state.current_eis

    if not selected_id or selected_id not in eisen:
        navigate_to_home()
        return

    eis = eisen[selected_id]

    # Terug-knop
    if st.button("\u2190 Terug naar overzicht"):
        navigate_to_home()

    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>{selected_id} {eis.get("titel", "")}</h1>
        <div class="subtitle">{eis.get("standaard", "")}</div>
    </div>
    """, unsafe_allow_html=True)

    # Eis beschrijving
    st.markdown(f"""
    <div class="eis-box">{eis.get("eisomschrijving", "")}</div>
    """, unsafe_allow_html=True)

    # Extra info
    with st.expander("Meer informatie over deze eis"):
        info_tabs = st.tabs(["Uitleg", "Focuspunten", "Tips", "Voorbeelden"])
        with info_tabs[0]:
            st.markdown(eis.get("uitleg", ""))
        with info_tabs[1]:
            st.markdown(eis.get("focuspunten", ""))
        with info_tabs[2]:
            st.markdown(eis.get("tips", ""))
        with info_tabs[3]:
            st.markdown(eis.get("voorbeelden", ""))

    # School invulling
    st.markdown("### Jullie invulling")

    # Initialiseer values in session state als ze nog niet bestaan
    for key in ["input_ambitie", "input_resultaat", "input_acties", "input_meten"]:
        if key not in st.session_state:
            st.session_state[key] = ""
    if "widget_version" not in st.session_state:
        st.session_state.widget_version = 0
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False

    v = st.session_state.widget_version

    ambitie = st.text_area(
        "Ambitie",
        value=st.session_state.input_ambitie,
        placeholder="Wat wil jullie school bereiken?",
        height=150,
        max_chars=settings.MAX_INPUT_CHARS,
        key=f"widget_ambitie_{v}",
    )
    st.session_state.input_ambitie = ambitie

    beoogd_resultaat = st.text_area(
        "Beoogd resultaat",
        value=st.session_state.input_resultaat,
        placeholder="Welke concrete doelen?",
        height=150,
        max_chars=settings.MAX_INPUT_CHARS,
        key=f"widget_resultaat_{v}",
    )
    st.session_state.input_resultaat = beoogd_resultaat

    concrete_acties = st.text_area(
        "Concrete acties",
        value=st.session_state.input_acties,
        placeholder="Welke stappen ondernemen jullie?",
        height=180,
        max_chars=settings.MAX_INPUT_CHARS,
        key=f"widget_acties_{v}",
    )
    st.session_state.input_acties = concrete_acties

    wijze_van_meten = st.text_area(
        "Wijze van meten",
        value=st.session_state.input_meten,
        placeholder="Hoe meten jullie succes?",
        height=150,
        max_chars=settings.MAX_INPUT_CHARS,
        key=f"widget_meten_{v}",
    )
    st.session_state.input_meten = wijze_van_meten

    # Opslaan knop
    if STORAGE_ENABLED:
        col_save, col_status = st.columns([1, 2])
        with col_save:
            if st.button("Opslaan", type="primary", use_container_width=True):
                save_invulling(
                    eis_id=selected_id,
                    ambitie=ambitie,
                    beoogd_resultaat=beoogd_resultaat,
                    concrete_acties=concrete_acties,
                    wijze_van_meten=wijze_van_meten,
                )
                st.session_state.save_success = True
                st.rerun()

        with col_status:
            if st.session_state.get("save_success"):
                st.success("Invulling opgeslagen!")
                st.session_state.save_success = False

            # Toon laatst opgeslagen timestamp
            existing = load_invulling(selected_id)
            if existing and existing.get("laatst_opgeslagen"):
                st.caption(f"Laatst opgeslagen: {existing['laatst_opgeslagen']}")

    # Maak school invulling object
    school_invulling = SchoolInvulling(
        ambitie=ambitie,
        beoogd_resultaat=beoogd_resultaat,
        concrete_acties=concrete_acties,
        wijze_van_meten=wijze_van_meten,
    )

    # ========================================================================
    # Document Context (RAG of enkel document)
    # ========================================================================
    rag_context = None
    rag_active = False

    if RAG_ENABLED:
        # RAG toggle en context ophalen
        rag_active, rag_context, _rag_sources = render_rag_toggle(selected_id, eis)

        if rag_active and rag_context:
            st.markdown("---")
        else:
            st.markdown("### Of: enkel document koppelen")
            st.caption("Als alternatief voor de documentdatabank kun je ook een enkel document uploaden.")
    else:
        st.markdown("### Beleidsdocument koppelen (optioneel)")

    # Single document upload (alleen tonen als RAG niet actief is)
    if not (rag_active and rag_context):
        uploaded_file = st.file_uploader(
            "Upload een PDF document",
            type=settings.ALLOWED_DOCUMENT_TYPES,
            help="Upload bijv. een taalbeleid, veiligheidsplan of ander beleidsdocument. "
                 "De AI gebruikt dit als context voor betere, specifiekere feedback.",
            key="document_uploader",
        )

        if uploaded_file is not None:
            if st.session_state.document_filename != uploaded_file.name:
                with st.spinner("Document verwerken..."):
                    result = extract_text_from_pdf(
                        file_bytes=uploaded_file.read(),
                        filename=uploaded_file.name,
                    )

                    if result.success:
                        st.session_state.document_text = result.text
                        st.session_state.document_filename = result.filename

                        status_msg = f"Document geladen: {result.page_count} pagina's, {result.char_count:,} karakters"
                        if result.truncated:
                            status_msg += " (ingekort)"
                        st.success(status_msg)
                    else:
                        st.error(result.error)
                        st.session_state.document_text = None
                        st.session_state.document_filename = None

        if st.session_state.document_text:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"Gekoppeld: **{st.session_state.document_filename}**")
            with col2:
                if st.button("Verwijder", key="remove_document"):
                    st.session_state.document_text = None
                    st.session_state.document_filename = None
                    st.rerun()

    st.markdown("---")

    # ========================================================================
    # AI Chat & Suggesties - Floating button approach
    # ========================================================================

    # Popover CSS (alleen op detail page)
    st.markdown("""
    <style>
        /* Style de popover trigger als floating button */
        div[data-testid="stPopover"] > div:first-child > button {
            position: fixed !important;
            bottom: 24px !important;
            right: 24px !important;
            width: 64px !important;
            height: 64px !important;
            border-radius: 50% !important;
            background: linear-gradient(135deg, #4599D5 0%, #2C81C0 100%) !important;
            box-shadow: 0 4px 16px rgba(69, 153, 213, 0.4) !important;
            z-index: 9999 !important;
            padding: 0 !important;
            min-height: unset !important;
            border: none !important;
        }
        div[data-testid="stPopover"] > div:first-child > button:hover {
            transform: scale(1.1) !important;
            box-shadow: 0 6px 24px rgba(69, 153, 213, 0.5) !important;
        }
        div[data-testid="stPopover"] > div:first-child > button p {
            font-size: 28px !important;
            margin: 0 !important;
            line-height: 1 !important;
        }
        /* Popover panel styling */
        div[data-testid="stPopoverBody"] {
            width: 900px !important;
            min-width: 900px !important;
            max-width: 900px !important;
            min-height: 600px !important;
            max-height: 85vh !important;
        }
        div[data-testid="stPopoverBody"] > div {
            width: 100% !important;
            min-height: 580px !important;
        }
        /* Fallback selectors */
        [data-baseweb="popover"] > div {
            width: 700px !important;
            min-width: 700px !important;
        }
        [data-baseweb="popover"] [data-testid="stVerticalBlockBorderWrapper"] {
            width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Floating AI Chat Button met popover
    with st.popover("\U0001f916", use_container_width=False):
        if SUGGESTIES_ENABLED:
            chat_tabs = st.tabs(["Chat", "Suggesties"])

            with chat_tabs[0]:
                render_chat_tab(
                    selected_id,
                    school_invulling,
                    document_text=st.session_state.document_text,
                    document_filename=st.session_state.document_filename,
                    rag_context=rag_context,
                )

            with chat_tabs[1]:
                render_suggesties_tab(
                    selected_id,
                    eis,
                    school_invulling,
                    document_text=st.session_state.document_text,
                    document_filename=st.session_state.document_filename,
                    rag_context=rag_context,
                )
        else:
            render_chat_tab(
                selected_id,
                school_invulling,
                document_text=st.session_state.document_text,
                document_filename=st.session_state.document_filename,
                rag_context=rag_context,
            )


# ============================================================================
# Main
# ============================================================================

def main():
    st.set_page_config(
        page_title="Kwaliteitszorg AI",
        page_icon="\U0001f393",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    inject_css()
    init_session_state()

    # Check Ollama verbinding bij eerste keer laden
    if "ollama_checked" not in st.session_state:
        from config.settings import check_ollama_connection
        success, message = check_ollama_connection()
        st.session_state.ollama_checked = True
        st.session_state.ollama_ok = success
        st.session_state.ollama_message = message

    if not st.session_state.ollama_ok:
        st.error(f"**Ollama niet beschikbaar:** {st.session_state.ollama_message}")
        st.info("Start Ollama en herlaad deze pagina.")
        st.stop()

    # Routing
    page = st.session_state.get("current_page", "home")
    if page == "eis_detail" and st.session_state.get("current_eis"):
        render_eis_detail_page()
    else:
        render_home_page()


if __name__ == "__main__":
    main()
