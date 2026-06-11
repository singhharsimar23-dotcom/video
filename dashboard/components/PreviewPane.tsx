'use client';

import type { ScenePreview, VideoFormat } from '../lib/types';

const defaultScenes: ScenePreview[] = [
  { scene_number: 1, role: 'HOOK', duration_seconds: 4, visual_prompt: 'Start mid-action on the strongest image. No intro card. No black leader.' },
  { scene_number: 2, role: 'BUILD', duration_seconds: 9, visual_prompt: 'Escalate the relatable POV so viewers recognize themselves.' },
  { scene_number: 3, role: 'TWIST', duration_seconds: 9, visual_prompt: 'Reveal the DM-worthy insight around the 15 second gate.' },
  { scene_number: 4, role: 'PAYOFF', duration_seconds: 6, visual_prompt: 'Echo the hook visually so the ending loops into a replay.' },
];

export default function PreviewPane({ format, scenes = defaultScenes }: { format: VideoFormat; scenes?: ScenePreview[] }) {
  return (
    <div className="device-wrap">
      <div className={`device ${format}`}>
        <div className="screen">
          <span className="badge">{format === 'reels' ? '9:16 Reels / Shorts' : '16:9 Long-form'}</span>
          {scenes.slice(0, format === 'reels' ? 4 : 6).map((scene) => (
            <article className="scene-card" key={scene.scene_number}>
              <b>Scene {scene.scene_number} · {scene.role} · {scene.duration_seconds}s</b>
              <p>{scene.visual_prompt}</p>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
