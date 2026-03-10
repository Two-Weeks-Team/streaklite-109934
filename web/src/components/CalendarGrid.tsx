import { useEffect, useState } from 'react';
import { getHabits, markCompleted } from '@/lib/api';
import { Habit } from '@/lib/api';

type DayBoxProps = {
  completed: boolean;
  date: string;
};

function DayBox({ completed, date }: DayBoxProps) {
  return (
    <div
      className={`w-5 h-5 sm:w-6 sm:h-6 rounded-sm border border-gray-300 ${completed ? 'bg-green-400' : 'bg-gray-200'}`}
      title={date}
    />
  );
}

export default function CalendarGrid() {
  const [habits, setHabits] = useState<Habit[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [grid, setGrid] = useState<boolean[]>(Array(30).fill(false));

  // Load habits on mount
  useEffect(() => {
    (async () => {
      const list = await getHabits();
      setHabits(list);
      if (list.length) setSelected(list[0].id);
    })();
  }, []);

  // Load calendar data for selected habit
  useEffect(() => {
    if (!selected) return;
    (async () => {
      try {
        const res = await fetch(`/api/habits/${selected}/calendar`, {
          credentials: 'include',
        });
        if (!res.ok) throw new Error('calendar fetch failed');
        const data: { dates: string[] } = await res.json();
        const today = new Date();
        const last30: boolean[] = [];
        for (let i = 29; i >= 0; i--) {
          const day = new Date();
          day.setDate(today.getDate() - i);
          const iso = day.toISOString().split('T')[0];
          last30.push(data.dates.includes(iso));
        }
        setGrid(last30);
      } catch (e) {
        console.error(e);
        setGrid(Array(30).fill(false));
      }
    })();
  }, [selected]);

  const handleMarkToday = async () => {
    if (!selected) return;
    await markCompleted(selected);
    // Refresh grid after marking
    const res = await fetch(`/api/habits/${selected}/calendar`, { credentials: 'include' });
    const data: { dates: string[] } = await res.json();
    const todayIso = new Date().toISOString().split('T')[0];
    const newGrid = [...grid];
    const idx = 29; // last position represents today
    newGrid[idx] = data.dates.includes(todayIso);
    setGrid(newGrid);
  };

  return (
    <section className="my-6 p-4 border rounded bg-white shadow-sm">
      <h2 className="text-xl font-semibold mb-2">Your Streak</h2>
      {habits.length === 0 && <p>No habits yet. Add one above.</p>}
      {habits.length > 0 && (
        <>
          <div className="mb-2">
            <label className="mr-2 font-medium">Habit:</label>
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="border rounded px-2 py-1"
            >
              {habits.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name}
                </option>
              ))}
            </select>
            <button
              onClick={handleMarkToday}
              className="ml-4 px-3 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700"
            >
              Mark Today Done
            </button>
          </div>
          <div className="grid grid-cols-30 gap-0.5">
            {grid.map((done, idx) => {
              const day = new Date();
              day.setDate(day.getDate() - (29 - idx));
              const iso = day.toISOString().split('T')[0];
              return <DayBox key={idx} completed={done} date={iso} />;
            })}
          </div>
        </>
      )}
    </section>
  );
}