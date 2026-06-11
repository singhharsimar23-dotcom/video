'use client';

import type { ScenePreview } from '../lib/types';

export default function SceneEditor({ scenes }: { scenes: ScenePreview[] }) {
  return (
    <div className="grid">
      {scenes.map((scene) => (
        <div className="scene-card" key={scene.scene_number}>
          <b>Scene {scene.scene_number} · {scene.role}</b>
          <p>{scene.visual_prompt}</p>
        </div>
      ))}
    </div>
  );
}
