"""
Eyal-AI Interface
=================

Dedicated interface for the AI Living Autobiography + Project Archive system.

This is SEPARATE from Creation Studio - it's specifically for:
1. Quick upload of memories, notes, session reports
2. Project archive management (source of truth)
3. Biography management (life story, patterns, documents)
4. Search and retrieval across all content

Usage Patterns:
    # CLI Quick Upload
    python eyal_ai_interface.py upload "happy childhood memory about grandmother" < memory.txt

    # Project Archive
    python eyal_ai_interface.py archive python3 "my-cool-project" --path ./project/

    # Search
    python eyal_ai_interface.py search "pattern recognition"

    # Session Import
    python eyal_ai_interface.py import-session claude ./session-report.md

Author: Eyal Nof
Date: December 2025
"""

import os
import sys
import json
import hashlib
import argparse
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from enum import Enum

# Import from persona_structure
from persona_structure import (
    EyalAIStructure,
    load_persona_structure,
    MemoryType,
    ProjectType,
    ContentType,
    KBEntry
)


# =============================================================================
# CONSTANTS
# =============================================================================

EYAL_BASE_PATH = "/storage/emulated/0/Download/synthesis-rules/4d_persona_architecture/personas/eyal"
INDEX_FILE = os.path.join(EYAL_BASE_PATH, "eyal_index.json")


class SessionSource(Enum):
    """Sources for AI session reports."""
    CLAUDE = "claude"
    PERPLEXITY = "perplexity"
    GEMINI = "gemini"
    CHATGPT = "chatgpt"
    OTHER = "other"


class UploadFormat(Enum):
    """Supported upload formats."""
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    CODE = "code"


# =============================================================================
# EYAL-AI INTERFACE
# =============================================================================

