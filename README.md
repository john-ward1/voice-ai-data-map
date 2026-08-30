# Voice AI Data Map

**Where does your voice data actually go?**

Voice AI Data Map is a small LiveKit experiment that maps sensitive data across the processing and data supply chain behind a realtime AI voice interaction.

Instead of treating a voice agent as a black box, the project captures a session report after each call and turns it into a local privacy/data-flow report showing:

- what sensitive information appeared in the conversation
- which components processed different types of data
- which speech, language, and voice models were involved
- what observability data the interaction generated
- what the application itself retained
- which processing or storage locations are known — and which are not

This is an educational experiment, not a compliance product.

---

## Why?

A realtime voice agent looks simple from the user's perspective:

```text
You speak → AI responds
```

Underneath, the interaction can involve several different systems:

```text
                         ┌──────────────────┐
                         │       USER       │
                         │    microphone    │
                         └────────┬─────────┘
                                  │
                                  │ raw audio
                                  ▼
                         ┌──────────────────┐
                         │  LIVEKIT CLOUD   │
                         │ realtime / WebRTC│
                         └────────┬─────────┘
                                  │
                                  │ audio
                                  ▼
                         ┌──────────────────┐
                         │       STT        │
                         │   AssemblyAI     │
                         │  audio → text    │
                         └────────┬─────────┘
                                  │
                                  │ transcript
                                  ▼
                         ┌──────────────────┐
                         │       LLM        │
                         │      Gemma       │
                         │ text → response  │
                         └────────┬─────────┘
                                  │
                                  │ response text
                                  ▼
                         ┌──────────────────┐
                         │       TTS        │
                         │    Fish Audio    │
                         │  text → audio    │
                         └────────┬─────────┘
                                  │
                                  ▼
                                 USER
```

At the same time, the interaction can generate transcripts, metrics, traces, logs, participant metadata, and other observability data.

This project makes that data flow visible.

---

## Current Voice Stack

The current demo uses:

| Layer | Technology |
|---|---|
| Realtime voice transport | LiveKit Cloud |
| Agent compute | Local Python process |
| Speech-to-text | AssemblyAI Universal 3.5 Pro |
| Language model | Gemma 4 31B |
| Text-to-speech | Fish Audio S2.1 Pro |
| Turn detection | LiveKit Turn Detector |
| Observability | LiveKit |
| Privacy analysis | Local Python |
| Report storage | Local JSON files |

The model names describe the configured inference chain. They should not automatically be interpreted as proof of the physical processor or processing region.

---

## What Data Does a Voice Agent Generate?

The experiment looks at several categories of data.

### Raw input

```text
microphone audio
```

### Derived data

```text
transcript
conversation context
assistant response
synthesized speech
```

### Metadata

```text
room ID
job ID
participant information
timestamps
model usage
latency
```

### Observability

```text
logs
traces
metrics
transcripts
session events
recording metadata
```

### Application-owned data

The project also creates its own local privacy report after the session ends.

That distinction matters:

```text
Inference processing
        ≠
Observability retention
        ≠
Application retention
```

---

## Sensitive Data Detection

After a session ends, the local analyzer scans the conversation for potentially sensitive information.

The current rule-based detector looks for:

- email addresses
- phone numbers
- SSN-like values
- card-like numbers
- financial amounts
- account identifiers

For example:

```text
SENSITIVE DATA
------------------------------------------------------------------------
EMAIL_ADDRESS               jane@example.com
ACCOUNT_IDENTIFIER          account 49382
FINANCIAL_AMOUNT            $4,200
```

Detection is heuristic.

It can produce both false positives and false negatives and should not be treated as a production PII detection system.

---

## CLI

Voice AI Data Map includes a small CLI for exploring locally captured sessions.

### List sessions

```bash
python src/datamap.py sessions
```

Example:

```text
========================================================================
VOICE AI SESSIONS
========================================================================

ROOM                        PRIVACY     FILE
------------------------------------------------------------------------
console-3377a4bb            3 found     session_20260830_141000.json
console-6560f366            none        session_20260830_141500.json
```

### Inspect a session

```bash
python src/datamap.py show console-3377a4bb
```

Example:

```text
========================================================================
VOICE AI DATA MAP — console-3377a4bb
========================================================================

SESSION
------------------------------------------------------------------------
Room:          console-3377a4bb
Agent compute: local machine

VOICE SUPPLY CHAIN
------------------------------------------------------------------------

LiveKit Cloud
  Purpose:  realtime voice transport
  Receives: raw audio, participant metadata
  Region:   unknown / dynamic

Speech-to-text
  Model:    assemblyai/universal-3-5-pro
  Purpose:  audio transcription
  Receives: raw user audio, derived transcript
  Region:   unknown

LLM
  Model:    google/gemma-4-31b-it
  Purpose:  reasoning and response generation
  Receives: transcript, conversation context
  Region:   unknown

Text-to-speech
  Model:    fishaudio/s2.1-pro
  Purpose:  speech synthesis
  Receives: assistant response text
  Region:   unknown

SENSITIVE DATA
------------------------------------------------------------------------
EMAIL_ADDRESS               jane@example.com
ACCOUNT_IDENTIFIER          account 49382
FINANCIAL_AMOUNT            $4,200

DATA EXPOSURE
------------------------------------------------------------------------
Raw audio
  → LiveKit realtime transport
  → Speech-to-text

Transcript
  → LiveKit session
  → Language model
  → Observability

Assistant response text
  → LiveKit session
  → Text-to-speech
  → Observability

Telemetry
  → LiveKit observability

Application privacy report
  → Local filesystem

LOCATION / RESIDENCY
------------------------------------------------------------------------
Agent compute:       local machine
LiveKit region:      unknown / dynamic
Model processing:    unknown
```

