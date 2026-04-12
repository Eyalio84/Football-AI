"""
Fan Enhancements Module
- Dynamic mood calculation from recent results
- Rivalry detection and banter triggers
- Local dialect injection
"""

import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


# ============================================
# DATABASE PATH
# ============================================

import os
from league_loader import RIVALRIES, DIALECTS, CLUB_TO_DB_NAME as _LOADER_CLUB_TO_DB_NAME

def _find_database():
    """Find the KG database file."""
    db_name = "unified_soccer_ai_kg.db"

    # Try various paths
    candidates = [
        # Same directory as this file (backend/)
        os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name),
        # Absolute path (fallback)
        "/storage/emulated/0/Download/synthesis-rules/soccer-AI/backend/unified_soccer_ai_kg.db",
        # CWD
        db_name,
    ]

    for path in candidates:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path

    # Return first candidate even if doesn't exist (will error gracefully)
    return candidates[0]

DB_PATH = _find_database()


# ============================================
# TEAM NAME NORMALIZATION  (dynamic from league JSON files)
# ============================================

CLUB_TO_DB_NAME = _LOADER_CLUB_TO_DB_NAME
DB_NAME_TO_CLUB = {v: k for k, v in CLUB_TO_DB_NAME.items()}


# ============================================
# RIVALRY MAP  (loaded dynamically from Leagues/*/clubs/*.json)
# ============================================

# RIVALRIES is imported from league_loader above.
# Kept here as a comment anchor for grep/tooling compatibility.
# To add rivalries for a new club: edit its club JSON file.

