export function LiveModePlaceholder() {
  return (
    <section className="px-6 py-16 max-w-5xl mx-auto">
      <div className="border border-dashed border-gray-300 rounded-xl p-8 text-center">
        <h2 className="text-xl font-semibold text-gray-900 mb-1">
          Try any public PR
        </h2>
        <p className="text-sm italic text-gray-500 mb-4">Phase 2, in development.</p>
        <p className="text-sm text-gray-600 max-w-lg mx-auto mb-4">
          Connect with GitHub, paste a public PR URL, and the backend will clone
          the repo using your token and run the same analysis in real time. Your
          API quota, not ours.
        </p>
        <p className="text-sm text-gray-500 max-w-lg mx-auto">
          Phase 2 ships an OAuth-gated FastAPI service on Render. Phase 1 (the
          four PRs above) is a complete walkthrough on its own.
        </p>
        <button
          type="button"
          disabled
          title="Phase 2 in development"
          className="mt-6 inline-flex items-center gap-2 px-4 py-2 rounded-md border border-gray-300 text-sm text-gray-400 cursor-not-allowed"
        >
          Connect with GitHub
        </button>
      </div>
    </section>
  );
}
