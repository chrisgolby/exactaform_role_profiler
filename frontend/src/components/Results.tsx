import { AttributeResponse, ProfilePayload } from '../App';

interface ResultsProps {
  profile: ProfilePayload | null;
  loading: boolean;
  error: string | null;
}

const SectionTitle = ({ title, subtitle }: { title: string; subtitle?: string }) => (
  <div className="flex flex-col">
    <h2 className="text-lg font-semibold text-brand">{title}</h2>
    {subtitle ? <p className="text-sm text-slate-500">{subtitle}</p> : null}
  </div>
);

const ScoreBreakdown = ({ attribute }: { attribute: AttributeResponse }) => (
  <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-600">
    {Object.entries(attribute.score_breakdown).map(([key, value]) => (
      <div key={key} className="flex justify-between">
        <dt className="capitalize">{key.replace('_', ' ')}</dt>
        <dd className="font-medium text-slate-800">{value.toFixed(2)}</dd>
      </div>
    ))}
  </dl>
);

const EvidencePills = ({ evidence }: { evidence: string[] }) => (
  <div className="flex flex-wrap gap-2">
    {evidence.map((item) => (
      <span key={item} className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600">
        {item}
      </span>
    ))}
  </div>
);

const AttributeCard = ({ attribute }: { attribute: AttributeResponse }) => (
  <div className="rounded-lg border border-slate-200 p-4 shadow-sm">
    <div className="flex items-start justify-between">
      <div>
        <h3 className="text-base font-semibold text-brand">{attribute.name}</h3>
        <p className="text-xs uppercase tracking-wide text-slate-500">{attribute.domain}</p>
      </div>
      <span className="text-sm font-semibold text-brand">{attribute.score.toFixed(2)}</span>
    </div>
    <div className="mt-3 space-y-3 text-sm text-slate-600">
      <p>{attribute.behaviour_pack.why_it_matters}</p>
      <div>
        <p className="font-medium text-slate-700">Risk if overused</p>
        <p>{attribute.behaviour_pack.risk_if_overused}</p>
      </div>
      <div>
        <p className="font-medium text-slate-700">Mitigation / probe</p>
        <p>{attribute.behaviour_pack.mitigation_and_probe}</p>
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        <div>
          <p className="font-medium text-slate-700">Do well indicators</p>
          <ul className="list-disc pl-4">
            {attribute.behaviour_pack.do_well_indicators.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="font-medium text-slate-700">Anti-patterns</p>
          <ul className="list-disc pl-4">
            {attribute.behaviour_pack.anti_patterns.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
      {attribute.evidence.length > 0 ? (
        <div>
          <p className="font-medium text-slate-700">Evidence phrases</p>
          <EvidencePills evidence={attribute.evidence} />
        </div>
      ) : null}
      <div>
        <p className="font-medium text-slate-700">Score blend</p>
        <ScoreBreakdown attribute={attribute} />
      </div>
    </div>
  </div>
);

const Placeholder = ({ loading }: { loading: boolean }) => (
  <div className="flex h-full flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
    {loading ? 'Analysing the job description…' : 'Results will appear here once generated.'}
  </div>
);

const ExplainabilityPanel = ({ profile }: { profile: ProfilePayload }) => (
  <section className="rounded-xl border border-slate-200 p-4">
    <SectionTitle title="Explainability" subtitle="Score blend per selection" />
    <div className="mt-3 space-y-3 text-sm text-slate-600">
      {profile.strengths.map((item) => (
        <div key={`exp-strength-${item.name}`} className="rounded-md bg-slate-50 p-3">
          <p className="text-sm font-semibold text-brand">{item.name}</p>
          <ScoreBreakdown attribute={item} />
          {item.rules_fired.length > 0 ? (
            <p className="mt-1 text-xs text-slate-500">Rules: {item.rules_fired.join('; ')}</p>
          ) : null}
        </div>
      ))}
      {profile.values.map((item) => (
        <div key={`exp-value-${item.name}`} className="rounded-md bg-white p-3">
          <p className="text-sm font-semibold text-brand">{item.name}</p>
          <ScoreBreakdown attribute={item} />
          {item.rules_fired.length > 0 ? (
            <p className="mt-1 text-xs text-slate-500">Rules: {item.rules_fired.join('; ')}</p>
          ) : null}
        </div>
      ))}
    </div>
  </section>
);

const Results = ({ profile, loading, error }: ResultsProps) => {
  if (loading) {
    return (
      <section className="rounded-xl bg-white p-6 shadow-sm">
        <SectionTitle title="Strengths & values" />
        <Placeholder loading={true} />
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-xl bg-white p-6 shadow-sm">
        <SectionTitle title="Strengths & values" />
        <p className="mt-4 text-sm text-red-600">{error}</p>
      </section>
    );
  }

  if (!profile) {
    return (
      <section className="rounded-xl bg-white p-6 shadow-sm">
        <SectionTitle title="Strengths & values" />
        <Placeholder loading={false} />
      </section>
    );
  }

  return (
    <section className="flex flex-col gap-4">
      <div className="rounded-xl bg-white p-6 shadow-sm">
        <SectionTitle title="Top CliftonStrengths" subtitle="Ranked blend with behaviour guides" />
        <div className="mt-4 grid gap-4">
          {profile.strengths.map((attribute) => (
            <AttributeCard key={attribute.name} attribute={attribute} />
          ))}
        </div>
      </div>
      <div className="rounded-xl bg-white p-6 shadow-sm">
        <SectionTitle title="Top Values" subtitle="Signals aligned to the role" />
        <div className="mt-4 grid gap-4">
          {profile.values.map((attribute) => (
            <AttributeCard key={attribute.name} attribute={attribute} />
          ))}
        </div>
      </div>
      <div className="rounded-xl bg-white p-6 shadow-sm">
        <SectionTitle title="Behavioural interview prompts" />
        <ol className="mt-4 list-decimal space-y-3 pl-6 text-sm text-slate-600">
          {profile.interview_questions.map((item) => (
            <li key={item.question}>
              <p className="font-medium text-brand">{item.question}</p>
              <p className="text-xs text-slate-500">Probe: {item.probe}</p>
            </li>
          ))}
        </ol>
      </div>
      <ExplainabilityPanel profile={profile} />
    </section>
  );
};

export default Results;
