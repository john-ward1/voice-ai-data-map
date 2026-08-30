import re
from typing import Any

PRIVACY_PATTERNS = {
    "EMAIL_ADDRESS": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "PHONE_NUMBER": re.compile(
        r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)"
        r"\d{3}[-.\s]?\d{4}\b"
    ),
    "SSN_LIKE": re.compile(
        r"\b\d{3}-\d{2}-\d{4}\b"
    ),
    "CARD_LIKE_NUMBER": re.compile(
        r"\b(?:\d[ -]*?){13,19}\b"
    ),
    "FINANCIAL_AMOUNT": re.compile(
        r"(?:\$|USD\s*)\d+(?:,\d{3})*(?:\.\d{2})?"
    ),
    "ACCOUNT_IDENTIFIER": re.compile(
        r"\b(?:account|acct|account number|customer id|customer number)"
        r"[\s:#-]*([A-Za-z0-9-]{4,})\b",
        re.IGNORECASE,
    ),
}


def find_sensitive_data(text: str) -> list[dict[str, Any]]:
    findings = []

    for category, pattern in PRIVACY_PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append(
                {
                    "category": category,
                    "value": match.group(0),
                }
            )

    return findings


def extract_conversation(session_report: dict) -> list[dict]:
    conversation = []

    chat_history = session_report.get("chat_history", {})
    items = chat_history.get("items", [])

    for item in items:
        if item.get("type") != "message":
            continue

        role = item.get("role")
        content = item.get("content", [])

        text_parts = [
            value for value in content
            if isinstance(value, str)
        ]

        text = " ".join(text_parts).strip()

        if not text:
            continue

        conversation.append(
            {
                "role": role,
                "text": text,
                "privacy_findings": find_sensitive_data(text),
                "metrics": item.get("metrics", {}),
            }
        )

    return conversation


def build_privacy_report(
    session_report: dict,
    *,
    stt_model: str,
    llm_model: str,
    tts_model: str,
    agent_location: str,
    livekit_region: str,
    model_processing_region: str,
) -> dict:

    conversation = extract_conversation(session_report)

    all_findings = []

    for index, message in enumerate(conversation):
        for finding in message["privacy_findings"]:
            all_findings.append(
                {
                    "message_index": index,
                    "role": message["role"],
                    **finding,
                }
            )

    categories = sorted(
    {finding["category"] for finding in all_findings}
)

    return {
        "session": {
            "room": session_report.get("room"),
            "room_id": session_report.get("room_id"),
            "job_id": session_report.get("job_id"),
            "sdk_version": session_report.get("sdk_version"),
        },

        "conversation": conversation,

        "privacy": {
            "sensitive_data_detected": bool(all_findings),
            "categories": categories,
            "findings": all_findings,
        },

        "supply_chain": [
            {
                "component": "LiveKit Cloud",
                "purpose": "realtime voice transport",
                "data": [
                    "raw audio",
                    "participant metadata",
                ],
                "processing_region": livekit_region,
                "risk": "voice data crosses realtime infrastructure",
            },
            {
                "component": "Speech-to-text",
                "provider_model": stt_model,
                "purpose": "audio transcription",
                "data": [
                    "raw user audio",
                    "derived transcript",
                ],
                "processing_region": model_processing_region,
                "risk": "raw voice may contain sensitive information",
            },
            {
                "component": "LLM",
                "provider_model": llm_model,
                "purpose": "reasoning and response generation",
                "data": [
                    "transcript",
                    "conversation context",
                ],
                "processing_region": model_processing_region,
                "risk": "sensitive transcript content reaches model inference",
            },
            {
                "component": "Text-to-speech",
                "provider_model": tts_model,
                "purpose": "speech synthesis",
                "data": [
                    "assistant response text",
                ],
                "processing_region": model_processing_region,
                "risk": "generated response is processed by voice provider",
            },
            {
                "component": "LiveKit Observability",
                "purpose": "debugging and monitoring",
                "data": [
                    "transcript",
                    "events",
                    "metrics",
                    "traces",
                    "recording when enabled",
                ],
                "processing_region": livekit_region,
                "risk": "observability itself creates retained data",
            },
            {
                "component": "Local privacy report",
                "purpose": "privacy supply-chain analysis",
                "data": [
                    "full transcript",
                    "privacy findings",
                    "model metadata",
                ],
                "processing_region": agent_location,
                "risk": "application-controlled copy of conversation",
            },
        ],

        "location": {
            "agent_compute": agent_location,
            "livekit_region": livekit_region,
            "model_processing_region": model_processing_region,
            "note": (
                "Unknown regions are intentionally left unknown. "
                "Session telemetry alone does not prove physical "
                "processing or storage location."
            ),
        },
    }


def print_privacy_report(report: dict) -> None:
    print()
    print("=" * 64)
    print("VOICE AI DATA MAP")
    print("=" * 64)

    print()
    print("SESSION")
    print("-" * 64)
    print(f"Room:          {report['session'].get('room')}")
    print(f"Agent compute: {report['location']['agent_compute']}")
    print(f"LiveKit region:{' ' if report['location']['livekit_region'] else ''}"
          f"{report['location']['livekit_region']}")

    print()
    print("SUPPLY CHAIN")
    print("-" * 64)

    for component in report["supply_chain"]:
        print()
        print(component["component"])

        if component.get("provider_model"):
            print(f"  Model:    {component['provider_model']}")

        print(f"  Receives: {', '.join(component['data'])}")
        print(f"  Region:   {component['processing_region']}")
        print(f"  Risk:     {component['risk']}")

    print()
    print("SENSITIVE DATA FOUND")
    print("-" * 64)

    findings = report["privacy"]["findings"]

    if not findings:
        print("No obvious sensitive values detected.")
    else:
        for finding in findings:
            print(
                f"{finding['category']:<22} "
                f"{finding['value']}"
            )

    print()
    print("=" * 64)
