"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  isLoggedIn,
  logout,
  getProfile,
  updateProfile,
  generatePlan,
  getPlanHistory,
} from "@/lib/api";

type Profile = {
  age?: number;
  sex?: string;
  height_cm?: number;
  weight_kg?: number;
  goal?: string;
  experience_level?: string;
  injuries?: string;
  dietary_preferences?: string;
  days_per_week?: number;
};

type PlanRecord = {
  id: number;
  plan_type: string;
  content_json: string;
  safety_notes?: string;
  created_at: string;
};

export default function Dashboard() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile>({});
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [plans, setPlans] = useState<PlanRecord[]>([]);
  const [latestResult, setLatestResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.push("/login");
      return;
    }
    getProfile().then(setProfile).catch(() => {});
    getPlanHistory().then(setPlans).catch(() => {});
  }, [router]);

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateProfile(profile);
      setProfile(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  }

  async function handleGeneratePlan() {
    setGenerating(true);
    setError(null);
    try {
      const result = await generatePlan("");
      setLatestResult(result.result);
      const history = await getPlanHistory();
      setPlans(history);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate plan");
    } finally {
      setGenerating(false);
    }
  }

  function field<K extends keyof Profile>(key: K, label: string, type = "text") {
    return (
      <div>
        <label className="text-sm text-fog/70">{label}</label>
        <input
          type={type}
          value={(profile[key] as string | number | undefined) ?? ""}
          onChange={(e) =>
            setProfile((p) => ({
              ...p,
              [key]: type === "number" ? Number(e.target.value) : e.target.value,
            }))
          }
          className="w-full mt-1 bg-panel border border-fog/20 rounded-md px-3 py-2 text-white focus:outline-none focus:border-lime"
        />
      </div>
    );
  }

  return (
    <main className="max-w-4xl mx-auto px-6 py-16">
      <div className="flex justify-between items-center mb-10">
        <h1 className="font-display text-4xl text-white">Your dashboard</h1>
        <button
          onClick={() => {
            logout();
            router.push("/login");
          }}
          className="text-sm text-fog/60 hover:text-white transition"
        >
          Log out
        </button>
      </div>

      <section className="bg-panel border border-fog/15 rounded-xl p-6 mb-10">
        <h2 className="text-white font-medium mb-4">Your profile</h2>
        <form onSubmit={handleSaveProfile} className="grid grid-cols-2 gap-4">
          {field("age", "Age", "number")}
          {field("sex", "Sex")}
          {field("height_cm", "Height (cm)", "number")}
          {field("weight_kg", "Weight (kg)", "number")}
          {field("goal", "Goal (e.g. build_muscle)")}
          {field("experience_level", "Experience level")}
          {field("days_per_week", "Days per week", "number")}
          <div className="col-span-2">{field("injuries", "Injuries / conditions")}</div>
          <div className="col-span-2">{field("dietary_preferences", "Dietary preferences")}</div>
          <div className="col-span-2">
            <button
              type="submit"
              disabled={saving}
              className="bg-lime text-charcoal font-semibold px-5 py-2 rounded-md hover:bg-lime/90 transition disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save profile"}
            </button>
          </div>
        </form>
      </section>

      <section className="mb-10">
        <button
          onClick={handleGeneratePlan}
          disabled={generating}
          className="bg-moss text-white font-semibold px-6 py-3 rounded-md hover:bg-moss/90 transition disabled:opacity-50"
        >
          {generating ? "Running your 6-agent crew..." : "Generate my plan"}
        </button>
        {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
        {generating && (
          <p className="text-fog/60 text-sm mt-3">
            Profile → workout planner → nutrition → safety review → progress check → email — this can take a minute.
          </p>
        )}
      </section>

      {latestResult && (
        <section className="bg-panel border border-lime/30 rounded-xl p-6 mb-10">
          <h2 className="text-white font-medium mb-3">Latest crew output</h2>
          <pre className="whitespace-pre-wrap text-sm text-fog/80">{latestResult}</pre>
        </section>
      )}

      <section>
        <h2 className="text-white font-medium mb-4">Plan history</h2>
        <div className="space-y-3">
          {plans.length === 0 && <p className="text-fog/50 text-sm">No plans generated yet.</p>}
          {plans.map((p) => (
            <div key={p.id} className="border border-fog/15 rounded-lg p-4 bg-panel">
              <div className="text-fog/50 text-xs mb-2">
                {new Date(p.created_at).toLocaleString()} — {p.plan_type}
              </div>
              <pre className="whitespace-pre-wrap text-sm text-fog/80 max-h-40 overflow-y-auto">
                {p.content_json}
              </pre>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