Unknown locations are intentionally left unknown rather than inferred.

---

## How It Works

The project hooks into the end of each LiveKit agent session:

```text
LiveKit voice session
        │
        ▼
  on_session_end
        │
        ▼
   SessionReport
        │
        ▼
 Privacy analyzer
        │
        ├── sensitive-data detection
        ├── supply-chain mapping
        ├── data-exposure mapping
        └── location / residency metadata
        │
        ▼
 reports/session_*.json
        │
        ▼
   datamap.py CLI
```

The session report is generated by the running agent and analyzed locally.

LiveKit provides the realtime voice infrastructure and agent framework. The privacy analysis, local report generation, and data-map CLI are implemented by this repository.

---

## Project Structure

```text
voice-ai-data-map/
├── src/
│   ├── agent.py
│   ├── privacy.py
│   └── datamap.py
│
├── reports/
│   └── session_*.json
│
├── tests/
├── .env.example
├── .gitignore
├── Dockerfile
├── pyproject.toml
├── README.md
└── uv.lock
```

`reports/` is intentionally excluded from Git because real reports may contain conversation transcripts and sensitive information.

---

## Running Locally

### Requirements

- Python
- `uv`
- a LiveKit Cloud project
- LiveKit CLI (optional, but convenient for authentication and development)

### 1. Clone the repository

```bash
git clone https://github.com/john-ward1/voice-ai-data-map.git
cd voice-ai-data-map
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure LiveKit

Create a local environment file from the example:

```bash
cp .env.example .env.local
```

Add your LiveKit project credentials to `.env.local`.

Do not commit `.env.local`.

### 4. Start this project's voice agent

The agent can be started directly from the repository:

```bash
uv run python src/agent.py dev
```

Alternatively, install the LiveKit CLI:

```bash
brew install livekit-cli
```

Authenticate with LiveKit Cloud:

```bash
lk cloud auth
```

Then run the agent defined by this repository:

```bash
lk agent dev
```

The LiveKit CLI does **not** provide the privacy-reporting functionality by itself. It is development tooling used to authenticate with LiveKit Cloud and run the agent defined in this repository.

The project-specific behavior lives in:

```text
src/agent.py
    ↓
captures the completed session

src/privacy.py
    ↓
detects potentially sensitive data
and builds the privacy/data-flow report

src/datamap.py
    ↓
provides the CLI for exploring reports
```

### 5. Have a voice conversation

Connect to the running agent using the LiveKit Agent Console and have a voice conversation.

When the session ends, the custom `on_session_end` logic in `src/agent.py` obtains the session report and passes it through the local privacy analyzer.

The resulting report is written to:

```text
reports/
```

Reports may contain real conversation data and are intentionally excluded from Git.

### 6. Explore the captured session

List locally captured sessions:

```bash
python src/datamap.py sessions
```

Inspect a specific session:

```bash
python src/datamap.py show <room-name>
```

For example:

```bash
python src/datamap.py show console-3377a4bb
```

Only sessions captured while this project's agent is running are indexed by the CLI.

Historical sessions visible in the LiveKit Cloud dashboard are not automatically downloaded or imported by Voice AI Data Map.

---

## Privacy Model

For every stage of the pipeline, the project asks:

```text
WHAT DATA?
    ↓
WHO SEES IT?
    ↓
WHERE IS IT PROCESSED?
    ↓
WHAT IS RETAINED?
    ↓
WHY IS IT NEEDED?
```

It also deliberately distinguishes three concepts that are easy to conflate.

### Processing

Who needs access to the data in order to perform the requested operation?

### Retention

Who keeps a copy after processing has finished?

### Training

Can the data be reused for model development or improvement?

These are separate questions.

---

## Known vs. Unknown

A goal of this project is to avoid presenting assumptions as privacy facts.

For example, a session may establish:

```text
Agent compute: local machine
STT model: assemblyai/universal-3-5-pro
LLM model: google/gemma-4-31b-it
TTS model: fishaudio/s2.1-pro
```

That does **not** necessarily establish the physical location where every inference request was processed.

When the available telemetry does not establish a location, the report says:

```text
unknown
```

rather than guessing.

---

## Local Data

Real session reports may contain:

- full conversation text
- email addresses
- account identifiers
- financial information
- participant/session identifiers
- model metadata

For that reason, the `reports/` directory and `.env.local` are excluded from version control.

Before committing changes, verify:

```bash
git status
```

Real session data and credentials should never appear in the staged files.

---

## Limitations

- Only sessions captured by the local agent are indexed by the CLI.
- Historical sessions visible in LiveKit Cloud are not automatically imported.
- Sensitive-data detection is currently rule-based.
- Detection may miss sensitive information or incorrectly flag benign values.
- Processing and storage regions are not inferred when they cannot be established.
- The current CLI stores local reports as JSON rather than using a database.
- This is an educational experiment, not a compliance or security product.

---

## Possible Next Steps

Future experiments could include:

- stronger local PII/entity detection
- masking sensitive values in CLI output
- comparing multiple STT providers
- identifying sensitive information in realtime
- visualizing data flows in a web interface
- OpenTelemetry analysis
- provider/retention policy metadata
- configurable privacy policies
- session-to-session privacy comparisons
- optional LiveKit Cloud analytics integration

---

## Built With

- Python
- LiveKit Agents
- LiveKit Cloud
- AssemblyAI
- Gemma
- Fish Audio

---

## Disclaimer

Voice AI Data Map is a learning and experimentation project.

The output should not be interpreted as a legal determination, compliance assessment, data-processing agreement review, or guarantee that all sensitive information has been detected.
