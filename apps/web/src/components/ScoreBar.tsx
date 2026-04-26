type Props = {
  label: string;
  score: number;
  maxScore?: number;
  color?: 'blue' | 'gray';
};

export function ScoreBar({ label, score, maxScore = 100, color = 'blue' }: Props) {
  const pct = Math.min((score / maxScore) * 100, 100);
  const bgClass = color === 'blue' ? 'bg-blue-600' : 'bg-gray-400';

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium text-gray-600">{label}</span>
        <span className="text-sm font-mono font-semibold tabular-nums text-gray-900">
          {score.toFixed(1)}
        </span>
      </div>
      <div className="w-full h-1.5 rounded-full bg-gray-100 overflow-hidden">
        <div
          className={`h-full rounded-full ${bgClass} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
