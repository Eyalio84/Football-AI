#!/usr/bin/env python3
"""
Implementation Gap Scanner
Scans documentation files to find features that are documented but not implemented.
Part of the "Implementation Gap Tracker" meta-tool.

Usage:
    python scripts/scan_implementation_gaps.py
    python scripts/scan_implementation_gaps.py --update-db
    python scripts/scan_implementation_gaps.py --report
"""

import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Add backend to path for database access
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Patterns to detect in documentation files
GAP_PATTERNS = [
    (r'\[ \]', 'TODO checkbox'),  # Markdown checkbox
    (r'TODO:', 'TODO comment'),
    (r'FIXME:', 'FIXME comment'),
    (r'(?:NOT|not)\s+(?:implemented|built|done|complete)', 'Not implemented'),
    (r'(?:Pending|PENDING)', 'Pending'),
    (r'Status:\s*(?:TODO|Pending|Not Started)', 'Status pending'),
    (r'Phase \d+.*?(?:Pending|TODO)', 'Phase pending'),
    (r'(?:should|need to|must)\s+(?:add|implement|create|build)', 'Should implement'),
]

# Files to scan
DOC_EXTENSIONS = ['.md', '.ctx']

# Directories to scan
SCAN_DIRS = [
    'docs',
    '.',  # Root
]


def find_doc_files(base_path: Path) -> List[Path]:
    """Find all documentation files to scan."""
    files = []
    for scan_dir in SCAN_DIRS:
        dir_path = base_path / scan_dir
        if dir_path.exists():
            for ext in DOC_EXTENSIONS:
                files.extend(dir_path.glob(f'*{ext}'))
    return sorted(set(files))


def scan_file_for_gaps(file_path: Path) -> List[Dict]:
    """Scan a single file for implementation gaps."""
    gaps = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  Error reading {file_path}: {e}")
        return gaps

    for line_num, line in enumerate(lines, 1):
        for pattern, gap_type in GAP_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Extract feature name from context
                feature_name = extract_feature_name(line, lines, line_num - 1)
                if feature_name:
                    gaps.append({
                        'feature_name': feature_name,
                        'source_doc': str(file_path.name),
                        'source_line': line_num,
                        'gap_type': gap_type,
                        'raw_line': line.strip()[:200]
                    })
                break  # Only report once per line

    return gaps


def extract_feature_name(line: str, lines: List[str], line_idx: int) -> str:
    """Extract a meaningful feature name from the line context."""
    # Clean the line
    line = line.strip()

    # Remove markdown formatting
    line = re.sub(r'^[\-\*\[\]x ]+', '', line)
    line = re.sub(r'^#+\s*', '', line)
    line = re.sub(r'TODO:?\s*', '', line, flags=re.IGNORECASE)
    line = re.sub(r'FIXME:?\s*', '', line, flags=re.IGNORECASE)

    # If line is too short, check previous lines for headers
    if len(line) < 10 and line_idx > 0:
        for i in range(line_idx - 1, max(0, line_idx - 5), -1):
            prev_line = lines[i].strip()
            if prev_line.startswith('#'):
                return re.sub(r'^#+\s*', '', prev_line)[:100]

    return line[:100] if line else None


def compare_with_endpoints(base_path: Path) -> List[Dict]:
    """Compare documented endpoints with actual implemented endpoints."""
    gaps = []

    # Read api_design.md for documented endpoints
    api_design = base_path / 'api_design.md'
    main_py = base_path / 'backend' / 'main.py'

    if not api_design.exists() or not main_py.exists():
        return gaps

    # Extract documented endpoints
    documented = set()
    with open(api_design, 'r') as f:
        for line in f:
            match = re.search(r'(GET|POST|PUT|DELETE)\s+(/api/v\d+/\S+)', line)
            if match:
                documented.add((match.group(1), match.group(2).split('?')[0]))

    # Extract implemented endpoints
    implemented = set()
    with open(main_py, 'r') as f:
        content = f.read()
        # Match @app.get("/api/..."), @app.post("/api/...") etc.
        for match in re.finditer(r'@app\.(get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']', content, re.IGNORECASE):
            method = match.group(1).upper()
            path = match.group(2)
            implemented.add((method, path))

    # Find gaps
    for method, path in documented - implemented:
        # Ignore path parameters in comparison
        base_path_clean = re.sub(r'\{[^}]+\}', '{param}', path)
        impl_paths = {re.sub(r'\{[^}]+\}', '{param}', p[1]) for p in implemented}

        if base_path_clean not in impl_paths:
            gaps.append({
                'feature_name': f'{method} {path}',
                'source_doc': 'api_design.md',
                'source_line': None,
                'gap_type': 'Endpoint not implemented',
                'raw_line': f'Documented but not found in main.py'
            })

    return gaps


