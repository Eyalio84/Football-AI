#!/bin/bash
# Soccer-AI Full Test Suite
# Run all test suites to verify system integrity

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              SOCCER-AI FULL TEST SUITE                    ║"
echo "║           62 Tests Across 7 Test Files                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

PASSED=0
FAILED=0

run_test() {
    local name=$1
    local file=$2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Running: $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if python3 "$file" > /dev/null 2>&1; then
        echo "✓ $name: PASSED"
        ((PASSED++))
    else
        echo "✗ $name: FAILED"
        ((FAILED++))
        # Show output on failure
        python3 "$file"
    fi
    echo ""
}

# Run all test suites
run_test "KG Core Tests (9)" "test_kg.py"
run_test "Hybrid RAG Tests (7)" "test_hybrid_rag.py"
run_test "KG-RAG Demo Tests (6)" "test_kg_rag_demo.py"
run_test "Data Expansion Tests (8)" "test_data_expansion.py"
run_test "API Endpoint Tests (18)" "test_api.py"
run_test "Analytics Tests (7)" "test_analytics.py"
run_test "KG Visualization Tests (7)" "test_kg_visualization.py"

# Summary
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    TEST SUMMARY                           ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║  Test Suites Passed: $PASSED/7                                   ║"
echo "║  Test Suites Failed: $FAILED/7                                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "★ ALL TESTS PASSED - SYSTEM READY FOR DEMO ★"
    echo ""
    echo "Test Coverage:"
    echo "  • CP1 Foundation: FastAPI + SQLite + FTS5"
    echo "  • CP2 Security: Injection detection + snap-back"
    echo "  • CP3 KG-RAG: Hybrid retrieval + multi-hop"
    echo "  • CP4 Data: Top 6 clubs with legends/moments"
    echo "  • CP5 API: 18 HTTP endpoint tests"
    echo "  • CP6 Analytics: Query logging + hot queries"
    echo "  • CP7 Visualization: KG export + vis.js viewer"
    echo ""
    echo "Demo endpoints:"
    echo "  • http://localhost:8000/docs        - API documentation"
    echo "  • http://localhost:8000/kg-viewer   - Knowledge Graph viewer"
    echo "  • http://localhost:8000/health      - Health check"
    echo ""
    exit 0
else
    echo ""
    echo "⚠ SOME TESTS FAILED - Review output above"
    exit 1
fi
