# OnSpect AI

Een AI-assistent die scholen helpt met het waarderingskader van de Inspectie van het Onderwijs.

## Wat is OnSpect AI?

OnSpect AI is een lokaal draaiende AI-assistent die scholen ondersteunt bij het werken met deugdelijkheidseisen uit het waarderingskader van de Inspectie van het Onderwijs. De assistent kan:

- **Uitleg geven** over wat een deugdelijkheidseis inhoudt
- **Feedback geven** op de invulling van een school
- **Suggesties doen** voor verbeteringen
- **Vragen beantwoorden** over het kwaliteitszorgproces

### Belangrijkste kenmerken

- **Volledig lokaal**: Draait op je eigen computer, geen data naar externe servers
- **Contextbewust**: Begrijpt de PDCA-cyclus en kwaliteitszorg in het onderwijs
- **Gestructureerde feedback**: Geeft concrete, bruikbare feedback met sterke punten en verbeterpunten
- **Streaming antwoorden**: Antwoorden worden direct getoond terwijl ze gegenereerd worden

## Installatie

### Vereisten

- Python 3.10 of hoger
- [Ollama](https://ollama.ai) geinstalleerd en draaiend
- Minimaal 16GB RAM (32GB aanbevolen)
- Voor Apple Silicon: M1/M2/M3 processor

### Stappen

1. **Clone de repository**
   ```bash
   git clone <repository-url>
   cd OnSpectAIv2
   ```

2. **Installeer dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download het AI model via Ollama**
   ```bash
   ollama pull qwen3:30b
   ```

4. **Kopieer de voorbeeldconfiguratie**
   ```bash
   cp .env.example .env
   ```

## Gebruik

### Demo starten

Start de web interface met:

```bash
./scripts/run_demo.sh
```

Of direct met Streamlit:

```bash
streamlit run app/streamlit_app.py
```

Open vervolgens http://localhost:8501 in je browser.

### Workflow

1. **Selecteer een deugdelijkheidseis** (bijv. VS1.1 - Algemene Veiligheid)
2. **Vul de vier onderdelen in**:
   - Ambitie
   - Beoogd resultaat
   - Concrete acties
   - Wijze van meten
3. **Kies het type vraag** (uitleg, feedback, suggestie, algemeen)
4. **Stel je vraag** en ontvang direct streaming feedback

## Projectstructuur

```
OnSpectAIv2/
├── config/
│   └── settings.py          # Centrale configuratie
├── src/onspect/
│   ├── models/              # Dataclasses
│   ├── core/                # Context en conversatie management
│   ├── assistant/           # AI assistent en prompts
│   └── utils/               # Database utilities
├── data/
│   └── deugdelijkheidseisen_db.json
├── app/
│   └── streamlit_app.py     # Web interface
├── tests/
│   └── test_scenarios.py    # Test scenarios
└── scripts/
    └── run_demo.sh          # Demo launcher
```

## Configuratie

Pas de instellingen aan via environment variables of `.env`:

| Variable | Default | Beschrijving |
|----------|---------|--------------|
| `ONSPECT_MODEL` | `qwen3:30b` | Het Ollama model |
| `ONSPECT_MAX_TOKENS` | `12000` | Maximum context tokens |

## Tests uitvoeren

Voer de testscenario's uit om te valideren dat de AI correct werkt:

```bash
python tests/test_scenarios.py
```

## Licentie

Intern project - niet voor externe distributie.
