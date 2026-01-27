# OnSpect AI - Technische Documentatie

Dit document beschrijft de technische architectuur en implementatie van OnSpect AI.

---

## 1. Systeemoverzicht

### Doel
OnSpect AI is een AI-gestuurde assistent die scholen helpt bij het werken met het waarderingskader van de Inspectie van het Onderwijs. Het systeem geeft feedback op de invulling van deugdelijkheidseisen binnen de PDCA-cyclus (Plan-Do-Check-Act).

### Doelgroep
- Schoolleiders en kwaliteitscoordinatoren in het voortgezet onderwijs
- Medewerkers die werken aan schoolplannen en kwaliteitszorg

### Kernfunctionaliteit
1. **Uitleg**: Verklaringen van deugdelijkheidseisen in begrijpelijke taal
2. **Feedback**: Beoordeling van schoolinvullingen met sterke punten en verbeterpunten
3. **Suggesties**: Concrete verbetervoorstellen gebaseerd op good practices
4. **Chat**: Doorlopende conversatie met vervolgvragen

---

## 2. Ollama en Lokale AI-modellen

### Wat is Ollama?

Ollama is een open-source platform waarmee je Large Language Models (LLMs) lokaal kunt draaien op je eigen hardware. In plaats van dat je verzoeken naar een externe dienst stuurt zoals ChatGPT of Claude, draait het AI-model volledig op je eigen computer of server. Dit heeft belangrijke voordelen voor privacy en kosten.

Ollama fungeert als een "runtime" voor AI-modellen. Het beheert het laden van modellen in het geheugen, optimaliseert de inferentie voor je specifieke hardware (CPU, GPU, of Apple Silicon), en biedt een eenvoudige API waarmee applicaties kunnen communiceren met het model.

### Hoe werkt een lokaal AI-model?

Een Large Language Model is in essentie een zeer groot neuraal netwerk dat getraind is op miljarden teksten. Het model heeft geleerd patronen in taal te herkennen en kan op basis daarvan coherente, contextbewuste antwoorden genereren. Bij elke vraag die je stelt:

1. **Tokenisatie**: Je tekst wordt opgesplitst in "tokens" (woorden of woorddelen)
2. **Context verwerking**: Het model verwerkt alle tokens samen met de systeeminstructies
3. **Generatie**: Token voor token wordt het antwoord gegenereerd, waarbij elk volgend token wordt voorspeld op basis van alle voorgaande tokens
4. **Streaming**: De tokens worden direct teruggestuurd zodat je het antwoord ziet verschijnen

Het model zelf is een bestand van enkele tot tientallen gigabytes dat volledig in het werkgeheugen (RAM) of videogeheugen (VRAM) moet worden geladen.

### Het Qwen3 model

OnSpect AI gebruikt standaard het **Gemma3:27b** model van Google. Dit is een open-source model met 27 miljard parameters. De "27b" staat voor 27 billion (miljard) parameters - dit zijn de geleerde gewichten in het neurale netwerk.

Kenmerken van Gemma3:27b:
- **Taalondersteuning**: Uitstekende prestaties in Nederlands en Engels
- **Context window**: Kan tot 128.000 tokens tegelijk verwerken
- **Reasoning**: Sterke capaciteiten voor redeneren en gestructureerde feedback
- **Multimodaal**: Ondersteunt ook afbeeldingen als input (niet gebruikt in deze applicatie)
- **Licentie**: Open-source, vrij te gebruiken

Er zijn ook kleinere varianten beschikbaar (4b, 12b) die minder geheugen nodig hebben maar ook minder capabel zijn.

---

## 3. Integratie met PHP-applicaties

De OnSpect AI assistent is geschreven in Python, maar kan eenvoudig communiceren met de bestaande PHP-applicatie. Er zijn verschillende integratiemethoden mogelijk, afhankelijk van de gewenste architectuur.

### Optie 1: REST API (Aanbevolen)

De meest robuuste oplossing is om de Python-applicatie als een microservice te draaien die een REST API aanbiedt. De PHP-applicatie doet HTTP-requests naar deze service.

**Voordelen:**
- Duidelijke scheiding van verantwoordelijkheden
- Onafhankelijk schaalbaar
- Standaard webprotocollen (HTTP/JSON)
- Eenvoudig te beveiligen met API-keys of tokens

**Implementatie Python-kant (met FastAPI):**

