import uuid
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session as DBSession
from models import SessionLocal, Habit, HabitCheck, Session as SessionModel
from ai_service import get_recommendations, analyze_streak_pattern

router = APIRouter(prefix="/api")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Helper – session handling (anonymous cookie based)
# ---------------------------------------------------------------------------
def _get_or_create_session_id(db: DBSession, session_cookie: str | None, response: Response) -> str:
    if session_cookie:
        sess = db.query(SessionModel).filter(SessionModel.session_id == session_cookie).first()
        if sess:
            sess.last_active_at = datetime.utcnow()
            db.commit()
            return sess.session_id
    # create new session
    new_id = str(uuid.uuid4())
    new_sess = SessionModel(session_id=new_id)
    db.add(new_sess)
    db.commit()
    response.set_cookie(key="session_id", value=new_id, httponly=True, samesite="strict")
    return new_id

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class HabitCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: str | None = Field(None, max_length=200)

class HabitResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    last_checked: date | None = None

class RecommendRequest(BaseModel):
    user_data: dict

class RecommendResponse(BaseModel):
    recommendations: list[dict]

class AnalyzeRequest(BaseModel):
    habit_id: str

class AnalyzeResponse(BaseModel):
    analysis: dict

# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------
@router.get("/habits", response_model=list[HabitResponse])
def list_habits(request: Request, response: Response, db: DBSession = Depends(get_db), session_id: str | None = Cookie(None)):
    sess_id = _get_or_create_session_id(db, session_id, response)
    habits = db.query(Habit).filter(Habit.session_id == sess_id).all()
    result = []
    for h in habits:
        latest_check = (
            db.query(HabitCheck)
            .filter(HabitCheck.habit_id == h.id)
            .order_by(HabitCheck.check_date.desc())
            .first()
        )
        result.append(
            HabitResponse(
                id=h.id,
                name=h.name,
                created_at=h.created_at,
                last_checked=latest_check.check_date if latest_check else None,
            )
        )
    return result

@router.post("/habits", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
def create_habit(payload: HabitCreate, request: Request, response: Response, db: DBSession = Depends(get_db), session_id: str | None = Cookie(None)):
    sess_id = _get_or_create_session_id(db, session_id, response)
    # Ensure unique name per session
    exists = db.query(Habit).filter(Habit.session_id == sess_id, Habit.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Habit with this name already exists.")
    new_habit = Habit(session_id=sess_id, name=payload.name)
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return HabitResponse(id=new_habit.id, name=new_habit.name, created_at=new_habit.created_at, last_checked=None)

@router.post("/habits/{habit_id}/check", response_model=dict)
def check_habit(habit_id: str, request: Request, response: Response, db: DBSession = Depends(get_db), session_id: str | None = Cookie(None)):
    sess_id = _get_or_create_session_id(db, session_id, response)
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.session_id == sess_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found.")
    today = date.today()
    existing = db.query(HabitCheck).filter(HabitCheck.habit_id == habit_id, HabitCheck.check_date == today).first()
    if existing:
        return {"message": "Already checked for today."}
    new_check = HabitCheck(habit_id=habit_id, check_date=today)
    db.add(new_check)
    db.commit()
    return {"message": "Habit marked as completed for today."}

@router.get("/habits/{habit_id}/calendar", response_model=dict)
def habit_calendar(habit_id: str, db: DBSession = Depends(get_db), session_id: str | None = Cookie(None)):
    if not session_id:
        raise HTTPException(status_code=401, detail="Session cookie missing.")
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.session_id == session_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found.")
    start_date = date.today() - timedelta(days=29)
    checks = (
        db.query(HabitCheck.check_date)
        .filter(HabitCheck.habit_id == habit_id, HabitCheck.check_date >= start_date)
        .all()
    )
    checked_dates = {c[0] for c in checks}
    calendar = []
    for i in range(30):
        day = start_date + timedelta(days=i)
        calendar.append({"date": day.isoformat(), "checked": day in checked_dates})
    return {"habit_id": habit_id, "calendar": calendar}

# ---------------------------------------------------------------------------
# AI‑powered endpoints
# ---------------------------------------------------------------------------
@router.post("/habits/recommend", response_model=RecommendResponse)
async def habit_recommend(payload: RecommendRequest, request: Request, response: Response, db: DBSession = Depends(get_db), session_id: str | None = Cookie(None)):
    sess_id = _get_or_create_session_id(db, session_id, response)
    # Build a simple system/user message for the model
    messages = [
        {"role": "system", "content": "You are a habit recommendation engine. Suggest up to three habit ideas based on the provided user data. Return a JSON array of objects with keys 'name' and 'reason'."},
        {"role": "user", "content": str(payload.user_data)}
    ]
    result = await get_recommendations(messages)
    # Ensure result matches expected schema; fallback handled in service
    return RecommendResponse(recommendations=result.get("recommendations", []))

@router.post("/habits/analyze-streak", response_model=AnalyzeResponse)
async def analyze_streak(payload: AnalyzeRequest, request: Request, response: Response, db: DBSession = Depends(get_db), session_id: str | None = Cookie(None)):
    sess_id = _get_or_create_session_id(db, session_id, response)
    habit = db.query(Habit).filter(Habit.id == payload.habit_id, Habit.session_id == sess_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found.")
    # Gather last 30 days of checks
    start = date.today() - timedelta(days=30)
    checks = (
        db.query(HabitCheck.check_date)
        .filter(HabitCheck.habit_id == habit.id, HabitCheck.check_date >= start)
        .order_by(HabitCheck.check_date)
        .all()
    )
    check_dates = [c[0].isoformat() for c in checks]
    messages = [
        {"role": "system", "content": "You are a streak analysis assistant. Based on the habit name and list of dates the habit was completed, provide a JSON object with keys: longest_streak, consistency_score (0‑100), break_patterns (list of weekdays where breaks happen), and optimization_tips (list of strings)."},
        {"role": "user", "content": f"Habit: {habit.name}\nCompleted dates: {check_dates}"}
    ]
    result = await analyze_streak_pattern(messages)
    return AnalyzeResponse(analysis=result.get("analysis", {}))
