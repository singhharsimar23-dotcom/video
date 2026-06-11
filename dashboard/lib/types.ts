export type VideoFormat = 'reels' | 'longform';
export type StudioStyle = 'cinematic' | 'documentary' | 'dreamy' | 'brutalist' | 'neon' | 'golden_hour';
export type Voice = 'male' | 'female';

export interface WorkflowInputs {
  topic: string;
  format: VideoFormat;
  style: StudioStyle;
  voice: Voice;
}

export interface ScenePreview {
  scene_number: number;
  role: string;
  visual_prompt: string;
  duration_seconds: number;
}

export interface LibraryVideo {
  id: string;
  title: string;
  topic: string;
  date: string;
  duration: number;
  format: VideoFormat;
  style: StudioStyle;
  badge: string;
  thumbnailUrl: string;
  youtubeUrl?: string | null;
  downloadUrl: string;
  instagramCaption?: string;
  instagramExportUrl?: string;
  postingStatus?: string;
  creativeScore?: { score: number; reasons: string[] };
  status: string;
}

export interface RunStatus {
  id?: number;
  rawStatus: string;
  conclusion?: string | null;
  label: string;
  progress: number;
  htmlUrl?: string;
  thumbnailUrl?: string;
  youtubeUrl?: string | null;
}