```python
# api_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.onspect import DeugdelijkheidseisAssistent, SchoolInvulling

app = FastAPI()
assistent = DeugdelijkheidseisAssistent()

class ChatRequest(BaseModel):
    eis_id: str
    vraag: str
    vraag_type: str = "algemeen"
    ambitie: str = ""
    beoogd_resultaat: str = ""
    concrete_acties: str = ""
    wijze_van_meten: str = ""
    session_id: str = None  # Voor chat-continuatie

@app.post("/chat")
def chat(request: ChatRequest):
    invulling = SchoolInvulling(
        ambitie=request.ambitie,
        beoogd_resultaat=request.beoogd_resultaat,
        concrete_acties=request.concrete_acties,
        wijze_van_meten=request.wijze_van_meten,
    )

    antwoord = assistent.chat(
        eis_id=request.eis_id,
        school_invulling=invulling,
        vraag=request.vraag,
        vraag_type=request.vraag_type,
    )

    return {"antwoord": antwoord, "vraag_type": request.vraag_type}

# Start met: uvicorn api_server:app --host 0.0.0.0 --port 8000
```

**Implementatie PHP-kant:**

```php
<?php
class OnSpectAIClient {
    private string $baseUrl;

    public function __construct(string $baseUrl = 'http://localhost:8000') {
        $this->baseUrl = $baseUrl;
    }

    public function chat(
        string $eisId,
        string $vraag,
        string $vraagType = 'algemeen',
        array $schoolInvulling = []
    ): array {
        $data = [
            'eis_id' => $eisId,
            'vraag' => $vraag,
            'vraag_type' => $vraagType,
            'ambitie' => $schoolInvulling['ambitie'] ?? '',
            'beoogd_resultaat' => $schoolInvulling['beoogd_resultaat'] ?? '',
            'concrete_acties' => $schoolInvulling['concrete_acties'] ?? '',
            'wijze_van_meten' => $schoolInvulling['wijze_van_meten'] ?? '',
        ];

        $ch = curl_init($this->baseUrl . '/chat');
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 120); // AI responses kunnen even duren

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode !== 200) {
            throw new Exception("OnSpect AI error: HTTP $httpCode");
        }

        return json_decode($response, true);
    }
}

// Gebruik in je PHP-applicatie:
$ai = new OnSpectAIClient('http://ai-server:8000');

$result = $ai->chat(
    eisId: 'VS1.5',
    vraag: 'Kun je feedback geven op onze invulling?',
    vraagType: 'feedback',
    schoolInvulling: [
        'ambitie' => $_POST['ambitie'],
        'beoogd_resultaat' => $_POST['beoogd_resultaat'],
        'concrete_acties' => $_POST['concrete_acties'],
        'wijze_van_meten' => $_POST['wijze_van_meten'],
    ]
);

echo $result['antwoord'];
```

### Optie 2: Direct Ollama aanroepen vanuit PHP

Als je de Python-laag wilt overslaan, kun je Ollama ook rechtstreeks vanuit PHP aanroepen. Ollama biedt namelijk zelf een REST API aan.

**Voordelen:**
- Geen Python-service nodig
- Directe communicatie met Ollama

**Nadelen:**
- Je moet de prompt-logica dupliceren in PHP
- Geen gebruik van de OnSpect-specifieke context en instructies
- Meer onderhoud bij wijzigingen

```php
<?php
class OllamaClient {
    private string $baseUrl;
    private string $model;

    public function __construct(
        string $baseUrl = 'http://localhost:11434',
        string $model = 'gemma3:27b'
    ) {
        $this->baseUrl = $baseUrl;
        $this->model = $model;
    }

    public function chat(string $systemPrompt, string $userMessage): string {
        $data = [
            'model' => $this->model,
            'messages' => [
                ['role' => 'system', 'content' => $systemPrompt],
                ['role' => 'user', 'content' => $userMessage],
            ],
            'stream' => false,
        ];

        $ch = curl_init($this->baseUrl . '/api/chat');
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 300);

        $response = curl_exec($ch);
        curl_close($ch);

        $result = json_decode($response, true);
        return $result['message']['content'] ?? '';
    }
}
```

### Optie 3: Message Queue (voor hoog volume)

Bij veel gelijktijdige gebruikers is een message queue architectuur het meest schaalbaar. Verzoeken worden in een queue geplaatst en door workers verwerkt.

```
PHP App  →  Redis/RabbitMQ  →  Python Worker(s)  →  Ollama
              ↑                      ↓
              └──────── Response ────┘
```

Dit vereist meer infrastructuur maar schaalt beter en voorkomt timeouts bij piekbelasting.

### Aanbevolen architectuur voor productie

Voor de OnSpect-applicatie adviseren we **Optie 1 (REST API)** met de volgende setup:

