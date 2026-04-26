import { useState } from 'react';
import type { FileSummary } from '../types';

type Props = {
  files: FileSummary[];
};

export function PRDiff({ files }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-900 mb-2">Files changed</h4>
      <div className="space-y-1">
        {files.map((f) => (
          <div key={f.path} className="border border-gray-100 rounded">
            <button
              type="button"
              className="w-full text-left px-3 py-2 flex items-center gap-3 hover:bg-gray-50 text-sm"
              onClick={() => setExpanded(expanded === f.path ? null : f.path)}
            >
              <span className="font-mono text-gray-700 truncate flex-1">
                {f.path}
              </span>
              <span className="text-green-600 text-xs font-mono shrink-0">
                +{f.additions}
              </span>
              <span className="text-red-500 text-xs font-mono shrink-0">
                -{f.deletions}
              </span>
              <span className="text-gray-400 text-xs">
                {expanded === f.path ? '\u25B2' : '\u25BC'}
              </span>
            </button>
            {expanded === f.path && f.patch_snippet && (
              <pre className="px-3 py-2 text-xs font-mono bg-gray-50 border-t border-gray-100 overflow-x-auto leading-relaxed whitespace-pre-wrap">
                {f.patch_snippet}
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