def determine_priority(gap: Dict) -> str:
    """Determine priority based on gap type and content."""
    feature = gap['feature_name'].lower()
    gap_type = gap['gap_type']

    if 'security' in feature or 'injection' in feature:
        return 'critical'
    elif gap_type == 'Endpoint not implemented':
        return 'medium'
    elif 'test' in feature:
        return 'high'
    elif 'TODO' in gap_type:
        return 'medium'
    else:
        return 'low'


def scan_all(base_path: Path, update_db: bool = False) -> List[Dict]:
    """Scan all documentation files for gaps."""
    all_gaps = []

    print("=" * 60)
    print("IMPLEMENTATION GAP SCANNER")
    print("=" * 60)

    # Scan documentation files
    doc_files = find_doc_files(base_path)
    print(f"\nScanning {len(doc_files)} documentation files...")

    for file_path in doc_files:
        gaps = scan_file_for_gaps(file_path)
        if gaps:
            print(f"  {file_path.name}: {len(gaps)} gaps found")
            all_gaps.extend(gaps)

    # Compare endpoints
    print("\nComparing documented vs implemented endpoints...")
    endpoint_gaps = compare_with_endpoints(base_path)
    print(f"  Found {len(endpoint_gaps)} missing endpoints")
    all_gaps.extend(endpoint_gaps)

    # Add priorities
    for gap in all_gaps:
        gap['priority'] = determine_priority(gap)

    # Update database if requested
    if update_db:
        print("\nUpdating database...")
        try:
            import database
            database.init_gap_tracker()

            for gap in all_gaps:
                database.add_implementation_gap(
                    feature_name=gap['feature_name'],
                    source_doc=gap['source_doc'],
                    source_line=gap.get('source_line'),
                    priority=gap['priority'],
                    notes=f"{gap['gap_type']}: {gap.get('raw_line', '')[:100]}"
                )
            print(f"  Added {len(all_gaps)} gaps to database")
        except Exception as e:
            print(f"  Error updating database: {e}")

    return all_gaps


def print_report(gaps: List[Dict]):
    """Print a formatted gap report."""
    print("\n" + "=" * 60)
    print("GAP REPORT SUMMARY")
    print("=" * 60)

    # Count by priority
    by_priority = {}
    for gap in gaps:
        p = gap.get('priority', 'medium')
        by_priority[p] = by_priority.get(p, 0) + 1

    print(f"\nTotal gaps found: {len(gaps)}")
    print("\nBy priority:")
    for p in ['critical', 'high', 'medium', 'low']:
        if p in by_priority:
            print(f"  {p.upper()}: {by_priority[p]}")

    # Count by source
    by_source = {}
    for gap in gaps:
        s = gap.get('source_doc', 'unknown')
        by_source[s] = by_source.get(s, 0) + 1

    print("\nBy source document:")
    for source, count in sorted(by_source.items(), key=lambda x: -x[1])[:10]:
        print(f"  {source}: {count}")

    # List critical and high priority gaps
    critical_high = [g for g in gaps if g.get('priority') in ['critical', 'high']]
    if critical_high:
        print("\n" + "-" * 60)
        print("CRITICAL AND HIGH PRIORITY GAPS")
        print("-" * 60)
        for gap in critical_high[:20]:
            print(f"\n[{gap['priority'].upper()}] {gap['feature_name']}")
            print(f"  Source: {gap['source_doc']}:{gap.get('source_line', '?')}")
            print(f"  Type: {gap['gap_type']}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Scan for implementation gaps')
    parser.add_argument('--update-db', action='store_true', help='Update database with found gaps')
    parser.add_argument('--report', action='store_true', help='Print detailed report')
    args = parser.parse_args()

    # Find base path (soccer-AI directory)
    script_path = Path(__file__).resolve()
    base_path = script_path.parent.parent

    gaps = scan_all(base_path, update_db=args.update_db)

    if args.report or len(gaps) > 0:
        print_report(gaps)

    print(f"\n{'=' * 60}")
    print("Scan complete.")
    if not args.update_db:
        print("Run with --update-db to save gaps to database")
