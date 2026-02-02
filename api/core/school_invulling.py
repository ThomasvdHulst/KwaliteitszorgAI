"""SchoolInvulling dataclass voor de invulling van een school."""

from dataclasses import dataclass


@dataclass
class SchoolInvulling:
    """De invulling van een school voor een deugdelijkheidseis."""

    ambitie: str = ""
    beoogd_resultaat: str = ""
    concrete_acties: str = ""
    wijze_van_meten: str = ""

    def is_leeg(self) -> bool:
        """Check of de school nog niks heeft ingevuld."""
        return not any([
            self.ambitie,
            self.beoogd_resultaat,
            self.concrete_acties,
            self.wijze_van_meten,
        ])

    def to_text(self) -> str:
        """Converteer naar leesbare tekst voor in de context."""
        if self.is_leeg():
            return "[Nog niet ingevuld door de school]"

        text = ""
        if self.ambitie:
            text += f"AMBITIE:\n{self.ambitie}\n\n"
        if self.beoogd_resultaat:
            text += f"BEOOGD RESULTAAT:\n{self.beoogd_resultaat}\n\n"
        if self.concrete_acties:
            text += f"CONCRETE ACTIES:\n{self.concrete_acties}\n\n"
        if self.wijze_van_meten:
            text += f"WIJZE VAN METEN:\n{self.wijze_van_meten}\n\n"

        return text.strip()
