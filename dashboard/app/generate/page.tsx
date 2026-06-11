'use client';

import { useEffect, useState } from 'react';
import JobStatusBar from '../../components/JobStatusBar';
import PreviewPane from '../../components/PreviewPane';
import StudioControls from '../../components/StudioControls';
import { getLatestRun, getWorkflowDispatchUrl, pollRunStatus } from '../../lib/github';
import type { RunStatus, WorkflowInputs } from '../../lib/types';

const initialInputs: WorkflowInputs = { topic: '', format: 'reels', style: 'cinematic', voice: 'female' };

export default function GeneratePage() {
  const [inputs, setInputs] = useState<WorkflowInputs>(initialInputs);
  const [status, setStatus] = useState<RunStatus>({ rawStatus: 'idle', label: 'Ready', progress: 0 });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => pollRunStatus(status.id, setStatus), [status.id]);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const url = getWorkflowDispatchUrl(inputs);
      window.open(url, '_blank', 'noopener,noreferrer');
      setError('Secure trigger opened in GitHub Actions. This dashboard never ships a write-capable token to the browser.');
      window.setTimeout(async () => setStatus(await getLatestRun()), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not trigger workflow');
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <section className="studio-layout">
        <div className="panel">
          <p className="kicker">Generate</p>
          <h2 style={{ fontSize: 44, letterSpacing: '-.05em', margin: '8px 0 18px' }}>Retention-first video command deck.</h2>
          <StudioControls value={inputs} busy={busy} onChange={setInputs} onSubmit={submit} />
          {error ? <p style={{ color: '#fca5a5' }}>{error}</p> : null}
        </div>
        <div className="panel">
          <PreviewPane format={inputs.format} />
        </div>
      </section>
      <JobStatusBar status={status} onRetry={submit} />
    </>
  );
}
