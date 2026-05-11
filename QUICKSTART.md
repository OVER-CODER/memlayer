# Quick Start Guide

Get MemLayer running in 10 minutes.

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Git

## 1. Clone and Navigate

```bash
cd /path/to/memlayer
git clone . # Already cloned
```

## 2. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key

## 3. Set Up Backend

```bash
cd memlayer-backend

# Install dependencies
poetry install

# Configure environment
cp .env.example .env

# Add your API key
nano .env
# Set: GEMINI_API_KEY=your_key_here

# Initialize database (make sure PostgreSQL is running)
python init_db.py

# Start backend
poetry run python -m uvicorn app.main:app --reload
```

✓ Backend is now running at http://localhost:8000

**Check it works:**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","version":"0.1.0"}
```

## 4. Set Up Frontend

In a **new terminal**:

```bash
cd memlayer-frontend

# Install dependencies
npm install

# Configure API
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start frontend
npm run dev
```

✓ Frontend is now running at http://localhost:3000

## 5. Try It Out

1. Open http://localhost:3000
2. Click "Create Workspace"
3. Enter a name (e.g., "My First Workspace")
4. Click the workspace to open it
5. Type a message and see the AI respond!

## What's Happening

When you send a message:

1. ✓ Your message is stored in memory
2. ✓ The system searches for relevant past memories
3. ✓ Context is compiled from those memories
4. ✓ Gemini AI generates a response
5. ✓ The response is stored as a new memory

**Try asking follow-up questions** - the system will remember context!

## Evaluate on LOCOMO Dataset

The system includes evaluation against the LOCOMO dataset:

```bash
cd memlayer-backend
poetry run python evaluate_locomo.py
```

This measures:
- Semantic search accuracy
- Ability to retrieve relevant context
- Performance on different question types

## Next Steps

- **Explore the code:** Check out `memlayer-backend/app/services/`
- **Read the docs:** See `README.md` for full architecture
- **Extend it:** Add new embedding providers or LLM backends
- **Build features:** Add file uploads, search UI, memory graphs

## Common Issues

**Backend won't start:**
```bash
# Make sure PostgreSQL is running
pg_isready

# If database doesn't exist:
python init_db.py
```

**Frontend can't reach backend:**
```bash
# Check .env.local has correct API URL
cat .env.local

# Verify backend is running
curl http://localhost:8000/health
```

**API Key errors:**
```bash
# Make sure GEMINI_API_KEY is set
cat memlayer-backend/.env | grep GEMINI

# Update it with your actual key
nano memlayer-backend/.env
```

## Architecture at a Glance

```
User Message
    ↓
Query Embedding (local)
    ↓
Semantic Search (pgvector)
    ↓
Context Compilation
    ↓
Gemini API
    ↓
Response + Store Memory
```

## Help

- Check logs in both terminals for errors
- Verify PostgreSQL is running: `pg_isready`
- Ensure Gemini API key is valid
- Read `README.md` for detailed docs

Good luck! 🚀
