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
from src.kwaliteitszorg.utils.pdf_processor import extract_text_from_pdf

# ============================================================================
# EXPERIMENTEEL: Suggestie feature import
# Verwijder dit blok + de aanroep in main() om de feature uit te schakelen
# ============================================================================
try:
    # Absolute import path voor robuustheid
    from app.suggestie_ui import render_suggesties_tab
    SUGGESTIES_ENABLED = True
except ImportError:
    try:
        # Fallback voor directe uitvoering vanuit app/ directory
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
    # Reset document (niet automatisch - gebruiker moet expliciet verwijderen)
    # st.session_state.document_text = None
    # st.session_state.document_filename = None


def render_chat_message(role: str, content: str, sources: list = None):
    """Render een chat bericht met optionele bronvermelding."""
    # Gebruik Streamlit's native chat_message voor correcte markdown rendering
    avatar = "🧑" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)
        # Toon bronvermelding als die er is
        if sources and role == "assistant":
            st.markdown("---")
            st.markdown("**Onderbouwing:**")
            for source in sources:
                st.caption(f"• {source}")


def extract_onderbouwing_from_response(response: str) -> tuple:
    """
    Extraheer de ONDERBOUWING sectie uit het AI-antwoord.

    De AI is geïnstrueerd om zijn antwoord te eindigen met:
    ONDERBOUWING:
    - document1.pdf
    - document2.pdf

    Args:
        response: Het AI-gegenereerde antwoord

    Returns:
        Tuple van (cleaned_response, used_sources)
        - cleaned_response: Antwoord zonder de ONDERBOUWING sectie
        - used_sources: Lijst van documentnamen
    """
    if not response:
        return response, []

    # Zoek naar de ONDERBOUWING sectie (case-insensitive)
    import re
    pattern = r'\n*ONDERBOUWING:\s*(.*)$'
    match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)

    if not match:
        return response, []

    # Haal het deel voor ONDERBOUWING
    onderbouwing_start = match.start()
    cleaned_response = response[:onderbouwing_start].strip()

    # Parse de bronnen uit de ONDERBOUWING sectie
    onderbouwing_text = match.group(1).strip()

    # Check voor "Geen documenten gebruikt" of vergelijkbaar
    if "geen" in onderbouwing_text.lower():
        return cleaned_response, []

    # Zoek naar document namen (elke regel die begint met - of *)
    sources = []
    for line in onderbouwing_text.split('\n'):
        line = line.strip()
        if line.startswith('-') or line.startswith('*') or line.startswith('•'):
            source = line.lstrip('-*• ').strip()
            if source:
                sources.append(source)
        elif line and not line.startswith('ONDERBOUWING'):
            # Soms zonder bullets
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
    """
    Verwerk een chat bericht en genereer een antwoord.

    Dit is een interne functie die zowel door de chat knop als door
    auto-triggers (bijv. vanuit suggesties) aangeroepen kan worden.
    """
    # Voeg user bericht toe aan weergave
    st.session_state.messages.append({"role": "user", "content": vraag})

    # Placeholder voor streaming response
    with st.spinner(""):
        response_placeholder = st.empty()
        response_buffer = ""

        def handle_chunk(chunk: str):
            nonlocal response_buffer
            response_buffer += chunk
            # Gebruik markdown voor streaming (zonder complexe HTML)
            response_placeholder.markdown(response_buffer)

        # Genereer antwoord met error handling
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
            # Verwijder het user bericht weer uit de lijst
            st.session_state.messages.pop()
            return

    # Extraheer ONDERBOUWING sectie uit het antwoord (als RAG actief was)
    used_sources = []
    display_content = antwoord
    if rag_context:
        display_content, used_sources = extract_onderbouwing_from_response(antwoord)

    # Voeg assistant bericht toe (met bronnen indien beschikbaar)
    message_data = {"role": "assistant", "content": display_content}
    if used_sources:
        message_data["sources"] = used_sources
    st.session_state.messages.append(message_data)

    # Rerun om UI te updaten
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

    # Check voor auto-chat trigger (van suggesties "Wat kan ik nu doen?")
    auto_trigger = st.session_state.get("auto_chat_trigger")
    if st.session_state.get("switch_to_chat"):
        st.info("💡 Vraag wordt automatisch verstuurd...")
        # Clear de flags nu we ze gaan verwerken
        st.session_state.pop("auto_chat_trigger", None)
        st.session_state.pop("switch_to_chat", None)

    # Toon context indicator
    if rag_context:
        st.info("Documentdatabank actief - relevante passages worden meegestuurd")
    elif document_text:
        st.info(f"Document gekoppeld: **{document_filename}**")

    # Toon bestaande berichten
    for msg in st.session_state.messages:
        render_chat_message(msg["role"], msg["content"], msg.get("sources"))

    # Verwerk auto-trigger als aanwezig
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
        return  # Stop hier, rerun gebeurt in _process_chat_message

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
            _process_chat_message(
                vraag=vraag,
                vraag_type=vraag_type,
                selected_id=selected_id,
                school_invulling=school_invulling,
                document_text=document_text,
                document_filename=document_filename,
                rag_context=rag_context,
            )


def main():
    st.set_page_config(
        page_title="Kwaliteitszorg AI",
        page_icon="🎓",
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

    # Velden onder elkaar met grotere hoogte en karakterlimiet
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

    # Initialiseer rag_context (altijd None tenzij RAG actief is)
    rag_context = None
    rag_active = False
    rag_available_sources = []  # Bronnen die beschikbaar zijn voor de AI

    if RAG_ENABLED:
        with st.expander("Documentdatabank beheren", expanded=False):
            render_document_databank()

        # RAG toggle en context ophalen
        rag_active, rag_context, rag_available_sources = render_rag_toggle(selected_id, eis)

        if rag_active and rag_context:
            # RAG is actief, geen single document nodig
            st.markdown("---")
        else:
            # Toon single document upload als alternatief
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

        # Verwerk geüpload document
        if uploaded_file is not None:
            # Check of dit een nieuw bestand is
            if st.session_state.document_filename != uploaded_file.name:
                with st.spinner("Document verwerken..."):
                    result = extract_text_from_pdf(
                        file_bytes=uploaded_file.read(),
                        filename=uploaded_file.name,
                    )

                    if result.success:
                        st.session_state.document_text = result.text
                        st.session_state.document_filename = result.filename

                        # Toon document info
                        status_msg = f"Document geladen: {result.page_count} pagina's, {result.char_count:,} karakters"
                        if result.truncated:
                            status_msg += " (ingekort)"
                        st.success(status_msg)
                    else:
                        st.error(result.error)
                        st.session_state.document_text = None
                        st.session_state.document_filename = None

        # Toon huidige document status en verwijder optie
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
    # ========================================================================


if __name__ == "__main__":
    main()
