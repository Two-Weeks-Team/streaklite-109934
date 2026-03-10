import { useState } from 'react';
import { createHabit, getHabits } from '@/lib/api';
import { Habit } from '@/lib/api';

export default function HabitForm() {
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [habits, setHabits] = useState<Habit[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    try {
      await createHabit(name.trim());
      const fresh = await getHabits();
      setHabits(fresh);
      setName('');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="my-6 p-4 border rounded bg-white shadow-sm">
      <h2 className="text-xl font-semibold mb-2">Add a New Habit</h2>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          placeholder="e.g., Morning Yoga"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          maxLength={50}
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Saving...' : 'Add'}
        </button>
      </form>
      {habits.length > 0 && (
        <ul className="mt-4 list-disc list-inside">
          {habits.map((h) => (
            <li key={h.id}>{h.name}</li>
          ))}
        </ul>
      )}
    </section>
  );
}