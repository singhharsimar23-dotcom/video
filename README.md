# Personal AI Video Studio

A single-user AI video studio for algorithmic distribution on Instagram Reels and YouTube Shorts. It runs from GitHub Actions and GitHub Pages, uses free tiers, and avoids self-hosting, R2, paid infrastructure, and credit cards.

## 2026 distribution philosophy

Every stage is optimized for five 2026 short-form signals:

- **Watch-through rate:** no intro card, no black leader, snappy crossfades, media validation before publish.
- **Replay rate:** Reels use Scene 1 / Scene 4 loop anchors and score candidate scripts for loop echo strength.
- **DM shares:** script candidates are scored for POV, identity, and friend-share angles before spending video-generation time.
- **First-3-second retention gate:** Scene 1 starts mid-action; validation blocks black hook frames.
- **Caption completeness:** edge-tts word timing becomes burned-in ASS captions with mobile-safe styling.

## What changed after the first MVP

- The static dashboard no longer ships `NEXT_PUBLIC_GITHUB_TOKEN` or any write-capable token. It opens a prefilled GitHub Actions dispatch page instead.
- Script generation now creates multiple candidates, scores them, stores `script_candidates.json`, and selects the strongest hook/loop/share/caption package.
- Video generation uses per-model Hugging Face adapters and a deterministic Ken Burns fallback instead of one generic call shape.
- Long-form generation can be sliced with `scene_start` and `scene_end`, with `data/jobs/{run_id}.json` tracking scene completion.
- Audio generation probes TTS duration and updates `script.json` scene durations where speech would otherwise be clipped.
- `pipeline/quality_validator.py` blocks broken resolution, codec, audio, black-hook, and quiet-audio outputs before publishing.
- Release upload now happens before library update; `DOWNLOAD_URL` is confirmed before `data/library.json` is committed.
- Every publish creates an Instagram-ready export package with MP4, thumbnail, captions, descriptions, and metadata.
- Dashboard progress reads real Actions job steps where possible instead of relying only on elapsed-time estimates.
- `pipeline/benchmark.py` and `benchmarks/topics.json` provide a repeatable creative benchmark suite.

## Repo layout

```text
.github/workflows/generate_video.yml   # generation, benchmark, validation, release, library commit
.github/workflows/deploy_dashboard.yml # static GitHub Pages dashboard deployment
pipeline/                              # Gemini, video, audio, captions, validation, ffmpeg, publishing
dashboard/                             # Next.js static studio dashboard
data/library.json                      # generated video library
data/jobs/                             # resumable scene job manifests
benchmarks/topics.json                 # creative benchmark prompts
music/ambient.mp3                      # low-volume royalty-free bed
main.py                                # local/GitHub orchestrator
auth_setup.py                          # one-time YouTube OAuth refresh token helper
```

## One-time setup

1. Fork this repo and make it **public** so GitHub Actions free minutes apply.
2. Create a Gemini API key at `aistudio.google.com`.
3. Create a Hugging Face read token at `huggingface.co/settings/tokens`.
4. In Google Cloud Console, enable YouTube Data API v3 and create OAuth2 Desktop credentials.
5. Download the OAuth client JSON as `client_secret.json`, then run:

   ```bash
   pip install -r requirements.txt
   python auth_setup.py --client-secrets client_secret.json
   ```

6. Copy the printed `YOUTUBE_REFRESH_TOKEN`.
7. Pick a unique `ntfy.sh` topic string; no account is required.
8. Add repository **Actions secrets**:
   - `GEMINI_API_KEY`
   - `HF_TOKEN`
   - `YOUTUBE_REFRESH_TOKEN`
   - `YOUTUBE_CLIENT_ID`
   - `YOUTUBE_CLIENT_SECRET`
   - `NTFY_TOPIC`
9. Add dashboard build variables:
   - `NEXT_PUBLIC_GITHUB_REPO=owner/repo`
   - Optional: `NEXT_PUBLIC_GITHUB_BRANCH=main`
10. In GitHub Pages settings, set Source to **GitHub Actions**.
11. Run **Deploy Dashboard** once.
12. Visit `https://{username}.github.io/{repo-name}`. The Generate button opens a secure GitHub Actions dispatch page with your chosen inputs; no browser token is exposed.

## Local dry run

```bash
pip install -r requirements.txt
python main.py --topic "AI tools that finally make focus feel cinematic" --format reels --style cinematic --voice female
```

Without `GEMINI_API_KEY`, script generation falls back to deterministic local candidates. Without YouTube credentials, the uploader still appends a release-only library entry after a confirmed release URL is available.

## Dashboard

The dashboard is a static Next.js export deployed to GitHub Pages. It is intentionally tokenless: it reads public Actions/job status and raw `data/library.json`, then opens GitHub’s native workflow dispatch page for secure triggering.

```bash
cd dashboard
npm ci
npm run build
```

## Pipeline order

1. `pipeline/script_generator.py` writes `script_candidates.json` and selected `script.json`.
2. `pipeline/video_generator.py` writes `raw_scene_XX.mp4` sequentially and can resume scene ranges.
3. `pipeline/audio_generator.py` writes `voice_scene_XX.mp3`, `timing_scene_XX.json`, and duration-adjusted `script.json`.
4. `pipeline/caption_generator.py` writes `final_captions.ass`.
5. `pipeline/video_assembler.py` writes `final_video.mp4` using ffmpeg.
6. `pipeline/quality_validator.py` validates codec, resolution, audio, duration, and sampled black frames.
7. GitHub Releases receives `final_video.mp4` and `quality_report.json`.
8. `pipeline/youtube_uploader.py` uploads to YouTube when credentials exist, creates an Instagram package, and appends `data/library.json`.

## Benchmarks

Run script-only creative benchmarks without spending video-generation time:

```bash
python pipeline/benchmark.py --format reels --style cinematic --output data/benchmarks.json
```

## Output guarantees

- Reels: 1080×1920 H.264/AAC, burned-in captions, hook-first 4-scene structure, loop-designed ending, `#Shorts` metadata.
- Long-form: 1920×1080 H.264/AAC, 10-scene structure, burned-in captions, resumable scene generation.
- No intro card and no static outro card.
- Voice remains dominant over music.
- Metadata uses keyword-rich prose instead of hashtag dumps.
- Publish records include YouTube URL when available, confirmed Release download URL, Instagram caption, and Instagram export package.
