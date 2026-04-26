import { HeaderGitHubBadge } from './HeaderGitHubBadge';

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <a href="#" className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
              <span className="text-white text-xs font-bold">SR</span>
            </div>
            <span className="text-base font-semibold text-gray-900">Smart-review</span>
          </a>
          <div className="hidden sm:flex items-center gap-4 text-sm text-gray-500">
            <a href="#demo" className="hover:text-gray-900 transition-colors">Demo</a>
            <a href="#live" className="hover:text-gray-900 transition-colors">Try it</a>
            <a href="#how" className="hover:text-gray-900 transition-colors">How it works</a>
          </div>
        </div>
        <HeaderGitHubBadge />
      </div>
    </nav>
  );
}
