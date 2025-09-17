import { useCallback, useState } from 'react';
import axios from 'axios';
import RoleForm, { RoleFormValues } from './components/RoleForm';
import Results from './components/Results';
import AskCodex, { AskMessage } from './components/AskCodex';

export interface AttributeBehaviour {
  why_it_matters: string;
  risk_if_overused: string;
  mitigation_and_probe: string;
  do_well_indicators: string[];
  anti_patterns: string[];
}

export interface AttributeResponse {
  name: string;
  domain: string;
  score: number;
  score_breakdown: Record<string, number>;
  evidence: string[];
  best_exemplar?: string | null;
  rules_fired: string[];
  behaviour_pack: AttributeBehaviour;
}

export interface InterviewQuestion {
  question: string;
  probe: string;
}

export interface ProfilePayload {
  strengths: AttributeResponse[];
  values: AttributeResponse[];
  interview_questions: InterviewQuestion[];
  explainability: Record<string, unknown>;
}

export interface AskResponsePayload {
  answer: string;
  attributes: Array<Record<string, unknown>>;
  changes?: Array<Record<string, unknown>>;
  profile?: ProfilePayload;
}

function App() {
  const [profile, setProfile] = useState<ProfilePayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<AskMessage[]>([]);
  const [lastInputs, setLastInputs] = useState<RoleFormValues | null>(null);

  const handleGenerate = useCallback(async (values: RoleFormValues) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post<ProfilePayload>('/profile/generate', {
        job_summary: values.jobSummary,
        key_responsibilities: values.keyResponsibilities,
        other_skills: values.otherSkills,
        context: {
          customer_volume: values.customerVolume,
          technical_complexity: values.technicalComplexity,
          strict_sla: values.strictSLA,
          shift_work: values.shiftWork
        }
      });
      setProfile(response.data);
      setLastInputs(values);
      setMessages([]);
    } catch (err) {
      setError('Unable to generate the profile. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleAsk = useCallback(async (question: string) => {
    if (!lastInputs) {
      setError('Provide role details before asking Codex.');
      return null;
    }
    try {
      const response = await axios.post<AskResponsePayload>('/codex/ask', {
        question,
        job_summary: lastInputs.jobSummary,
        key_responsibilities: lastInputs.keyResponsibilities,
        other_skills: lastInputs.otherSkills,
        context: {
          customer_volume: lastInputs.customerVolume,
          technical_complexity: lastInputs.technicalComplexity,
          strict_sla: lastInputs.strictSLA,
          shift_work: lastInputs.shiftWork
        },
        current_profile: profile
      });
      if (response.data.profile) {
        setProfile(response.data.profile);
      }
      return response.data;
    } catch (err) {
      setError('Ask Codex is unavailable just now.');
      return null;
    }
  }, [lastInputs, profile]);

  const handleMessagesChange = useCallback((items: AskMessage[]) => {
    setMessages(items);
  }, []);

  const handleCopyJson = useCallback(() => {
    if (!profile) return;
    navigator.clipboard.writeText(JSON.stringify(profile, null, 2));
  }, [profile]);

  const handleExportPdf = useCallback(() => {
    window.print();
  }, []);

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-2xl font-semibold text-brand">Exactaform Role Profiler</h1>
            <p className="text-sm text-slate-500">Generate CliftonStrengths, values, interview probes, and Codex insights from a job description.</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCopyJson}
              className="rounded-md bg-brand text-white px-3 py-2 text-sm shadow-sm hover:bg-slate-800 disabled:bg-slate-300"
              disabled={!profile}
            >
              Copy JSON
            </button>
            <button
              onClick={handleExportPdf}
              className="rounded-md border border-brand text-brand px-3 py-2 text-sm shadow-sm hover:bg-brand hover:text-white"
            >
              Export PDF
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[1.1fr_2fr_1.2fr]">
        <RoleForm onGenerate={handleGenerate} loading={loading} />
        <Results profile={profile} loading={loading} error={error} />
        <AskCodex
          disabled={!profile}
          onAsk={handleAsk}
          messages={messages}
          onMessagesChange={handleMessagesChange}
        />
      </main>
    </div>
  );
}

export default App;