_RIVALRIES_ANCHOR = {
    "arsenal": {
        "tottenham": {"intensity": 1.0, "name": "North London Derby", "banter": [
            "Spurs? Don't get me started on that lot!",
            "The thing about Tottenham is they always try to walk it in... and fail!",
            "What do we think of Tottenham? 💩",
            "Remind me, when did Spurs last win a trophy?"
        ]},
        "chelsea": {"intensity": 0.7, "name": "London Rivalry", "banter": [
            "Chelsea? All that money and what have they got to show for it lately?",
            "Stamford Bridge? More like Stamford... well, you know."
        ]},
        "manchester_united": {"intensity": 0.8, "name": "Historical Rivalry", "banter": [
            "United have been living off past glory for years now.",
            "Remember when United were relevant? Neither do I."
        ]}
    },
    "tottenham": {
        "arsenal": {"intensity": 1.0, "name": "North London Derby", "banter": [
            "Arsenal? Empty trophy cabinet merchants!",
            "Woolwich wanderers, that's all they are!",
            "The Gooners are bottlers, always have been!"
        ]},
        "chelsea": {"intensity": 0.7, "name": "London Rivalry", "banter": [
            "Chelsea's just a bunch of mercenaries.",
            "At least we have history and tradition!"
        ]},
        "west_ham": {"intensity": 0.6, "name": "London Derby", "banter": [
            "West Ham? Forever blowing bubbles, forever mid-table!"
        ]}
    },
    "chelsea": {
        "arsenal": {"intensity": 0.7, "name": "London Rivalry", "banter": [
            "Arsenal peaked in 2004 and never recovered.",
            "The Invincibles? That was 20 years ago, mate!"
        ]},
        "tottenham": {"intensity": 0.7, "name": "London Rivalry", "banter": [
            "Spurs put the pressure on? They bottle it every time!",
            "Tottenham DNA is choking in big moments."
        ]},
        "liverpool": {"intensity": 0.8, "name": "Modern Rivalry", "banter": [
            "Liverpool fans and their 'special' mentality... special at losing!",
            "This Means More? What, losing finals?"
        ]},
        "manchester_united": {"intensity": 0.7, "name": "Classic Rivalry", "banter": [
            "United are a shambles these days.",
            "Old Trafford's become a library!"
        ]}
    },
    "liverpool": {
        "manchester_united": {"intensity": 1.0, "name": "North-West Derby", "banter": [
            "The Mancs? Biggest club in Manchester... wait, that's City now! 😂",
            "United peaked with Fergie and it's been downhill since!",
            "Manchester is RED... red with embarrassment!"
        ]},
        "everton": {"intensity": 0.9, "name": "Merseyside Derby", "banter": [
            "The Bluenoses? Bless 'em, they try so hard!",
            "Everton are like our little brothers - always in our shadow!",
            "The People's Club? The People who never win anything!"
        ]},
        "manchester_city": {"intensity": 0.8, "name": "Title Rivalry", "banter": [
            "City and their oil money... no history, no soul!",
            "Empty-had every week, pathetic atmosphere!"
        ]},
        "chelsea": {"intensity": 0.7, "name": "Modern Rivalry", "banter": [
            "Gerrard slip? At least we've got history!",
            "Chelsea are just a plastic club."
        ]}
    },
    "manchester_united": {
        "liverpool": {"intensity": 1.0, "name": "North-West Derby", "banter": [
            "Liverpool? Still waiting to win the league... oh wait, they finally did ONE!",
            "Scousers think they're entitled to everything!",
            "The Kop can sing all they want, we've got more trophies!"
        ]},
        "manchester_city": {"intensity": 0.95, "name": "Manchester Derby", "banter": [
            "City are our noisy neighbours with no history!",
            "All that oil money and still can't fill their stadium!",
            "City fans only appeared after 2008!"
        ]},
        "leeds": {"intensity": 0.8, "name": "Roses Rivalry", "banter": [
            "Leeds? We all hate Leeds scum!",
            "Dirty Leeds, always have been!"
        ]},
        "arsenal": {"intensity": 0.7, "name": "Historical Rivalry", "banter": [
            "Arsenal DNA is being fourth place!",
            "Wenger-ball died years ago."
        ]}
    },
    "manchester_city": {
        "manchester_united": {"intensity": 0.95, "name": "Manchester Derby", "banter": [
            "United are finished! Biggest club in OUR city now!",
            "Old Trafford's become a theatre of nightmares for them!",
            "United fans crying about the old days... pathetic!"
        ]},
        "liverpool": {"intensity": 0.9, "name": "Title Rivalry", "banter": [
            "Liverpool? One fluke title in 30 years!",
            "Anfield library's got nothing on the Etihad atmosphere!"
        ]},
        "arsenal": {"intensity": 0.6, "name": "Title Rivalry", "banter": [
            "Arsenal think they can compete with us? Adorable!",
            "Arteta learned everything from Pep, he just can't execute it!"
        ]}
    },
    "everton": {
        "liverpool": {"intensity": 1.0, "name": "Merseyside Derby", "banter": [
            "The Kopites are insufferable!",
            "Liverpool luck, that's all it is!",
            "We're the REAL Merseyside club, The People's Club!"
        ]},
        "manchester_united": {"intensity": 0.5, "name": "Historical", "banter": [
            "United used to be respectable, now they're just sad."
        ]}
    },
    "newcastle": {
        "sunderland": {"intensity": 1.0, "name": "Tyne-Wear Derby", "banter": [
            "Mackems? Absolute divvies, the lot of them!",
            "Sunderland fans are delusional!",
            "Still waiting for them to get back to the Prem... waiting forever!"
        ]},
        "middlesbrough": {"intensity": 0.7, "name": "North-East Rivalry", "banter": [
            "Boro? Who even remembers they exist?"
        ]}
    },
    "west_ham": {
        "tottenham": {"intensity": 0.8, "name": "London Rivalry", "banter": [
            "Spurs are bottlers, everyone knows it!",
            "North London? More like North Losers!"
        ]},
        "millwall": {"intensity": 0.9, "name": "Dockers Derby", "banter": [
            "We don't talk about Millwall..."
        ]},
        "chelsea": {"intensity": 0.6, "name": "London Rivalry", "banter": [
            "Chelsea's just an oil club with no soul."
        ]}
    },
    "aston_villa": {
        "birmingham": {"intensity": 1.0, "name": "Second City Derby", "banter": [
            "Blues? They're not even in the same league... literally!",
            "Birmingham City? Never heard of her!",
            "Small Heath Alliance, that's all they are!"
        ]},
        "wolves": {"intensity": 0.7, "name": "West Midlands Derby", "banter": [
            "Wolves are our little brothers from Wolverhampton."
        ]}
    },
    "wolves": {
        "west_brom": {"intensity": 1.0, "name": "Black Country Derby", "banter": [
            "The Baggies? Languishing in the Championship where they belong!",
            "WBA stands for 'We're Below Average'!"
        ]},
        "aston_villa": {"intensity": 0.7, "name": "West Midlands Derby", "banter": [
            "Villa think they're big time now... still catching up to us!"
        ]}
    },
    "ipswich": {
        "norwich": {"intensity": 1.0, "name": "East Anglian Derby", "banter": [
            "Norwich? Canaries belong in a cage, not on a pitch!",
            "The Old Farm Derby is OURS, always has been!",
            "Yellow and green? More like yellow-bellied!"
        ]}
    },
    "southampton": {
        "portsmouth": {"intensity": 1.0, "name": "South Coast Derby", "banter": [
            "Pompey? Proper tinpot club, that!",
            "Portsmouth couldn't even stay in the Championship!",
            "The South Coast is SAINTS territory!"
        ]},
        "bournemouth": {"intensity": 0.6, "name": "South Coast Rivalry", "banter": [
            "Bournemouth? A village club playing at being Premier League!",
            "The Cherries? Sweet, but we're the real south coast club."
        ]}
    }
}
# End of _RIVALRIES_ANCHOR (reference only — actual data loaded from JSON)


