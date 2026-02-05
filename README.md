# Google Play Console CLI Skills

A collection of Agent Skills for shipping with the [Google Play Console CLI](https://github.com/tamtom/play-console-cli) (`gplay`). These skills are designed for zero-friction automation around Android builds, releases, metadata, in-app purchases, and signing.

Skills follow the Agent Skills format.

## Available Skills

### gplay-cli-usage

Guidance for running `gplay` commands (flags, pagination, output, auth).

**Use when:**
- You need the correct `gplay` command or flag combination
- You want JSON-first output and pagination tips for automation

### gplay-gradle-build

Build, sign, and package Android apps with Gradle before uploading.

**Use when:**
- You need to create an APK or AAB for upload
- You're setting up CI/CD build pipelines
- You need to configure signing configs
- You're troubleshooting ProGuard/R8 issues

### gplay-release-flow

End-to-end release workflows for internal, beta, and production tracks.

**Use when:**
- You want to upload, release, and rollout in one flow
- You need the manual sequence for fine-grained control
- You're releasing to multiple tracks

### gplay-signing-setup

Android app signing, keystores, and Play App Signing.

**Use when:**
- You are setting up signing for a new app
- You need to migrate to Play App Signing
- You need to create or rotate signing keys

### gplay-metadata-sync

Metadata and localization sync (including Fastlane format).

**Use when:**
- You are updating Play Store metadata or localizations
- You need to validate character limits before upload
- You need to sync with Fastlane directory structure

### gplay-iap-setup

In-app products, subscriptions, base plans, and offers.

**Use when:**
- You are setting up in-app purchases or subscriptions
- You need to create subscription offers or pricing
- You're managing monetization products

### gplay-review-management

Review monitoring, filtering, and automated responses.

**Use when:**
- You want to monitor and respond to user reviews
- You need to filter reviews by rating or territory
- You're setting up automated review responses

### gplay-rollout-management

Staged rollout orchestration and monitoring.

**Use when:**
- You want to release to a percentage of users first
- You need to halt, resume, or complete rollouts
- You're implementing gradual rollout strategies

### gplay-purchase-verification

Server-side purchase verification for in-app products and subscriptions.

**Use when:**
- You need to verify purchase tokens from your backend
- You're implementing receipt validation
- You need to check subscription status

### gplay-testers-orchestration

Beta testing groups and tester management.

**Use when:**
- You manage multiple testing groups
- You need to add/remove testers
- You're setting up closed testing tracks

## Installation

Install this skill pack:

```bash
npx add-skill tamtom/gplay-cli-skills
```

## Usage

Skills are automatically available once installed. The agent will use them when relevant tasks are detected.

**Examples:**

```
Build and upload my Android app to Google Play internal track
```

```
Release build v1.2.3 to production with 10% staged rollout
```

```
Set up in-app subscription with monthly and yearly base plans
```

```
Sync Fastlane metadata from ./metadata and upload to Play Store
```

```
Respond to all 1-star reviews from the last week
```

## Skill Structure

Each skill contains:
- `SKILL.md` - Instructions for the agent
- `scripts/` - Helper scripts for automation (optional)
- `references/` - Supporting documentation (optional)

## License

MIT
