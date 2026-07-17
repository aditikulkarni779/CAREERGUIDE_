"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { GapHeatmap } from "@/components/GapHeatmap";
import { RoadmapTimeline } from "@/components/RoadmapTimeline";
import { ScoreGauge } from "@/components/ScoreGauge";
import { SkillRadar } from "@/components/SkillRadar";
import {
  api,
  tokenStore,
  type Readiness,
  type RoadmapFull,
  type SkillGap,
  type User,
  type UserSkill,
} from "@/lib/api";

const CATEGORY_LABEL: Record<string, string> = {
  language: "Languages",
  framework: "Frameworks",
  library: "Libraries",
  db: "Databases",
  tool: "Tools",
  cloud: "Cloud",
  ai: "AI/ML",
  soft: "Soft",
  cert: "Certs",
};

function radarAxes(skills: UserSkill[]) {
  const byCat = new Map<string, number[]>();
  for (const s of skills) {
    const arr = byCat.get(s.category) ?? [];
    arr.push(s.proficiency);
    byCat.set(s.category, arr);
  }
  return [...byCat.entries()].map(([cat, vals]) => ({
    label: CATEGORY_LABEL[cat] ?? cat,
    value: vals.reduce((a, b) => a + b, 0) / vals.length,
  }));
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [skills, setSkills] = useState<UserSkill[]>([]);
  const [gaps, setGaps] = useState<SkillGap[]>([]);
  const [roadmap, setRoadmap] = useState<RoadmapFull | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = tokenStore.access();
    if (!token) {
      router.push("/login");
      return;
    }
    Promise.all([api.me(token), api.getReadiness(), api.getSkills()])
      .then(([u, r, s]) => {
        setUser(u);
        setReadiness(r);
        setSkills(s);
      })
      .catch(() => {
        tokenStore.clear();
        router.push("/login");
      })
      .finally(() => setLoading(false));
    // best-effort: gaps + roadmap need a career goal / existing roadmap
    api.gapAnalysis().then(setGaps).catch(() => {});
    api.getRoadmap().then(setRoadmap).catch(() => {});
  }, [router]);

  if (loading) return <main className="p-8 text-gray-500">Loading…</main>;
  if (!user) return null;

  const hasProfile = skills.length > 0 || (readiness?.overall ?? 0) > 0;

  return (
    <main className="mx-auto max-w-4xl space-y-6 p-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-gray-500">{user.email}</p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/chat"
            className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white"
          >
            Chat with mentor
          </Link>
          <button
            onClick={() => {
              tokenStore.clear();
              router.push("/login");
            }}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm"
          >
            Sign out
          </button>
        </div>
      </header>

      {!hasProfile && (
        <div className="rounded-xl border border-dashed border-gray-300 p-6 text-center">
          <p className="mb-3 text-gray-600">Build your Career Twin to unlock recommendations.</p>
          <Link
            href="/onboarding"
            className="inline-block rounded-md bg-black px-5 py-2 text-sm font-medium text-white"
          >
            Start onboarding
          </Link>
        </div>
      )}

      <section className="grid gap-6 md:grid-cols-2">
        <div className="flex flex-col items-center rounded-xl border border-gray-200 p-6">
          <h2 className="mb-3 self-start text-sm font-semibold text-gray-500">
            Career Readiness
            {readiness?.target_role_slug ? ` · ${readiness.target_role_slug}` : ""}
          </h2>
          <ScoreGauge value={readiness?.overall ?? 0} label="Readiness" />
        </div>

        <div className="flex flex-col items-center rounded-xl border border-gray-200 p-6">
          <h2 className="mb-3 self-start text-sm font-semibold text-gray-500">Skill Radar</h2>
          <SkillRadar axes={radarAxes(skills)} />
        </div>
      </section>

      {roadmap && (
        <section className="rounded-xl border border-gray-200 p-6">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-500">Learning Roadmap</h2>
            <Link href="/roadmap" className="text-xs text-gray-500 underline">
              Open roadmap →
            </Link>
          </div>
          <RoadmapTimeline roadmap={roadmap} />
        </section>
      )}

      {gaps.length > 0 && (
        <section className="rounded-xl border border-gray-200 p-6">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-500">
              Skill Gaps {readiness?.target_role_slug ? `· ${readiness.target_role_slug}` : ""}
            </h2>
            {!roadmap && (
              <Link href="/roadmap" className="text-xs text-gray-500 underline">
                Generate roadmap →
              </Link>
            )}
          </div>
          <GapHeatmap gaps={gaps} />
        </section>
      )}

      <section className="rounded-xl border border-gray-200 p-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-500">Skills ({skills.length})</h2>
          <Link href="/onboarding" className="text-xs text-gray-500 underline">
            Edit
          </Link>
        </div>
        <div className="flex flex-wrap gap-2">
          {skills.map((s) => (
            <span
              key={s.skill_id}
              className="rounded-full border border-gray-200 px-3 py-1 text-xs"
            >
              {s.name} · {s.proficiency}
            </span>
          ))}
          {skills.length === 0 && <span className="text-sm text-gray-400">No skills yet.</span>}
        </div>
      </section>
    </main>
  );
}
