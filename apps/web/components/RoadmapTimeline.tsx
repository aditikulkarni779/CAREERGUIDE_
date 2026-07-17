// Compact milestone timeline for the dashboard (read-only).
import type { RoadmapFull } from "@/lib/api";

export function RoadmapTimeline({ roadmap }: { roadmap: RoadmapFull }) {
  const byMilestone = new Map<number, typeof roadmap.items>();
  for (const it of roadmap.items) {
    const arr = byMilestone.get(it.milestone) ?? [];
    arr.push(it);
    byMilestone.set(it.milestone, arr);
  }
  const milestones = [...byMilestone.entries()].sort((a, b) => a[0] - b[0]);
  const done = roadmap.items.filter((i) => i.status === "done").length;
  const pct = roadmap.items.length ? Math.round((done / roadmap.items.length) * 100) : 0;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-xs text-gray-500">
        <span>
          {roadmap.target_role_name} · v{roadmap.version}
        </span>
        <span>
          {done}/{roadmap.items.length} done ({pct}%)
        </span>
      </div>
      <div className="mb-3 h-1.5 w-full rounded bg-gray-200">
        <div className="h-1.5 rounded bg-green-600" style={{ width: `${pct}%` }} />
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {milestones.map(([m, items]) => {
          const hrs = items.reduce((s, i) => s + i.est_hours, 0);
          const allDone = items.every((i) => i.status === "done");
          return (
            <div
              key={m}
              className={`min-w-[120px] rounded-lg border p-2 text-xs ${
                allDone ? "border-green-300 bg-green-50" : "border-gray-200"
              }`}
            >
              <div className="mb-1 font-semibold text-gray-600">
                M{m} · {hrs}h
              </div>
              {items.slice(0, 4).map((i) => (
                <div key={i.id} className="truncate text-gray-500">
                  {i.status === "done" ? "✓ " : "• "}
                  {i.skill_name}
                </div>
              ))}
              {items.length > 4 && (
                <div className="text-gray-400">+{items.length - 4} more</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
