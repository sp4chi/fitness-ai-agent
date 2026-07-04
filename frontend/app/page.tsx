import Link from "next/link";

export default function Home() {
  return (
    <main className="max-w-3xl mx-auto px-6 py-24">
      <p className="text-lime uppercase tracking-widest text-xs mb-4">Six agents. One coach.</p>
      <h1 className="font-display text-6xl leading-[0.95] mb-6 text-white">
        Train smarter.<br />Eat sharper.<br />Stay safe.
      </h1>
      <p className="text-fog/80 text-lg mb-10 max-w-xl">
        A crew of specialized AI agents builds your workout plan, your meal plan,
        checks it against real injury-safety guidance, tracks your progress, and
        emails you the result — all from real data, not guesses.
      </p>
      <div className="flex gap-4">
        <Link
          href="/signup"
          className="bg-lime text-charcoal font-semibold px-6 py-3 rounded-md hover:bg-lime/90 transition"
        >
          Get started
        </Link>
        <Link
          href="/login"
          className="border border-fog/30 px-6 py-3 rounded-md hover:border-fog/60 transition"
        >
          Log in
        </Link>
      </div>

      <div className="mt-20 grid grid-cols-2 gap-4 text-sm">
        {[
          ["Profile agent", "Reads your goals & constraints"],
          ["Workout planner", "Real exercises via ExerciseDB"],
          ["Nutrition agent", "Real recipes via Spoonacular"],
          ["Safety reviewer", "RAG-checked against injury guidance"],
          ["Progress tracker", "Analyzes your logged history"],
          ["Notifier", "Emails your finished plan"],
        ].map(([title, desc]) => (
          <div key={title} className="border border-fog/15 rounded-lg p-4 bg-panel">
            <div className="text-white font-medium">{title}</div>
            <div className="text-fog/60 mt-1">{desc}</div>
          </div>
        ))}
      </div>
    </main>
  );
}