```
┌─────────────────┐      HTTP/JSON       ┌─────────────────┐
│                 │  ←────────────────→  │                 │
│  PHP Applicatie │                      │  Python API     │
│  (bestaand)     │                      │  (FastAPI)      │
│                 │                      │                 │
└─────────────────┘                      └────────┬────────┘
                                                  │
                                                  ▼
                                         ┌─────────────────┐
                                         │                 │
                                         │     Ollama      │
                                         │  (lokaal model) │
                                         │                 │
                                         └─────────────────┘
```

**Deployment tips:**
- Draai de Python API en Ollama op dezelfde server voor minimale latency
- Gebruik een reverse proxy (nginx) voor SSL-terminatie en load balancing
- Implementeer rate limiting om overbelasting te voorkomen
- Voeg health checks toe voor monitoring

---

## 4. Architectuur

### Componentendiagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Web UI                            │
│                   (app/streamlit_app.py)                        │
│                                                                 │
│  - Eis selectie en weergave                                     │
│  - Schoolinvulling formulier                                    │
│  - Chat interface met geschiedenis                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DeugdelijkheidseisAssistent                    │
│              (src/onspect/assistant/assistent.py)               │
│                                                                 │
│  - Bouwt system prompt met context                              │
│  - Beheert chatgeschiedenis                                     │
│  - Communiceert met Ollama                                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Ollama                                  │
│                   (localhost:11434)                             │
│                                                                 │
│  - Laadt en beheert AI-model                                    │
│  - Verwerkt prompts en genereert responses                      │
│  - Streaming output                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Dataflow

1. Gebruiker selecteert deugdelijkheidseis en vult schoolgegevens in
2. Bij elke vraag wordt de volledige context meegestuurd:
   - Systeeminstructies (wie is de assistent, hoe moet deze reageren)
   - Deugdelijkheidseis informatie (omschrijving, uitleg, focuspunten, tips)
   - Schoolinvulling (ambitie, beoogd resultaat, acties, meten)
   - Chatgeschiedenis (voorgaande vragen en antwoorden)
3. Ollama genereert een streaming response
4. Response wordt real-time getoond in de interface
5. Vraag en antwoord worden toegevoegd aan de chatgeschiedenis

### Modules

| Module | Verantwoordelijkheid |
|--------|---------------------|
| `config/settings.py` | Centrale configuratie (model, tokens, parameters) |
| `src/onspect/models/school_invulling.py` | Dataclass voor schoolinvulling |
| `src/onspect/assistant/prompts.py` | System prompt en taak-instructies |
| `src/onspect/assistant/assistent.py` | Hoofdklasse met chat-logica |
| `src/onspect/utils/database.py` | Laden van deugdelijkheidseisen |

---

## 5. Hardware en Software Vereisten

### Minimale vereisten (development/demo)
- **OS**: macOS 12+, Linux, of Windows 10+
- **CPU**: Moderne multi-core processor
- **RAM**: 16GB (met kleiner model)
- **Opslag**: 10GB vrij
- **Python**: 3.10+

### Aanbevolen configuratie (productie)
- **Hardware**: Apple Silicon Mac of Linux server met GPU
- **RAM**: 32GB of meer
- **Model**: gemma3:27b

### Modelalternatieven

| Model | RAM nodig | Kwaliteit | Snelheid | Aanbevolen voor |
|-------|-----------|-----------|----------|-----------------|
| gemma3:4b | 4GB | Basis | Zeer snel | Demo, testing |
| gemma3:12b | 12GB | Goed | Snel | Licht productiegebruik |
| gemma3:27b | 24GB | Zeer goed | Gemiddeld | Productie (aanbevolen) |

---

## 6. Installatie

### Stap 1: Ollama installeren

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Of download van https://ollama.ai
```

### Stap 2: Model downloaden

```bash
ollama pull gemma3:27b
```

Dit downloadt ongeveer 17GB aan modeldata.

### Stap 3: Python dependencies

```bash
pip install -r requirements.txt
```

### Stap 4: Starten

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start de applicatie
streamlit run app/streamlit_app.py
```

---

## 7. Configuratie

### Environment Variables

| Variable | Default | Beschrijving |
|----------|---------|--------------|
| `ONSPECT_MODEL` | `gemma3:27b` | Ollama model naam |
| `ONSPECT_MAX_TOKENS` | `16000` | Maximum context tokens |

### Parameters (config/settings.py)

| Parameter | Waarde | Beschrijving |
|-----------|--------|--------------|
| `NUM_CTX` | 32768 | Context window grootte |
| `TEMPERATURE_DEFAULT` | 0.6 | Creativiteit van responses (0=deterministisch, 1=creatief) |
| `MAX_GENERATE_TOKENS` | 4000 | Maximum lengte van antwoorden |
| `MAX_CONVERSATION_HISTORY` | 10 | Aantal bericht-paren in geheugen |

---


