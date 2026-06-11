'use client';

import type { RunStatus } from '../lib/types';

export default function JobStatusBar({ status, onRetry }: { status: RunStatus; onRetry: () => void }) {
  const failed = status.rawStatus === 'completed' && status.conclusion !== 'success';
  return (
    <div className="status-bar">
      <div className="status-body">
        <div className="status-label">
          <strong>{status.label}</strong>
          <span>{Math.round(status.progress)}%</span>
        </div>
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${status.progress}%` }} />
        </div>
        <p className="status-hint">Optimized for watch-through, replay loops, DM shares, first-3-second retention, and complete captions.</p>
      </div>
      {status.thumbnailUrl ? <img src={status.thumbnailUrl} alt="Latest generated thumbnail" style={{ width: 64, height: 64, borderRadius: 14, objectFit: 'cover' }} /> : null}
      {status.youtubeUrl ? <a className="btn-secondary" href={status.youtubeUrl} target="_blank">YouTube</a> : null}
      {status.htmlUrl ? <a className="btn-secondary" href={status.htmlUrl} target="_blank">Actions log</a> : null}
      {failed ? <button className="btn-secondary" onClick={onRetry}>Retry</button> : null}
    </div>
  );
}
