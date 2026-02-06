"""
UI componenten voor de suggestie-feature.

Dit bestand kan worden verwijderd samen met src/kwaliteitszorg/assistant/suggesties.py
om de feature volledig te verwijderen.
"""

import html
import streamlit as st
from typing import Dict

# Importeer alleen wat nodig is
from src.kwaliteitszorg.assistant.suggesties import SuggestieGenerator, VeldSuggestie, SuggestieResultaat
from src.kwaliteitszorg import SchoolInvulling


# Kleuren voor diff weergave
COLORS = {
    "old_bg": "#FEE2E2",      # Licht rood
    "new_bg": "#DCFCE7",      # Licht groen
    "old_border": "#F87171",  # Rood
    "new_border": "#4ADE80",  # Groen
    "neutral_bg": "#F8FAFD",
}


def render_suggestie_css():
    """Injecteer CSS voor suggestie weergave."""
    st.markdown("""
    <style>
        .suggestie-container {
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            background: white;
        }
        .suggestie-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }
        .suggestie-header h4 {
            margin: 0;
            color: #14194A;
            font-size: 0.95rem;
        }
        .suggestie-toelichting {
            font-size: 0.85rem;
            color: #496580;
            margin-bottom: 0.75rem;
            padding: 0.5rem;
            background: #F8FAFD;
            border-radius: 6px;
        }
        .diff-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        .diff-box {
            padding: 0.75rem;
            border-radius: 8px;
            font-size: 0.9rem;
            line-height: 1.5;
            white-space: pre-wrap;
        }
        .diff-old {
            background: #FEE2E2;
            border-left: 3px solid #F87171;
        }
        .diff-new {
            background: #DCFCE7;
            border-left: 3px solid #4ADE80;
        }
        .diff-label {
            font-size: 0.75rem;
            font-weight: 600;
            color: #64748B;
            margin-bottom: 0.25rem;
        }
        .no-suggestie {
            color: #64748B;
            font-style: italic;
        }
    </style>
    """, unsafe_allow_html=True)


VELD_LABELS = {
    "ambitie": "Ambitie",
    "beoogd_resultaat": "Beoogd resultaat",
    "concrete_acties": "Concrete acties",
    "wijze_van_meten": "Wijze van meten",
}

# Mapping van veldnamen naar input keys in streamlit_app.py
VELD_INPUT_KEYS = {
    "ambitie": "input_ambitie",
    "beoogd_resultaat": "input_resultaat",
    "concrete_acties": "input_acties",
    "wijze_van_meten": "input_meten",
}


