"""
Unified Persona Structure
=========================

All personas in Creation Studio follow this structure:

    persona-name/
    ├── domain/          # WHAT they know (content/data)
    │   └── [topic subfolders organized by subject]
    │
    └── identity/        # WHO they are (config/personality)
        └── [instructions, APIs, voice, personality]

This module provides:
1. PersonaStructure dataclass for representing personas
2. Factory functions for creating/loading personas
3. KB update mechanisms for all personas
4. Special handlers for Eyal-AI archive/biography

Author: Eyal Nof
Date: December 2025
"""

import os
import json
import yaml
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from enum import Enum


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class ContentType(Enum):
    """Types of content that can be uploaded to personas."""
    DOCUMENT = "document"          # General documents
    NOTE = "note"                  # Short notes
    MEMORY = "memory"              # Personal memories (Eyal-AI)
    PROJECT = "project"            # Project archive (Eyal-AI)
    SESSION_REPORT = "session_report"  # AI session transcripts
    API_CONFIG = "api_config"      # API configurations
    INSTRUCTION = "instruction"    # Persona instructions


class MemoryType(Enum):
    """Types of memories for Eyal-AI biography."""
    HAPPY = "happy"
    SAD = "sad"
    NEUTRAL = "neutral"
    TRAUMA = "trauma"
    MIXED = "mixed"


class ProjectType(Enum):
    """Types of projects for Eyal-AI archive."""
    PYTHON3 = "python3"
    WEB_APP = "web-apps"
    WEB_SITE = "web-sites"
    PROJECT = "projects"
    SCRIPT = "scripts"
    GAME = "games"
    TOOL = "tools"
    PLAYBOOK = "playbooks"
    COMPONENT = "components"
    MCP_SERVER = "mcp-servers"
    PLUGIN = "plugins"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class KBEntry:
    """A single entry in the knowledge base."""
    id: str
    content: str
    content_type: ContentType
    source_file: Optional[str] = None
    embeddings: List[str] = field(default_factory=list)  # Tags for categorization
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)
    linked_entries: List[str] = field(default_factory=list)  # Connected memories

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "content_type": self.content_type.value,
            "source_file": self.source_file,
            "embeddings": self.embeddings,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
            "linked_entries": self.linked_entries
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KBEntry":
        data["content_type"] = ContentType(data["content_type"])
        return cls(**data)


@dataclass
class PersonaStructure:
    """
    Unified persona structure with domain/ and identity/ folders.

    All personas have:
    - domain/: Subject matter knowledge (calculus, football, projects)
    - identity/: Who they are (voice, instructions, APIs)
    """
    persona_id: str
    name: str
    role: str
    description: str
    base_path: str

    # Paths
    domain_path: str = ""
    identity_path: str = ""

    # Configuration loaded from YAML
    voice_config: Dict[str, Any] = field(default_factory=dict)
    four_d_config: Dict[str, Any] = field(default_factory=dict)
    knowledge_config: Dict[str, Any] = field(default_factory=dict)

    # Runtime state
    kb_entries: List[KBEntry] = field(default_factory=list)

    def __post_init__(self):
        """Set up paths after initialization."""
        self.domain_path = os.path.join(self.base_path, "domain")
        self.identity_path = os.path.join(self.base_path, "identity")

    def get_domain_topics(self) -> List[str]:
        """Get list of domain topic folders."""
        if not os.path.exists(self.domain_path):
            return []
        return [d for d in os.listdir(self.domain_path)
                if os.path.isdir(os.path.join(self.domain_path, d))]

    def get_identity_components(self) -> List[str]:
        """Get list of identity component folders."""
        if not os.path.exists(self.identity_path):
            return []
        return [d for d in os.listdir(self.identity_path)
                if os.path.isdir(os.path.join(self.identity_path, d))]

    def add_kb_entry(self, entry: KBEntry) -> str:
        """Add a new KB entry and return its ID."""
        # Find related entries for linking
        related = self._find_related_entries(entry)
        entry.linked_entries = [r.id for r in related[:5]]  # Link to top 5 related

        self.kb_entries.append(entry)
        return entry.id

    def _find_related_entries(self, new_entry: KBEntry) -> List[KBEntry]:
        """Find entries related to the new entry based on embeddings."""
        related = []
        for entry in self.kb_entries:
            # Check embedding overlap
            overlap = set(new_entry.embeddings) & set(entry.embeddings)
            if overlap:
                related.append((len(overlap), entry))

        # Sort by overlap count and return entries
        related.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in related]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "base_path": self.base_path,
            "domain_topics": self.get_domain_topics(),
            "identity_components": self.get_identity_components(),
            "kb_entry_count": len(self.kb_entries)
        }


