#!/usr/bin/env python3
"""
Soccer-AI Fact Ingestion CLI

Quick commands for adding facts to your KB.

Usage:
    # Add a single fact
    python ingest.py fact "Liverpool won the 2024-25 Premier League"

    # Add facts from a text file
    python ingest.py file facts.txt

    # Ingest a PDF
    python ingest.py pdf /path/to/document.pdf

    # Ingest all PDFs from folder
    python ingest.py folder /path/to/folder

    # Search facts
    python ingest.py search "Ferguson"

    # Show stats
    python ingest.py stats

    # Query using RAG
    python ingest.py query "Who won more titles, United or City?"
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fact_ingestion_pipeline import FactPipeline
from kg_kb_rag import SoccerAIRAG


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    if command == "fact":
        if not args:
            print("Usage: python ingest.py fact \"Your fact here\"")
            return

        fact = " ".join(args)
        pipeline = FactPipeline()
        success, msg = pipeline.add_fact(fact)
        print(msg)
        pipeline.close()

    elif command == "file":
        if not args:
            print("Usage: python ingest.py file facts.txt")
            return

        filepath = args[0]
        with open(filepath, 'r') as f:
            content = f.read()

        pipeline = FactPipeline()
        result = pipeline.ingest_web_facts(content, source_url=filepath)
        print(f"Added: {result.facts_added}, Skipped: {result.facts_skipped}, Links: {result.entities_linked}")
        pipeline.close()

    elif command == "pdf":
        if not args:
            print("Usage: python ingest.py pdf /path/to/document.pdf")
            return

        pdf_path = args[0]
        pipeline = FactPipeline()
        result = pipeline.ingest_pdf(pdf_path)
        print(f"Facts: {result.facts_added}, Skipped: {result.facts_skipped}, Links: {result.entities_linked}")
        if result.errors:
            print(f"Errors: {result.errors}")
        pipeline.close()

    elif command == "folder":
        if not args:
            print("Usage: python ingest.py folder /path/to/folder")
            return

        folder_path = args[0]
        pipeline = FactPipeline()
        results = pipeline.ingest_all_pdfs(folder_path)

        total = 0
        for filename, result in results.items():
            print(f"{filename}: {result.facts_added} facts")
            total += result.facts_added
        print(f"\nTotal: {total} facts added")
        pipeline.close()

    elif command == "search":
        if not args:
            print("Usage: python ingest.py search \"query\"")
            return

        query = " ".join(args)
        pipeline = FactPipeline()
        facts = pipeline.search_facts(query)

        if not facts:
            print("No facts found")
        else:
            for fact in facts:
                print(f"[{fact['type']}] {fact['content']}")
        pipeline.close()

    elif command == "stats":
        pipeline = FactPipeline()
        stats = pipeline.get_stats()

        print("=== Soccer-AI KB Stats ===")
        print(f"  Facts:        {stats['facts']}")
        print(f"  Documents:    {stats['documents']}")
        print(f"  Entity Links: {stats['entity_links']}")
        print(f"  KG Nodes:     {stats['kg_nodes']}")
        print(f"  KG Edges:     {stats['kg_edges']}")
        pipeline.close()

    elif command == "query":
        if not args:
            print("Usage: python ingest.py query \"Your question\"")
            return

        question = " ".join(args)
        rag = SoccerAIRAG()
        result = rag.query(question)

        print(result.combined_context)
        rag.close()

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
