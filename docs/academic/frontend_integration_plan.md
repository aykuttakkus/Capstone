# Calma Frontend Integration Plan

## Purpose

This document plans how to connect the backend features that currently exist but are not yet exposed in the frontend.

The goal is not to add random UI. The goal is to expose only the backend capabilities that improve session control, transparency, and feedback while keeping the demo stable.

## Scope Rules

- keep the current chat flow unchanged unless a feature strictly needs UI support
- do not redesign the entire interface
- expose only the backend features that improve user control or explainability
- keep maintenance-only tools backend-first unless a maintainer view is truly needed

## Existing Backend-Only Features

### User-facing features that should be connected to the UI

- session search
- session archive
- session delete
- session export
- feedback submit
- feedback list / history
- retrieval diagnostics

### Backend or maintenance-only features that should stay mostly non-UI

- corpus versioning
- offline evaluation
- freeze / submission documents

These can stay in docs, scripts, or maintainer workflows unless a lightweight admin view is intentionally added later.

## Phase 0. Scope Lock

### Goal

Decide exactly which backend features deserve UI exposure now and which should remain backend-only.

### Work Items

- confirm the current UI surface is only for user-facing actions
- keep corpus versioning and evaluation outside the primary user UI
- decide whether a lightweight admin/maintainer view is needed later
- define the minimum set of new controls for the sidebar and message area

### Deliverables

- final UI scope list
- feature ownership list: user-facing vs backend-only
- no ambiguity about what gets a frontend component

### Tests

- scope review against the list above
- no UI expansion beyond the approved items

### Exit Criteria

- all backend-only features are classified correctly
- no feature is accidentally left in an undefined state

## Phase 1. Session Management UI

### Goal

Give the user direct control over old sessions.

### Features to expose

- search sessions by title, topic, date, and safety mode
- archive a session
- delete a session
- export a session as JSON or Markdown

### Suggested UI surfaces

- search input at the top of the session list
- filter chips for topic and safety mode
- session overflow menu with archive/delete/export actions
- export download feedback
- delete confirmation modal

### Deliverables

- searchable session list
- session action menu
- export/download behavior
- archive and delete confirmations

### Tests

- search returns matching sessions
- archive updates the session list state
- delete removes the session from the list
- export returns a downloadable file or structured content

### Exit Criteria

- the user can manage chat history without leaving the app

## Phase 2. Feedback UI

### Goal

Capture lightweight quality feedback directly from the chat experience.

### Features to expose

- helpful / not helpful feedback on assistant answers
- optional short comment field
- simple feedback history view if useful

### Suggested UI surfaces

- thumbs up / thumbs down or equivalent buttons under assistant replies
- optional comment drawer or inline field
- small feedback confirmation state

### Deliverables

- feedback capture controls on the chat screen
- stored feedback records visible in a simple history view if needed

### Tests

- feedback submission stores the expected record
- feedback can be attached to a session or message
- feedback history loads without breaking the chat flow

### Exit Criteria

- the app can collect qualitative improvement data locally

## Phase 3. Retrieval Transparency UI

### Goal

Show why an answer was grounded the way it was.

### Features to expose

- source rank
- source reason tags
- topic alignment information
- query overlap indicators
- retrieval diagnostics panel or drawer

### Suggested UI surfaces

- expandable source list under assistant responses
- a debug-style retrieval panel behind a toggle
- compact badges for rank and reason tags

### Deliverables

- visible source trace for each grounded answer
- optional debug drawer for deeper inspection

### Tests

- source cards render rank and tags correctly
- diagnostics panel shows top chunk information
- grounded answers still render normally when diagnostics are hidden

### Exit Criteria

- the user can inspect source behavior without reading backend logs

## Phase 4. Session Restore UX

### Goal

Make the existing session restore behavior easy to use.

### Features to expose

- open a previous session from the list
- load the session’s messages into the chat view
- show archived vs active session state clearly

### Suggested UI surfaces

- click-to-open session item
- visual state badges for archived/active
- session header showing title/topic/date

### Deliverables

- session restore from the UI
- active session context shown in the chat area

### Tests

- opening a session loads the correct messages
- archived sessions are labeled correctly
- restoring a session does not clear the wrong state

### Exit Criteria

- old conversations can be reopened in a predictable way

## Phase 5. Maintenance-Only Features

### Goal

Keep backend-only tooling out of the regular user experience while making sure it remains documented and easy to operate.

### Features to keep backend-first

- corpus versioning
- offline evaluation
- freeze / submission documents

### Recommended treatment

- corpus versioning stays in scripts, manifests, and docs unless a future admin view is needed
- offline evaluation stays in `tests/eval` and local scripts
- freeze and submission notes stay in docs only

### Deliverables

- documented maintenance workflow
- no unnecessary UI exposure for internal tooling

### Tests

- versioning files are generated correctly by scripts
- evaluation script runs offline
- documentation files remain current

### Exit Criteria

- maintainers can operate the backend without adding user-facing clutter

## Phase 6. UI Regression Protection

### Goal

Prevent the new frontend controls from breaking the existing demo flow.

### Work Items

- keep onboarding intact
- keep chat sending unchanged
- keep screening untouched
- keep the current brand/layout intact

### Deliverables

- stable demo flow
- no regression in the core user journey

### Tests

- login still works
- onboarding still works
- chat still works
- screening still works
- session actions do not break the core flow

### Exit Criteria

- added controls do not damage the current experience

## Recommended Order

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 4
6. Phase 5
7. Phase 6

## Final Rule

If a backend feature does not improve user control, clarity, or presentation quality, keep it backend-only.
