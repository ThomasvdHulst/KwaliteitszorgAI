# OnSpectAI API

REST API voor AI-gestuurde feedback op deugdelijkheidseisen in het onderwijs. Ontworpen voor integratie met de OnSpect Laravel-applicatie.

---

## Wat doet deze API?

De OnSpectAI API biedt scholen AI-gestuurde ondersteuning bij het invullen van deugdelijkheidseisen voor de onderwijsinspectie. De API:

1. **Geeft feedback** op schoolinvullingen (ambitie, beoogd resultaat, concrete acties, wijze van meten)
2. **Legt eisen uit** in begrijpelijke taal
3. **Doet suggesties** voor verbeteringen
4. **Beantwoordt vragen** over specifieke eisen

De AI is getraind op de PDCA-cyclus (Plan-Do-Check-Act) en kent de specifieke eisen van de onderwijsinspectie.

---

## Architectuur

```
┌─────────────────────────────────────────────────────────────────┐
│                        Laravel (OnSpect)                        │
│                                                                 │
│  ┌─────────────┐    HTTP/JSON     ┌─────────────────────────┐  │
│  │ Controller  │ ───────────────► │    OnSpectAI API        │  │
│  │             │ ◄─────────────── │    (FastAPI/Python)     │  │
│  └─────────────┘                  └───────────┬─────────────┘  │
│                                               │                 │
│                                               ▼                 │
│                                   ┌─────────────────────────┐  │
│                                   │   Ollama (LLM Server)   │  │
│                                   │   Model: gemma3:27b     │  │
│                                   └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Componenten

| Component | Technologie | Functie |
|-----------|-------------|---------|
| **OnSpectAI API** | Python/FastAPI | REST endpoints, request validatie, prompt engineering |
| **Ollama** | Go | LLM inference server, draait het AI-model lokaal |
| **gemma3:27b** | - | Google's open-source taalmodel (27 miljard parameters) |

### Waarom deze architectuur?

- **Privacy**: Het AI-model draait lokaal, schooldata verlaat de server niet
- **Kosten**: Geen API-kosten per request (zoals bij OpenAI/Claude)
- **Controle**: Volledige controle over het model en de prompts
- **Snelheid**: Geen externe API-calls, lage latency

---

## API Endpoints

### Health Check

```
GET /health
```

Controleert of de API en Ollama bereikbaar zijn. Geen authenticatie vereist.

**Response:**
```json
{
  "status": "ok",
  "ollama": "connected",
  "model": "gemma3:27b",
  "message": ""
}
```

---

### Lijst alle eisen

```
GET /api/v1/eisen
Header: X-API-Key: <api-key>
```

Haalt een overzicht op van alle beschikbare deugdelijkheidseisen.

**Response:**
```json
{
  "eisen": [
    { "id": "VS 1.1", "standaard": "VS1 - Veiligheid", "titel": "Algemene Veiligheid" },
    { "id": "VS 1.5", "standaard": "VS1 - Veiligheid", "titel": "Anti-pestcoördinator" },
    { "id": "OP 0.1", "standaard": "OP0 - Basisvaardigheden", "titel": "Doelgericht en samenhangend curriculum..." }
  ],
  "totaal": 5
}
```

---

### Haal eis details op

```
GET /api/v1/eisen/{eis_id}
Header: X-API-Key: <api-key>
```

Haalt de volledige informatie van een specifieke eis op, inclusief uitleg, focuspunten en tips.

**Response:**
```json
{
  "id": "VS 1.5",
  "standaard": "VS1 - Veiligheid",
  "titel": "Anti-pestcoördinator",
  "eisomschrijving": "De school heeft een persoon aangesteld...",
  "uitleg": "KERNVRAAG: Heeft de school een benoemde...",
  "focuspunten": "• Eén persoon voor beide taken...",
  "tips": "De persoon aanstellen:\n• Kies iemand die...",
  "voorbeelden": "VOORBEELD 1: Uitstekende invulling..."
}
```

---

### Chat (AI feedback)

```
POST /api/v1/chat
Header: X-API-Key: <api-key>
Content-Type: application/json
```

Dit is de kern van de API: hier vraag je AI-feedback op een schoolinvulling.

**Request:**
```json
{
  "eis_id": "VS 1.5",
  "vraag": "Geef feedback op onze invulling",
  "vraag_type": "feedback",
  "school_invulling": {
    "ambitie": "Onze school streeft naar een duidelijk aanspreekpunt...",
    "beoogd_resultaat": "90% van de leerlingen kent de anti-pestcoördinator...",
    "concrete_acties": "Mevrouw Bakker is aangesteld als anti-pestcoördinator...",
    "wijze_van_meten": "Jaarlijkse enquête onder leerlingen..."
  }
}
```

**Vraag types:**
- `feedback` - Geef feedback op de invulling
- `uitleg` - Leg de eis uit
- `suggestie` - Doe suggesties voor verbetering
- `algemeen` - Beantwoord een algemene vraag

**Response:**
```json
{
  "antwoord": "Jullie invulling van VS 1.5 is goed op weg! Sterke punten:\n\n1. **Concrete persoon benoemd**: Mevrouw Bakker is expliciet aangesteld...\n\nVerbeterpunten:\n1. **Vermelding in schoolgids**: ...",
  "eis_id": "VS 1.5",
  "vraag_type": "feedback"
}
```

---

## Laravel Integratie

### Service Class

```php
<?php
// app/Services/OnSpectAIService.php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Http\Client\RequestException;

