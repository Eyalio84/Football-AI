#!/usr/bin/env python3
"""
Test fan persona with KG-KB-RAG integration.
Shows how the RAG context enhances fan responses.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_kb_rag import SoccerAIRAG

# Fan persona templates (simplified from ai_response.py)
FAN_TEMPLATES = {
    "liverpool": {
        "intro": "*adjusts Kop scarf* 🔴",
        "style": "Scouse passion, YNWA spirit",
        "sign_off": "You'll Never Walk Alone!"
    },
    "arsenal": {
        "intro": "*leans back confidently* 🔴⚪",
        "style": "North London superiority, Highbury heritage",
        "sign_off": "Victoria Concordia Crescit!"
    },
    "chelsea": {
        "intro": "*adjusts blue scarf* 💙",
        "style": "West London swagger, Roman era pride",
        "sign_off": "Keep The Blue Flag Flying High!"
    },
    "manchester_united": {
        "intro": "*glances at Stretford End* 🔴",
        "style": "Fergie time belief, Theatre of Dreams nostalgia",
        "sign_off": "Glory Glory Man United!"
    }
}


def generate_fan_response(query: str, club: str = "liverpool"):
    """Generate a fan-style response using RAG context."""

    # Get RAG context
    rag = SoccerAIRAG()
    result = rag.query(query)
    rag.close()

    # Get fan template
    fan = FAN_TEMPLATES.get(club.lower().replace(" ", "_"), FAN_TEMPLATES["liverpool"])

    # Build response
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"FAN PERSONA: {club.title()}")
    print(f"{'='*60}")

    print(f"\n{fan['intro']}")
    print(f"\nRight, let me tell you what I know...\n")

    # Show KG context (structured knowledge)
    if result.kg_context:
        print("📊 From the records:")
        for item in result.kg_context[:5]:  # Top 5
            if item["type"] == "entity":
                print(f"   • {item['name']} - {item.get('description', '')[:60]}...")
            elif item["type"] == "relationship":
                print(f"   • {item['from']} → {item['relationship']} → {item['to']}")

    # Show KB facts (unstructured knowledge)
    if result.kb_facts:
        print("\n📝 What the history books say:")
        for fact in result.kb_facts[:5]:  # Top 5
            conf = f"[{fact['confidence']:.0%}]" if fact.get('confidence') else ""
            print(f"   {conf} {fact['content'][:80]}...")

    print(f"\n{fan['sign_off']}")
    print(f"{'='*60}\n")

    return result


def main():
    print("\n" + "🏟️ "*20)
    print("SOCCER-AI FAN PERSONA + KG-KB-RAG TEST")
    print("🏟️ "*20)

    # Test queries with different fan personas
    tests = [
        ("Tell me about Liverpool's European glory", "liverpool"),
        ("How good were Arsenal's Invincibles?", "arsenal"),
        ("What did Ferguson achieve?", "manchester_united"),
        ("Tell me about Chelsea's trophies", "chelsea"),
    ]

    for query, club in tests:
        generate_fan_response(query, club)


if __name__ == "__main__":
    main()
