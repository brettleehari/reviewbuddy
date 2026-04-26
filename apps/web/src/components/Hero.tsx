export function Hero() {
  return (
    <section className="px-6 pt-12 pb-8 max-w-6xl mx-auto">
      <div className="max-w-3xl">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-medium mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
          Pre-vibe-coding era (2019-2020)
        </div>
        <p className="text-lg font-semibold text-gray-500 mb-1">Smart-review</p>
        <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-gray-900 mb-4">
          Pick the right code reviewer.<br />
          Every time.
        </h1>
        <p className="text-base text-gray-600 leading-relaxed max-w-2xl">
          Smart-review combines what the team explicitly knows about itself
          (language experts, namespace owners, mandatory reviewers) with what
          the git history reveals. It surfaces who should have reviewed the PR,
          who actually did, and what the gap likely cost.
        </p>
        <p className="text-xs text-gray-400 mt-3">
          Designed, developed, and deployed in 2019-2020. Happily open-sourced in 2020.
        </p>
      </div>
    </section>
  );
}
