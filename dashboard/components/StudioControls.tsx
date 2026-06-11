'use client';

import type { StudioStyle, VideoFormat, Voice, WorkflowInputs } from '../lib/types';

const styles: { key: StudioStyle; label: string }[] = [
  { key: 'cinematic', label: 'Cinematic' },
  { key: 'documentary', label: 'Documentary' },
  { key: 'dreamy', label: 'Dreamy' },
  { key: 'brutalist', label: 'Brutalist' },
  { key: 'neon', label: 'Neon' },
  { key: 'golden_hour', label: 'Golden Hour' },
];

export default function StudioControls({ value, busy, onChange, onSubmit }: { value: WorkflowInputs; busy: boolean; onChange: (next: WorkflowInputs) => void; onSubmit: () => void }) {
  const update = <K extends keyof WorkflowInputs>(key: K, next: WorkflowInputs[K]) => onChange({ ...value, [key]: next });
  return (
    <div className="controls">
      <div className="field">
        <label>Format</label>
        <div className="toggle">
          <button className={value.format === 'reels' ? 'active' : ''} onClick={() => update('format', 'reels' as VideoFormat)}>REELS 9:16</button>
          <button className={value.format === 'longform' ? 'active' : ''} onClick={() => update('format', 'longform' as VideoFormat)}>LONG-FORM 16:9</button>
        </div>
      </div>
      <div className="field">
        <label>Topic</label>
        <textarea className="textarea" value={value.topic} onChange={(event) => update('topic', event.target.value)} placeholder="Describe a POV, identity moment, useful insight, or leave blank for Surprise me." />
        <button className="secondary" style={{ marginTop: 8 }} onClick={() => update('topic', '')}>Surprise me</button>
      </div>
      <div className="field">
        <label>Style</label>
        <div className="style-grid">
          {styles.map((style) => <button key={style.key} className={`style-btn ${value.style === style.key ? 'active' : ''}`} onClick={() => update('style', style.key)}>{style.label}</button>)}
        </div>
      </div>
      <div className="field">
        <label>Voice</label>
        <div className="voice-row">
          <button className={`voice-btn ${value.voice === 'male' ? 'active' : ''}`} onClick={() => update('voice', 'male' as Voice)}>Male<br /><small>Andrew</small></button>
          <button className={`voice-btn ${value.voice === 'female' ? 'active' : ''}`} onClick={() => update('voice', 'female' as Voice)}>Female<br /><small>Ava</small></button>
        </div>
      </div>
      <button className="primary" disabled={busy} onClick={onSubmit}>{busy ? 'Generating…' : 'Generate Video'}</button>
    </div>
  );
}
