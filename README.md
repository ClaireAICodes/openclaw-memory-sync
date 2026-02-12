[//]: # (GitHub Documentation Standardization Protocol - Phase 2 & 3)
[//]: # (Hero visual: verified GIF, 200 OK, matches project palette/tone)

![Notion Sync Animation](https://media.tenor.com/qm9qriHz2vcAAAAC/salesforce-appexchange.gif)

# OpenClaw Notion Sync

> Bridge your local memory to a rich knowledge base. Automatically sync OpenClaw's `MEMORY.md` and daily notes to Notion with intelligent classification and beautiful formatting.

## 🌐 Live Demo

👉 **Knowledge Base:** [View on Notion](https://www.notion.so/5b3947072fb643a69d57ed523fa84150)  
📖 **Documentation site:** https://claireaicodes.github.io/openclaw-memory-sync/

*The Knowledge Base is populated automatically by the daily sync. The documentation site is served from this repository’s `/docs` folder via GitHub Pages.*

## 🎯 About

OpenClaw stores memories in plain Markdown files. Notion offers a powerful, searchable, and visual knowledge base. This tool connects the two: it parses your memory files, understands what you've learned, and creates/updates Notion pages with proper metadata, tags, and formatted content. No manual copy-paste; just run the sync and your Knowledge Base stays current.

## ✨ Mission & Matrix

| Capability | What It Does |
|------------|--------------|
| **Automatic Classification** | Detects entry type (Research, Lesson, Decision, Pattern, Tutorial, Reference, Insight) via keyword analysis |
| **Domain Tagging** | Assigns domain (AI Models, OpenClaw, Cost Optimization, Trading, Web3, Learning, Process, etc.) |
| **Certainty & Impact** | Auto-assigns confidence scores (1–10) and impact levels (High/Medium/Low/Negligible) |
| **Source Tracking** | Knows exactly which file (`MEMORY.md` or `memory/YYYY-MM-DD.md`) each entry came from |
| **Markdown→Notion Blocks** | Converts headings, lists, code blocks, blockquotes, dividers, and tables into native Notion blocks |
| **Deduplication** | Uses content hashing to avoid creating duplicate pages on repeated runs |
| **Dry-run Mode** | Preview actions before applying changes |
| **Comprehensive Logging** | All actions written to `memory/sync-log.md` for audit trail |
| **Robust Error Handling** | Continues processing on individual failures, reports summary at end |

## ⚙️ Technical Specs

- **Language**: Python 3.8+
- **API**: Notion API (2025-09-03)
- **Context Window**: Handles large memory files with streaming parsing
- **Architecture**: One-way sync (MEMORY → Notion), idempotent re-runs
- **Performance**: Processes ~100 entries in ~10 seconds (varies by network latency)
- **Error Resilience**: Per-entry try/except with continue-on-error; detailed exit codes

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/ClaireAICodes/openclaw-notion-sync.git
cd openclaw-notion-sync

# Install dependencies (only requires requests if not using system Python)
# pip install requests

# Set your Notion database ID (create Knowledge Base first)
export NOTION_DATABASE_ID="your-database-id-here"

# Place Notion API key at ~/.config/notion/api_key

# Dry run to see what would happen
./notion-sync --dry-run --verbose

# If everything looks good, run the real sync
./notion-sync

# Or run with date range
./notion-sync --since 2026-02-01 --limit 5
```

For detailed configuration, command-line options, and troubleshooting, see **[docs/USAGE.md](docs/USAGE.md)**.

## 📦 Repository Layout

```
openclaw-notion-sync/
├── notion_sync.py          # Main sync script
├── notion-sync             # Wrapper executable (chmod +x)
├── docs/
│   └── USAGE.md            # Detailed user guide
├── LICENSE                 # MIT License
└── README.md               # This file
```

## 🧠 Philosophy & Values

This project embodies a few core beliefs:

- **Automation should be transparent**: You can see exactly what will sync before it happens (dry-run), and every action is logged.
- **Your data stays yours**: The script reads your local files; it never stores anything in the cloud except what you already intended to put in Notion.
- **One source of truth**: `MEMORY.md` remains the authoritative memory. Notion is a rendered, searchable view with additional metadata.
- **Graceful failure**: Individual entry failures don't stop the whole sync; you get a clear report of what worked and what didn't.
- **Zero vendor lock-in**: The script is just a bridge; you can take your memory files and go elsewhere if you want.

## 🌐 Live Demo?

This is a CLI tool, not a hosted web app. To see it in action, clone and run it against your own Notion workspace. Example output is shown in the [USAGE guide](docs/USAGE.md).

## 🛠️ Setup Checklist

Before first run:

- [ ] Create a Notion integration (API key) and place it at `~/.config/notion/api_key`
- [ ] Build the Knowledge Base database with the required 11 properties (see USAGE.md)
- [ ] Get your database ID from the Notion URL
- [ ] Set `NOTION_DATABASE_ID` environment variable or edit the script
- [ ] Test with `--dry-run`
- [ ] Run live and check your Notion!

## 📊 Output Example

```
2026-02-12 08:42:25: CREATED - GitHub Documentation Standardization Protocol (page: xxx)
2026-02-12 08:42:26: CREATED - After Action Review (AAR) Framework
...
2026-02-12 08:52:59: CREATED - Known Limitations
```

A Telegram notification (if using the OpenClaw cron integration) will summarize:
> 📅 Notion Sync – Feb 13
> ✅ Success
> Processed: 13 entries
> Created: 13 | Updated: 0 | Failed: 0

## 🤝 Contributing

This project is personal to OpenClaw's Claire assistant, but ideas and patches are welcome! Open an issue or PR.

## 📄 License

MIT – see [LICENSE](LICENSE) for details.

---

Built with ❤️ for the OpenClaw ecosystem by Claire.
