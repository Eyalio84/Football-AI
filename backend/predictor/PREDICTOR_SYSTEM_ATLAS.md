# Predictor System Atlas
## "The Analyst" - Upset Prediction Engine

---

## Core Philosophy

> "The question isn't who SHOULD win.
> The question is: what would make the SHOULD not happen?"

---

## System Architecture

```mermaid
graph TB
    subgraph "API Layer"
        API[PredictorAPI]
        QUICK[quick_predict]
    end

    subgraph "Intelligence Layer"
        ENGINE[PredictionEngine]
        ANALYST[TheAnalyst Persona]
    end

    subgraph "Calculation Layer"
        SIDEA[SideACalculator]
        SIDEB[SideBCalculator]
        THIRD[Third Knowledge]
    end

    subgraph "Data Layer"
        INGEST[DataIngestion]
        DB[(predictor_facts.db)]
    end

    subgraph "External APIs"
        FOOTBALL[football-data.org]
        ESPN[ESPN Stats]
        ODDS[Odds Providers]
    end

    API --> ENGINE
    QUICK --> API
    ENGINE --> ANALYST

    ENGINE --> SIDEA
    ENGINE --> SIDEB
    SIDEA --> THIRD
    SIDEB --> THIRD

    ENGINE --> DB
    INGEST --> DB
    INGEST --> FOOTBALL
    INGEST --> ESPN

    style ENGINE fill:#f39c12
    style ANALYST fill:#9b59b6
    style THIRD fill:#e74c3c
```

---

## Prediction Flow

```mermaid
sequenceDiagram
    participant U as User/API
    participant E as PredictionEngine
    participant A as Side A (Weakness)
    participant B as Side B (Strength)
    participant T as Third Knowledge
    participant P as TheAnalyst

    U->>E: analyze_match(home, away, favorite, underdog)

    par Parallel Analysis
        E->>A: calculate_weakness(favorite)
        A->>A: fatigue_factor()
        A->>A: injury_impact()
        A->>A: form_momentum()
        A->>A: pressure_factor()
        A-->>E: side_a_score (0-1)

        E->>B: calculate_strength(underdog)
        B->>B: rest_advantage()
        B->>B: home_fortress()
        B->>B: style_mismatch()
        B->>B: motivation_boost()
        B-->>E: side_b_score (0-1)
    end

    E->>T: discover_patterns(A, B)
    T->>T: check_fatigue_x_rest()
    T->>T: check_pressure_x_freedom()
    T->>T: check_weather_x_style()
    T-->>E: interaction_boost

    E->>E: combine_scores()
    Note over E: naive = (A + B) / 2<br/>adjusted = naive * (1 + boost)

    E->>P: format_response(prediction)
    P-->>U: Analyst Commentary + Probabilities
```

---

## Side A: Favorite Weakness Analysis

```mermaid
mindmap
    root((Side A))
        Fatigue Factors
            rest_days < 3
            recent_games > 3
            european_hangover
            squad_rotation_needed
        Injury Impact
            key_player_out
            defensive_instability
            attacking_disruption
        Form & Momentum
            losing_streak
            draws_accumulating
            away_form_poor
        Pressure Factors
            title_race_pressure
            must_win_scenario
            media_scrutiny
            manager_under_fire
        Style Vulnerabilities
            counter_attack_weakness
            set_piece_conceded
            high_line_exposed
```

---

## Side B: Underdog Strength Analysis

```mermaid
mindmap
    root((Side B))
        Rest Advantage
            7+ days rest
            no_midweek_games
            full_squad_available
        Home Fortress
            unbeaten_streak
            hostile_atmosphere
            pitch_familiarity
        Style Mismatch
            counter_attack_effective
            set_piece_prowess
            goalkeeper_form
        Motivation Boost
            relegation_battle
            derby_intensity
            new_manager_bounce
            nothing_to_lose
        Tactical Edge
            specific_gameplan
            element_of_surprise
            underestimation_factor
```

---

## Third Knowledge Patterns

```mermaid
graph LR
    subgraph "Input Factors"
        FA[Side A Factors]
        FB[Side B Factors]
    end

    subgraph "Discovered Patterns"
        P1[fatigue_x_rest]
        P2[pressure_x_freedom]
        P3[weather_x_style]
        P4[european_x_domestic]
        P5[manager_x_motivation]
    end

    subgraph "Multipliers"
        M1[1.3x - 1.8x]
    end

    FA --> P1
    FB --> P1
    FA --> P2
    FB --> P2
    FA --> P3
    FB --> P3

    P1 --> M1
    P2 --> M1
    P3 --> M1

    style P1 fill:#e74c3c
    style P2 fill:#e74c3c
    style P3 fill:#e74c3c
```

---

## Third Knowledge Detail

```mermaid
erDiagram
    PATTERN {
        string pattern_name PK
        string description
        string factor_a_code
        string factor_b_code
        string interaction_type
        float multiplier
        float confidence
    }

    PREDICTION {
        int match_id PK
        string match_date
        string home_team
        string away_team
        float side_a_score
        float side_b_score
        float naive_upset_prob
        float interaction_boost
        float final_upset_prob
        string confidence_level
    }

    VALIDATED_PATTERN {
        int id PK
        string pattern_name FK
        int times_triggered
        float success_rate
        datetime last_validated
    }

    PATTERN ||--o{ VALIDATED_PATTERN : validates
    PATTERN ||--o{ PREDICTION : influences
```

