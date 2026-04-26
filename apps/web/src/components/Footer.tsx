import { ExternalLink } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-white">
      <div className="max-w-6xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-3">
        <p className="text-xs text-gray-500">
          Designed, developed, and deployed in 2019-2020, pre-vibe-coding era.
          Happily open-sourced in 2020.
        </p>
        <div className="flex items-center gap-4 text-xs">
          <a
            href="https://www.linkedin.com/in/haripm4ai"
            className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-900 transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink className="w-3 h-3" />
            LinkedIn
          </a>
          <a
            href="https://brettleehari.github.io/Hari.me/"
            className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-900 transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink className="w-3 h-3" />
            About me
          </a>
          <a
            href="https://github.com/pitchdarkdata/MVP1"
            className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-900 transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink className="w-3 h-3" />
            Original repo
          </a>
        </div>
      </div>
    </footer>
  );
}
