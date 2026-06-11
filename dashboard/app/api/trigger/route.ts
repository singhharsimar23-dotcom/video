import { NextResponse } from 'next/server';
import { supabase } from '../../../lib/supabase';

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

    // Generate a unique jobId (64-bit safe positive random integer as string)
    const jobId = Math.floor(10000000000 + Math.random() * 90000000000).toString();

    // Insert placeholder row in Supabase
    if (supabase) {
      const { error: dbErr } = await supabase
        .from('videos')
        .insert({
          id: jobId,
          title: `Generating: ${topic || 'Surprise POV'}`,
          topic: topic || 'Surprise POV',
          date: new Date().toISOString(),
          format: format || 'reels',
          style: style || 'cinematic',
          download_url: `https://github.com/${repo}/releases/download/video-${jobId}/final_video.mp4`,
          status: 'queued',
          badge: 'Queued',
          algorithm_signals: { progress: 0, logs: ["Generation triggered from dashboard."] }
        });
      if (dbErr) {
        console.error("Failed to insert placeholder in Supabase:", dbErr);
      } else {
        console.log(`Inserted placeholder record in Supabase with jobId ${jobId}`);
      }
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
          job_id: jobId,
        }
      }),
    });

    if (!res.ok) {
      const errText = await res.text();
      // Update status to failed in Supabase if GitHub trigger failed
      if (supabase) {
        await supabase
          .from('videos')
          .update({
            status: 'failed',
            badge: 'Trigger Failed',
            algorithm_signals: { progress: 0, logs: ["GitHub Action trigger failed: " + errText] }
          })
          .eq('id', jobId);
      }
      return NextResponse.json({ error: `GitHub API error: ${errText}` }, { status: 500 });
    }

    return NextResponse.json({ success: true, jobId });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
