# Soccer-AI User Guide

## Getting Started

Soccer-AI is an emotionally intelligent football companion that supports your Premier League club with authentic fan emotion.

### Quick Start

1. **Start the backend**:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

2. **Open the chat**:
   - Flask frontend: `http://localhost:5000/chat`
   - Or React frontend: `http://localhost:5173`

3. **Select your club** from the dropdown menu

4. **Start chatting!**

---

## Features

### 1. Club Personas

Each of the 20 Premier League clubs has a unique persona with:
- Emotional state based on recent results
- Regional dialect (Scouse, Mancunian, Cockney, etc.)
- Knowledge of legends and historic moments
- Awareness of rivalries

**Example**: Chat with a Liverpool fan:
> "What do you think of Everton?"
>
> *"Ah, the Blues? Bless 'em, like. They're right there across Stanley Park but light years behind in trophies, aren't they? 6 European Cups we've got, la. Six. They've got... well, they've got a nice new stadium coming, I'll give 'em that."*

### 2. 4D Position Indicator

The chat header shows the AI's current 4D state:

| Axis | What It Shows |
|------|---------------|
| **X (Emotional)** | Mood based on recent results (euphoric, confident, neutral, nervous, frustrated) |
| **Y (Relational)** | Active rivalry when a rival is mentioned |
| **Z (Linguistic)** | Regional dialect being used |
| **T (Temporal)** | Conversation turn and momentum |

### 3. Mood System

The AI's mood is **computed from real match results**, not declared:

| Form | Mood | Emoji |
|------|------|-------|
| WWWWW | Euphoric | 🎉 |
| WWDWL | Confident | 😊 |
| WLDLW | Neutral | 😐 |
| LLLDW | Nervous | 😰 |
| LLLLL | Frustrated | 😤 |

The form badges show the last 5 results (W=Win, D=Draw, L=Loss).

### 4. Rivalry Detection

When you mention a rival club, the AI activates "rivalry mode":

| Your Club | Rival | Derby Name |
|-----------|-------|------------|
| Arsenal | Tottenham | North London Derby |
| Liverpool | Manchester United | North West Derby |
| Liverpool | Everton | Merseyside Derby |
| Chelsea | Tottenham | London Derby |

The Y-axis indicator will show ⚔️ and the rival's name.

### 5. Trivia Mode

Type `/trivia` to play a quiz game about your club:
- Questions about legends, history, and records
- Multiple choice answers
- Score tracking

---

## Chat Commands

| Command | Action |
|---------|--------|
| `/trivia` | Start trivia quiz |
| `/stream` | Toggle streaming mode on/off |

---

## Dialects

The AI speaks with regional authenticity:

### North
- **Liverpool/Everton**: Scouse ("la", "sound", "boss")
- **Man United/Man City**: Mancunian ("our kid", "nowt")
- **Newcastle**: Geordie ("howay", "canny")

### Midlands
- **Aston Villa, Wolves, Leicester**: Midlands dialect

### London
- **Arsenal, Chelsea, Spurs, West Ham**: Cockney ("blimey", "leave it out")

### South
- **Brighton, Bournemouth**: Neutral English

---

## API Endpoints

### Chat
```
POST /api/v1/chat
{
  "message": "How did we play last weekend?",
  "club": "arsenal"
}
```

### 4D State
```
GET /api/v1/fan/arsenal/4d-state
```

### Mood
```
GET /api/v1/fan/arsenal/mood
```

### Check Rivalry
```
POST /api/v1/fan/arsenal/check-rivalry
{"message": "What about Spurs?"}
```

---

## Tips

1. **Ask about legends**: "Who's the greatest player in our history?"
2. **Discuss rivals**: "What do you think of [rival team]?"
3. **Check the mood**: The AI's mood reflects real recent results
4. **Try different clubs**: Each club has unique personality and knowledge
5. **Use UK English**: The AI understands "match", "nil", "pitch"

---

## Troubleshooting

### "Failed to connect to backend"
- Make sure the backend is running on port 8000
- Check if `ANTHROPIC_API_KEY` is set in `.env`

### Mood showing as "neutral"
- The API might be offline
- The system will fallback to database match history

### Rivalry not activating
- Try using the full club name or common alias
- Example: "Spurs" or "Tottenham" both work

---

## The Vision

> *"What if the AI wasn't neutral? What if it was a fan?"*

Soccer-AI is designed to:
- **Feel** the weight of rivalries
- **Know** you don't casually mention "that Agüero goal" to a Man United supporter
- **Understand** pre-match hope vs post-loss grief
- **Speak** authentic football language

**Fan at heart. Analyst in nature.** ⚽
