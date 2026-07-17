"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  api,
  tokenStore,
  type RoadmapFull,
  type RoadmapItemFull,
  type RoadmapStatus,
  type RoadmapVersion,
} from "@/lib/api";

const STATUSES: RoadmapStatus[] = ["todo", "doing", "done", "skipped"];
const STATUS_STYLE: Record<RoadmapStatus, string> = {
  todo: "bg-gray-100 text-gray-600",
  doing: "bg-amber-100 text-amber-700",
  done: "bg-green-100 text-green-700",
  skipped: "bg-gray-100 text-gray-400 line-through",
};

export default function RoadmapPage() {
  const router = useRouter();
  const [roadmap, setRoadmap] = useState<RoadmapFull | null>(null);
  const [versions, setVersions] = useState<RoadmapVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openWhy, setOpenWhy] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const rm = await api.getRoadmap();
      setRoadmap(rm);
      setVersions(await api.getRoadmapVersions());
    } catch (e) {
      if (String(e).includes("401")) {
        tokenStore.clear();
        router.push("/login");
      }
      // 404 = no roadmap yet: leave roadmap null
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (!tokenStore.access()) {
      router.push("/login");
      return;
    }
    load();
  }, [router, load]);

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const rm = await api.generateRoadmap();
      setRoadmap(rm);
      setVersions(await api.getRoadmapVersions());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not generate roadmap");
    } finally {
      setBusy(false);
    }
  }

  async function setStatus(item: RoadmapItemFull, status: RoadmapStatus) {
    if (!roadmap) return;
    setRoadmap({
      ...roadmap,
      items: roadmap.items.map((i) => (i.id === item.id ? { ...i, status } : i)),
    });
    try {
      await api.patchRoadmapItem(item.id, status);
    } catch {
      load(); // revert to server truth on failure
    }
  }

  if (loading) return <main className="p-8 text-gray-500">Loading…</main>;

  if (!roadmap) {
    return (
      <main className="mx-auto max-w-2xl space-y-4 p-8">
        <Link href="/dashboard" className="text-sm text-gray-500 underline">
          ← Dashboard
        </Link>
        <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center">
          <p className="mb-3 text-gray-600">
            No roadmap yet. Generate one from your Career Twin and target role.
          </p>
          {error && <p className="mb-2 text-sm text-red-600">{error}</p>}
          <button
            onClick={generate}
            disabled={busy}
            className="rounded-md bg-black px-5 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {busy ? "Generating…" : "Generate roadmap"}
          </button>
          <p className="mt-2 text-xs text-gray-400">
            Requires a career goal — set it in onboarding first.
          </p>
        </div>
      </main>
    );
  }

  const byMilestone = new Map<number, RoadmapItemFull[]>();
  for (const it of roadmap.items) {
    const arr = byMilestone.get(it.milestone) ?? [];
    arr.push(it);
    byMilestone.set(it.milestone, arr);
  }
  const milestones = [...byMilestone.entries()].sort((a, b) => a[0] - b[0]);
  const done = roadmap.items.filter((i) => i.status === "done").length;
  const pct = roadmap.items.length ? Math.round((done / roadmap.items.length) * 100) : 0;
  const totalHours = roadmap.items.reduce((s, i) => s + i.est_hours, 0);

  return (
    <main className="mx-auto max-w-3xl space-y-6 p-8">
      <div className="flex items-center justify-between">
        <Link href="/dashboard" className="text-sm text-gray-500 underline">
          ← Dashboard
        </Link>
        <button
          onClick={generate}
          disabled={busy}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-xs disabled:opacity-50"
        >
          {busy ? "Re-planning…" : "Re-generate"}
        </button>
      </div>

      <header>
        <h1 className="text-2xl font-bold">
          {roadmap.target_role_name} Roadmap
          <span className="ml-2 text-sm font-normal text-gray-400">
            v{roadmap.version} · {totalHours}h · {milestones.length} milestones
          </span>
        </h1>
        <div className="mt-2 h-2 w-full rounded bg-gray-200">
          <div className="h-2 rounded bg-green-600" style={{ width: `${pct}%` }} />
        </div>
        <p className="mt-1 text-xs text-gray-500">
          {done}/{roadmap.items.length} complete ({pct}%)
        </p>
      </header>

      <div className="space-y-6">
        {milestones.map(([m, items]) => (
          <section key={m}>
            <h2 className="mb-2 text-sm font-semibold text-gray-500">
              Milestone {m} · {items.reduce((s, i) => s + i.est_hours, 0)}h
            </h2>
            <div className="space-y-2">
              {items.map((it) => (
                <div key={it.id} className="rounded-lg border border-gray-200 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <span className="font-medium">{it.skill_name}</span>
                      <span className="ml-2 text-xs text-gray-400">
                        ~{it.est_hours}h · importance {it.importance} · difficulty {it.difficulty}
                      </span>
                    </div>
                    <select
                      value={it.status}
                      onChange={(e) => setStatus(it, e.target.value as RoadmapStatus)}
                      className={`rounded-md px-2 py-1 text-xs ${STATUS_STYLE[it.status]}`}
                    >
                      {STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={() => setOpenWhy(openWhy === it.id ? null : it.id)}
                    className="mt-1 text-xs text-gray-400 underline"
                  >
                    Why this?
                  </button>
                  {openWhy === it.id && (
                    <p className="mt-1 text-xs text-gray-500">
                      {it.explanation.why} {it.explanation.impact}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>

      {versions.length > 1 && (
        <p className="text-xs text-gray-400">
          {versions.length} versions · showing latest (v{roadmap.version})
        </p>
      )}
    </main>
  );
}
