export function ArchitectureNote() {
  return (
    <section className="px-6 py-12 max-w-3xl mx-auto">
      <h2 className="text-2xl font-semibold text-gray-900 mb-4">How it works</h2>
      <div className="space-y-4 text-sm text-gray-600 leading-relaxed">
        <p>
          For each file touched by a pull request, Smart-review traverses the
          git history using{' '}
          <a
            href="https://github.com/ishepard/pydriller"
            className="text-blue-600 hover:underline"
            target="_blank"
            rel="noopener"
          >
            PyDriller
          </a>{' '}
          and extracts per-author metrics: commit count, lines authored, first
          and last contribution dates, and ownership percentage.
        </p>
        <p>These metrics feed two scores per candidate:</p>
        <ul className="list-none space-y-2 pl-0">
          <li className="flex gap-3">
            <span className="shrink-0 w-24 font-semibold text-gray-900">Expertise</span>
            <span>
              Ownership share (40%), commit density relative to the top contributor
              (25%), lines authored (15%), and recency of last contribution with a
              365-day half-life (20%).
            </span>
          </li>
          <li className="flex gap-3">
            <span className="shrink-0 w-24 font-semibold text-gray-900">Seniority</span>
            <span>
              Tenure span from first contribution (45%, saturating at 4 years),
              total commits (30%), and consistency of contributions over time
              (25%).
            </span>
          </li>
        </ul>
        <p>
          Both scores are computed per file, then aggregated using a weighted
          average where files with more changes weigh more. The result is a 0-100
          score on each axis for every contributor who has touched the affected
          files.
        </p>
        <p>
          The original 2020 implementation was a{' '}
          <a
            href="https://probot.github.io/"
            className="text-blue-600 hover:underline"
            target="_blank"
            rel="noopener"
          >
            Probot
          </a>{' '}
          app that hooked into GitHub PR webhooks. This demo wraps the same
          PyDriller-based analysis in a FastAPI service that accepts arbitrary
          public PR URLs.
        </p>
      </div>
    </section>
  );
}
