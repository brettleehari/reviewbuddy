import type { ScoredPR } from '../types';
import { PRCard } from './PRCard';

type Props = {
  prs: ScoredPR[];
};

export function FeaturedPRsList({ prs }: Props) {
  return (
    <section className="px-6 py-12 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          See it in action
        </h2>
        <p className="text-gray-600">
          Real pull requests from popular open-source repos, closed in 2020.
          Same analysis the live mode runs — pre-computed so it loads instantly.
        </p>
      </div>
      <div className="space-y-4">
        {prs.map((pr) => (
          <PRCard key={`${pr.repo}-${pr.pr_number}`} pr={pr} />
        ))}
      </div>
    </section>
  );
}
