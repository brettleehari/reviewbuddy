import type { Contribution } from '../types';

type Props = {
  contributions: Contribution[];
  handle: string;
};

export function ContributionTable({ contributions, handle }: Props) {
  if (!contributions.length) return null;

  return (
    <div className="mt-3">
      <div className="text-xs font-medium text-gray-500 mb-2">
        @{handle}'s file contributions
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left bg-gray-50">
              <th className="py-2 px-3 text-xs uppercase tracking-wide font-semibold text-gray-600">File</th>
              <th className="py-2 px-3 text-xs uppercase tracking-wide font-semibold text-gray-600 text-right">Commits</th>
              <th className="py-2 px-3 text-xs uppercase tracking-wide font-semibold text-gray-600 text-right">Lines</th>
              <th className="py-2 px-3 text-xs uppercase tracking-wide font-semibold text-gray-600 text-right">Own %</th>
              <th className="py-2 px-3 text-xs uppercase tracking-wide font-semibold text-gray-600">First</th>
              <th className="py-2 px-3 text-xs uppercase tracking-wide font-semibold text-gray-600">Last</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {contributions.map((c) => (
              <tr key={c.file}>
                <td className="py-2 px-3 font-mono text-sm text-gray-700 truncate max-w-48">
                  {c.file.split('/').pop()}
                </td>
                <td className="py-2 px-3 text-right font-mono tabular-nums">{c.commits}</td>
                <td className="py-2 px-3 text-right font-mono tabular-nums">{c.lines_authored}</td>
                <td className="py-2 px-3 text-right font-mono tabular-nums">{c.ownership_pct.toFixed(1)}%</td>
                <td className="py-2 px-3 text-sm text-gray-500">{formatDate(c.first_contribution)}</td>
                <td className="py-2 px-3 text-sm text-gray-500">{formatDate(c.last_contribution)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatDate(iso: string): string {
  if (!iso) return '-';
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
    });
  } catch {
    return iso.slice(0, 10);
  }
}
