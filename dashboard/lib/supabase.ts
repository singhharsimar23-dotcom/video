import { createClient } from '@supabase/supabase-js';
import type { LibraryVideo } from './types';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

export const supabase = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

export async function getLibraryFromSupabase(): Promise<LibraryVideo[]> {
  if (!supabase) return [];
  try {
    const { data, error } = await supabase
      .from('videos')
      .select('*')
      .order('date', { ascending: false });
    if (error) throw error;
    return (data || []).map((row: any) => ({
      id: row.id,
      title: row.title,
      topic: row.topic,
      date: row.date,
      duration: row.duration,
      format: row.format,
      style: row.style,
      badge: row.badge,
      thumbnailUrl: row.thumbnail_url,
      youtubeUrl: row.youtube_url,
      downloadUrl: row.download_url,
      instagramCaption: row.instagram_caption,
      instagramExportUrl: row.instagram_export_url,
      postingStatus: row.posting_status,
      status: row.status,
      creativeScore: row.creative_score,
    }));
  } catch {
    return [];
  }
}