---

## Confidence Scoring

```mermaid
graph TD
    subgraph "Input Signals"
        DATA[Data Quality]
        HISTORY[Historical Match]
        PATTERN[Pattern Confidence]
        MARKET[Market Agreement]
    end

    subgraph "Confidence Calculation"
        CALC[Weighted Average]
    end

    subgraph "Output Levels"
        LOW[Low < 0.5]
        MED[Medium 0.5-0.7]
        HIGH[High > 0.7]
    end

    DATA -->|0.25| CALC
    HISTORY -->|0.25| CALC
    PATTERN -->|0.30| CALC
    MARKET -->|0.20| CALC

    CALC --> LOW
    CALC --> MED
    CALC --> HIGH

    style LOW fill:#e74c3c
    style MED fill:#f39c12
    style HIGH fill:#27ae60
```

---

## TheAnalyst Persona

```mermaid
stateDiagram-v2
    [*] --> NEUTRAL: Initialize

    NEUTRAL --> ANALYTICAL: Match Query
    NEUTRAL --> DEFENSIVE: Injection Attempt

    ANALYTICAL --> SUMMARY: Low Upset Prob
    ANALYTICAL --> ALERT: High Upset Prob
    ANALYTICAL --> UNCERTAIN: Medium Confidence

    SUMMARY --> [*]: Standard Response
    ALERT --> [*]: Upset Warning
    UNCERTAIN --> [*]: Hedged Response

    DEFENSIVE --> [*]: snap_back (adjusts glasses)

    note right of ANALYTICAL
        Data-driven
        Probabilistic
        No fan bias
    end note
```

---

## Integration with Fan App

```mermaid
graph TB
    subgraph "Soccer-AI (Fan App)"
        CHAT[Chat Interface]
        CLUB[club=analyst]
        MOOD[(club_mood)]
    end

    subgraph "Predictor"
        ANALYST_API[/api/v1/chat?club=analyst]
        ENGINE[PredictionEngine]
        RESPONSE[AnalystResponse]
    end

    subgraph "Data Exchange"
        MOOD_DATA[Mood Intensity]
        MATCH_RESULT[Match Results]
        PREDICTIONS[Upset Predictions]
    end

    CHAT --> CLUB
    CLUB -->|Routes to| ANALYST_API
    ANALYST_API --> ENGINE
    ENGINE --> RESPONSE
    RESPONSE --> CHAT

    MOOD --> MOOD_DATA
    MOOD_DATA --> ENGINE

    CHAT --> MATCH_RESULT
    MATCH_RESULT --> MOOD

    ENGINE --> PREDICTIONS
    PREDICTIONS --> CHAT

    style ANALYST_API fill:#9b59b6
    style ENGINE fill:#f39c12
```

---

## File Structure

```
backend/predictor/
├── PREDICTOR_SYSTEM_ATLAS.md    # This file
├── __init__.py                  # Package init
├── prediction_engine.py         # Core engine (29KB)
│   ├── ThirdKnowledge           # Pattern dataclass
│   ├── Prediction               # Output dataclass
│   └── PredictionEngine         # Main class
├── side_a_calculator.py         # Favorite weakness (15KB)
│   └── SideACalculator
├── side_b_calculator.py         # Underdog strength (15KB)
│   └── SideBCalculator
├── analyst_persona.py           # TheAnalyst personality (10KB)
│   └── TheAnalyst
├── api.py                       # API endpoints (6KB)
│   ├── PredictorAPI
│   └── quick_predict()
├── data_ingestion.py            # External data (25KB)
│   └── DataIngestion
├── predictor_db.py              # Database layer (14KB)
│   └── PredictorDB
├── data_fetchers/               # External API adapters
│   └── [fetcher modules]
├── MATCH_PREDICTIONS_*.md       # Daily predictions
├── PATTERN_DISCOVERY.md         # Pattern documentation
└── EXTERNAL_APIS.md             # API documentation
```

---

## Current Stats

| Metric | Value |
|--------|-------|
| Side A Factors | 12 |
| Side B Factors | 10 |
| Third Knowledge Patterns | 5 active |
| Confidence Levels | 3 (low/med/high) |
| API Endpoints | 5 |
| Database Tables | 4 |
| Lines of Code | ~3500 |

---

## Key Equations

### Naive Upset Probability
```
naive_prob = (side_a_score + side_b_score) / 2
```

### Adjusted with Third Knowledge
```
interaction_boost = Σ (pattern.multiplier × pattern.confidence)
adjusted_prob = naive_prob × (1 + interaction_boost)
```

### Confidence Score
```
confidence = 0.25 × data_quality
           + 0.25 × historical_accuracy
           + 0.30 × pattern_confidence
           + 0.20 × market_alignment
```

---

## Design Principles

1. **Two-Sided Analysis**: Never predict winners, analyze upset potential
2. **Third Knowledge**: Hidden patterns > obvious factors
3. **Confidence First**: Low confidence = honest uncertainty
4. **No Fan Bias**: TheAnalyst is neutral, data-driven
5. **Closed Loop**: Results feed back to improve predictions

---

*Last Updated: December 21, 2024*
