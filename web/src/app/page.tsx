import HabitForm from '@/components/HabitForm';
import CalendarGrid from '@/components/CalendarGrid';
import Suggestions from '@/components/Suggestions';

export default function Home() {
  return (
    <main className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4 text-center">StreakLite</h1>
      <p className="text-center mb-8">
        One‑click habit streak tracker – simple, private, no‑login.
      </p>
      <HabitForm />
      <Suggestions />
      <CalendarGrid />
    </main>
  );
}