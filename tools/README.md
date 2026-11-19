# Hire Commons job video kit

Makes a ~20–30 second 4:5 (1080x1350) explainer video for one job: AI voice-over (free, offline Kokoro voice), burned-in captions, Hire Commons green branding. Five scenes: town hook → employer + title → pay (or schedule) → highlights → apply CTA.

## Use
```bash
bash tools/setup.sh                                    # once per session; downloads the voice from GitHub (~350 MB)
python3 tools/make_job_video.py job.json out.mp4 --preview   # writes out.png contact sheet: check for overflow
python3 tools/make_job_video.py job.json out.mp4             # writes out.mp4 and out-cover.jpg (thumbnail)
```
Write `job.json` like `job-example.json`, using only facts from the job page.
- `voice_lines`: exactly 5, in spoken spelling ("seventeen fifty", "hire commons dot com", "Connecticut").
- `captions`: the same 5 lines in normal spelling ("$17.50", "hirecommons.com", "CT").
- `pay`: "" if none listed; the third scene then shows the first chip (e.g. "Full time") and the third voice line should describe the schedule instead.
- `highlights`: 2–4 rows with a short title `t` and optional subtitle `s`.

Rendering takes about 20–40 seconds. Needs onnxruntime, numpy, scipy, Pillow, ffmpeg and the Inter font (all preinstalled in Claude's workspace).

Daily outputs go in `media/YYYY/MM/`. Public link pattern:
`https://raw.githubusercontent.com/oldmanmacken/hirecommons-media/main/media/YYYY/MM/<file>`
