import type { Reviewer } from '../types';
import { ReviewerCard } from './ReviewerCard';
import { ContributionTable } from './ContributionTable';

type Props = {
  actualReviewers: Reviewer[];
  bestPick: Reviewer | null;
  costOfGap: string;
  reviewerMatch?: boolean;
};

export function ReviewerComparison({ actualReviewers, bestPick, costOfGap, reviewerMatch }: Props) {
  if (!bestPick) return null;

  // Match case: actual reviewer IS the best pick
  if (reviewerMatch) {
    return (
      <div className="space-y-4">
        <h4 className="text-sm font-semibold text-gray-900">Reviewer scores</h4>

        <div
          className="rounded-lg p-4 border"
          style={{ backgroundColor: '#ecfdf5', borderColor: '#a7f3d0' }}
        >
          <div className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: '#065f46' }}>
            Match confirmed
          </div>
          <p className="text-sm text-gray-700">
            Smart-review's top pick (@{bestPick.handle}, combined{' '}
            {(bestPick.expertise_score + bestPick.seniority_score).toFixed(1)})
            was already assigned as a reviewer. The team got this one right.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-3">
          {actualReviewers.map((r) => (
            <div key={r.handle}>
              <ReviewerCard
                reviewer={r}
                label={r.handle === bestPick.handle ? 'Top pick (assigned)' : 'Assigned'}
                variant={r.handle === bestPick.handle ? 'best' : 'actual'}
              />
            </div>
          ))}
        </div>

        {/* Show contribution table for the top pick only */}
        <ContributionTable contributions={bestPick.contributions} handle={bestPick.handle} />
      </div>
    );
  }

  // Gap case: best pick was NOT an actual reviewer
  return (
    <div className="space-y-4">
      <h4 className="text-sm font-semibold text-gray-900">Reviewer comparison</h4>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-3">
          {actualReviewers.length > 0 ? (
            actualReviewers.map((r) => (
              <div key={r.handle}>
                <ReviewerCard reviewer={r} label="Actual reviewer" variant="actual" />
                <ContributionTable contributions={r.contributions} handle={r.handle} />
              </div>
            ))
          ) : (
            <div className="border border-gray-200 rounded-lg p-4">
              <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
                Actual reviewer
              </span>
              <p className="text-sm text-gray-500 mt-2 italic">
                No formal reviewer was assigned to this PR.
              </p>
            </div>
          )}
        </div>

        <div>
          <ReviewerCard reviewer={bestPick} label="Smart-review's pick" variant="best" />
          <ContributionTable contributions={bestPick.contributions} handle={bestPick.handle} />
        </div>
      </div>

      {costOfGap && (
        <div style={{ backgroundColor: '#fffbeb', borderColor: '#fde68a' }} className="rounded-lg p-4 border">
          <div className="text-xs font-medium uppercase tracking-widest text-amber-700 mb-2">
            Cost of the gap
          </div>
          <p className="text-sm text-amber-900 leading-relaxed">{costOfGap}</p>
        </div>
      )}
    </div>
  );
}