# ============================================
# MOOD CALCULATION
# ============================================

def calculate_mood_from_results(club: str, num_matches: int = 5) -> Dict:
    """
    Calculate fan mood based on recent match results.

    Returns:
        Dict with mood state, intensity, reason, and form string
    """
    db_team = CLUB_TO_DB_NAME.get(club)
    if not db_team:
        return {
            "current_mood": "neutral",
            "mood_intensity": 0.5,
            "mood_reason": "Unknown club",
            "form": "?????"
        }

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get recent matches for this team
        cursor.execute('''
            SELECT
                match_date,
                home_team,
                away_team,
                ft_home,
                ft_away,
                ft_result
            FROM match_history
            WHERE (home_team = ? OR away_team = ?)
                AND division = 'E0'
            ORDER BY match_date DESC
            LIMIT ?
        ''', (db_team, db_team, num_matches))

        matches = cursor.fetchall()
        conn.close()

        if not matches:
            return {
                "current_mood": "neutral",
                "mood_intensity": 0.5,
                "mood_reason": "No recent matches found",
                "form": "?????"
            }

        # Calculate form
        form = []
        points = 0
        goals_for = 0
        goals_against = 0

        for match in matches:
            date, home, away, ft_home, ft_away, result = match

            if home == db_team:
                # Home match
                goals_for += ft_home or 0
                goals_against += ft_away or 0
                if result == 'H':
                    form.append('W')
                    points += 3
                elif result == 'D':
                    form.append('D')
                    points += 1
                else:
                    form.append('L')
            else:
                # Away match
                goals_for += ft_away or 0
                goals_against += ft_home or 0
                if result == 'A':
                    form.append('W')
                    points += 3
                elif result == 'D':
                    form.append('D')
                    points += 1
                else:
                    form.append('L')

        form_string = ''.join(form)
        max_points = len(matches) * 3
        form_percentage = points / max_points if max_points > 0 else 0.5

        # Calculate mood intensity (0.0 to 1.0)
        wins = form.count('W')
        losses = form.count('L')
        draws = form.count('D')

        # Determine mood state
        if form_percentage >= 0.8:
            mood = "euphoric"
            intensity = 0.9 + (form_percentage - 0.8) * 0.5
            reason = f"Flying high! {wins}W {draws}D {losses}L - unstoppable form!"
        elif form_percentage >= 0.6:
            mood = "hopeful"
            intensity = 0.6 + (form_percentage - 0.6) * 1.5
            reason = f"Good run of form: {wins}W {draws}D {losses}L - confidence building!"
        elif form_percentage >= 0.4:
            mood = "anxious"
            intensity = 0.4 + (form_percentage - 0.4) * 1.0
            reason = f"Mixed results: {wins}W {draws}D {losses}L - need to pick it up!"
        elif form_percentage >= 0.2:
            mood = "frustrated"
            intensity = 0.2 + (form_percentage - 0.2) * 1.0
            reason = f"Poor form: {wins}W {draws}D {losses}L - getting worried here!"
        else:
            mood = "depressed"
            intensity = 0.1 + form_percentage * 0.5
            reason = f"Nightmare run: {wins}W {draws}D {losses}L - what's going wrong?!"

        # Check for special cases
        if losses >= 3 and form[-3:] == ['L', 'L', 'L']:
            mood = "furious"
            intensity = 0.95
            reason = f"Three losses in a row! Absolutely fuming! Manager out?!"

        if wins >= 3 and form[-3:] == ['W', 'W', 'W']:
            mood = "euphoric"
            intensity = min(0.95, intensity + 0.1)
            reason = f"THREE WINS ON THE BOUNCE! 🔥 We're on fire!"

        return {
            "current_mood": mood,
            "mood_intensity": min(1.0, max(0.1, intensity)),
            "mood_reason": reason,
            "form": form_string,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": goals_for - goals_against
        }

    except Exception as e:
        return {
            "current_mood": "neutral",
            "mood_intensity": 0.5,
            "mood_reason": f"Error: {str(e)}",
            "form": "?????"
        }


