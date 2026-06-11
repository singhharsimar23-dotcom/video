'use client';

import { useEffect, useState } from 'react';
import VideoLibrary from '../../components/VideoLibrary';
import { getLibrary } from '../../lib/github';
import type { LibraryVideo } from '../../lib/types';

export default function LibraryPage() {
  const [videos, setVideos] = useState<LibraryVideo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getLibrary().then((v) => {
      setVideos(v);
      setLoading(false);
    });
  }, []);

  return (
    <section className="panel">
      <p className="kicker">Library</p>
      <h2 style={{ fontSize: 44, letterSpacing: '-.05em', margin: '8px 0' }}>Published videos and release downloads.</h2>
      <p className="subhead">Sorted by date descending. Filter by format or visual style, then jump straight to YouTube or the GitHub Releases MP4.</p>
      {loading ? <p style={{ color: '#94a3b8', marginTop: 24 }}>Loading library…</p> : <VideoLibrary videos={videos} />}
    </section>
  );
}
