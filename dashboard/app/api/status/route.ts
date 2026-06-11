import { NextResponse } from 'next/server';
import { supabase } from '../../../lib/supabase';

function mapRowToStatus(row: any): any {
  const signals = row.algorithm_signals || {};
  const progress = typeof signals.progress === 'number' ? signals.progress : 0;
  const logs = Array.isArray(signals.logs) ? signals.logs : [];
  const lastLog = logs[logs.length - 1] || 'Processing...';

  if (row.status === 'published' || row.status === 'release-only' || row.status === 'completed') {
    return {
      id: row.id,
      rawStatus: 'completed',
      conclusion: 'success',
      label: 'Done ✓',
      progress: 100,
      thumbnailUrl: row.thumbnail_url,
      youtubeUrl: row.youtube_url,
      downloadUrl: row.download_url,
    };
  }

  if (row.status === 'failed') {
    return {
      id: row.id,
      rawStatus: 'completed',
      conclusion: 'failure',
      label: lastLog || 'Failed',
      progress: 100,
    };
  }

  return {
    id: row.id,
    rawStatus: row.status || 'in_progress',
    label: lastLog,
    progress: progress,
    downloadUrl: row.download_url,
  };
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const runId = searchParams.get('runId');
    const jobId = searchParams.get('jobId');
    const repo = process.env.NEXT_PUBLIC_GITHUB_REPO || '';
    const token = process.env.GITHUB_TOKEN || process.env.GH_PAT || '';

    // If jobId is provided, check Supabase first
    if (jobId && supabase) {
      const { data, error } = await supabase
        .from('videos')
        .select('*')
        .eq('id', jobId)
        .maybeSingle();
      if (!error && data) {
        return NextResponse.json(mapRowToStatus(data));
      }
    }

    // If no jobId, but we have supabase, check if there's any active/processing job in the database
    if (!runId && supabase) {
      const { data, error } = await supabase
        .from('videos')
        .select('*')
        .in('status', ['queued', 'processing'])
        .order('date', { ascending: false })
        .limit(1)
        .maybeSingle();
      
      if (!error && data) {
        return NextResponse.json(mapRowToStatus(data));
      }
    }

    // Fall back to GitHub API
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
