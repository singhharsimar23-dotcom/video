'use client';

import type { RunStatus } from '../lib/types';

export default function JobStatusBar({ status, onRetry }: { status: RunStatus; onRetry: () => void }) {
  const failed = status.rawStatus === 'completed' && status.conclusion !== 'success';
  return (
    <div className="jobbar">
      <div style={{ flex: 1 }}>
        <div className="job-top"><strong>{status.label}</strong><span>{Math.round(status.progress)}%</span></div>
        <div className="progress"><div style={{ width: `${status.progress}%` }} /></div>
        <small>Optimized for watch-through, replay loops, DM shares, first-3-second retention, and complete captions.</small>
      </div>
      {status.thumbnailUrl ? <img src={status.thumbnailUrl} alt="Latest generated thumbnail" style={{ width: 64, height: 64, borderRadius: 14, objectFit: 'cover' }} /> : null}
      {status.youtubeUrl ? <a className="secondary" href={status.youtubeUrl} target="_blank">YouTube</a> : null}
      {status.htmlUrl ? <a className="secondary" href={status.htmlUrl} target="_blank">Actions log</a> : null}
      {failed ? <button className="secondary" onClick={onRetry}>Retry</button> : null}
    </div>
  );
}
