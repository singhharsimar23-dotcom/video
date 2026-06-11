'use client';

import { useMemo, useState } from 'react';
import type { LibraryVideo, StudioStyle, VideoFormat } from '../lib/types';

export default function VideoLibrary({ videos }: { videos: LibraryVideo[] }) {
  const [format, setFormat] = useState<'all' | VideoFormat>('all');
  const [style, setStyle] = useState<'all' | StudioStyle>('all');
  const filtered = useMemo(() => videos
    .filter((video) => format === 'all' || video.format === format)
    .filter((video) => style === 'all' || video.style === style)
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()), [videos, format, style]);
  return (
    <>
      <div className="library-filters">
        <select className="select" style={{ maxWidth: 220 }} value={format} onChange={(event) => setFormat(event.target.value as 'all' | VideoFormat)}>
          <option value="all">All formats</option><option value="reels">Reels</option><option value="longform">Long-form</option>
        </select>
        <select className="select" style={{ maxWidth: 220 }} value={style} onChange={(event) => setStyle(event.target.value as 'all' | StudioStyle)}>
          <option value="all">All styles</option><option value="cinematic">Cinematic</option><option value="documentary">Documentary</option><option value="dreamy">Dreamy</option><option value="brutalist">Brutalist</option><option value="neon">Neon</option><option value="golden_hour">Golden Hour</option>
        </select>
      </div>
      <div className="library-grid">
        {filtered.map((video) => (
          <article className={`video-card ${video.format}`} key={video.id}>
            <div className="video-thumb">
              {video.thumbnailUrl ? <img src={video.thumbnailUrl} alt="" /> : <span className="thumb-placeholder">🎬</span>}
            </div>
            <div className="video-body">
              <div className="video-tags">
                <span className="tag violet">{video.badge}</span>
                {video.creativeScore ? <span className="tag gold">Score {video.creativeScore.score}</span> : null}
              </div>
              <h3 className="video-title">{video.title}</h3>
              <p className="video-meta">{new Date(video.date).toLocaleDateString()} · {video.duration}s · {video.style}</p>
              <div className="video-actions">
                {video.youtubeUrl ? <a className="btn-secondary" href={video.youtubeUrl} target="_blank">YouTube</a> : null}
                <a className="btn-secondary" href={video.downloadUrl} target="_blank">Download</a>
                {video.instagramExportUrl ? <a className="btn-secondary" href={video.instagramExportUrl} target="_blank">IG package</a> : null}
                {video.instagramCaption ? <button className="btn-secondary" onClick={() => navigator.clipboard?.writeText(video.instagramCaption || '')}>Copy IG caption</button> : null}
              </div>
            </div>
          </article>
        ))}
      </div>
    </>
  );
}
