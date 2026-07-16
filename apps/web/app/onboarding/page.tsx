"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, tokenStore, type OnboardingPayload } from "@/lib/api";

const ROLES = [
  "ML Engineer",
  "Data Scientist",
  "AI Engineer",
  "Software Engineer",
  "Backend Developer",
  "Frontend Developer",
  "Full Stack Developer",
  "Data Engineer",
];
const LEARNING_STYLES = ["Visual", "Reading", "Hands-on", "Video"];

const STEPS = ["Education", "Skills", "Goal", "Time", "Targets", "Review"];

function csv(s: string): string[] {
  return s.split(",").map((x) => x.trim()).filter(Boolean);
}

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [degree, setDegree] = useState("");
  const [languages, setLanguages] = useState("");
  const [frameworks, setFrameworks] = useState("");
  const [careerGoal, setCareerGoal] = useState(ROLES[0]);
  const [interests, setInterests] = useState("");
  const [weeklyHours, setWeeklyHours] = useState(10);
  const [learningStyle, setLearningStyle] = useState(LEARNING_STYLES[0]);
  const [targetCompanies, setTargetCompanies] = useState("");
  const [expectedSalary, setExpectedSalary] = useState<number | "">("");
  const [github, setGithub] = useState("");

  async function submit() {
    setError(null);
    setLoading(true);
    const payload: OnboardingPayload = {
      education: degree ? [{ degree }] : [],
      languages: csv(languages),
      frameworks: csv(frameworks),
      career_goal: careerGoal,
      interests: csv(interests),
      weekly_hours: weeklyHours,
      learning_style: learningStyle,
      target_companies: csv(targetCompanies),
      expected_salary: expectedSalary === "" ? undefined : Number(expectedSalary),
      github_username: github || undefined,
    };
    try {
      await api.onboarding(payload);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Onboarding failed");
      if (String(err).includes("401")) {
        tokenStore.clear();
        router.push("/login");
      }
    } finally {
      setLoading(false);
    }
  }

  const input = "w-full rounded-md border border-gray-300 px-3 py-2 text-sm";
  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));
  const back = () => setStep((s) => Math.max(s - 1, 0));

  return (
    <main className="mx-auto max-w-lg p-6">
      <div className="mb-6">
        <div className="mb-2 flex justify-between text-xs text-gray-500">
          {STEPS.map((s, i) => (
            <span key={s} className={i === step ? "font-bold text-black" : ""}>
              {s}
            </span>
          ))}
        </div>
        <div className="h-1 w-full rounded bg-gray-200">
          <div
            className="h-1 rounded bg-black transition-all"
            style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
          />
        </div>
      </div>

      <div className="space-y-4 rounded-xl border border-gray-200 p-6 shadow-sm">
        {step === 0 && (
          <>
            <h2 className="text-lg font-semibold">Education</h2>
            <input
              className={input}
              placeholder="Highest qualification (e.g. B.Tech CSE)"
              value={degree}
              onChange={(e) => setDegree(e.target.value)}
            />
          </>
        )}
        {step === 1 && (
          <>
            <h2 className="text-lg font-semibold">Skills & Languages</h2>
            <input
              className={input}
              placeholder="Languages (comma separated: Python, SQL)"
              value={languages}
              onChange={(e) => setLanguages(e.target.value)}
            />
            <input
              className={input}
              placeholder="Frameworks (comma separated: React, FastAPI)"
              value={frameworks}
              onChange={(e) => setFrameworks(e.target.value)}
            />
            <p className="text-xs text-gray-400">Unknown skills are skipped automatically.</p>
          </>
        )}
        {step === 2 && (
          <>
            <h2 className="text-lg font-semibold">Career Goal</h2>
            <select
              className={input}
              value={careerGoal}
              onChange={(e) => setCareerGoal(e.target.value)}
            >
              {ROLES.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
            <input
              className={input}
              placeholder="Interests (comma separated: NLP, MLOps)"
              value={interests}
              onChange={(e) => setInterests(e.target.value)}
            />
          </>
        )}
        {step === 3 && (
          <>
            <h2 className="text-lg font-semibold">Time & Learning</h2>
            <label className="block text-sm text-gray-600">
              Weekly study hours: {weeklyHours}
            </label>
            <input
              type="range"
              min={1}
              max={40}
              value={weeklyHours}
              onChange={(e) => setWeeklyHours(Number(e.target.value))}
              className="w-full"
            />
            <select
              className={input}
              value={learningStyle}
              onChange={(e) => setLearningStyle(e.target.value)}
            >
              {LEARNING_STYLES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </>
        )}
        {step === 4 && (
          <>
            <h2 className="text-lg font-semibold">Targets</h2>
            <input
              className={input}
              placeholder="Target companies (comma separated)"
              value={targetCompanies}
              onChange={(e) => setTargetCompanies(e.target.value)}
            />
            <input
              className={input}
              type="number"
              placeholder="Expected salary (optional)"
              value={expectedSalary}
              onChange={(e) => setExpectedSalary(e.target.value === "" ? "" : Number(e.target.value))}
            />
            <input
              className={input}
              placeholder="GitHub username (optional)"
              value={github}
              onChange={(e) => setGithub(e.target.value)}
            />
          </>
        )}
        {step === 5 && (
          <>
            <h2 className="text-lg font-semibold">Review</h2>
            <ul className="space-y-1 text-sm text-gray-600">
              <li>Goal: {careerGoal}</li>
              <li>Languages: {csv(languages).join(", ") || "—"}</li>
              <li>Frameworks: {csv(frameworks).join(", ") || "—"}</li>
              <li>Hours/week: {weeklyHours}</li>
              <li>Learning: {learningStyle}</li>
            </ul>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </>
        )}

        <div className="flex justify-between pt-2">
          <button
            onClick={back}
            disabled={step === 0}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm disabled:opacity-40"
          >
            Back
          </button>
          {step < STEPS.length - 1 ? (
            <button
              onClick={next}
              className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white"
            >
              Next
            </button>
          ) : (
            <button
              onClick={submit}
              disabled={loading}
              className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {loading ? "Building…" : "Build my Career Twin"}
            </button>
          )}
        </div>
      </div>
    </main>
  );
}
