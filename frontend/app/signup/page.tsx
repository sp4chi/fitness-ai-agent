"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signup } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signup(email, password, fullName);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-sm mx-auto px-6 py-24">
      <h1 className="font-display text-4xl text-white mb-8">Create your account</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-sm text-fog/70">Full name</label>
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full mt-1 bg-panel border border-fog/20 rounded-md px-3 py-2 text-white focus:outline-none focus:border-lime"
          />
        </div>
        <div>
          <label className="text-sm text-fog/70">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full mt-1 bg-panel border border-fog/20 rounded-md px-3 py-2 text-white focus:outline-none focus:border-lime"
          />
        </div>
        <div>
          <label className="text-sm text-fog/70">Password</label>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full mt-1 bg-panel border border-fog/20 rounded-md px-3 py-2 text-white focus:outline-none focus:border-lime"
          />
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-lime text-charcoal font-semibold py-2 rounded-md hover:bg-lime/90 transition disabled:opacity-50"
        >
          {loading ? "Creating account..." : "Sign up"}
        </button>
      </form>
      <p className="text-fog/60 text-sm mt-6">
        Already have an account?{" "}
        <Link href="/login" className="text-lime hover:underline">
          Log in
        </Link>
      </p>
    </main>
  );
}
