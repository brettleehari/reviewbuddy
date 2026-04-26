import { ChevronRight, ChevronDown } from 'lucide-react';

type Props = {
  actualLines: string[];
  proposedLines: string[];
};

export function OutcomeContrast({ actualLines, proposedLines }: Props) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-900 mb-3">
        What happened vs. what we proposed
      </h4>
      <div className="grid md:grid-cols-[1fr_auto_1fr] gap-3 items-stretch">
        {/* What happened */}
        <div
          className="rounded-lg p-5 border"
          style={{ backgroundColor: '#fff1f2', borderColor: '#fecdd3' }}
        >
          <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: '#9f1239' }}>
            What happened
          </div>
          <div className="space-y-2.5">
            {actualLines.map((line, i) => (
              <p key={i} className="text-sm text-gray-700 leading-relaxed">{line}</p>
            ))}
          </div>
        </div>

        {/* Chevron */}
        <div className="hidden md:flex items-center justify-center px-1">
          <ChevronRight className="w-5 h-5 text-gray-300" />
        </div>
        <div className="flex md:hidden items-center justify-center py-1">
          <ChevronDown className="w-5 h-5 text-gray-300" />
        </div>

        {/* What Smart-review would have done */}
        <div
          className="rounded-lg p-5 border"
          style={{ backgroundColor: '#ecfdf5', borderColor: '#a7f3d0' }}
        >
          <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: '#065f46' }}>
            What Smart-review would have done
          </div>
          <div className="space-y-2.5">
            {proposedLines.map((line, i) => (
              <p key={i} className="text-sm text-gray-700 leading-relaxed">{line}</p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
