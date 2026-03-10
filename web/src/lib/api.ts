export type Habit = {
  id: string;
  name: string;
  created_at: string;
};

export type Recommendation = {
  name: string;
  reason: string;
};

export type StreakAnalysis = {
  longest_streak: number;
  consistency_score: number;
  break_patterns: string[];
  optimization_tips: string[];
};

const API_BASE = '/api';

export async function createHabit(name: string, description?: string): Promise<Habit> {
  const res = await fetch(`${API_BASE}/habits`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to create habit');
  return res.json();
}

export async function getHabits(): Promise<Habit[]> {
  const res = await fetch(`${API_BASE}/habits`, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to fetch habits');
  return res.json();
}

export async function markCompleted(habitId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/habits/${habitId}/check`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to mark habit completed');
}

export async function getRecommendations(): Promise<Recommendation[]> {
  const res = await fetch(`${API_BASE}/habits/recommend`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to get recommendations');
  const data = await res.json();
  return data.recommendations;
}

export async function analyzeStreak(habitId: string): Promise<StreakAnalysis> {
  const res = await fetch(`${API_BASE}/habits/analyze-streak`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ habit_id: habitId }),
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to analyze streak');
  const data = await res.json();
  return data.analysis;
}