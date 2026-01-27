"""
Kwaliteitszorg AI - Streamlit Web Interface

Chat-interface voor kwaliteitszorg onderwijs.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from config import settings
from src.kwaliteitszorg import DeugdelijkheidseisAssistent, SchoolInvulling
from src.kwaliteitszorg.utils.database import load_database

# ============================================================================
# EXPERIMENTEEL: Suggestie feature import
# Verwijder dit blok + de aanroep in main() om de feature uit te schakelen
# ============================================================================
try:
    from suggestie_ui import render_suggesties_tab
    SUGGESTIES_ENABLED = True
except ImportError:
    SUGGESTIES_ENABLED = False
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

        /* Floating AI Chat Button */
        .ai-chat-button {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["primary_dark"]} 100%);
            box-shadow: 0 4px 16px rgba(69, 153, 213, 0.4);
            cursor: pointer;
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            border: none;
        }}
        .ai-chat-button:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 24px rgba(69, 153, 213, 0.5);
        }}
        .ai-chat-button img {{
            width: 32px;
            height: 32px;
        }}

        /* Chat Panel */
        .chat-panel {{
            position: fixed;
            bottom: 100px;
            right: 24px;
            width: 420px;
            max-height: 70vh;
            background: {COLORS["bg_white"]};
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            z-index: 9998;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        .chat-panel-header {{
            background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["primary_dark"]} 100%);
            color: white;
            padding: 1rem 1.25rem;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .chat-panel-body {{
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            max-height: calc(70vh - 120px);
        }}
        .chat-panel-footer {{
            padding: 0.75rem;
            border-top: 1px solid {COLORS["border"]};
            background: {COLORS["bg_light"]};
        }}
    </style>
    """, unsafe_allow_html=True)


@st.cache_data
def get_database() -> dict:
    return load_database(str(settings.DATABASE_PATH))


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


def render_chat_message(role: str, content: str):
    """Render een chat bericht."""
    role_label = "Jij" if role == "user" else "Kwaliteitszorg AI"
    css_class = "user" if role == "user" else "assistant"

    st.markdown(f"""
    <div class="chat-message {css_class}">
        <div class="role">{role_label}</div>
        <div class="content">{content}</div>
    </div>
    """, unsafe_allow_html=True)


def render_chat_tab(selected_id: str, school_invulling: SchoolInvulling):
    """Render de chat tab."""
    st.markdown("### Chat met Kwaliteitszorg AI")

    # Toon bestaande berichten
    for msg in st.session_state.messages:
        render_chat_message(msg["role"], msg["content"])

    # Chat input
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

    # Verstuur knop
    if st.button("Verstuur", type="primary", use_container_width=True):
        if not vraag.strip():
            st.warning("Typ eerst een vraag.")
        else:
            # Voeg user bericht toe aan weergave
            st.session_state.messages.append({"role": "user", "content": vraag})

            # Placeholder voor streaming response
            with st.spinner(""):
                response_placeholder = st.empty()
                response_buffer = ""

                def handle_chunk(chunk: str):
                    nonlocal response_buffer
                    response_buffer += chunk
                    response_placeholder.markdown(f"""
                    <div class="chat-message assistant">
                        <div class="role">Kwaliteitszorg AI</div>
                        <div class="content">{response_buffer}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Genereer antwoord
                assistent = get_assistent()
                antwoord = assistent.chat(
                    eis_id=selected_id,
                    school_invulling=school_invulling,
                    vraag=vraag,
                    vraag_type=vraag_type,
                    stream_handler=handle_chunk,
                )

            # Voeg assistant bericht toe
            st.session_state.messages.append({"role": "assistant", "content": antwoord})

            # Rerun om input te clearen
            st.rerun()


def main():
    st.set_page_config(
        page_title="Kwaliteitszorg AI",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    inject_css()
    init_session_state()

    database = get_database()
    eisen = database.get("deugdelijkheidseisen", {})

    if not eisen:
        st.error("Geen deugdelijkheidseisen gevonden.")
        return

    # Sidebar
    with st.sidebar:
        st.markdown("### Instellingen")
        eis_ids = sorted(eisen.keys())
        selected_id = st.selectbox(
            "Deugdelijkheidseis",
            eis_ids,
            format_func=lambda x: f"{x} - {eisen[x].get('titel', '')}",
        )

        # Reset chat als eis wijzigt
        if st.session_state.current_eis != selected_id:
            st.session_state.current_eis = selected_id
            reset_chat()

        if st.button("Nieuwe chat", use_container_width=True):
            reset_chat()
            st.rerun()

    eis = eisen.get(selected_id, {})

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

    # Widget version wordt verhoogd bij suggestie-acceptatie om widgets te resetten
    v = st.session_state.widget_version

    # Velden onder elkaar met grotere hoogte
    ambitie = st.text_area(
        "Ambitie",
        value=st.session_state.input_ambitie,
        placeholder="Wat wil jullie school bereiken?",
        height=150,
        key=f"widget_ambitie_{v}",
    )
    st.session_state.input_ambitie = ambitie

    beoogd_resultaat = st.text_area(
        "Beoogd resultaat",
        value=st.session_state.input_resultaat,
        placeholder="Welke concrete doelen?",
        height=150,
        key=f"widget_resultaat_{v}",
    )
    st.session_state.input_resultaat = beoogd_resultaat

    concrete_acties = st.text_area(
        "Concrete acties",
        value=st.session_state.input_acties,
        placeholder="Welke stappen ondernemen jullie?",
        height=180,
        key=f"widget_acties_{v}",
    )
    st.session_state.input_acties = concrete_acties

    wijze_van_meten = st.text_area(
        "Wijze van meten",
        value=st.session_state.input_meten,
        placeholder="Hoe meten jullie succes?",
        height=150,
        key=f"widget_meten_{v}",
    )
    st.session_state.input_meten = wijze_van_meten

    # Maak school invulling object
    school_invulling = SchoolInvulling(
        ambitie=ambitie,
        beoogd_resultaat=beoogd_resultaat,
        concrete_acties=concrete_acties,
        wijze_van_meten=wijze_van_meten,
    )

    st.markdown("---")

    # ========================================================================
    # AI Chat & Suggesties - Floating button approach
    # ========================================================================

    # Floating AI button container (rechtsonder)
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
        /* Popover panel styling - meerdere selectors voor compatibiliteit */
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
    with st.popover("🤖", use_container_width=False):
        if SUGGESTIES_ENABLED:
            chat_tabs = st.tabs(["Chat", "Suggesties"])

            with chat_tabs[0]:
                render_chat_tab(selected_id, school_invulling)

            with chat_tabs[1]:
                render_suggesties_tab(selected_id, eis, school_invulling)
        else:
            render_chat_tab(selected_id, school_invulling)
    # ========================================================================


if __name__ == "__main__":
    main()
