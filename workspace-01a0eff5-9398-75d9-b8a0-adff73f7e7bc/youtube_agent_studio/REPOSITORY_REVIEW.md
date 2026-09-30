# Candidate repository review — CreatorOps upgrade

Reviewed on 2026-09-30. This is a source/README/licensing triage, not a security audit or a validation of live publishing. None of the five repositories was cloned, installed or executed. CreatorOps was upgraded in place; this is not an AgentTube release.

## Decisions

| Candidate | Audit result | Decision |
|---|---|---|
| [pavelblank/socialai-agent](https://github.com/pavelblank/socialai-agent) | README/topic metadata claims local generation and seven platform connectors. The checked repository page has no `LICENSE` file, so no reuse rights are established. Platform claims and cost statements were not tested. | Do not copy or install. Implemented our own honest adapter matrix and copy-only distribution exports. Only YouTube upload is active. |
| [notageek88/faceless-youtube-niche-research](https://github.com/notageek88/faceless-youtube-niche-research) | MIT-licensed research skill with an evidence-led process, citations/windows/geography, explicit unknowns and instructions not to invent metrics. It is a skill/report workflow, not a verified CPM database or six-month forecasting engine. | Adapted the evidence-led method: cohort metadata, source URLs, methodology, confidence/limitations and a human-readable evidence ledger. No code was copied. |
| [ecfromthedc/youtube-growth-playbook](https://github.com/ecfromthedc/youtube-growth-playbook) | MIT-described collection of playbook documents/prompts and agent-role guidance; useful as a planning reference, not demonstrated autonomous publishing software. | Implemented a CreatorOps-native 14-day pilot playbook, experiments, calendar and analytics review loop. No code or prompt files were copied. |
| [jayadevrana/ai-youtube-documentary-engine](https://github.com/jayadevrana/ai-youtube-documentary-engine) | The fetched README identifies the project as an MT5 trading REST API client, not a documentary video engine. Its license notice states a USD $1,000/year commercial permission requirement and prohibits AI ingestion/re-creation. The title/topic listing does not match the actual README. | Rejected. Do not clone, use, ingest or recreate its code. CreatorOps' documentary workflow was implemented independently. |
| [iliasaberkane6-lab/claude-skill-media-pipeline](https://github.com/iliasabk/claude-skill-media-pipeline) | MIT media-pipeline skill. It describes a fal.ai dependency and estimates about $0.75 per six-minute video; it is not a zero-cost rendering guarantee. | Adopted the one-command workflow concept only. CreatorOps can build a package and local text/shape preview; optional voice/network provider and media costs are disclosed. No code was copied. |

## Safety and scope conclusions

- A public GitHub repository without a license is not treated as permission to copy/repackage its code.
- Multi-platform names in a README do not prove API approval, reliable connectors, free media generation or successful publishing. CreatorOps marks TikTok, Telegram, Bluesky, Mastodon, Discord and Meta as **copy-only exports**; no posts are sent to those services.
- Live publication uses the existing official YouTube OAuth/Data API path, and remains blocked until credentials and content gates are ready.
- The niche scan uses public metadata samples only. It cannot infer private retention, future RPM, competitor earnings or guaranteed six-month sustainability.
- The paid-media estimate in a candidate README is not a CreatorOps cost estimate. Actual providers, voice, visual assets, hosting, quota and account approval may cost money.
- Marketing claims such as fixed RPMs, “3× watch time,” “2× RPM,” “5× faster,” zero-cost publishing or guaranteed YPP approval are not used as verified performance facts.

## What this project added instead

- Three publication cohorts (0–30, 31–90, 91–180 days), with sample dates, query, region/language filters, video links, cohort summaries and explicit sampling limitations.
- A saved 14-day growth playbook that uses own-channel Analytics snapshots when present and otherwise says no baseline exists.
- A documentary-style package with editor-supplied research notes/links, a source log, research questions, unverified claim ledger, scene plan, timeline and captions. CreatorOps does not fetch or verify source URLs.
- One-command package + storyboard preview, with optional opt-in voice generation. Previews are not finished videos and do not clear rights or facts.
- Copy-ready social text variants and a platform adapter status matrix. Non-YouTube platforms remain export-only until an official adapter, credentials, permissions and platform-specific tests are implemented.
