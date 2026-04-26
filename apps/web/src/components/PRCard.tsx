import type { ScoredPR } from '../types';
import { PRDiff } from './PRDiff';
import { OutcomeContrast } from './OutcomeContrast';
import { ReviewerComparison } from './ReviewerComparison';

type Props = {
  pr: ScoredPR;
};

export function PRCard({ pr }: Props) {
  const closedDate = pr.closed_at
    ? new Date(pr.closed_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : '';

  return (
    <div className="space-y-6">
      {/* PR header */}
      <div>
        <div className="flex items-center gap-3 text-sm text-gray-500 mb-1">
          <span>by @{pr.author}</span>
          <span>{pr.files_changed.length} files</span>
          {closedDate && <span>merged {closedDate}</span>}
          {pr.actual_reviewers.length > 0 ? (
            <span>
              reviewed by{' '}
              {pr.actual_reviewers.map((r) => `@${r.handle}`).join(', ')}
            </span>
          ) : (
            <span className="text-amber-600">no reviewer assigned</span>
          )}
        </div>
      </div>

      {/* Files changed */}
      <PRDiff files={pr.files_changed} />

      {/* Outcome contrast */}
      {pr.outcome_contrast && (
        <OutcomeContrast
          actualLines={pr.outcome_contrast.actual_lines}
          proposedLines={pr.outcome_contrast.proposed_lines}
        />
      )}

      {/* Reviewer comparison */}
      <ReviewerComparison
        actualReviewers={pr.actual_reviewers}
        bestPick={pr.best_pick}
        costOfGap={pr.cost_of_gap}
        reviewerMatch={pr.reviewer_match}
      />

      {/* PR metadata badges */}
      <div className="flex items-center gap-2 flex-wrap pt-3 border-t border-gray-100">
        {pr.best_pick && (
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
            pr.reviewer_match
              ? 'bg-emerald-50 text-emerald-700'
              : 'bg-blue-50 text-blue-700'
          }`}>
            {pr.reviewer_match
              ? `Match: @${pr.best_pick.handle} was already assigned`
              : `Best pick: @${pr.best_pick.handle}`
            }
          </span>
        )}
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
          {pr.files_changed.length} files analyzed
        </span>
      </div>
    </div>
  );
}
