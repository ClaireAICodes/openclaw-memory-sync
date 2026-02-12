# Notion Sync Script

Automatic synchronization of OpenClaw memory files to Notion Knowledge Base.

## Overview

This script reads your `MEMORY.md` and daily `memory/YYYY-MM-DD.md` files, extracts knowledge entries (research, lessons, decisions, patterns, insights), and syncs them to a Notion database with rich formatting and metadata.

## Prerequisites

1. **Notion Integration** set up with API key at `~/.config/notion/api_key`
2. **Knowledge Base database** created in Notion (set its ID via environment variable or edit the script)
3. **Python 3.8+** installed

## Quick Start

```bash
# Dry run (preview changes without making them)
python3 scripts/notion_sync.py --dry-run --verbose

# Full sync (last 7 days)
python3 scripts/notion_sync.py

# Sync specific date range
python3 scripts/notion_sync.py --since 2026-02-01

# Limit number of entries (testing)
python3 scripts/notion_sync.py --limit 5
```

## Command-Line Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview changes without creating/updating Notion pages |
| `--verbose` | Show detailed debug logs |
| `--since DATE` | Only sync entries from DATE onwards (format: YYYY-MM-DD) |
| `--limit N` | Process only first N entries (useful for testing) |

## How It Works

1. **Parse** MEMORY.md and recent daily files (default: last 7 days)
2. **Extract** knowledge entries based on section headers and content
3. **Classify** each entry:
   - Content Type: Research, Lesson, Decision, Pattern, Tutorial, Reference, Insight
   - Domain: AI Models, OpenClaw, Cost Optimization, Trading, Web3, Learning, Process, etc.
   - Certainty: Verified, Likely, Speculative, Opinion
   - Impact: High, Medium, Low, Negligible
   - Auto-generate confidence score (1-10) and extract tags
4. **Convert** Markdown content to Notion blocks (headings, lists, code blocks, quotes, dividers)
5. **Deduplicate** using content hash (avoid duplicates)
6. **Create/Update** pages in Notion with full metadata and formatted body
7. **Log** all actions to `memory/sync-log.md`

## Output

- **Notion pages** created in the Knowledge Base database with all properties filled
- **Sync log** appended to `memory/sync-log.md` with timestamps
- **Console output** showing progress and statistics

## Database Schema

The script expects a Notion database with these properties (spaces matter!):

- `Name` (title)
- `Content Type` (select: Research, Lesson, Decision, Pattern, Tutorial, Reference, Insight)
- `Domain` (select: AI Models, OpenClaw, Cost Optimization, etc.)
- `Certainty` (select: Verified, Likely, Speculative, Opinion)
- `Source` (select: Research, Experiment, Conversation, Reading, Observation, Manual)
- `Confidence Score` (number: 1-10)
- `Impact` (select: High, Medium, Low, Negligible)
- `Tags` (multi_select)
- `External URL` (url)
- `Body` (rich_text) - summary of content
- `Source File` (rich_text) - tracks origin file (e.g., "memory/2026-02-12.md")

## Wrapper Command

After setup, you can use:
```bash
openclaw notion-sync [options]
```

This is an alias to the Python script with the correct environment.

## Customization

### Setting Your Notion Database ID

**Option A: Environment Variable** (recommended):
```bash
export NOTION_DATABASE_ID="your-database-id-here"
```
Then run the script normally.

**Option B: Edit the script**:
Open `notion_sync.py` and replace `'YOUR_NOTION_DATABASE_ID_HERE'` with your actual database ID (keep quotes).

#### How to Find Your Database ID

1. Open your Notion database in a browser.
2. Look at the URL: `https://www.notion.so/YourWorkspace/DatabaseName-<span style="background-color: yellow;">DATABASE_ID</span>?view=...`
3. The part after the dash and before the `?` is your database ID (it's a long hex string with hyphens).
4. Copy that and use it as your `NOTION_DATABASE_ID`.

### Other Adjustments

Edit the script to adjust:
- `MAX_BODY_LENGTH` - truncation limit (default 2000, Notion's Rich Text limit)
- Keyword mappings in `EntryClassifier` for better auto-tagging
- Days back to scan (`days_back` parameter)

## Troubleshooting

**"Notion API key not found"**
 → Place your API key at `~/.config/notion/api_key`

**"Property does not exist" errors**
 → Check that your Notion database has all required properties with EXACT names (including spaces)

**"Body length exceeds 2000"**
 → The script now handles truncation automatically; if issues persist, increase `MAX_BODY_LENGTH` or check content length

**Duplicate pages**
 → The script uses content hashing for deduplication; if you see duplicates, check `Source File` tracking

## Logging

All sync actions are logged to:
```
memory/sync-log.md
```

Format:
```markdown
- 2026-02-12 08:52:50: CREATED - GitHub Documentation Standardization Protocol (page: xxx)
- 2026-02-12 08:52:51: UPDATED - Existing page...
```

## License

Part of OpenClaw. See OpenClaw documentation for details.