class OnSpectAIService
{
    private string $baseUrl;
    private string $apiKey;
    private int $timeout;

    public function __construct()
    {
        $this->baseUrl = config('services.onspectai.url');
        $this->apiKey = config('services.onspectai.key');
        $this->timeout = config('services.onspectai.timeout', 120);
    }

    /**
     * Vraag AI-feedback op een schoolinvulling.
     */
    public function chat(
        string $eisId,
        string $vraag,
        array $schoolInvulling,
        string $vraagType = 'feedback'
    ): array {
        $response = Http::baseUrl($this->baseUrl)
            ->timeout($this->timeout)
            ->withHeaders(['X-API-Key' => $this->apiKey])
            ->post('/api/v1/chat', [
                'eis_id' => $eisId,
                'vraag' => $vraag,
                'vraag_type' => $vraagType,
                'school_invulling' => [
                    'ambitie' => $schoolInvulling['ambitie'] ?? '',
                    'beoogd_resultaat' => $schoolInvulling['beoogd_resultaat'] ?? '',
                    'concrete_acties' => $schoolInvulling['concrete_acties'] ?? '',
                    'wijze_van_meten' => $schoolInvulling['wijze_van_meten'] ?? '',
                ],
            ]);

        if ($response->failed()) {
            throw new RequestException($response);
        }

        return $response->json();
    }

    /**
     * Haal alle beschikbare eisen op.
     */
    public function getEisen(): array
    {
        return Http::baseUrl($this->baseUrl)
            ->withHeaders(['X-API-Key' => $this->apiKey])
            ->get('/api/v1/eisen')
            ->json('eisen');
    }

    /**
     * Haal details van een specifieke eis op.
     */
    public function getEis(string $eisId): array
    {
        return Http::baseUrl($this->baseUrl)
            ->withHeaders(['X-API-Key' => $this->apiKey])
            ->get("/api/v1/eisen/{$eisId}")
            ->json();
    }

    /**
     * Check of de API beschikbaar is.
     */
    public function health(): array
    {
        return Http::baseUrl($this->baseUrl)
            ->get('/health')
            ->json();
    }
}
```

### Config

```php
// config/services.php
return [
    // ... andere services

    'onspectai' => [
        'url' => env('ONSPECTAI_URL', 'http://localhost:8000'),
        'key' => env('ONSPECTAI_API_KEY'),
        'timeout' => env('ONSPECTAI_TIMEOUT', 120),
    ],
];
```

### Gebruik in Controller

```php
<?php
// app/Http/Controllers/DeugdelijkheidController.php

namespace App\Http\Controllers;

use App\Services\OnSpectAIService;
use Illuminate\Http\Request;

class DeugdelijkheidController extends Controller
{
    public function __construct(
        private OnSpectAIService $ai
    ) {}

