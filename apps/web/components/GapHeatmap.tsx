// Skill-gap heatmap: current vs target proficiency per required skill.
import type { SkillGap } from "@/lib/api";

function barColor(gap: number): string {
  if (gap >= 60) return "#dc2626"; // large gap
  if (gap >= 30) return "#d97706";
  return "#16a34a";
}

export function GapHeatmap({ gaps }: { gaps: SkillGap[] }) {
  if (gaps.length === 0) {
    return <p className="text-sm text-gray-400">No gaps — you cover this role’s core skills. 🎉</p>;
  }
  return (
    <div className="space-y-2">
      {gaps.map((g) => (
        <div key={g.skill_slug} className="flex items-center gap-3 text-xs">
          <span className="w-32 shrink-0 truncate" title={g.skill_name}>
            {g.skill_name}
          </span>
          <div className="relative h-3 flex-1 rounded bg-gray-100">
            {/* target marker */}
            <div
              className="absolute top-0 h-3 w-px bg-gray-400"
              style={{ left: `${g.target}%` }}
              title={`target ${g.target}`}
            />
            {/* current fill */}
            <div
              className="h-3 rounded"
              style={{ width: `${g.current}%`, backgroundColor: barColor(g.gap) }}
            />
          </div>
          <span className="w-16 shrink-0 text-right text-gray-400">
            {g.current}→{g.target}
          </span>
          <span className="w-10 shrink-0 text-right text-gray-400">{g.est_hours}h</span>
        </div>
      ))}
    </div>
  );
}
