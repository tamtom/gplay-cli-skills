---
name: gplay-preflight
description: Offline compliance and hygiene scanning of an AAB or APK with `gplay preflight` — manifest flags, restricted permissions, 64-bit and 16 KB page alignment, listing assets, secrets, billing, privacy SDKs, target API floor, and size. Use before uploading a build, as a CI gate, or when diagnosing a Play rejection. Runs entirely offline with no credentials.
---

# gplay preflight — offline build scanning

`gplay preflight` inspects a local `.aab` or `.apk` and reports findings. It
makes **no API calls and needs no credentials**, so it works on any machine, in
any CI job, before the artifact has ever touched Play.

Reach for it *before* `gplay validate` (which needs auth and hits the API) and
before any upload. It catches the class of problem that Play rejects hours
later, or that fails at install time on a user's device.

## Preconditions

- A built `.aab` or `.apk` on disk.
- Nothing else. No `gplay auth login`, no `--package`, no network.

## Basic usage

```bash
# Scan a bundle
gplay preflight --file app-release.aab

# Also validate the store listing in the same pass
gplay preflight --file app-release.aab --listings-dir ./fastlane/metadata/android

# Machine-readable
gplay preflight --file app-release.aab --output json --pretty

# See what scanners exist
gplay preflight --list-scanners
```

## How preflight reads the build

`preflight` fully decodes `AndroidManifest.xml` — binary AXML for APKs, aapt2
protobuf for App Bundles — so findings reflect real, typed attribute values
rather than substring guesses.

This matters when you interpret results: an attribute pointing at a resource
reference (for example `android:debuggable="@bool/isDebug"`) is reported as
*not statically determinable*, not as `false`. Do not read a missing finding as
proof of absence in that case.

Aggressive code shrinking can rename or remove classes, so **SDK detection
misses are not proof an SDK is absent**. Matches, however, are high confidence.

## The nine scanners

Every scanner has an ID. Select with `--only` or exclude with `--skip`
(comma-separated).

### `manifest`

Manifest-level correctness and release-blocking flags.

- `android:debuggable="true"` — **error**. Ships a debuggable build.
- `android:testOnly="true"` — **error**. Play rejects the upload outright.
- Component with an `<intent-filter>` and no `android:exported` on
  `targetSdk` 31+ — **error**. This is an *install failure* on Android 12+,
  not a warning. Launcher activities are exempt.
- Exported `<provider>` with `grantUriPermissions` — **error**. Any app can
  reach the granted URIs.
- Foreground service type without its matching permission on `targetSdk` 34+ —
  Android 14 throws `SecurityException` at runtime. A `dataSync` type needs
  `FOREGROUND_SERVICE_DATA_SYNC`.
- `usesCleartextTraffic="true"` — warning, downgraded to info when a
  `networkSecurityConfig` is present.
- `allowBackup`, `requestLegacyExternalStorage`, package/version sanity.

### `permissions`

- **Restricted permissions** that require a Play declaration form: SMS and Call
  Log groups, `MANAGE_EXTERNAL_STORAGE`, `ACCESS_BACKGROUND_LOCATION`,
  `QUERY_ALL_PACKAGES`, `SYSTEM_ALERT_WINDOW`, `BIND_ACCESSIBILITY_SERVICE`,
  `USE_FULL_SCREEN_INTENT`, `SCHEDULE_EXACT_ALARM`, and others. Each finding
  carries the Play policy documentation link.
- **Sensitive permissions** that need a Data safety disclosure (info level).
- Legacy storage: `WRITE_EXTERNAL_STORAGE` without `maxSdkVersion` on
  `targetSdk` 30+, `READ_EXTERNAL_STORAGE` on 33+.
- Duplicates and deprecated permissions.

### `native_libs`

- Missing `arm64-v8a` — **error**. Play has required 64-bit since 2019.
- **16 KB memory page alignment**, read from real ELF program headers. Error on
  `targetSdk` 35+, warning below. Android 15 devices with 16 KB pages will not
  load misaligned `.so` files.
- `x86` without `x86_64`, bare `armeabi`.
- Unstripped `.debug_*` / `.symtab` sections — wasted download size.
- `extractNativeLibs="true"` — larger install footprint.

### `metadata`

**Requires `--listings-dir`.** Skipped otherwise. Expects a Fastlane-style
layout (`<dir>/<locale>/title.txt`, `<dir>/<locale>/images/...`).

- Title ≤ 30, short description ≤ 80, full description ≤ 4000, release notes
  ≤ 500 characters — counted in runes, not bytes.
- **Real pixel dimensions**: icon 512×512, feature graphic 1024×500, promo
  graphic 180×120, TV banner 1280×720.
- Screenshots: min 320px per side, max 3840px, max 2:1 aspect ratio, at least 2
  phone screenshots, at most 8 per form factor, max 8 MB each.