    public function feedback(Request $request, string $eisId)
    {
        $validated = $request->validate([
            'ambitie' => 'nullable|string|max:5000',
            'beoogd_resultaat' => 'nullable|string|max:5000',
            'concrete_acties' => 'nullable|string|max:5000',
            'wijze_van_meten' => 'nullable|string|max:5000',
        ]);

        $result = $this->ai->chat(
            eisId: $eisId,
            vraag: 'Geef feedback op onze invulling',
            schoolInvulling: $validated,
            vraagType: 'feedback'
        );

        return response()->json([
            'feedback' => $result['antwoord'],
        ]);
    }
}
```

---

## Datastructuur

### Deugdelijkheidseisen Database

De eisen zijn opgeslagen in `api/data/deugdelijkheidseisen_db.json`:

```json
{
  "deugdelijkheidseisen": {
    "VS 1.5": {
      "id": "VS 1.5",
      "standaard": "VS1 - Veiligheid",
      "titel": "Anti-pestcoördinator",
      "eisomschrijving": "De school heeft een persoon aangesteld...",
      "uitleg": "Uitgebreide uitleg over de eis...",
      "focuspunten": "Waar de inspectie op let...",
      "tips": "Praktische tips voor scholen...",
      "voorbeelden": "Goede en slechte voorbeelden..."
    }
  }
}
```

### Huidige eisen in de database

| ID | Standaard | Titel |
|----|-----------|-------|
| VS 1.1 | VS1 - Veiligheid | Algemene Veiligheid |
| VS 1.5 | VS1 - Veiligheid | Anti-pestcoördinator |
| OP 0.1 | OP0 - Basisvaardigheden | Doelgericht en samenhangend curriculum voor Nederlandse taal |
| OP 2.1 | OP2 - Zicht op ontwikkeling | Verzamelen van (toets)informatie |
| OP 4.5 | OP4 - Onderwijstijd | Maatwerk in onderwijstijd |

---

## Beveiliging

### API Key Authenticatie

Alle `/api/v1/*` endpoints vereisen een API key via de `X-API-Key` header.

```bash
curl -H "X-API-Key: your-secret-key" http://api.example.com/api/v1/eisen
```

**Belangrijk**:
- De API key authenticatie is bedoeld voor server-to-server communicatie
- Laravel beheert de gebruikersauthenticatie en stuurt requests namens gebruikers
- Eindgebruikers krijgen nooit de API key te zien

### Input Validatie

- Maximum 5000 karakters per invullingsveld (ambitie, beoogd_resultaat, etc.)
- Maximum 2000 karakters voor de vraag
- Prompt injection bescherming in de systeemprompt

### CORS

CORS is geconfigureerd om requests van de Laravel-applicatie toe te staan. Pas `CORS_ORIGINS` aan in de environment variabelen.

---

## Deployment

### Docker (aanbevolen)

De API is ontworpen om te draaien in Docker containers:

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ONSPECTAI_API_KEY=your-secret-key
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    # GPU support (optioneel):
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - capabilities: [gpu]
```

### Starten

```bash
cd docker
docker-compose up -d

# Model downloaden (eenmalig)
docker-compose exec ollama ollama pull gemma3:27b
```

### Environment variabelen

| Variabele | Default | Beschrijving |
|-----------|---------|--------------|
| `ONSPECTAI_API_KEY` | `development-key` | API key voor authenticatie |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `KWALITEITSZORG_MODEL` | `gemma3:27b` | Te gebruiken AI model |
| `CORS_ORIGINS` | `*` | Toegestane origins voor CORS |

---

## Lokaal testen

### Vereisten

- Python 3.10+
- Ollama geïnstalleerd met `gemma3:27b` model

### Installatie

```bash
# Virtuele omgeving
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies
pip install -r api_requirements.txt

# Ollama starten (in aparte terminal)
ollama serve

# Model downloaden (eenmalig)
ollama pull gemma3:27b
```

### API starten

```bash
uvicorn api.main:app --reload --port 8000
```

### Testen

**Health check:**
```bash
curl http://localhost:8000/health
```

**Eisen ophalen:**
```bash
curl -H "X-API-Key: development-key" http://localhost:8000/api/v1/eisen
```

**Chat testen:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "X-API-Key: development-key" \
  -H "Content-Type: application/json" \
  -d '{"eis_id":"VS 1.5","vraag":"Leg deze eis uit","vraag_type":"uitleg","school_invulling":{"ambitie":"Test"}}'
```

### Swagger UI

Open http://localhost:8000/docs voor interactieve API documentatie.

---

## Testdata

In `api/data/voorbeeld_invullingen.json` staan voorbeeldinvullingen voor elke eis:

- **goed**: Volledige, concrete invulling
- **gemiddeld**: Op weg maar mist nog wat
- **zwak**: Zeer ondermaat

Handig voor het testen van de feedback-functionaliteit.

---

## Mapstructuur

```
api/
├── __init__.py
├── main.py                 # FastAPI applicatie
├── config.py               # Configuratie en settings
├── core/                   # Kernfunctionaliteit
│   ├── __init__.py
│   ├── assistant.py        # AI assistent logica
│   ├── database.py         # Database operaties
│   ├── prompts.py          # Systeemprompts voor de AI
│   └── school_invulling.py # Data model
├── data/
│   ├── deugdelijkheidseisen_db.json  # Eisen database
│   └── voorbeeld_invullingen.json    # Testdata
├── middleware/
│   ├── __init__.py
│   └── auth.py             # API key verificatie
├── models/
│   ├── __init__.py
│   ├── requests.py         # Request models
│   └── responses.py        # Response models
├── routes/
│   ├── __init__.py
│   ├── chat.py             # POST /chat endpoint
│   ├── eisen.py            # GET /eisen endpoints
│   └── health.py           # GET /health endpoint
└── services/
    ├── __init__.py
    └── chat_service.py     # Chat service wrapper
```

---