@dataclass
class EyalAIStructure(PersonaStructure):
    """
    Special structure for Eyal-AI with additional features:
    - Archive: Projects organized by type
    - Biography: Memories organized by emotional type
    - Quick upload mechanism
    - Source of truth for projects
    """

    # Archive-specific (domain/ for Eyal = archive of projects)
    archive_index: Dict[str, List[str]] = field(default_factory=dict)  # type -> [project_ids]

    # Biography-specific (identity/ for Eyal = life story)
    memory_index: Dict[str, List[str]] = field(default_factory=dict)  # type -> [memory_ids]

    def get_archive_path(self) -> str:
        """Alias for domain_path - Eyal's domain IS his archive."""
        return self.domain_path

    def get_biography_path(self) -> str:
        """Alias for identity_path - Eyal's identity IS his biography."""
        return self.identity_path

    def add_project(self, project_type: ProjectType, project_data: Dict[str, Any]) -> str:
        """Add a project to the archive."""
        project_id = self._generate_id(project_data.get("name", "project"))

        entry = KBEntry(
            id=project_id,
            content=json.dumps(project_data),
            content_type=ContentType.PROJECT,
            embeddings=[project_type.value, "archive", "project"],
            metadata={
                "project_type": project_type.value,
                "name": project_data.get("name"),
                "status": project_data.get("status", "active")
            }
        )

        self.add_kb_entry(entry)

        # Update archive index
        if project_type.value not in self.archive_index:
            self.archive_index[project_type.value] = []
        self.archive_index[project_type.value].append(project_id)

        return project_id

    def add_memory(self, memory_type: MemoryType, content: str,
                   tags: List[str], metadata: Dict[str, Any] = None) -> str:
        """Add a memory to the biography."""
        memory_id = self._generate_id(content[:20])

        # Build embeddings from tags and memory type
        embeddings = [memory_type.value, "memory", "biography"] + tags

        entry = KBEntry(
            id=memory_id,
            content=content,
            content_type=ContentType.MEMORY,
            embeddings=embeddings,
            metadata={
                "memory_type": memory_type.value,
                **(metadata or {})
            }
        )

        self.add_kb_entry(entry)

        # Update memory index
        if memory_type.value not in self.memory_index:
            self.memory_index[memory_type.value] = []
        self.memory_index[memory_type.value].append(memory_id)

        return memory_id

    def quick_upload(self, description: str, content: str) -> Tuple[str, Dict[str, Any]]:
        """
        Quick upload mechanism for Eyal-AI.

        Usage: "This is about a bad date I had in 2019. Upload to eyal-ai"

        Automatically:
        1. Parses the description for tags
        2. Determines memory type or project type
        3. Creates appropriate KB entry
        4. Links to related memories

        Returns: (entry_id, generated_tags)
        """
        # Parse description for automatic tagging
        tags, memory_type, is_project = self._parse_upload_description(description)

        if is_project:
            project_type = self._detect_project_type(description, tags)
            entry_id = self.add_project(
                project_type,
                {"name": description[:50], "content": content, "auto_tags": tags}
            )
        else:
            entry_id = self.add_memory(memory_type, content, tags, {"description": description})

        return entry_id, {"tags": tags, "type": memory_type.value if not is_project else project_type.value}

    def _parse_upload_description(self, description: str) -> Tuple[List[str], MemoryType, bool]:
        """Parse upload description to extract tags and determine type."""
        import re
        desc_lower = description.lower()
        tags = []
        memory_type = MemoryType.NEUTRAL
        is_project = False

        # Detect if it's a project (use word boundaries to avoid "happy" matching "app")
        project_keywords = ["app", "project", "script", "website", "tool", "game", "code", "built", "developed", "created"]
        for kw in project_keywords:
            # Use word boundary regex to match whole words only
            if re.search(r'\b' + kw + r'\b', desc_lower):
                is_project = True
                break

        # Detect memory type
        happy_words = ["happy", "good", "great", "wonderful", "joy", "love", "fun", "exciting", "amazing"]
        sad_words = ["sad", "bad", "terrible", "awful", "pain", "hurt", "loss", "grief"]
        trauma_words = ["trauma", "abuse", "neglect", "abandon", "betray", "violent", "assault"]

        if any(w in desc_lower for w in trauma_words):
            memory_type = MemoryType.TRAUMA
        elif any(w in desc_lower for w in sad_words):
            memory_type = MemoryType.SAD
        elif any(w in desc_lower for w in happy_words):
            memory_type = MemoryType.HAPPY

        # Extract topic tags
        topic_patterns = {
            "relationships": ["relationship", "date", "dating", "romantic", "partner", "girlfriend", "boyfriend", "wife", "husband", "marriage"],
            "family": ["family", "mother", "father", "parent", "sibling", "brother", "sister", "grandmother", "grandfather"],
            "childhood": ["childhood", "child", "kid", "young", "school", "growing up"],
            "work": ["work", "job", "career", "professional", "business", "office"],
            "friendship": ["friend", "friendship", "buddy", "mate"],
            "health": ["health", "sick", "hospital", "doctor", "medical"],
        }

        for tag, patterns in topic_patterns.items():
            if any(p in desc_lower for p in patterns):
                tags.append(tag)

        # Add memory type as tag
        tags.append(memory_type.value)

        return tags, memory_type, is_project

    def _detect_project_type(self, description: str, tags: List[str]) -> ProjectType:
        """Detect project type from description and tags."""
        # Combine description and tags for detection
        combined = f"{description.lower()} {' '.join(tags).lower()}"

        # Order matters: check more specific patterns first
        if "python" in combined or "py " in combined or ".py" in combined:
            return ProjectType.PYTHON3
        elif ("web" in combined and "app" in combined) or "webapp" in combined:
            return ProjectType.WEB_APP
        elif "website" in combined or "web site" in combined or "static site" in combined:
            return ProjectType.WEB_SITE
        elif "game" in combined:
            return ProjectType.GAME
        elif "script" in combined:
            return ProjectType.SCRIPT
        elif "tool" in combined or "cli" in combined or "utility" in combined:
            return ProjectType.TOOL
        elif "mcp" in combined or "model context protocol" in combined:
            return ProjectType.MCP_SERVER
        elif "plugin" in combined or "extension" in combined:
            return ProjectType.PLUGIN
        elif "playbook" in combined:
            return ProjectType.PLAYBOOK
        elif "component" in combined:
            return ProjectType.COMPONENT
        else:
            return ProjectType.PROJECT

    def _generate_id(self, seed: str) -> str:
        """Generate unique ID for entries."""
        timestamp = datetime.now().isoformat()
        hash_input = f"{seed}_{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def load_persona_structure(persona_path: str, yaml_path: str = None) -> PersonaStructure:
    """
    Load a persona from its folder structure and optional YAML config.

    Args:
        persona_path: Path to persona folder (e.g., .../personas/barry)
        yaml_path: Optional path to YAML config file

    Returns:
        PersonaStructure or EyalAIStructure
    """
    persona_id = os.path.basename(persona_path)

    # Load YAML config if provided
    config = {}
    if yaml_path and os.path.exists(yaml_path):
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)

    # Determine if this is Eyal-AI (special case)
    is_eyal = persona_id.lower() == "eyal"

    # Create appropriate structure
    if is_eyal:
        structure = EyalAIStructure(
            persona_id=persona_id,
            name=config.get("name", persona_id.title()),
            role=config.get("role", ""),
            description=config.get("description", ""),
            base_path=persona_path,
            voice_config=config.get("voice", {}),
            four_d_config=config.get("four_d_state", {}),
            knowledge_config=config.get("knowledge", {})
        )
    else:
        structure = PersonaStructure(
            persona_id=persona_id,
            name=config.get("name", persona_id.title()),
            role=config.get("role", ""),
            description=config.get("description", ""),
            base_path=persona_path,
            voice_config=config.get("voice", {}),
            four_d_config=config.get("four_d_state", {}),
            knowledge_config=config.get("knowledge", {})
        )

    return structure


