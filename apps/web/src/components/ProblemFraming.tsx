export function ProblemFraming() {
  return (
    <section className="px-6 pb-8 max-w-6xl mx-auto">
      <div className="grid md:grid-cols-3 gap-4">
        <Card
          title="The wrong default"
          body="The most common mistake is the simplest one: adding the same senior maintainers to every change. It feels safe, but it creates review fatigue, and the engineer who actually wrote 80% of the file never sees the diff. When the same two people review everything, they stop reading carefully. Reviews become rubber-stamps."
        />
        <Card
          title="The right question"
          body="Code review is the last human checkpoint in software development. The question isn't who's best on the team. The question is who's best for this specific PR, right now."
        />
        <Card
          title="The fix"
          body="Score every candidate on expertise and seniority for the specific files being changed. Surface the right person, not just the default person. Load-share review across the team with data, not guesswork."
        />
      </div>
    </section>
  );
}

function Card({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600 leading-relaxed">{body}</p>
    </div>
  );
}
