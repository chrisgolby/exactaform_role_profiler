import { FormEvent, useEffect, useRef, useState } from 'react';
import { AskResponsePayload } from '../App';

export interface AskMessage {
  author: 'user' | 'codex';
  content: string;
  metadata?: {
    attributes?: Array<Record<string, unknown>>;
    changes?: Array<Record<string, unknown>>;
  };
}

interface AskCodexProps {
  disabled: boolean;
  onAsk: (question: string) => Promise<AskResponsePayload | null>;
  messages: AskMessage[];
  onMessagesChange: (items: AskMessage[]) => void;
}

const AskCodex = ({ disabled, onAsk, messages, onMessagesChange }: AskCodexProps) => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!input.trim() || disabled) return;
    const question = input.trim();
    const userMessage: AskMessage = { author: 'user', content: question };
    const nextMessages = [...messages, userMessage];
    onMessagesChange(nextMessages);
    setInput('');
    setLoading(true);
    const response = await onAsk(question);
    if (response) {
      const codexMessage: AskMessage = {
        author: 'codex',
        content: response.answer,
        metadata: {
          attributes: response.attributes,
          changes: response.changes
        }
      };
      onMessagesChange([...nextMessages, codexMessage]);
    } else {
      onMessagesChange([
        ...nextMessages,
        { author: 'codex', content: 'I could not process that request just now.' }
      ]);
    }
    setLoading(false);
  };

  return (
    <section className="flex h-full flex-col rounded-xl bg-white shadow-sm">
      <header className="border-b border-slate-200 p-4">
        <h2 className="text-lg font-semibold text-brand">Ask Codex</h2>
        <p className="text-xs text-slate-500">Ask “why” questions or test what-if scenarios such as “increase technical troubleshooting”.</p>
      </header>
      <div ref={containerRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4 text-sm text-slate-600">
        {messages.length === 0 ? (
          <p className="text-xs text-slate-500">Codex will respond here once you ask a question.</p>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`rounded-md px-3 py-2 ${message.author === 'user' ? 'bg-brand text-white ml-auto max-w-[85%]' : 'bg-slate-100 text-slate-700 mr-auto max-w-[90%]'}`}>
              <p className="text-xs uppercase tracking-wide opacity-70">{message.author === 'user' ? 'You' : 'Codex'}</p>
              <p className="mt-1 text-sm">{message.content}</p>
              {message.metadata?.attributes && message.metadata.attributes.length > 0 ? (
                <div className="mt-2 space-y-1 text-xs">
                  <p className="font-semibold">Attributes referenced</p>
                  <ul className="list-disc pl-4">
                    {message.metadata.attributes.map((item, i) => (
                      <li key={`attr-${i}`}>{JSON.stringify(item)}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {message.metadata?.changes && message.metadata.changes.length > 0 ? (
                <div className="mt-2 space-y-1 text-xs">
                  <p className="font-semibold">Profile adjustments</p>
                  <ul className="list-disc pl-4">
                    {message.metadata.changes.map((item, i) => (
                      <li key={`change-${i}`}>{JSON.stringify(item)}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ))
        )}
      </div>
      <form onSubmit={handleSubmit} className="border-t border-slate-200 p-4">
        <label className="flex items-center gap-2">
          <input
            className="flex-1 rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={disabled ? 'Generate a profile to start the chat.' : 'Ask Codex anything about the profile…'}
            disabled={disabled || loading}
          />
          <button
            type="submit"
            className="rounded-md bg-brand px-3 py-2 text-sm font-medium text-white shadow disabled:bg-slate-300"
            disabled={disabled || loading}
          >
            {loading ? 'Sending…' : 'Send'}
          </button>
        </label>
      </form>
    </section>
  );
};

export default AskCodex;
