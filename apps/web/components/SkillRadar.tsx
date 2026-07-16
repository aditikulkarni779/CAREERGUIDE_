// Inline-SVG radar chart of average proficiency per skill category.
type Axis = { label: string; value: number };

export function SkillRadar({ axes }: { axes: Axis[] }) {
  const size = 260;
  const cx = size / 2;
  const cy = size / 2;
  const radius = 95;
  const n = axes.length;

  if (n < 3) {
    return (
      <div className="flex h-[260px] items-center justify-center text-sm text-gray-400">
        Add skills in 3+ categories to see your radar.
      </div>
    );
  }

  const point = (i: number, frac: number): [number, number] => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    return [cx + radius * frac * Math.cos(angle), cy + radius * frac * Math.sin(angle)];
  };

  const rings = [0.25, 0.5, 0.75, 1];
  const dataPts = axes.map((a, i) => point(i, Math.max(0, Math.min(1, a.value / 100))));
  const dataPath = dataPts.map(([x, y]) => `${x},${y}`).join(" ");

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {rings.map((ring) => (
        <polygon
          key={ring}
          points={axes.map((_, i) => point(i, ring).join(",")).join(" ")}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="1"
        />
      ))}
      {axes.map((_, i) => {
        const [x, y] = point(i, 1);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#e5e7eb" strokeWidth="1" />;
      })}
      <polygon points={dataPath} fill="rgba(37,99,235,0.25)" stroke="#2563eb" strokeWidth="2" />
      {axes.map((a, i) => {
        const [x, y] = point(i, 1.18);
        return (
          <text key={a.label} x={x} y={y} textAnchor="middle" fontSize="10" fill="#6b7280">
            {a.label}
          </text>
        );
      })}
    </svg>
  );
}