def create_persona_structure(
    personas_dir: str,
    persona_id: str,
    name: str,
    role: str,
    description: str,
    domain_folders: List[str],
    identity_folders: List[str] = None
) -> PersonaStructure:
    """
    Create a new persona with the unified folder structure.

    Args:
        personas_dir: Base personas directory
        persona_id: Unique ID for the persona
        name: Display name
        role: Role description
        description: Full description
        domain_folders: List of domain topic folders to create
        identity_folders: List of identity folders (defaults to standard set)

    Returns:
        PersonaStructure
    """
    base_path = os.path.join(personas_dir, persona_id)
    domain_path = os.path.join(base_path, "domain")
    identity_path = os.path.join(base_path, "identity")

    # Default identity folders
    if identity_folders is None:
        identity_folders = ["instructions", "voice", "ground-truth"]

    # Create folders
    os.makedirs(domain_path, exist_ok=True)
    os.makedirs(identity_path, exist_ok=True)

    for folder in domain_folders:
        os.makedirs(os.path.join(domain_path, folder), exist_ok=True)

    for folder in identity_folders:
        os.makedirs(os.path.join(identity_path, folder), exist_ok=True)

    # Create structure
    structure = PersonaStructure(
        persona_id=persona_id,
        name=name,
        role=role,
        description=description,
        base_path=base_path
    )

    return structure


# =============================================================================
# KB UPDATE SYSTEM
# =============================================================================

