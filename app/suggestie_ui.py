"""
UI componenten voor de suggestie-feature.

Dit bestand kan worden verwijderd samen met src/kwaliteitszorg/assistant/suggesties.py
om de feature volledig te verwijderen.
"""

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

    # Render de suggestie
    st.markdown(f"""
    <div class="suggestie-container">
        <div class="suggestie-header">
            <h4>{label}</h4>
        </div>
        {f'<div class="suggestie-toelichting">{suggestie.toelichting}</div>' if suggestie.toelichting else ''}
        <div class="diff-container">
            <div>
                <div class="diff-label">HUIDIGE TEKST</div>
                <div class="diff-box diff-old">{suggestie.huidige_tekst or '[leeg]'}</div>
            </div>
            <div>
                <div class="diff-label">SUGGESTIE</div>
                <div class="diff-box diff-new">{suggestie.nieuwe_tekst or '[leeg]'}</div>
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


def render_suggesties_tab(
    eis_id: str,
    eis: dict,
    school_invulling: SchoolInvulling,
):
    """
    Render de volledige suggesties tab.

    Args:
        eis_id: ID van de deugdelijkheidseis
        eis: De eisdata
        school_invulling: Huidige invulling
    """
    render_suggestie_css()

    st.markdown("### Suggesties voor verbetering")
    st.markdown(
        "Laat de AI concrete suggesties genereren voor je invulling. "
        "Je kunt elke suggestie accepteren of weigeren."
    )

    # Check of er al suggesties zijn
    if "suggestie_resultaat" not in st.session_state:
        st.session_state.suggestie_resultaat = None

    # Genereer knop
    if st.button("Genereer suggesties", type="primary", use_container_width=True):
        generator = SuggestieGenerator()

        with st.spinner("AI analyseert je invulling..."):
            resultaat = generator.genereer_suggesties(
                eis_id=eis_id,
                school_invulling=school_invulling,
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
