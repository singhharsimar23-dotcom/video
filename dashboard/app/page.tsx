import Link from 'next/link';

export default function HomePage() {
  return (
    <section className="panel">
      <p className="kicker">2026 distribution engine</p>
      <h2 className="headline">A cinematic AI studio for videos people finish, replay, and share.</h2>
      <p className="subhead">Generate Reels, Shorts, and long-form videos with hook-first scripts, loopable endings, burned-in captions, YouTube publishing, and a GitHub-backed library — all on free tiers.</p>
      <div className="card-actions" style={{ marginTop: 26 }}>
        <Link className="primary" style={{ width: 'auto', display: 'inline-block' }} href="/generate/">Open Generator</Link>
        <Link className="secondary" href="/library/">View Library</Link>
      </div>
    </section>
  );
}