### `secrets`

Errors: private key blocks, AWS access keys, Stripe `sk_live_`, GitHub tokens,
Slack tokens and webhooks, SendGrid keys, Google OAuth client secrets,
OpenAI/Anthropic keys, service-account JSON, shipped keystores (`.jks`,
`.keystore`, `.p12`, `.pfx`, `.pem`, `.ppk`), and `.git/` or `.env` leakage.

Warnings: Google API keys (`AIza…`) and JWTs.

> Google API keys are a **warning, not an error**, on purpose. Android apps
> embed Maps and Firebase keys by design. The fix is restricting the key to your
> package name and signing certificate in Cloud Console — not removing it from
> the binary. Do not tell the user to delete it.

Dex bytecode is scanned too, so hardcoded string literals are caught.

### `billing`

Third-party payment processors (Stripe, Braintree, PayPal, Adyen, Razorpay…)
present in the build — a warning on its own, downgraded to info when Play
Billing is also present. Also flags `com.android.vending.BILLING` declared with
no billing implementation, and billing wrappers (RevenueCat, Adapty,
Qonversion) shipped without the Play Billing Library.

### `privacy`

Inventory of 40+ analytics, attribution, and ads SDKs (info). Reconciles the
`AD_ID` permission: warns when an ads/tracking SDK is present on `targetSdk`
33+ but the permission is missing, and notes the reverse case.

### `policy`

- `targetSdkVersion` below Play's floor. Override with `--min-target-sdk`
  when Google's annual bump lands before a new gplay release.
- Restricted services: accessibility, VPN, device admin, notification listener.
- APK-vs-AAB upload format.

### `size`

Download size budget (`--max-size`), per-dex budget (`--max-dex`), dex
fragmentation, and a payload breakdown by bucket with the largest entries.

## CI gating

```bash
# Block only on hard blockers
gplay preflight --file app-release.aab --fail-on error

# Stricter: warnings fail too
gplay preflight --file app-release.aab --fail-on warning

# Narrow the gate to the scanners you care about
gplay preflight --file app-release.aab \
  --only manifest,permissions,native_libs,secrets \
  --fail-on warning

# Faster: skip the secrets scan on very large builds
gplay preflight --file app-release.aab --skip-secrets
```

Exit codes:

| Code | Meaning |
|------|---------|
| 0 | No findings at or above `--fail-on` |
| 1 | Findings at or above `--fail-on` |

GitHub Actions:

```yaml
- name: Offline preflight
  run: |
    gplay preflight \
      --file app/build/outputs/bundle/release/app-release.aab \
      --listings-dir fastlane/metadata/android \
      --fail-on error
```

## JSON output

`--output json` emits the full report: format, package, version code and name,
min/target SDK, per-scanner run status, and every finding with its `check`,
`severity`, `message`, `entry`, `hint`, and (where one applies) a `ref` policy
link.

```bash
# Just the errors
gplay preflight --file app.aab --output json | jq '[.findings[] | select(.severity=="error")]'

# Which scanners were skipped and why
gplay preflight --file app.aab --output json | jq '.scanners[] | select(.skipped)'
```

## Where preflight fits

| Tool | Needs auth | Scope |
|------|-----------|-------|
| `gplay preflight` | No | The artifact itself, offline. Manifest, libs, secrets, listing files |
| `gplay validate` | Yes | Release readiness: local checks plus live track and listing state |
| `gplay checks analyze` | Yes | Google Checks privacy/policy analysis, server-side and async |
| `gplay release --dry-run` | Yes | Full pipeline against a real edit, discarded before commit |

Run them in that order. `preflight` is the cheapest and catches the most.

## Agent behavior

- Run `gplay preflight --file <artifact>` **before** any upload or release
  command, and report findings before proceeding.
- Pass `--listings-dir` whenever a metadata directory exists — otherwise the
  `metadata` scanner is skipped and listing problems go unreported.
- Treat `error` findings as blocking. Do not upload past them without the user
  explicitly saying to.
- Report the `hint` and `ref` fields, not just the message. The hint says what
  to actually change.
- Never advise deleting a Google API key found by the secrets scanner. Advise
  restricting it.
- A missing finding is not proof of compliance when the manifest could not be
  decoded or the build is heavily obfuscated. Say so rather than claiming the
  build is clean.
- Confirm flags with `gplay preflight --help` before constructing a command.
- `--only` and `--skip` take comma-separated scanner IDs; get the current list
  from `gplay preflight --list-scanners`.

## Notes

- `preflight` reads the archive once and streams large entries in bounded
  chunks, so memory stays flat on big bundles.
- Scanner IDs are stable; finding `check` names are preserved across versions
  for JSON consumers.
- The `policy` scanner's target API floor is a constant that Google raises each
  August. If it looks stale, pass `--min-target-sdk`.