class KBUpdateSystem:
    """
    Unified KB update system for all personas.

    Provides:
    - Add content to any persona's KB
    - Link new content to existing related content
    - Index for fast retrieval
    - Special handling for Eyal-AI quick upload
    """

    def __init__(self, personas_dir: str):
        self.personas_dir = personas_dir
        self.personas: Dict[str, PersonaStructure] = {}
        self._load_all_personas()

    def _load_all_personas(self):
        """Load all persona structures."""
        for item in os.listdir(self.personas_dir):
            persona_path = os.path.join(self.personas_dir, item)
            if os.path.isdir(persona_path) and not item.startswith("__"):
                # Check for YAML config
                yaml_path = os.path.join(self.personas_dir, f"{item}.yaml")
                if not os.path.exists(yaml_path):
                    yaml_path = None

                try:
                    self.personas[item] = load_persona_structure(persona_path, yaml_path)
                except Exception as e:
                    print(f"Warning: Could not load persona {item}: {e}")

    def add_content(
        self,
        persona_id: str,
        content: str,
        content_type: ContentType,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        source_file: str = None
    ) -> str:
        """
        Add content to a persona's KB.

        Args:
            persona_id: Target persona
            content: The content to add
            content_type: Type of content
            tags: Tags for categorization and linking
            metadata: Additional metadata
            source_file: Source file path if applicable

        Returns:
            Entry ID
        """
        if persona_id not in self.personas:
            raise ValueError(f"Unknown persona: {persona_id}")

        persona = self.personas[persona_id]

        entry = KBEntry(
            id=self._generate_id(content[:20]),
            content=content,
            content_type=content_type,
            source_file=source_file,
            embeddings=tags or [],
            metadata=metadata or {}
        )

        return persona.add_kb_entry(entry)

    def quick_upload_to_eyal(self, description: str, content: str) -> Tuple[str, Dict[str, Any]]:
        """
        Quick upload to Eyal-AI with automatic categorization.

        Usage pattern: "This is about X. Upload to eyal-ai"
        """
        if "eyal" not in self.personas:
            raise ValueError("Eyal-AI persona not loaded")

        eyal = self.personas["eyal"]
        if not isinstance(eyal, EyalAIStructure):
            raise ValueError("Eyal persona is not EyalAIStructure")

        return eyal.quick_upload(description, content)

    def get_persona_stats(self, persona_id: str) -> Dict[str, Any]:
        """Get statistics for a persona's KB."""
        if persona_id not in self.personas:
            raise ValueError(f"Unknown persona: {persona_id}")

        persona = self.personas[persona_id]

        stats = {
            "persona_id": persona_id,
            "name": persona.name,
            "domain_topics": persona.get_domain_topics(),
            "identity_components": persona.get_identity_components(),
            "kb_entries": len(persona.kb_entries),
            "content_types": {}
        }

        for entry in persona.kb_entries:
            ct = entry.content_type.value
            stats["content_types"][ct] = stats["content_types"].get(ct, 0) + 1

        if isinstance(persona, EyalAIStructure):
            stats["archive_index"] = persona.archive_index
            stats["memory_index"] = persona.memory_index

        return stats

    def _generate_id(self, seed: str) -> str:
        """Generate unique ID."""
        timestamp = datetime.now().isoformat()
        hash_input = f"{seed}_{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]


# =============================================================================
# CLI FOR TESTING
# =============================================================================

if __name__ == "__main__":
    import sys

    PERSONAS_DIR = "/storage/emulated/0/Download/synthesis-rules/4d_persona_architecture/personas"

    print("=" * 60)
    print("  Persona Structure System - Test")
    print("=" * 60)

    # Initialize KB system
    kb_system = KBUpdateSystem(PERSONAS_DIR)

    print(f"\nLoaded {len(kb_system.personas)} personas:")
    for pid, persona in kb_system.personas.items():
        print(f"\n  {pid}:")
        print(f"    Name: {persona.name}")
        print(f"    Role: {persona.role}")
        print(f"    Domain topics: {persona.get_domain_topics()}")
        print(f"    Identity components: {persona.get_identity_components()}")

        if isinstance(persona, EyalAIStructure):
            print(f"    [SPECIAL] Eyal-AI with archive + biography support")

    # Test quick upload for Eyal-AI
    if "eyal" in kb_system.personas:
        print("\n" + "=" * 60)
        print("  Testing Eyal-AI Quick Upload")
        print("=" * 60)

        test_description = "This is a happy memory about my grandmother from childhood"
        test_content = "I remember sitting with my grandmother in her garden..."

        entry_id, tags = kb_system.quick_upload_to_eyal(test_description, test_content)
        print(f"\n  Description: {test_description}")
        print(f"  Generated tags: {tags}")
        print(f"  Entry ID: {entry_id}")

        # Get stats
        stats = kb_system.get_persona_stats("eyal")
        print(f"\n  Eyal-AI Stats:")
        print(f"    KB entries: {stats['kb_entries']}")
        print(f"    Memory index: {stats.get('memory_index', {})}")