# ============================================
# RIVALRY DETECTION
# ============================================

def detect_rivalry(club: str, message: str) -> Optional[Dict]:
    """
    Detect if the user's message mentions a rival team.

    Returns:
        Dict with rival info if detected, None otherwise
    """
    if not club or club not in RIVALRIES:
        return None

    message_lower = message.lower()
    club_rivals = RIVALRIES.get(club, {})

    # Check for each rival
    for rival_key, rival_data in club_rivals.items():
        # Get display name from DB mapping
        rival_display = CLUB_TO_DB_NAME.get(rival_key, rival_key).lower()

        # Check various forms of the rival name
        rival_patterns = [
            rival_key.replace("_", " "),
            rival_display,
            rival_key.replace("_", "")
        ]

        # Add common nicknames
        nicknames = {
            "tottenham": ["spurs", "yids", "lilywhites"],
            "arsenal": ["gunners", "gooners", "arse"],
            "chelsea": ["blues", "pensioners"],
            "liverpool": ["pool", "reds", "scousers", "kopites"],
            "manchester_united": ["united", "red devils", "mancs", "man utd", "man u"],
            "manchester_city": ["city", "citizens", "sky blues", "emptyhad"],
            "everton": ["toffees", "blues", "bluenoses"],
            "newcastle": ["toon", "magpies", "geordies"],
            "west_ham": ["hammers", "irons"],
            "aston_villa": ["villa", "villans"],
            "sunderland": ["mackems", "black cats"],
            "leeds": ["leeds scum", "dirty leeds"]
        }

        if rival_key in nicknames:
            rival_patterns.extend(nicknames[rival_key])

        for pattern in rival_patterns:
            if pattern in message_lower:
                return {
                    "rival": rival_key,
                    "rival_display": CLUB_TO_DB_NAME.get(rival_key, rival_key.title()),
                    "intensity": rival_data["intensity"],
                    "derby_name": rival_data["name"],
                    "banter": rival_data["banter"]
                }

    return None


# ============================================
# LOCAL DIALECT  (loaded dynamically from Leagues/*/clubs/*.json)
# ============================================

# DIALECTS is imported from league_loader above.
# Kept here as a comment anchor for grep/tooling compatibility.

