---
name: social-analytics
description: Analyze social performance exports and join local video summary metrics.
---

Read WORKFLOWS.md in the social-studio checkout (or SOCIAL_STUDIO_ROOT).
Run `social analytics export.csv --out jobs/performance-v2.json` on normalized CSV or JSON.
Seconds: avg_watch_time,duration. Ratios: retention_3s,completion_rate (0–1 or explicit %).
Use job or video_id for explicit summary.json joins; inspect analysis_join skipped reasons.
Report pairwise n with Pearson r; missing values and constant series stay null.
Do not infer 3s retention from average watch time or claim causality. Separate channels/languages
when interpreting associations. Preserve source exports and version output files.
