// Inline-SVG circular gauge (0-100). No external chart deps.
export function ScoreGauge({ value, label }: { value: number; label: string }) {
  const r = 52;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value));
  const dash = (pct / 100) * c;
  const color = pct >= 70 ? "#16a34a" : pct >= 40 ? "#d97706" : "#dc2626";

  return (
    <div className="flex flex-col items-center">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={r} fill="none" stroke="#e5e7eb" strokeWidth="12" />
        <circle
          cx="70"
          cy="70"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c - dash}`}
          transform="rotate(-90 70 70)"
        />
        <text x="70" y="66" textAnchor="middle" className="fill-current" fontSize="28" fontWeight="700">
          {pct}
        </text>
        <text x="70" y="88" textAnchor="middle" fill="#9ca3af" fontSize="11">
          / 100
        </text>
      </svg>
      <span className="mt-1 text-sm font-medium text-gray-600">{label}</span>
    </div>
  );
}