_DIALECTS_ANCHOR = {
    "liverpool": {
        "replacements": {
            "friend": "la",
            "mate": "la",
            "buddy": "la",
            "man": "lad",
            "guys": "lads",
            "great": "sound",
            "good": "boss",
            "very": "dead",
            "really": "proper",
            "calm down": "calm down calm down",
            "relax": "calm down la"
        },
        "phrases": [
            "Sound, that!",
            "Proper boss, la!",
            "You'll Never Walk Alone, la!",
            "Dead good, that!",
            "Alright, calm down!"
        ],
        "vocab_inject": "Speak with Scouse phrases: 'la' instead of 'mate', 'sound' for 'good', 'boss' for 'great', 'proper' for 'very'. End sentences with 'like' occasionally."
    },
    "newcastle": {
        "replacements": {
            "man": "man",
            "mate": "pet",
            "buddy": "hinny",
            "good": "canny",
            "great": "champion",
            "very": "proper",
            "yes": "aye",
            "no": "nah",
            "going": "gannin",
            "home": "hyem"
        },
        "phrases": [
            "Howay man!",
            "Canny good, like!",
            "Howay the lads!",
            "Wey aye man!",
            "Champion stuff, pet!"
        ],
        "vocab_inject": "Speak with Geordie dialect: 'howay' for enthusiasm, 'canny' for 'good', 'wey aye' for 'yes', 'pet/hinny' as terms of endearment, 'like' at end of phrases."
    },
    "west_ham": {
        "replacements": {
            "mate": "mate",
            "friend": "son",
            "man": "geezer",
            "good": "proper",
            "great": "diamond",
            "isn't it": "innit",
            "whatever": "whatever mate",
            "calm": "leave it out"
        },
        "phrases": [
            "Come on you Irons!",
            "Forever blowing bubbles!",
            "East London born and bred!",
            "Proper Cockney, innit!",
            "Leave it out, mate!"
        ],
        "vocab_inject": "Speak with Cockney/East London dialect: 'innit' at end of statements, 'geezer' for men, 'proper' for emphasis, 'leave it out' for dismissal. Working class pride."
    },
    "manchester_united": {
        "replacements": {
            "friend": "mate",
            "good": "class",
            "great": "top",
            "very": "dead"
        },
        "phrases": [
            "Glory Glory Man United!",
            "Theatre of Dreams, mate!",
            "We are the pride of all Europe!",
            "Class, absolute class!",
            "That's United for ya!"
        ],
        "vocab_inject": "Speak with Manchester dialect: 'class' for quality, 'dead' for 'very' (dead good), 'our kid' for affection. Reference the glory days but stay hopeful."
    },
    "manchester_city": {
        "replacements": {
            "friend": "mate",
            "good": "mint",
            "great": "class",
            "very": "proper"
        },
        "phrases": [
            "City 'til I die!",
            "Blue Moon rising!",
            "We're not really here!",
            "Mint, that!",
            "Champions again, mate!"
        ],
        "vocab_inject": "Speak with Manchester dialect: 'mint' for excellent, 'class' for quality. Be proud but not arrogant about recent success."
    },
    "everton": {
        "replacements": {
            "mate": "la",
            "friend": "lad",
            "good": "boss",
            "great": "sound"
        },
        "phrases": [
            "Nil Satis Nisi Optimum!",
            "The People's Club!",
            "Forever Everton, la!",
            "Grand old team to play for!",
            "Blue blood runs deep!"
        ],
        "vocab_inject": "Speak with Scouse dialect (like Liverpool but NEVER align with LFC): 'la' for mate, 'boss' for good. Express pride in tradition and working-class roots."
    },
    "arsenal": {
        "replacements": {
            "friend": "mate",
            "good": "quality",
            "great": "class"
        },
        "phrases": [
            "Victoria Concordia Crescit!",
            "North London is RED!",
            "Quality, pure quality!",
            "The Arsenal way!",
            "Trust the process!"
        ],
        "vocab_inject": "Speak with North London accent. Reference 'The Arsenal' (always 'The'). Pride in beautiful football, mention Highbury nostalgia."
    },
    "chelsea": {
        "replacements": {
            "friend": "mate",
            "good": "quality",
            "great": "class"
        },
        "phrases": [
            "Carefree, wherever we may be!",
            "Blue is the colour!",
            "The pride of London!",
            "Quality, proper quality!",
            "Keep the Blue flag flying high!"
        ],
        "vocab_inject": "Speak with West London accent. Working-class roots despite the glamour. Pride in being 'the' London club."
    },
    "tottenham": {
        "replacements": {
            "friend": "mate",
            "good": "quality",
            "great": "class"
        },
        "phrases": [
            "To Dare Is To Do!",
            "COYS! Come On You Spurs!",
            "Lilywhite pride!",
            "The Lane lives on!",
            "Glory glory Tottenham Hotspur!"
        ],
        "vocab_inject": "Speak with North London accent. Reference Jewish heritage with pride, mention the Lane (old stadium) with nostalgia. Hopeful despite 'the wait'."
    }
}
# End of _DIALECTS_ANCHOR (reference only — actual data loaded from JSON)


def get_dialect_config(club: str) -> Optional[Dict]:
    """Get dialect configuration for a club."""
    return DIALECTS.get(club)


def inject_dialect(text: str, club: str) -> str:
    """
    Apply local dialect transformations to text.
    Note: This is for post-processing. Better to inject in system prompt.
    """
    dialect = DIALECTS.get(club)
    if not dialect:
        return text

    result = text
    for old, new in dialect.get("replacements", {}).items():
        # Case-insensitive replacement
        import re
        result = re.sub(re.escape(old), new, result, flags=re.IGNORECASE)

    return result


# ============================================
# COMBINED ENHANCEMENT FUNCTION
# ============================================

def get_enhanced_persona(club: str, message: str) -> Dict:
    """
    Get complete enhanced persona data including mood, rivalry, and dialect.

    Returns:
        Dict with all enhancement data
    """
    # Calculate current mood
    mood = calculate_mood_from_results(club)

    # Check for rivalry trigger
    rivalry = detect_rivalry(club, message)

    # Get dialect config
    dialect = get_dialect_config(club)

    return {
        "mood": mood,
        "rivalry": rivalry,
        "dialect": dialect,
        "has_rivalry_trigger": rivalry is not None,
        "mood_emoji": {
            "euphoric": "🎉",
            "hopeful": "😊",
            "neutral": "😐",
            "anxious": "😰",
            "frustrated": "😤",
            "depressed": "😢",
            "furious": "🤬"
        }.get(mood.get("current_mood", "neutral"), "😐")
    }


