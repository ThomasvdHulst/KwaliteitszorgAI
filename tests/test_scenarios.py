"""
Test scenarios voor OnSpect AI.

Test de chat-functionaliteit met verschillende invullingen.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.onspect import DeugdelijkheidseisAssistent, SchoolInvulling


def print_stream(chunk: str) -> None:
    print(chunk, end="", flush=True)


def test_chat_flow():
    """Test de chat flow met vervolgvragen."""
    print("=" * 80)
    print("TEST: CHAT FLOW MET VERVOLGVRAGEN")
    print("=" * 80)

    assistent = DeugdelijkheidseisAssistent()

    invulling = SchoolInvulling(
        ambitie="Duidelijk aanspreekpunt voor pesten",
        beoogd_resultaat="90% bekendheid anti-pestcoordinator",
        concrete_acties="Mw. De Vries aangesteld, posters opgehangen, in schoolgids",
        wijze_van_meten="Jaarlijkse enquete",
    )

    # Eerste vraag
    print("\n[VRAAG 1: Feedback]")
    print("-" * 40)
    assistent.chat(
        eis_id="VS1.5",
        school_invulling=invulling,
        vraag="Kun je feedback geven op onze invulling?",
        vraag_type="feedback",
        stream_handler=print_stream,
    )

    # Vervolgvraag
    print("\n\n[VRAAG 2: Vervolgvraag]")
    print("-" * 40)
    assistent.chat(
        eis_id="VS1.5",
        school_invulling=invulling,
        vraag="Kun je meer uitleg geven over het punt van de scholing?",
        vraag_type="algemeen",
        stream_handler=print_stream,
    )

    # Nog een vervolgvraag
    print("\n\n[VRAAG 3: Concrete suggestie]")
    print("-" * 40)
    assistent.chat(
        eis_id="VS1.5",
        school_invulling=invulling,
        vraag="Welke training zou je aanraden?",
        vraag_type="suggestie",
        stream_handler=print_stream,
    )

    print("\n\n" + "=" * 80)
    print(f"Chat history: {len(assistent.get_chat_history())} berichten")
    print("=" * 80)


def test_feedback_scenarios():
    """Test feedback op verschillende invullingen."""
    print("\n" + "=" * 80)
    print("TEST: FEEDBACK SCENARIOS")
    print("=" * 80)

    assistent = DeugdelijkheidseisAssistent()

    scenarios = [
        ("GOEDE INVULLING", SchoolInvulling(
            ambitie="Duidelijk aanspreekpunt voor pesten met coordinator die beide taken combineert",
            beoogd_resultaat="90% bekendheid, alle meldingen binnen 24u opgepakt",
            concrete_acties="Mw. De Vries als coordinator (aanspreekpunt + beleid), training gevolgd, posters, schoolgids, 0.2 fte",
            wijze_van_meten="Jaarlijkse enquete, registratie meldingen, evaluatiegesprekken",
        )),
        ("TAKEN VERDEELD (FOUT)", SchoolInvulling(
            ambitie="Aanspreekpunten bij pesten",
            beoogd_resultaat="Leerlingen kunnen terecht bij mentoren",
            concrete_acties="Mentoren zijn aanspreekpunt, Mw. Janssen coordineert beleid apart",
            wijze_van_meten="Evaluatie met mentoren",
        )),
        ("TE ALGEMEEN (FOUT)", SchoolInvulling(
            ambitie="Pestvrije school",
            beoogd_resultaat="Minder dan 3 incidenten per jaar",
            concrete_acties="Anti-pestprotocol, mentorlessen, Week tegen Pesten",
            wijze_van_meten="Veiligheidsmonitor",
        )),
    ]

    for name, invulling in scenarios:
        print(f"\n[{name}]")
        print("-" * 40)
        assistent.chat(
            eis_id="VS1.5",
            school_invulling=invulling,
            vraag="Geef feedback op onze invulling",
            vraag_type="feedback",
            stream_handler=print_stream,
        )
        assistent.reset_chat()
        print("\n")


if __name__ == "__main__":
    test_chat_flow()
    test_feedback_scenarios()
    print("\nAlle tests voltooid!")
