import { FormEvent, useState } from 'react';

export interface RoleFormValues {
  jobSummary: string;
  keyResponsibilities: string;
  otherSkills: string;
  customerVolume: number;
  technicalComplexity: number;
  strictSLA: number;
  shiftWork: number;
}

interface RoleFormProps {
  onGenerate: (values: RoleFormValues) => Promise<void>;
  loading: boolean;
}

const defaultValues: RoleFormValues = {
  jobSummary: '',
  keyResponsibilities: '',
  otherSkills: '',
  customerVolume: 0,
  technicalComplexity: 0,
  strictSLA: 0,
  shiftWork: 0
};

const RoleForm = ({ onGenerate, loading }: RoleFormProps) => {
  const [values, setValues] = useState<RoleFormValues>(defaultValues);

  const handleToggle = (key: keyof RoleFormValues) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const checked = event.target.checked;
    const numericValue = checked ? 1 : 0;
    setValues((prev) => ({ ...prev, [key]: numericValue }));
  };

  const handleChange = (key: keyof RoleFormValues) => (
    event: React.ChangeEvent<HTMLTextAreaElement>
  ) => {
    setValues((prev) => ({ ...prev, [key]: event.target.value }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await onGenerate(values);
  };

  return (
    <section className="rounded-xl bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-brand">Role inputs</h2>
      <p className="text-sm text-slate-500">Describe the role in UK English. Include the phrases that matter.</p>
      <form className="mt-4 flex flex-col gap-4" onSubmit={handleSubmit}>
        <label className="flex flex-col gap-2">
          <span className="text-sm font-medium text-slate-600">Job summary</span>
          <textarea
            className="min-h-[100px] rounded-md border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-brand focus:outline-none"
            placeholder="Overview of the role, mission, customers served..."
            value={values.jobSummary}
            onChange={handleChange('jobSummary')}
            required
          />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-sm font-medium text-slate-600">Key responsibilities</span>
          <textarea
            className="min-h-[140px] rounded-md border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-brand focus:outline-none"
            placeholder="Ticket ownership, escalation steps, tooling, behaviours..."
            value={values.keyResponsibilities}
            onChange={handleChange('keyResponsibilities')}
            required
          />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-sm font-medium text-slate-600">Other skills / experience</span>
          <textarea
            className="min-h-[120px] rounded-md border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-brand focus:outline-none"
            placeholder="Certifications, desirable skills, additional notes..."
            value={values.otherSkills}
            onChange={handleChange('otherSkills')}
          />
        </label>
        <fieldset className="rounded-md border border-slate-200 p-3">
          <legend className="px-1 text-sm font-semibold text-slate-600">Context toggles</legend>
          <div className="space-y-2 text-sm text-slate-600">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={values.customerVolume > 0}
                onChange={handleToggle('customerVolume')}
              />
              High customer volume / frontline contact
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={values.technicalComplexity > 0}
                onChange={handleToggle('technicalComplexity')}
              />
              High technical complexity / troubleshooting depth
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={values.strictSLA > 0}
                onChange={handleToggle('strictSLA')}
              />
              Strict SLAs / regulatory commitments
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={values.shiftWork > 0}
                onChange={handleToggle('shiftWork')}
              />
              Shift or night work expected
            </label>
          </div>
        </fieldset>
        <button
          type="submit"
          className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white shadow hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          disabled={loading}
        >
          {loading ? 'Generating…' : 'Generate profile'}
        </button>
      </form>
    </section>
  );
};

export default RoleForm;
