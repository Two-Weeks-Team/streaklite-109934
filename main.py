import os
import uuid
from fastapi import FastAPI, Request, Response, Cookie, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from models import SessionLocal, engine, Habit, HabitCheck, Session as SessionModel
from routes import router

app = FastAPI(title="StreakLite Backend", version="0.1.0")
app.include_router(router)

# Create tables on startup (if they don't exist)
@app.on_event("startup")
def on_startup():
    from models import Base
    Base.metadata.create_all(bind=engine)

@app.get("/health", response_model=dict)
def health():
    return {"status": "ok"}

def _get_or_create_session(session_id: str | None = None, response: Response | None = None):
    db = SessionLocal()
    try:
        if session_id:
            sess = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
            if sess:
                sess.last_active_at = "NOW()"
                db.commit()
                return sess.session_id
        # create new session
        new_id = str(uuid.uuid4())
        new_sess = SessionModel(session_id=new_id)
        db.add(new_sess)
        db.commit()
        if response is not None:
            response.set_cookie(key="session_id", value=new_id, httponly=True, samesite="strict")
        return new_id
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def landing_page(request: Request, session_id: str | None = Cookie(None), response: Response = None):
    # Ensure a session cookie exists
    _ = _get_or_create_session(session_id, response)
    html = """
    <html>
    <head>
        <title>StreakLite API</title>
        <style>
            body {background-color:#1a1a1a;color:#e0e0e0;font-family:Arial,Helvetica,sans-serif;padding:2rem;}
            h1 {color:#4fd1c5;}
            a {color:#81e6d9;}
            table {border-collapse:collapse;width:100%;margin-top:1rem;}
            th, td {border:1px solid #333;padding:0.5rem;text-align:left;}
            th {background:#2d2d2d;}
        </style>
    </head>
    <body>
        <h1>StreakLite Backend</h1>
        <p>One‑click habit streak tracker – simple, private, no‑login.</p>
        <h2>Available Endpoints</h2>
        <table>
            <tr><th>Method</th><th>Path</th><th>Description</th></tr>
            <tr><td>GET</td><td>/health</td><td>Health check</td></tr>
            <tr><td>GET</td><td>/habits</td><td>List habits for current session</td></tr>
            <tr><td>POST</td><td>/habits</td><td>Create a new habit</td></tr>
            <tr><td>POST</td><td>/habits/{habit_id}/check</td><td>Mark habit as completed for today</td></tr>
            <tr><td>GET</td><td>/habits/{habit_id}/calendar</td><td>30‑day streak calendar</td></tr>
            <tr><td>POST</td><td>/habits/recommend</td><td>AI‑generated habit recommendations</td></tr>
            <tr><td>POST</td><td>/habits/analyze-streak</td><td>AI‑powered streak analysis</td></tr>
        </table>
        <p>Docs: <a href="/docs">/docs</a> | <a href="/redoc">/redoc</a></p>
        <h2>Tech Stack</h2>
        <ul>
            <li>FastAPI 0.115.0</li>
            <li>SQLAlchemy 2.0.35 (PostgreSQL/SQLite)</li>
            <li>DigitalOcean Serverless Inference (openai-gpt-oss-120b)</li>
            <li>Python 3.12</li>
        </ul>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)
