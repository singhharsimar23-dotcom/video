import VideoLibrary from '../../components/VideoLibrary';
import { getLibrary } from '../../lib/github';

export default async function LibraryPage() {
  const videos = await getLibrary();
  return (
    <section className="panel">
      <p className="kicker">Library</p>
      <h2 style={{ fontSize: 44, letterSpacing: '-.05em', margin: '8px 0' }}>Published videos and release downloads.</h2>
      <p className="subhead">Sorted by date descending. Filter by format or visual style, then jump straight to YouTube or the GitHub Releases MP4.</p>
      <VideoLibrary videos={videos} />
    </section>
  );
}
