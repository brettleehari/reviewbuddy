import type { Reviewer } from '../types';
import { ScoreBar } from './ScoreBar';

type Props = {
  reviewer: Reviewer;
  label: string;
  variant: 'actual' | 'best';
};

export function ReviewerCard({ reviewer, label, variant }: Props) {
  const borderClass = variant === 'best' ? 'border-blue-200 bg-blue-50/50' : 'border-gray-200';

  return (
    <div className={`border rounded-lg p-4 ${borderClass}`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
            {label}
          </span>
          <div className="flex items-center gap-2 mt-1">
            <a
              href={`https://github.com/${reviewer.handle}`}
              className="text-sm font-semibold text-gray-900 hover:text-blue-600"
              target="_blank"
              rel="noopener"
            >
              @{reviewer.handle}
            </a>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500">Combined</div>
          <div className="text-lg font-mono font-bold text-gray-900">
            {(reviewer.expertise_score + reviewer.seniority_score).toFixed(1)}
          </div>
        </div>
      </div>
      <div className="space-y-2">
        <ScoreBar
          label="Expertise"
          score={reviewer.expertise_score}
          color={variant === 'best' ? 'blue' : 'gray'}
        />
        <ScoreBar
          label="Seniority"
          score={reviewer.seniority_score}
          color={variant === 'best' ? 'blue' : 'gray'}
        />
      </div>
    </div>
  );
}
