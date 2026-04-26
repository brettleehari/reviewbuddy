import { GitBranch, FileJson } from 'lucide-react';

export function HowItWorks() {
  return (
    <section id="how" className="px-6 py-10 max-w-6xl mx-auto">
      <h2 className="text-2xl font-semibold text-gray-900 mb-4">How it works</h2>
      <p className="text-base text-gray-700 leading-relaxed mb-10">
        Smart-review is two complementary signals applied to every pull request.
        They run in parallel, then merge into a single recommended reviewer set.
      </p>

      <div className="grid md:grid-cols-2 gap-10 mb-10">
        {/* Dynamic */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center justify-center w-7 h-7 rounded-full bg-blue-100 text-blue-700 text-xs font-bold">
              1
            </div>
            <GitBranch className="w-4 h-4 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Dynamic: git history</h3>
          </div>
          <div className="space-y-4 text-sm text-gray-700 leading-relaxed">
            <p>
              For each file touched by a pull request, Smart-review walks the git
              history and extracts per-author metrics: commit count, lines
              authored, first and last contribution dates, and ownership
              percentage. These metrics feed two scores per candidate.
            </p>
            <p>
              <strong className="text-gray-900">Expertise.</strong> Ownership
              share (40%), commit density relative to the top contributor (25%),
              lines authored (15%), and recency of last contribution with a
              365-day half-life (20%).
            </p>
            <p>
              <strong className="text-gray-900">Seniority.</strong> Tenure span
              from first contribution (45%, saturating at 4 years), total commits
              (30%), and consistency of contributions over time (25%).
            </p>
            <p>
              Both scores are computed per file, then aggregated using a weighted
              average where files with more changes weigh more. The result is a
              0-100 score on each axis for every contributor who has touched the
              affected files.
            </p>
          </div>
        </div>

        {/* Static */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center justify-center w-7 h-7 rounded-full bg-blue-100 text-blue-700 text-xs font-bold">
              2
            </div>
            <FileJson className="w-4 h-4 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Static: digitize ownership</h3>
          </div>
          <div className="space-y-4 text-sm text-gray-700 leading-relaxed">
            <p>
              Most source-control tools don't have the granularity needed to
              load-share code review across a team. Smart-review reads a small
              JSON config that captures three things the team knows about itself
              but the git history can't tell you:
            </p>
            <ul className="space-y-2">
              <li>
                <strong className="text-gray-900">LanguageExperts.</strong> A map
                from file extension to the team members who are experts in that
                language. If a PR touches a <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">.py</code> file, the Python experts are surfaced
                regardless of who recently touched that specific file.
              </li>
              <li>
                <strong className="text-gray-900">namespace-specific-reviewers.</strong> A
                list of glob patterns mapped to reviewers. Touch{' '}
                <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">auth/.*</code> and
                the auth team is surfaced.
              </li>
              <li>
                <strong className="text-gray-900">AddOnAllPRs.</strong> Reviewers
                who must be added to every PR regardless of file path. Useful for
                compliance reviewers or principal engineers who want eyes on
                everything.
              </li>
            </ul>
            <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
              <pre className="p-4 text-xs font-mono text-gray-700 overflow-x-auto leading-relaxed">{`{
  "LanguageExperts": {
    "py": ["pythonExpert1", "pythonExpert2"],
    "ts": ["typescriptExpert"],
    "go": ["goExpert"]
  },
  "namespace-specific-reviewers": [
    { "match": "auth/.*",     "reviewers": ["alice", "bob"] },
    { "match": "payments/.*", "reviewers": ["charlie"] }
  ],
  "AddOnAllPRs": ["securityLead", "principalEngineer"]
}`}</pre>
            </div>
            <p className="text-xs text-gray-500">
              Configurable per repo. Sample in the{' '}
              <a
                href="https://github.com/pitchdarkdata/MVP1/blob/main/digitize_ownership_sample.json"
                className="text-blue-600 hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                original repo
              </a>
              .
            </p>
          </div>
        </div>
      </div>

      {/* Why both halves matter */}
      <div className="bg-blue-50/50 border border-blue-200 rounded-lg p-6 mb-10">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Why both halves matter</h3>
        <p className="text-sm text-gray-700 leading-relaxed">
          Dynamic alone misses the engineer who didn't write the code but is the
          team's Python expert. Static alone misses the engineer who quietly
          authored 80% of a file two years ago. Combining them is how you
          load-share review without losing the right person.
        </p>
      </div>

      {/* Original repo description */}
      <p className="text-sm text-gray-600 leading-relaxed mb-10">
        The original 2020 implementation was a Probot app published in the GitHub
        Marketplace.
      </p>

      {/* Limitations */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Limitations</h3>
        <p className="text-sm text-gray-600 leading-relaxed">
          What this doesn't capture: review responsiveness (whether someone has
          time), domain knowledge that lives outside commits and config
          (architecture decisions in design docs, decisions made in chat threads),
          or recent context from non-public discussion. Smart-review is one signal
          among several. It's best used to surface candidates the team hadn't
          considered, not as a sole arbiter.
        </p>
      </div>
    </section>
  );
}
