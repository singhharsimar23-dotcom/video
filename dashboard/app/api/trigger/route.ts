import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { topic, format, style, voice } = await request.json();
    const repo = process.env.NEXT_PUBLIC_GITHUB_REPO || '';
    const branch = process.env.NEXT_PUBLIC_GITHUB_BRANCH || 'main';
    const token = process.env.GITHUB_TOKEN || process.env.GH_PAT || '';

    if (!repo) {
      return NextResponse.json({ error: 'Repo not configured' }, { status: 400 });
    }

    if (!token) {
      // Return a status indicating a fallback to manual trigger is required
      return NextResponse.json({
        error: 'No GITHUB_TOKEN configured on server',
        fallback: true
      }, { status: 200 });
    }

    const res = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/generate_video.yml/dispatches`, {
      method: 'POST',
      headers: {
        Accept: 'application/vnd.github+json',
        Authorization: `Bearer ${token}`,
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ref: branch,
        inputs: {
          topic: topic || '',
          format: format || 'reels',
          style: style || 'cinematic',
          voice: voice || 'female',
        }
      }),
    });

    if (!res.ok) {
      const errText = await res.text();
      return NextResponse.json({ error: `GitHub API error: ${errText}` }, { status: 500 });
    }

    return NextResponse.json({ success: true });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
