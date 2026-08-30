import argparse
import json
from pathlib import Path

REPORT_DIR = Path("reports")


def load_reports():
    reports = []

    if not REPORT_DIR.exists():
        return reports

    for path in sorted(REPORT_DIR.glob("session_*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                report = json.load(f)

            reports.append(
                {
                    "path": path,
                    "report": report,
                }
            )

        except Exception as exc:
            print(f"Warning: could not read {path}: {exc}")

    return reports


def display_sessions():
    reports = load_reports()

    print()
    print("=" * 72)
    print("VOICE AI SESSIONS")
    print("=" * 72)

    if not reports:
        print()
        print("No local session reports found.")
        print("Run the voice agent and complete a call first.")
        print()
        return

    print()
    print(f"{'ROOM':<28}{'PRIVACY':<12}{'FILE'}")
    print("-" * 72)

    for item in reports:
        report = item["report"]
        path = item["path"]

        room = report.get("session", {}).get("room", "unknown")

        findings = report.get("privacy", {}).get("findings", [])

        privacy_status = f"{len(findings)} found" if findings else "none"

        print(f"{room:<28}{privacy_status:<12}{path.name}")

    print()


def find_report_by_room(room_name):
    reports = load_reports()

    matches = []

    for item in reports:
        room = item["report"].get("session", {}).get("room")

        if room == room_name:
            matches.append(item)

    if not matches:
        return None

    # If there are multiple reports for the same room name,
    # use the newest file.
    return matches[-1]


def display_data_map(room_name):
    item = find_report_by_room(room_name)

    if item is None:
        print()
        print(f"No local report found for room: {room_name}")
        print()
        print("Available rooms:")
        print()

        reports = load_reports()

        for report_item in reports:
            room = report_item["report"].get("session", {}).get("room", "unknown")

            print(f"  {room}")

        print()
        return

    report = item["report"]

    session = report.get("session", {})
    privacy = report.get("privacy", {})
    supply_chain = report.get("supply_chain", [])
    location = report.get("location", {})

    print()
    print("=" * 72)
    print(f"VOICE AI DATA MAP — {room_name}")
    print("=" * 72)

    print()
    print("SESSION")
    print("-" * 72)
    print(f"Room:          {session.get('room', 'unknown')}")
    print(f"Room ID:       {session.get('room_id', 'unknown')}")
    print(f"Job ID:        {session.get('job_id', 'unknown')}")
    print(f"Agent compute: {location.get('agent_compute', 'unknown')}")

    print()
    print("VOICE SUPPLY CHAIN")
    print("-" * 72)

    for component in supply_chain:
        name = component.get("component", "Unknown component")
        model = component.get("provider_model")
        purpose = component.get("purpose", "unknown")
        data = component.get("data", [])
        region = component.get(
            "processing_region",
            "unknown",
        )

        print()
        print(name)

        if model:
            print(f"  Model:    {model}")

        print(f"  Purpose:  {purpose}")
        print(f"  Receives: {', '.join(data)}")
        print(f"  Region:   {region}")

    print()
    print("SENSITIVE DATA")
    print("-" * 72)

    findings = privacy.get("findings", [])

    if not findings:
        print("No obvious sensitive values detected.")
    else:
        for finding in findings:
            category = finding.get("category", "UNKNOWN")
            value = finding.get("value", "")

            print(f"{category:<28}{value}")

    findings = privacy.get("findings", [])

    if not findings:
        print("No obvious sensitive values detected.")

    else:
        counts = {}

        for finding in findings:
            category = finding.get(
                "category",
                "UNKNOWN",
            )

            counts[category] = counts.get(category, 0) + 1

        for category, count in sorted(counts.items()):
            print(f"{category:<28}{count} detected")

    print()
    print("DATA EXPOSURE")
    print("-" * 72)

    print("Raw audio")
    print("  → LiveKit realtime transport")
    print("  → Speech-to-text")

    print()
    print("Transcript")
    print("  → LiveKit session")
    print("  → Language model")
    print("  → Observability")

    print()
    print("Assistant response text")
    print("  → LiveKit session")
    print("  → Text-to-speech")
    print("  → Observability")

    print()
    print("Telemetry")
    print("  → LiveKit observability")

    print()
    print("Application privacy report")
    print("  → Local filesystem")

    print()
    print("LOCATION / RESIDENCY")
    print("-" * 72)

    print(f"Agent compute:      {location.get('agent_compute', 'unknown')}")

    print(f"LiveKit region:     {location.get('livekit_region', 'unknown')}")

    print(f"Model processing:   {location.get('model_processing_region', 'unknown')}")

    print()
    print("Unknown locations are intentionally left unknown instead of being inferred.")

    print()
    print(f"Source report: {item['path']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Explore local Voice AI Data Map reports."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "sessions",
        help="List locally recorded voice sessions.",
    )

    show_parser = subparsers.add_parser(
        "show",
        help="Display the data map for one room.",
    )

    show_parser.add_argument(
        "room",
        help="LiveKit room name, e.g. console-3377a4bb",
    )

    args = parser.parse_args()

    if args.command == "sessions":
        display_sessions()

    elif args.command == "show":
        display_data_map(args.room)


if __name__ == "__main__":
    main()