class EyalAIInterface:
    """
    Dedicated interface for Eyal-AI - the AI Living Autobiography.

    Features:
    - Quick upload with automatic categorization
    - Project archive management
    - Biography/memory management
    - AI session report ingestion
    - Full-text search across all content
    - Cross-reference linking between related content
    """

    def __init__(self, base_path: str = EYAL_BASE_PATH):
        self.base_path = base_path
        self.domain_path = os.path.join(base_path, "domain")
        self.identity_path = os.path.join(base_path, "identity")

        # Load or create index
        self.index = self._load_index()

        # Load EyalAIStructure
        self.structure = self._load_structure()

    def _load_index(self) -> Dict[str, Any]:
        """Load the master index file."""
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, 'r') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "stats": {
                "total_memories": 0,
                "total_projects": 0,
                "total_sessions": 0
            },
            "memories": [],      # List of memory entry IDs
            "projects": {},      # project_type -> [project_ids]
            "sessions": [],      # List of session IDs
            "tags": {},          # tag -> [entry_ids]
            "search_index": {}   # word -> [entry_ids] for full-text search
        }

    def _save_index(self):
        """Save the master index file."""
        self.index["updated"] = datetime.now().isoformat()
        with open(INDEX_FILE, 'w') as f:
            json.dump(self.index, f, indent=2)

    def _load_structure(self) -> EyalAIStructure:
        """Load or create EyalAIStructure."""
        structure = load_persona_structure(self.base_path)
        if not isinstance(structure, EyalAIStructure):
            # Shouldn't happen, but fallback
            structure = EyalAIStructure(
                persona_id="eyal",
                name="Eyal-AI",
                role="AI Living Autobiography",
                description="An AI that speaks as Eyal Nof in first person",
                base_path=self.base_path
            )
        return structure

    # =========================================================================
    # QUICK UPLOAD
    # =========================================================================

    def quick_upload(
        self,
        description: str,
        content: str,
        format: UploadFormat = UploadFormat.TEXT
    ) -> Dict[str, Any]:
        """
        Quick upload with automatic categorization.

        Args:
            description: Description like "happy memory about grandmother"
            content: The actual content to store
            format: Content format (text, markdown, json, etc.)

        Returns:
            Dict with entry_id, detected_type, tags, location
        """
        # Use structure's quick_upload for auto-detection
        entry_id, result = self.structure.quick_upload(description, content)

        # Determine storage location
        detected_type = result["type"]
        tags = result["tags"]

        # Check if this is a project by seeing if type is a valid ProjectType value
        project_type_values = [pt.value for pt in ProjectType]
        is_project = detected_type in project_type_values

        if is_project:
            location = self._store_project(entry_id, detected_type, content, description, tags)
            self.index["stats"]["total_projects"] += 1
            if detected_type not in self.index["projects"]:
                self.index["projects"][detected_type] = []
            self.index["projects"][detected_type].append(entry_id)
        else:
            location = self._store_memory(entry_id, detected_type, content, description, tags)
            self.index["stats"]["total_memories"] += 1
            self.index["memories"].append(entry_id)

        # Update tag index
        for tag in tags:
            if tag not in self.index["tags"]:
                self.index["tags"][tag] = []
            self.index["tags"][tag].append(entry_id)

        # Update search index
        self._update_search_index(entry_id, content, description)

        # Save index
        self._save_index()

        return {
            "entry_id": entry_id,
            "detected_type": detected_type,
            "tags": tags,
            "location": location,
            "is_project": is_project
        }

    def _store_memory(
        self,
        entry_id: str,
        memory_type: str,
        content: str,
        description: str,
        tags: List[str]
    ) -> str:
        """Store a memory in the appropriate identity subfolder."""
        # Map memory type to folder
        type_to_folder = {
            "happy": "happy-memories",
            "sad": "neutral-experiences",  # Could add sad-memories folder
            "trauma": "trauma",
            "neutral": "neutral-experiences",
            "mixed": "neutral-experiences"
        }

        folder = type_to_folder.get(memory_type, "neutral-experiences")
        folder_path = os.path.join(self.identity_path, folder)
        os.makedirs(folder_path, exist_ok=True)

        # Create entry file
        entry_file = os.path.join(folder_path, f"{entry_id}.md")

        entry_content = f"""---
id: {entry_id}
type: memory
memory_type: {memory_type}
created: {datetime.now().isoformat()}
tags: {tags}
description: {description}
---

# Memory: {description[:50]}...

{content}
"""

        with open(entry_file, 'w') as f:
            f.write(entry_content)

        return entry_file

    def _store_project(
        self,
        entry_id: str,
        project_type: str,
        content: str,
        description: str,
        tags: List[str]
    ) -> str:
        """Store a project in the appropriate domain subfolder."""
        folder_path = os.path.join(self.domain_path, project_type)
        os.makedirs(folder_path, exist_ok=True)

        # Create project folder
        project_folder = os.path.join(folder_path, entry_id)
        os.makedirs(project_folder, exist_ok=True)

        # Create README
        readme_content = f"""---
id: {entry_id}
type: project
project_type: {project_type}
created: {datetime.now().isoformat()}
tags: {tags}
description: {description}
status: active
---

# {description[:80]}

## Overview

{content[:500]}...

## Files

_Project files will be stored here_

## Notes

_Add project notes here_
"""

        readme_file = os.path.join(project_folder, "README.md")
        with open(readme_file, 'w') as f:
            f.write(readme_content)

        # Also save full content
        content_file = os.path.join(project_folder, "content.md")
        with open(content_file, 'w') as f:
            f.write(content)

        return project_folder

    def _update_search_index(self, entry_id: str, content: str, description: str):
        """Update full-text search index."""
        # Combine content and description
        text = f"{description} {content}".lower()

        # Extract words (simple tokenization)
        words = re.findall(r'\b\w+\b', text)

        # Only index words 3+ chars
        for word in set(words):
            if len(word) >= 3:
                if word not in self.index["search_index"]:
                    self.index["search_index"][word] = []
                if entry_id not in self.index["search_index"][word]:
                    self.index["search_index"][word].append(entry_id)

    # =========================================================================
    # PROJECT ARCHIVE
    # =========================================================================

    def archive_project(
        self,
        project_type: str,
        name: str,
        description: str,
        source_path: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Archive a project as source of truth.

        Args:
            project_type: Type (python3, web-apps, tools, etc.)
            name: Project name
            description: Project description
            source_path: Optional path to copy files from
            content: Optional direct content
            metadata: Additional metadata

        Returns:
            Dict with project_id, location, status
        """
        # Validate project type
        valid_types = [pt.value for pt in ProjectType]
        if project_type not in valid_types:
            raise ValueError(f"Invalid project type: {project_type}. Valid: {valid_types}")

        # Generate project ID
        project_id = self._generate_id(name)

        # Create project folder
        project_folder = os.path.join(self.domain_path, project_type, project_id)
        os.makedirs(project_folder, exist_ok=True)

        # Create manifest
        manifest = {
            "id": project_id,
            "name": name,
            "type": project_type,
            "description": description,
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "status": "active",
            "source_path": source_path,
            "metadata": metadata or {},
            "files": []
        }

        # Copy files if source_path provided
        if source_path and os.path.exists(source_path):
            manifest["files"] = self._copy_project_files(source_path, project_folder)

        # Save content if provided
        if content:
            content_file = os.path.join(project_folder, "content.md")
            with open(content_file, 'w') as f:
                f.write(content)
            manifest["files"].append("content.md")

        # Save manifest
        manifest_file = os.path.join(project_folder, "manifest.json")
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        # Update index
        if project_type not in self.index["projects"]:
            self.index["projects"][project_type] = []
        self.index["projects"][project_type].append(project_id)
        self.index["stats"]["total_projects"] += 1
        self._save_index()

        return {
            "project_id": project_id,
            "location": project_folder,
            "type": project_type,
            "files_count": len(manifest["files"]),
            "status": "archived"
        }

    def _copy_project_files(self, source_path: str, dest_folder: str) -> List[str]:
        """Copy project files from source to archive."""
        import shutil

        copied_files = []
        source = Path(source_path)

        if source.is_file():
            # Single file
            dest = os.path.join(dest_folder, source.name)
            shutil.copy2(source, dest)
            copied_files.append(source.name)
        elif source.is_dir():
            # Directory - copy recursively but skip common ignores
            ignore_patterns = [
                '__pycache__', '.git', 'node_modules', '.env',
                '*.pyc', '.DS_Store', 'venv', '.venv'
            ]

            for item in source.rglob('*'):
                if item.is_file():
                    # Check if should ignore
                    skip = False
                    for pattern in ignore_patterns:
                        if pattern in str(item):
                            skip = True
                            break

                    if not skip:
                        rel_path = item.relative_to(source)
                        dest = os.path.join(dest_folder, str(rel_path))
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        shutil.copy2(item, dest)
                        copied_files.append(str(rel_path))

        return copied_files

    def list_projects(self, project_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List archived projects, optionally filtered by type."""
        projects = []

        types_to_list = [project_type] if project_type else list(self.index["projects"].keys())

        for ptype in types_to_list:
            if ptype in self.index["projects"]:
                for pid in self.index["projects"][ptype]:
                    manifest_file = os.path.join(self.domain_path, ptype, pid, "manifest.json")
                    if os.path.exists(manifest_file):
                        with open(manifest_file, 'r') as f:
                            manifest = json.load(f)
                            projects.append(manifest)

        return projects

    # =========================================================================
    # SESSION IMPORT
    # =========================================================================

    def import_session(
        self,
        source: SessionSource,
        content: str,
        session_date: Optional[str] = None,
        title: Optional[str] = None,
        extract_insights: bool = True
    ) -> Dict[str, Any]:
        """
        Import an AI session report.

        Args:
            source: Which AI (claude, perplexity, gemini, etc.)
            content: Session transcript/report content
            session_date: Date of session
            title: Optional title for the session
            extract_insights: Whether to auto-extract insights

        Returns:
            Dict with session_id, location, insights_found
        """
        session_id = self._generate_id(f"session_{source.value}")

        # Create session folder
        sessions_folder = os.path.join(self.identity_path, "documents", "sessions")
        os.makedirs(sessions_folder, exist_ok=True)

        # Create session file
        session_file = os.path.join(sessions_folder, f"{session_id}.md")

        # Extract insights if requested
        insights = []
        if extract_insights:
            insights = self._extract_insights(content)

        session_content = f"""---
id: {session_id}
type: session_report
source: {source.value}
date: {session_date or datetime.now().isoformat()}
title: {title or f"Session with {source.value.title()}"}
created: {datetime.now().isoformat()}
insights_count: {len(insights)}
---

# {title or f"Session with {source.value.title()}"}

**Source:** {source.value}
**Date:** {session_date or datetime.now().strftime("%Y-%m-%d")}

## Session Content

{content}

## Extracted Insights

{chr(10).join(f"- {i}" for i in insights) if insights else "_No insights extracted_"}
"""

        with open(session_file, 'w') as f:
            f.write(session_content)

        # Update index
        self.index["sessions"].append(session_id)
        self.index["stats"]["total_sessions"] += 1

        # Add to search index
        self._update_search_index(session_id, content, title or "")

        self._save_index()

        return {
            "session_id": session_id,
            "source": source.value,
            "location": session_file,
            "insights_found": len(insights),
            "insights": insights
        }

    def _extract_insights(self, content: str) -> List[str]:
        """Extract insights from session content (simple keyword-based)."""
        insights = []

        # Look for insight patterns
        patterns = [
            r'(?:insight|realization|learned|discovered|understood):\s*(.+?)(?:\.|$)',
            r'(?:key point|important|conclusion):\s*(.+?)(?:\.|$)',
            r'(?:this means|therefore|so,)\s*(.+?)(?:\.|$)'
        ]

        content_lower = content.lower()
        for pattern in patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            insights.extend(matches)

        # Also extract lines that look like conclusions
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('- ', '* ', '> ')) and len(line) > 20:
                # Check if it looks like an insight
                insight_words = ['means', 'shows', 'proves', 'indicates', 'suggests', 'reveals']
                if any(w in line.lower() for w in insight_words):
                    insights.append(line.lstrip('- *> '))

        # Deduplicate and limit
        unique_insights = list(set(insights))[:10]
        return unique_insights

    # =========================================================================
    # SEARCH
    # =========================================================================

    def search(
        self,
        query: str,
        search_type: str = "all",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search across all content.

        Args:
            query: Search query
            search_type: "all", "memories", "projects", "sessions"
            limit: Maximum results

        Returns:
            List of matching entries with metadata
        """
        results = []
        query_words = query.lower().split()

        # Find matching entry IDs from search index
        matching_ids = set()
        for word in query_words:
            if word in self.index["search_index"]:
                matching_ids.update(self.index["search_index"][word])

        # Filter by type if specified
        if search_type == "memories":
            matching_ids &= set(self.index["memories"])
        elif search_type == "projects":
            all_project_ids = set()
            for pids in self.index["projects"].values():
                all_project_ids.update(pids)
            matching_ids &= all_project_ids
        elif search_type == "sessions":
            matching_ids &= set(self.index["sessions"])

        # Load and return results
        for entry_id in list(matching_ids)[:limit]:
            entry_data = self._load_entry(entry_id)
            if entry_data:
                # Calculate relevance score
                score = sum(1 for w in query_words if w in entry_data.get("content", "").lower())
                entry_data["relevance_score"] = score
                results.append(entry_data)

        # Sort by relevance
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return results

    def _load_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Load an entry by ID."""
        # Search in memories
        for folder in os.listdir(self.identity_path):
            folder_path = os.path.join(self.identity_path, folder)
            if os.path.isdir(folder_path):
                entry_file = os.path.join(folder_path, f"{entry_id}.md")
                if os.path.exists(entry_file):
                    return self._parse_entry_file(entry_file, "memory")

                # Check in subdirectories (like documents/sessions)
                for subfolder in os.listdir(folder_path) if os.path.isdir(folder_path) else []:
                    sub_path = os.path.join(folder_path, subfolder)
                    if os.path.isdir(sub_path):
                        entry_file = os.path.join(sub_path, f"{entry_id}.md")
                        if os.path.exists(entry_file):
                            return self._parse_entry_file(entry_file, "session")

        # Search in projects
        for project_type in os.listdir(self.domain_path):
            type_path = os.path.join(self.domain_path, project_type)
            if os.path.isdir(type_path):
                project_folder = os.path.join(type_path, entry_id)
                manifest_file = os.path.join(project_folder, "manifest.json")
                if os.path.exists(manifest_file):
                    with open(manifest_file, 'r') as f:
                        return json.load(f)

        return None

    def _parse_entry_file(self, file_path: str, entry_type: str) -> Dict[str, Any]:
        """Parse a markdown entry file with YAML frontmatter."""
        with open(file_path, 'r') as f:
            content = f.read()

        # Parse YAML frontmatter
        metadata = {}
        body = content

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                import yaml
                try:
                    metadata = yaml.safe_load(parts[1])
                except:
                    pass
                body = parts[2].strip()

        return {
            "id": metadata.get("id", os.path.basename(file_path).replace(".md", "")),
            "type": entry_type,
            "file_path": file_path,
            "metadata": metadata,
            "content": body[:500]  # Preview
        }

    # =========================================================================
    # UTILITIES
    # =========================================================================

    def _generate_id(self, seed: str) -> str:
        """Generate unique ID."""
        timestamp = datetime.now().isoformat()
        hash_input = f"{seed}_{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return {
            "version": self.index["version"],
            "created": self.index["created"],
            "updated": self.index["updated"],
            "stats": self.index["stats"],
            "project_types": list(self.index["projects"].keys()),
            "tag_count": len(self.index["tags"]),
            "search_index_size": len(self.index["search_index"])
        }

    def get_by_tag(self, tag: str) -> List[str]:
        """Get all entry IDs with a specific tag."""
        return self.index["tags"].get(tag, [])

    def list_tags(self) -> List[Tuple[str, int]]:
        """List all tags with their counts."""
        return [(tag, len(ids)) for tag, ids in self.index["tags"].items()]


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Eyal-AI Interface - AI Living Autobiography & Project Archive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick upload a memory
  python eyal_ai_interface.py upload "happy childhood memory about grandmother" "I remember sitting in her garden..."

  # Archive a project
  python eyal_ai_interface.py archive python3 "my-tool" --description "A cool tool" --path ./project/

  # Import a Claude session
  python eyal_ai_interface.py import-session claude ./session.md --title "Architecture discussion"

  # Search
  python eyal_ai_interface.py search "pattern recognition"

  # Get stats
  python eyal_ai_interface.py stats
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Quick upload content")
    upload_parser.add_argument("description", help="Description for auto-categorization")
    upload_parser.add_argument("content", nargs="?", help="Content (or read from stdin)")

    # Archive command
    archive_parser = subparsers.add_parser("archive", help="Archive a project")
    archive_parser.add_argument("type", help="Project type (python3, web-apps, tools, etc.)")
    archive_parser.add_argument("name", help="Project name")
    archive_parser.add_argument("--description", "-d", help="Project description")
    archive_parser.add_argument("--path", "-p", help="Path to copy files from")

    # Import session command
    import_parser = subparsers.add_parser("import-session", help="Import AI session")
    import_parser.add_argument("source", choices=["claude", "perplexity", "gemini", "chatgpt", "other"])
    import_parser.add_argument("file", help="Session file path")
    import_parser.add_argument("--title", "-t", help="Session title")
    import_parser.add_argument("--date", help="Session date (YYYY-MM-DD)")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search content")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--type", "-t", choices=["all", "memories", "projects", "sessions"], default="all")
    search_parser.add_argument("--limit", "-l", type=int, default=20)

    # List commands
    list_parser = subparsers.add_parser("list", help="List content")
    list_parser.add_argument("what", choices=["projects", "tags", "sessions"])
    list_parser.add_argument("--type", "-t", help="Filter by type")

    # Stats command
    subparsers.add_parser("stats", help="Show statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize interface
    interface = EyalAIInterface()

    # Execute command
    if args.command == "upload":
        content = args.content
        if not content:
            print("Reading content from stdin...")
            content = sys.stdin.read()

        result = interface.quick_upload(args.description, content)

        print("\n" + "=" * 50)
        print("  Quick Upload Complete")
        print("=" * 50)
        print(f"  Entry ID: {result['entry_id']}")
        print(f"  Type: {result['detected_type']}")
        print(f"  Is Project: {result['is_project']}")
        print(f"  Tags: {', '.join(result['tags'])}")
        print(f"  Location: {result['location']}")

    elif args.command == "archive":
        result = interface.archive_project(
            project_type=args.type,
            name=args.name,
            description=args.description or f"Project: {args.name}",
            source_path=args.path
        )

        print("\n" + "=" * 50)
        print("  Project Archived")
        print("=" * 50)
        print(f"  Project ID: {result['project_id']}")
        print(f"  Type: {result['type']}")
        print(f"  Files: {result['files_count']}")
        print(f"  Location: {result['location']}")

    elif args.command == "import-session":
        with open(args.file, 'r') as f:
            content = f.read()

        source = SessionSource(args.source)
        result = interface.import_session(
            source=source,
            content=content,
            session_date=args.date,
            title=args.title
        )

        print("\n" + "=" * 50)
        print("  Session Imported")
        print("=" * 50)
        print(f"  Session ID: {result['session_id']}")
        print(f"  Source: {result['source']}")
        print(f"  Insights Found: {result['insights_found']}")
        print(f"  Location: {result['location']}")
        if result['insights']:
            print("\n  Extracted Insights:")
            for i, insight in enumerate(result['insights'][:5], 1):
                print(f"    {i}. {insight[:80]}...")

    elif args.command == "search":
        results = interface.search(
            query=args.query,
            search_type=args.type,
            limit=args.limit
        )

        print("\n" + "=" * 50)
        print(f"  Search Results: '{args.query}'")
        print("=" * 50)
        print(f"  Found: {len(results)} results")

        for i, result in enumerate(results, 1):
            print(f"\n  [{i}] {result['id']}")
            print(f"      Type: {result['type']}")
            print(f"      Score: {result.get('relevance_score', 0)}")
            preview = result.get('content', '')[:100].replace('\n', ' ')
            print(f"      Preview: {preview}...")

    elif args.command == "list":
        if args.what == "projects":
            projects = interface.list_projects(args.type)
            print("\n" + "=" * 50)
            print(f"  Projects ({len(projects)})")
            print("=" * 50)
            for p in projects:
                print(f"\n  [{p['type']}] {p['name']}")
                print(f"    ID: {p['id']}")
                print(f"    Status: {p['status']}")
                print(f"    Created: {p['created']}")

        elif args.what == "tags":
            tags = interface.list_tags()
            tags.sort(key=lambda x: x[1], reverse=True)
            print("\n" + "=" * 50)
            print(f"  Tags ({len(tags)})")
            print("=" * 50)
            for tag, count in tags[:30]:
                print(f"  {tag}: {count}")

        elif args.what == "sessions":
            stats = interface.get_stats()
            print("\n" + "=" * 50)
            print(f"  Sessions ({stats['stats']['total_sessions']})")
            print("=" * 50)
            # Would need to load sessions to list them
            print("  Use 'search' command to find specific sessions")

    elif args.command == "stats":
        stats = interface.get_stats()
        print("\n" + "=" * 50)
        print("  Eyal-AI Statistics")
        print("=" * 50)
        print(f"  Version: {stats['version']}")
        print(f"  Created: {stats['created']}")
        print(f"  Updated: {stats['updated']}")
        print(f"\n  Content:")
        print(f"    Memories: {stats['stats']['total_memories']}")
        print(f"    Projects: {stats['stats']['total_projects']}")
        print(f"    Sessions: {stats['stats']['total_sessions']}")
        print(f"\n  Project Types: {', '.join(stats['project_types']) or 'None yet'}")
        print(f"  Tags: {stats['tag_count']}")
        print(f"  Search Index Size: {stats['search_index_size']} words")


if __name__ == "__main__":
    main()
