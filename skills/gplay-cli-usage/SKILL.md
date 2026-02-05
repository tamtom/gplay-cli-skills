---
name: gplay-cli-usage
description: Guidance for using the Google Play Console CLI in this repo (flags, output formats, pagination, auth, and discovery). Use when asked to run or design gplay commands or interact with Google Play Console via the CLI.
---

# Google Play CLI usage

Use this skill when you need to run or design `gplay` commands for Google Play Console.

## Command discovery
- Always use `--help` to discover commands and flags.
  - `gplay --help`
  - `gplay tracks --help`
  - `gplay tracks list --help`

## Flag conventions
- Use explicit long flags (e.g., `--package`, `--output`).
- No interactive prompts; destructive operations require `--confirm`.
- Use `--paginate` when the user wants all pages.

## Output formats
- Default output is minified JSON.
- Use `--output table` or `--output markdown` only for human-readable output.
- `--pretty` is only valid with JSON output.

## Authentication and defaults
- Prefer service account auth via `gplay auth login --service-account /path/to/sa.json`.
- Fallback env vars: `GPLAY_SERVICE_ACCOUNT`, `GPLAY_PACKAGE`.
- `GPLAY_PACKAGE` can provide a default package name.

## Timeouts
- `GPLAY_TIMEOUT` / `GPLAY_TIMEOUT_SECONDS` control request timeouts.
- `GPLAY_UPLOAD_TIMEOUT` / `GPLAY_UPLOAD_TIMEOUT_SECONDS` control upload timeouts.

## Common patterns

### List with pagination
```bash
gplay tracks list --package com.example.app --paginate
```

### Parse JSON output with jq
```bash
gplay tracks list --package com.example.app | jq '.tracks[] | select(.track == "production")'
```

### Use profiles
```bash
gplay auth add-profile production --service-account /path/to/prod-sa.json
gplay auth use-profile production
gplay --profile production tracks list --package com.example.app
```

### Debug mode
```bash
GPLAY_DEBUG=1 gplay tracks list --package com.example.app
GPLAY_DEBUG=api gplay tracks list --package com.example.app  # HTTP details
```

## Edit sessions
Most write operations require an edit session:
```bash
# Create edit
gplay edits create --package com.example.app
# Returns: edit_id

# Make changes
gplay bundles upload --package com.example.app --edit <edit_id> --file app.aab

# Commit changes (publishes)
gplay edits commit --package com.example.app --edit <edit_id>
```

## High-level vs manual commands
- **High-level**: `gplay release` (creates edit, uploads, commits)
- **Manual**: `gplay edits create` → `gplay bundles upload` → `gplay edits commit`

Use high-level for simplicity, manual for fine-grained control.
