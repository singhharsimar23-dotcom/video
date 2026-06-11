import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const runId = searchParams.get('runId');
    const repo = process.env.NEXT_PUBLIC_GITHUB_REPO || '';
    const token = process.env.GITHUB_TOKEN || process.env.GH_PAT || '';

    if (!repo) {
      return NextResponse.json({ error: 'Repo not configured' }, { status: 400 });
    }

    const headers: Record<string, string> = {
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
    };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    if (runId) {
      // Fetch specific run jobs
      const response = await fetch(`https://api.github.com/repos/${repo}/actions/runs/${runId}/jobs`, { headers, cache: 'no-store' });
      if (!response.ok) {
        return NextResponse.json({ error: `GitHub API error: ${response.statusText}` }, { status: response.status });
      }
      const data = await response.json();
      return NextResponse.json(data);
    } else {
      // Fetch latest run list
      const response = await fetch(`https://api.github.com/repos/${repo}/actions/runs?per_page=1`, { headers, cache: 'no-store' });
      if (!response.ok) {
        return NextResponse.json({ error: `GitHub API error: ${response.statusText}` }, { status: response.status });
      }
      const data = await response.json();
      return NextResponse.json(data);
    }
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
