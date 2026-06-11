'use client';

import { useEffect, useRef, useState } from 'react';
import type { LibraryVideo } from '../lib/types';

interface VideoPlayerModalProps {
  video: LibraryVideo | null;
  onClose: () => void;
}

export default function VideoPlayerModal({ video, onClose }: VideoPlayerModalProps) {
  const [copied, setCopied] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Lock scrolling on page background when modal is open
    if (video) {
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [video]);

  if (!video) return null;

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) {
      onClose();
    }
  };

  const handleCopyCaption = () => {
    if (video.instagramCaption) {
      navigator.clipboard.writeText(video.instagramCaption);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="modal-overlay" ref={overlayRef} onClick={handleOverlayClick}>
      <div className="modal-content">
        <button className="modal-close" onClick={onClose} aria-label="Close modal">
          ✕
        </button>
        <div className="modal-body">
          <div className={`modal-player-wrap ${video.format}`}>
            <video
              className="modal-video"
              src={video.downloadUrl}
              controls
              autoPlay
              playsInline
            />
          </div>
          <div className="modal-info">
            <div className="modal-title-wrap">
              <span className="tag violet" style={{ marginBottom: 8, display: 'inline-block' }}>
                {video.badge}
              </span>
              <h3 className="modal-title">{video.title}</h3>
              <p className="modal-meta">
                Topic: {video.topic} <br />
                Style: {video.style} · Duration: {video.duration}s
              </p>
            </div>

            {video.instagramCaption && (
              <div>
                <p className="modal-desc-title">Instagram Caption</p>
                <div className="modal-desc-box">{video.instagramCaption}</div>
              </div>
            )}

            <div className="modal-actions-wrap">
              {video.youtubeUrl && (
                <a className="btn-primary" href={video.youtubeUrl} target="_blank" rel="noopener noreferrer">
                  Watch on YouTube
                </a>
              )}
              <a className="btn-secondary" href={video.downloadUrl} target="_blank" rel="noopener noreferrer" download>
                Download MP4 File
              </a>
              {video.instagramExportUrl && (
                <a className="btn-secondary" href={video.instagramExportUrl} target="_blank" rel="noopener noreferrer">
                  Download Instagram Zip Package
                </a>
              )}
              {video.instagramCaption && (
                <button className="btn-secondary" onClick={handleCopyCaption}>
                  {copied ? 'Copied ✓' : 'Copy Instagram Caption'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
