"""
NBA-AI Knowledge Graph Module

Reuses the Soccer-AI KG infrastructure to prove domain-agnostic architecture.
This module demonstrates that the same NLKE-compliant schema works for any domain.
"""

from .nba_migration import migrate_nba_kg, run_nba_migration

__all__ = ['migrate_nba_kg', 'run_nba_migration']
