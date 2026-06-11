import type { LibraryVideo, RunStatus, WorkflowInputs } from './types';

const repo = process.env.NEXT_PUBLIC_GITHUB_REPO || '';
const branch = process.env.NEXT_PUBLIC_GITHUB_BRANCH || 'main';

function headers() {
  return {
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
  };
}

function assertRepo() {
  if (!repo || !repo.includes('/')) {
    throw new Error('Set NEXT_PUBLIC_GITHUB_REPO to owner/repo before building the dashboard.');
  }
}

export function getWorkflowDispatchUrl(inputs: WorkflowInputs) {
  assertRepo();
  const params = new URLSearchParams({
    topic: inputs.topic,
    format: inputs.format,
    style: inputs.style,
    voice: inputs.voice,
  });
  return `https://github.com/${repo}/actions/workflows/generate_video.yml?${params.toString()}`;
}

export async function triggerWorkflow(inputs: WorkflowInputs) {
  const url = getWorkflowDispatchUrl(inputs);
  throw new Error(`For security, this static GitHub Pages dashboard never exposes a workflow-write token. Open GitHub Actions to run with these inputs: ${url}`);
}

export async function getLatestRun(): Promise<RunStatus> {
  assertRepo();
  const response = await fetch(`https://api.github.com/repos/${repo}/actions/runs?per_page=1`, { headers: headers(), cache: 'no-store' });
  if (!response.ok) throw new Error(`Could not load latest run: ${response.status}`);
  const data = await response.json();
  const run = data.workflow_runs?.[0];
  if (!run) return { rawStatus: 'idle', label: 'Ready', progress: 0 };
  const latestLibrary = await getLibrary();
  const status = await mapRun(run);
  if (run.status === 'completed' && run.conclusion === 'success' && latestLibrary[0]) {
    status.thumbnailUrl = latestLibrary[0].thumbnailUrl;
    status.youtubeUrl = latestLibrary[0].youtubeUrl;
  }
  return status;
}

export async function getLibrary(): Promise<LibraryVideo[]> {
  if (!repo || !repo.includes('/')) return [];
  const raw = `https://raw.githubusercontent.com/${repo}/${branch}/data/library.json?ts=${Date.now()}`;
  const response = await fetch(raw, { cache: 'no-store' });
  if (!response.ok) return [];
  const data = await response.json();
  return Array.isArray(data) ? data.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()) : [];
}

export async function getCurrentJob() {
  if (!repo || !repo.includes('/')) return null;
  const raw = `https://raw.githubusercontent.com/${repo}/${branch}/data/current_job.json?ts=${Date.now()}`;
  const response = await fetch(raw, { cache: 'no-store' });
  if (!response.ok) return null;
  return response.json();
}

export function pollRunStatus(runId: number | undefined, onStatus: (status: RunStatus) => void) {
  let stopped = false;
  async function tick() {
    if (stopped) return;
    try {
      const status = await getLatestRun();
      onStatus(status);
    } catch (error) {
      onStatus({ rawStatus: 'error', label: error instanceof Error ? error.message : 'Polling failed', progress: 0 });
    } finally {
      if (!stopped) window.setTimeout(tick, 8000);
    }
  }
  tick();
  return () => { stopped = true; };
}

async function mapRun(run: any): Promise<RunStatus> {
  if (run.status === 'queued') return base(run, 'Queued', 8);
  if (run.status === 'completed') {
    if (run.conclusion === 'success') return base(run, 'Done ✓', 100);
    return base(run, 'Failed — check Actions log', 100);
  }
  const stepStatus = await getRunStepStatus(run.id);
  if (stepStatus) return base(run, stepStatus.label, stepStatus.progress);
  return base(run, 'Running pipeline...', 40);
}

async function getRunStepStatus(runId: number): Promise<{ label: string; progress: number } | null> {
  try {
    const response = await fetch(`https://api.github.com/repos/${repo}/actions/runs/${runId}/jobs`, { headers: headers(), cache: 'no-store' });
    if (!response.ok) return null;
    const data = await response.json();
    const steps = data.jobs?.flatMap((job: any) => job.steps || []) || [];
    const active = steps.find((step: any) => step.status === 'in_progress') || [...steps].reverse().find((step: any) => step.conclusion === 'success');
    const name = active?.name || '';
    if (/Scripting/i.test(name)) return { label: 'Scripting — choosing best hook variant', progress: 15 };
    if (/Generating clips/i.test(name)) return { label: 'Generating clips — model fallback chain active', progress: 35 };
    if (/Generating audio/i.test(name)) return { label: 'Fitting voice timing', progress: 58 };
    if (/Adding captions/i.test(name)) return { label: 'Adding captions — mute-safe', progress: 68 };
    if (/Assembling/i.test(name)) return { label: 'Assembling loopable edit', progress: 78 };
    if (/Quality validation/i.test(name)) return { label: 'Quality validation — blocking bad exports', progress: 86 };
    if (/Release|Uploading/i.test(name)) return { label: 'Uploading + packaging IG export', progress: 94 };
    return null;
  } catch {
    return null;
  }
}

function base(run: any, label: string, progress: number): RunStatus {
  return {
    id: run.id,
    rawStatus: run.status,
    conclusion: run.conclusion,
    label,
    progress,
    htmlUrl: run.html_url,
  };
}