def render_veld_suggestie(veld: str, suggestie: VeldSuggestie) -> str:
    """
    Render een enkele veldsuggestie met accept/reject knoppen.

    Returns:
        "accepted" als geaccepteerd, "rejected" als geweigerd, None anders
    """
    label = VELD_LABELS.get(veld, veld)

    # Check of dit veld al behandeld is
    behandeld_key = f"suggestie_behandeld_{veld}"
    if behandeld_key in st.session_state:
        status = st.session_state[behandeld_key]
        if status == "accepted":
            st.success(f"✓ {label}: overgenomen")
        else:
            st.info(f"✗ {label}: geweigerd")
        return None

    if not suggestie.heeft_suggestie:
        st.markdown(f"""
        <div class="suggestie-container">
            <div class="suggestie-header">
                <h4>{label}</h4>
            </div>
            <p class="no-suggestie">Geen wijziging nodig</p>
        </div>
        """, unsafe_allow_html=True)
        return None

    # Render de suggestie (HTML-escaped tegen XSS via AI output)
    safe_toelichting = html.escape(suggestie.toelichting) if suggestie.toelichting else ""
    safe_huidige = html.escape(suggestie.huidige_tekst) if suggestie.huidige_tekst else "[leeg]"
    safe_nieuwe = html.escape(suggestie.nieuwe_tekst) if suggestie.nieuwe_tekst else "[leeg]"

    st.markdown(f"""
    <div class="suggestie-container">
        <div class="suggestie-header">
            <h4>{label}</h4>
        </div>
        {f'<div class="suggestie-toelichting">{safe_toelichting}</div>' if safe_toelichting else ''}
        <div class="diff-container">
            <div>
                <div class="diff-label">HUIDIGE TEKST</div>
                <div class="diff-box diff-old">{safe_huidige}</div>
            </div>
            <div>
                <div class="diff-label">SUGGESTIE</div>
                <div class="diff-box diff-new">{safe_nieuwe}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Accept/reject knoppen
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button(f"✓ Accepteer", key=f"accept_{veld}", type="primary"):
            return "accepted"
    with col2:
        if st.button(f"✗ Weiger", key=f"reject_{veld}"):
            return "rejected"

    return None


from typing import Optional, List


def render_context_vragen(eis: dict, eis_id: str) -> Dict[str, str]:
    """
    Render de contextvragen voor een eis en return de antwoorden.

    Args:
        eis: De eisdata met eventuele context_vragen
        eis_id: ID van de eis (voor unieke session state keys)

    Returns:
        Dict met vraag_id -> antwoord mappings
    """
    vragen = eis.get("context_vragen", [])
    if not vragen:
        return {}

    # Initialiseer session state voor context antwoorden als dat nog niet is gebeurd
    context_key = f"school_context_{eis_id}"
    if context_key not in st.session_state:
        st.session_state[context_key] = {}

    st.markdown("#### Context over jullie school")
    st.caption(
        "Deze informatie helpt de AI gerichtere suggesties te geven. "
        "Vul in wat je weet - alles is optioneel."
    )

    antwoorden = {}

    for vraag in vragen:
        vraag_id = vraag["id"]
        input_key = f"context_input_{eis_id}_{vraag_id}"

        # Haal eventueel opgeslagen waarde op
        default_value = st.session_state[context_key].get(vraag_id, "")

        antwoord = st.text_input(
            vraag["vraag"],
            value=default_value,
            placeholder=vraag.get("placeholder", ""),
            key=input_key,
            help=f"Optioneel - helpt de AI betere suggesties te geven"
        )

        if antwoord and antwoord.strip():
            antwoorden[vraag_id] = antwoord.strip()
            # Sla op in session state voor persistentie
            st.session_state[context_key][vraag_id] = antwoord.strip()
        elif vraag_id in st.session_state[context_key]:
            # Verwijder als leeggemaakt
            del st.session_state[context_key][vraag_id]

    st.markdown("---")

    return antwoorden


def _build_school_context_text(antwoorden: Dict[str, str], vragen: list) -> str:
    """
    Bouw een leesbare context tekst van de school-antwoorden.

    Args:
        antwoorden: Dict met vraag_id -> antwoord
        vragen: Lijst van vraag-objecten uit de database

    Returns:
        Geformatteerde context string voor de prompt
    """
    if not antwoorden:
        return ""

    # Maak een mapping van vraag_id naar vraag tekst
    vraag_teksten = {v["id"]: v["vraag"] for v in vragen}

    lines = []
    for vraag_id, antwoord in antwoorden.items():
        vraag_tekst = vraag_teksten.get(vraag_id, vraag_id)
        # Verwijder het vraagteken en "jullie" voor kortere weergave
        vraag_kort = vraag_tekst.rstrip("?").replace("jullie ", "")
        lines.append(f"- {vraag_kort}: {antwoord}")

    return "\n".join(lines)


def render_suggesties_tab(
    eis_id: str,
    eis: dict,
    school_invulling: SchoolInvulling,
    document_text: Optional[str] = None,
    document_filename: Optional[str] = None,
    rag_context: Optional[str] = None,
):
    """
    Render de volledige suggesties tab.

    Args:
        eis_id: ID van de deugdelijkheidseis
        eis: De eisdata
        school_invulling: Huidige invulling
        document_text: Optioneel - tekst uit gekoppeld beleidsdocument
        document_filename: Optioneel - naam van het beleidsdocument
        rag_context: Optioneel - context van RAG-opgehaalde passages
    """
    render_suggestie_css()

    st.markdown("### Suggesties voor verbetering")
    st.markdown(
        "Laat de AI concrete suggesties genereren voor je invulling. "
        "Je kunt elke suggestie accepteren of weigeren."
    )

    # Toon context indicator
    if rag_context:
        st.info("Documentdatabank actief - suggesties worden gebaseerd op relevante passages")
    elif document_text:
        st.info(f"Beleidsdocument gekoppeld: **{document_filename}** - suggesties worden hierop gebaseerd")

    # === SCHOOL CONTEXT VRAGEN ===
    # Toon contextvragen als de eis deze heeft
    context_vragen = eis.get("context_vragen", [])
    context_antwoorden = {}
    school_context_text = None

    if context_vragen:
        context_antwoorden = render_context_vragen(eis, eis_id)
        if context_antwoorden:
            school_context_text = _build_school_context_text(context_antwoorden, context_vragen)

    # === QUERY VERRIJKING TOGGLE ===
    # Toon alleen als er RAG context EN school context is
    enrich_query = False
    if rag_context and school_context_text:
        enrich_query = st.toggle(
            "Query verrijking",
            value=st.session_state.get("enrich_query_enabled", False),
            key="enrich_query_toggle",
            help="Verrijk de zoekquery met jullie schoolcontext voor relevantere documentpassages. "
                 "Dit doet een extra AI-aanroep en kan iets langer duren."
        )
        st.session_state.enrich_query_enabled = enrich_query

        if enrich_query:
            st.caption("De AI zal de zoekquery aanpassen op basis van jullie schoolcontext.")

    # Check of er al suggesties zijn
    if "suggestie_resultaat" not in st.session_state:
        st.session_state.suggestie_resultaat = None

    # Genereer knop
    if st.button("Genereer suggesties", type="primary", use_container_width=True):
        generator = SuggestieGenerator()

        spinner_text = "AI analyseert je invulling..."
        if enrich_query:
            spinner_text = "AI verrijkt zoekquery en analyseert documenten..."
        elif school_context_text:
            spinner_text = "AI analyseert je invulling met jullie schoolcontext..."
        if rag_context and not enrich_query:
            spinner_text = "AI analyseert je invulling en documentdatabank..."
        elif document_text:
            spinner_text = "AI analyseert je invulling en beleidsdocument..."

        # Haal geselecteerde document IDs op voor gefilterde retrieval
        selected_doc_ids = st.session_state.get("rag_selected_docs", None)

        with st.spinner(spinner_text):
            resultaat = generator.genereer_suggesties(
                eis_id=eis_id,
                school_invulling=school_invulling,
                document_text=document_text,
                document_filename=document_filename,
                rag_context=rag_context,
                school_context=school_context_text,
                enrich_query=enrich_query,
                selected_doc_ids=selected_doc_ids,
            )

            st.session_state.suggestie_resultaat = resultaat

            # Reset behandeld-status voor alle velden
            for veld in ["ambitie", "beoogd_resultaat", "concrete_acties", "wijze_van_meten"]:
                if f"suggestie_behandeld_{veld}" in st.session_state:
                    del st.session_state[f"suggestie_behandeld_{veld}"]

        st.rerun()

    # Toon resultaten
    resultaat = st.session_state.suggestie_resultaat

    if resultaat is None:
        st.info("Klik op 'Genereer suggesties' om te beginnen.")
        return

    if not resultaat.success:
        st.error(f"Er ging iets mis: {resultaat.error}")
        if resultaat.raw_response:
            with st.expander("Ruwe AI response (debug)"):
                st.code(resultaat.raw_response)
        return

    # Toon suggesties per veld
    st.markdown("---")

    for veld in ["ambitie", "beoogd_resultaat", "concrete_acties", "wijze_van_meten"]:
        suggestie = resultaat.suggesties.get(veld)
        if suggestie:
            actie = render_veld_suggestie(veld, suggestie)
            if actie == "accepted":
                # Update het input veld direct
                input_key = VELD_INPUT_KEYS[veld]
                st.session_state[input_key] = suggestie.nieuwe_tekst or ""
                st.session_state[f"suggestie_behandeld_{veld}"] = "accepted"
                # Verhoog widget_version om Streamlit te dwingen de widgets te resetten
                if "widget_version" in st.session_state:
                    st.session_state.widget_version += 1
                st.rerun()
            elif actie == "rejected":
                st.session_state[f"suggestie_behandeld_{veld}"] = "rejected"
                st.rerun()

    # Toon onderbouwing (gebruikte bronnen - direct van de AI)
    if resultaat.gebruikte_bronnen:
        st.markdown("---")
        st.markdown("**Onderbouwing:**")
        st.caption("De volgende documenten zijn gebruikt voor deze suggesties:")
        for source in resultaat.gebruikte_bronnen:
            st.caption(f"• {source}")

    # === WAT KAN IK NU DOEN? ===
    render_vervolgacties(eis_id, eis)


def render_vervolgacties(eis_id: str, eis: dict):
    """
    Render de 'Wat kan ik nu doen?' sectie met vervolgacties na suggesties.

    Bij klik wordt de gebruiker naar de chat tab gestuurd met een automatische vraag.
    """
    st.markdown("---")
    st.markdown("### Wat kan ik nu doen?")

    # Check of er een pending actie is (voor visuele feedback)
    if st.session_state.get("auto_chat_trigger"):
        trigger = st.session_state.get("auto_chat_trigger")
        actie_naam = {
            "feedback": "Audit invulling",
            "uitleg": "Uitleg eis",
        }.get(trigger.get("type"), "Actie")
        st.success(f"✓ **{actie_naam}** klaargezet! Klik op de **Chat** tab hierboven om het antwoord te zien.")
        return

    st.caption("Kies een vervolgactie om verder te gaan met de AI-assistent:")

    # CSS voor de actie knoppen
    st.markdown("""
    <style>
        .actie-knop {
            background: linear-gradient(135deg, #F8FAFD 0%, #DCEEFA 100%);
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .actie-knop:hover {
            border-color: #4599D5;
            box-shadow: 0 2px 8px rgba(69, 153, 213, 0.15);
        }
        .actie-titel {
            font-weight: 600;
            color: #14194A;
            margin-bottom: 0.25rem;
        }
        .actie-beschrijving {
            font-size: 0.85rem;
            color: #496580;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "📋 Audit mijn invulling",
            key="actie_audit",
            use_container_width=True,
            help="Laat de AI je volledige invulling beoordelen met sterke punten en verbeterpunten"
        ):
            # Stel session state in voor auto-chat
            st.session_state.auto_chat_trigger = {
                "type": "feedback",
                "vraag": f"Geef feedback op mijn invulling voor {eis_id}. Beoordeel alle vier de velden en geef concrete verbeterpunten.",
            }
            st.session_state.switch_to_chat = True
            st.rerun()

    with col2:
        if st.button(
            "💡 Leg deze eis uit",
            key="actie_uitleg",
            use_container_width=True,
            help="Krijg uitleg over wat deze eis inhoudt en hoe je invulling hier bij past"
        ):
            st.session_state.auto_chat_trigger = {
                "type": "uitleg",
                "vraag": f"Leg uit wat eis {eis_id} ({eis.get('titel', '')}) precies inhoudt en hoe onze huidige invulling hieraan voldoet.",
            }
            st.session_state.switch_to_chat = True
            st.rerun()

    with col3:
        if st.button(
            "📁 Maak kwaliteitsproject",
            key="actie_project",
            use_container_width=True,
            help="Binnenkort beschikbaar: maak een verbeterproject aan op basis van de feedback",
            disabled=True,  # Placeholder - nog niet geïmplementeerd
        ):
            st.info("Deze functie wordt binnenkort toegevoegd!")

    # Toon beschrijvingen onder de knoppen
    st.markdown("""
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
        <div class="actie-beschrijving">Krijg een volledige beoordeling met oordeel, sterke punten en verbeterpunten</div>
        <div class="actie-beschrijving">Begrijp de eis beter en zie hoe je invulling aansluit</div>
        <div class="actie-beschrijving">Zet verbeterpunten om in een concreet actieplan (coming soon)</div>
    </div>
    """, unsafe_allow_html=True)
