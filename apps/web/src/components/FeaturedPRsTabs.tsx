import { useState } from 'react';
import type { ScoredPR } from '../types';
import { PRCard } from './PRCard';

type Props = {
  prs: ScoredPR[];
};

const TAB_HINTS: Record<string, string> = {
  'rails/rails-38211': 'Regression in 12 days',
  'facebook/react-18580': 'Reverted in 25 days',
  'huggingface/transformers-8308': 'In-place mutation bug',
  'prometheus/prometheus-6643': 'Parser panic from fuzz',
  'huggingface/transformers-4874': 'Intuition got it right',
};

export function FeaturedPRsTabs({ prs }: Props) {
  const [activeIndex, setActiveIndex] = useState(0);
  const activePR = prs[activeIndex];

  return (
    <section id="demo" className="px-6 py-10 max-w-6xl mx-auto">
      <div className="flex items-baseline justify-between mb-4 flex-wrap gap-2">
        <h2 className="text-lg font-semibold text-gray-900">
          See it in action
        </h2>
        <p className="text-xs text-gray-400">
          Real PRs from popular OSS repos, closed in 2020. Same analysis the live mode runs.
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-2 mb-5 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
        {prs.map((pr, i) => {
          const key = `${pr.repo}-${pr.pr_number}`;
          const hint = TAB_HINTS[key] || '';
          const isActive = i === activeIndex;
          return (
            <button
              key={key}
              type="button"
              onClick={() => setActiveIndex(i)}
              className={`
                shrink-0 flex flex-col items-start px-4 py-2 rounded-lg text-left transition-all border
                ${isActive
                  ? 'bg-white border-gray-200 shadow-sm'
                  : 'bg-transparent border-transparent hover:bg-gray-100'
                }
              `}
            >
              <span className={`text-xs font-medium ${isActive ? 'text-gray-900' : 'text-gray-500'}`}>
                {pr.repo.split('/')[1]} #{pr.pr_number}
              </span>
              {hint && (
                <span className={`text-[10px] mt-0.5 ${isActive ? 'text-blue-600' : 'text-gray-400'}`}>
                  {hint}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Active PR content */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="bg-gray-50 border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <div>
            <span className="text-sm font-medium text-gray-900">{activePR.title}</span>
            <span className="text-xs text-gray-400 ml-3">{activePR.repo}</span>
          </div>
          <a
            href={activePR.url}
            className="text-xs text-blue-600 hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            View on GitHub
          </a>
        </div>
        <div className="p-6">
          <PRCard pr={activePR} />
        </div>
      </div>
    </section>
  );
}
