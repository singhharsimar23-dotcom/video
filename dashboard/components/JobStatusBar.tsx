'use client';

import { useState } from 'react';
import type { RunStatus } from '../lib/types';
import VideoPlayerModal from './VideoPlayerModal';

export default function JobStatusBar({ status, onRetry }: { status: RunStatus; onRetry: () => void }) {
  const [showPlayer, setShowPlayer] = useState(false);
  const failed = status.rawStatus === 'completed' && status.conclusion !== 'success';

  const mockVideo = status.downloadUrl ? {
    id: 'latest',
    title: 'Latest Generated Video',
    topic: 'Generated workflow',
    date: new Date().toISOString(),
    duration: 30, // Default fallback dur
    format: 'reels' as const,
    style: 'cinematic' as const,
    badge: 'Latest Done ✓',
    thumbnailUrl: status.thumbnailUrl || '',
    youtubeUrl: status.youtubeUrl,
    downloadUrl: status.downloadUrl,
    status: 'published',
  } : null;

  return (
    <>
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
        {status.thumbnailUrl ? (
          <img
            src={status.thumbnailUrl}
            alt="Latest generated thumbnail"
            onClick={() => status.downloadUrl && setShowPlayer(true)}
            style={{
              width: 64,
              height: 64,
              borderRadius: 14,
              objectFit: 'cover',
              cursor: status.downloadUrl ? 'pointer' : 'default',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          />
        ) : null}
        {status.downloadUrl ? (
          <button className="btn-primary" onClick={() => setShowPlayer(true)}>
            Watch Video
          </button>
        ) : null}
        {status.youtubeUrl ? <a className="btn-secondary" href={status.youtubeUrl} target="_blank">YouTube</a> : null}
        {status.htmlUrl ? <a className="btn-secondary" href={status.htmlUrl} target="_blank">Actions log</a> : null}
        {failed ? <button className="btn-secondary" onClick={onRetry}>Retry</button> : null}
      </div>

      {mockVideo && (
        <VideoPlayerModal video={showPlayer ? mockVideo : null} onClose={() => setShowPlayer(false)} />
      )}
    </>
  );
}