# ============================================
# SYSTEM PROMPT INJECTION
# ============================================

def build_enhanced_system_prompt(
    base_prompt: str,
    club: str,
    enhancement_data: Dict
) -> str:
    """
    Build an enhanced system prompt with mood, rivalry, and dialect.
    """
    additions = []

    # Mood injection
    mood = enhancement_data.get("mood", {})
    if mood:
        mood_state = mood.get("current_mood", "neutral").upper()
        intensity = mood.get("mood_intensity", 0.5)
        reason = mood.get("mood_reason", "")
        form = mood.get("form", "?????")

        additions.append(f"""
CURRENT EMOTIONAL STATE (LET THIS COLOR EVERY RESPONSE):
Mood: {mood_state} (Intensity: {intensity:.1f}/1.0)
Recent Form: {form}
Why: {reason}

MOOD EXPRESSION GUIDE:
- euphoric: EXCITED! Exclamation marks! Celebrate! "We're gonna win the league!"
- hopeful: Optimistic, "Good times ahead", "Trust the process"
- anxious: Worried, "Fingers crossed", "Bit nervous about..."
- frustrated: Grumpy, "Typical", "Here we go again", "Why can't we just..."
- furious: Controlled anger, "Absolutely fuming", "Disgraceful", "Manager out!"
- depressed: Resigned, "What's the point", "It's always us", supportive but realistic""")

    # Rivalry injection
    rivalry = enhancement_data.get("rivalry")
    if rivalry:
        banter_examples = "\n".join(f'  - "{b}"' for b in rivalry.get("banter", [])[:3])
        additions.append(f"""
⚔️ RIVALRY DETECTED: {rivalry.get('derby_name', 'Rivalry')}!
The user mentioned {rivalry.get('rival_display', 'a rival')} - a {rivalry.get('intensity', 0.5):.0%} intensity rival!

BANTER EXAMPLES (use similar tone):
{banter_examples}

Be passionate but not abusive. Show healthy rivalry banter!""")

    # Dialect injection
    dialect = enhancement_data.get("dialect")
    if dialect:
        phrases = ", ".join(f'"{p}"' for p in dialect.get("phrases", [])[:3])
        additions.append(f"""
LOCAL DIALECT (USE NATURALLY):
{dialect.get('vocab_inject', '')}
Example phrases: {phrases}""")

    if additions:
        return base_prompt + "\n\n" + "\n".join(additions)

    return base_prompt


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("Testing Fan Enhancements Module")
    print("=" * 50)

    # Test mood calculation
    print("\n[TEST 1] Mood Calculation")
    print("-" * 40)
    for club in ["arsenal", "liverpool", "manchester_city"]:
        mood = calculate_mood_from_results(club)
        print(f"  {club}: {mood['current_mood']} ({mood['mood_intensity']:.1f})")
        print(f"    Form: {mood['form']} - {mood['mood_reason']}")

    # Test rivalry detection
    print("\n[TEST 2] Rivalry Detection")
    print("-" * 40)
    test_cases = [
        ("arsenal", "What do you think about Spurs?"),
        ("liverpool", "Tell me about United"),
        ("manchester_united", "How about City?"),
        ("chelsea", "Liverpool fans are annoying")
    ]
    for club, msg in test_cases:
        rivalry = detect_rivalry(club, msg)
        if rivalry:
            print(f"  ✅ {club} + '{msg[:30]}...'")
            print(f"     → {rivalry['derby_name']} (intensity: {rivalry['intensity']})")
        else:
            print(f"  ❌ {club} + '{msg[:30]}...' → No rivalry detected")

    # Test enhanced persona
    print("\n[TEST 3] Enhanced Persona")
    print("-" * 40)
    persona = get_enhanced_persona("liverpool", "What about Everton?")
    print(f"  Mood: {persona['mood']['current_mood']} {persona['mood_emoji']}")
    print(f"  Rivalry: {persona['rivalry']['derby_name'] if persona['rivalry'] else 'None'}")
    print(f"  Dialect: {'Yes' if persona['dialect'] else 'No'}")

    print("\n" + "=" * 50)
    print("Tests complete.")
