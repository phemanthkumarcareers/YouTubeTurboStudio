# YouTubeTurboStudio — Agent Instructions

Before making architectural or feature changes, read:

`docs/MASTER_ARCHITECTURE.md`

## 1. Core Rules

- This is an existing working application. Do not rebuild it from scratch unless explicitly approved.
- Preserve all existing working functionality.
- Implement the master architecture incrementally, one requested phase at a time.
- The platform has two video engines:
  1. `media_video` for **The AI Brief It**.
  2. `animation`, shared by Kids, Elders, and future animated channels.
- Kids and Elders must NOT have duplicated animation-engine implementations.
- Channels must be dynamically configurable. Do not hard-code exactly three channels.
- Every generation job must retain its `channel_id` through upload.
- Every channel must have isolated credentials and YouTube OAuth.
- Never commit API keys, OAuth tokens, client secrets, refresh tokens, or other credentials.
- Never print full secrets in logs or UI.
- Test videos must remain local/private and must not be automatically uploaded.
- Run focused tests after each phase and fix failures before moving on.
- Do not perform unrelated refactors merely because they are possible.
- Support Shorts and long-form videos according to each channel's configuration.
- Kids-specific safeguards are mandatory for Kids and must not automatically apply to Elders.
- The current machine should default to one heavy render pipeline at a time.

## 2. Mandatory Content Creation Modes

The Studio UI must expose exactly three primary generation choices for every channel:

1. **Long Video** — Generate a long-form video.
2. **Shorts** — Generate an independent, standalone Short with no parent link.
3. **Shorts - Link Long Video** — Generate purpose-built Shorts linked to a selected long video from the same active channel.

### 2.1 Long Video

- Generate a long-form video using the engine configured for the active channel.
- Associate the generation job with the active `channel_id`.
- Preserve channel identity throughout planning, generation, rendering, storage, and publishing.
- Respect the active channel's supported formats and configuration.

### 2.2 Shorts

- Generate an independent, standalone Short.
- Do not associate it with a parent long video.
- Do not create a parent/content-family relationship for standalone Shorts.
- Do not automatically insert a parent video URL into its description.
- Respect the active channel's Shorts configuration and safeguards.

### 2.3 Shorts - Link Long Video

- Generate purpose-built Shorts associated with a selected long video.
- The selected parent long video must belong to the same active channel.
- Keep this option disabled until an eligible long video exists for the active channel.
- Allow users to select an eligible parent long video from the active channel.
- Never allow a linked Short to reference a parent video belonging to another channel.
- Persist the parent video relationship and content-family relationship.
- Preserve the relationship across generation, rendering, storage, publishing, and retries.
- After the parent video is published, automatically include its real YouTube URL in the linked Short's description.
- Never fabricate, guess, or prematurely generate a YouTube URL.
- If the parent is not published, do not insert a fabricated or placeholder URL as though it were real.
- Resolve the actual published YouTube URL from trusted application or YouTube publishing data.
- Ensure the final description is updated with the real parent URL before the linked Short is published, according to the application's publishing workflow.
- Handle failures and retries without creating duplicate or incorrect parent relationships.
- If the parent cannot be resolved or does not have a valid published URL, prevent incorrect cross-linking and handle the condition safely.

## 3. Shared Content Planning and Publishing

Implement the three content creation modes once as shared content-planning and publishing functionality.

- Do not duplicate content-planning or publishing logic for individual channels.
- Route rendering to the appropriate video engine based on the active channel's configuration.
- Use `media_video` for The AI Brief It.
- Use the shared `animation` engine for Kids, Elders, and future animated channels.
- Keep channel-specific behavior configurable rather than embedding assumptions about a fixed number of channels.
- Keep generation mode, `channel_id`, parent video identity, and content-family identity available throughout the job lifecycle.
- Validate channel ownership before accepting or processing linked-Short requests.
- Enforce server-side validation in addition to UI restrictions.
- Keep publishing and upload behavior consistent with the existing architecture.
- Preserve all existing working functionality.

## 4. Channel Isolation and Security

- Every channel must have isolated credentials and YouTube OAuth.
- Never reuse one channel's OAuth credentials for another channel.
- Never expose secrets in logs, error messages, API responses, or UI.
- Keep API keys, client secrets, access tokens, and refresh tokens out of source control.
- Use the project's established environment-variable and secret-management conventions.
- Ensure every generation job retains its original `channel_id` through upload.
- Validate that a parent video and linked Short belong to the same channel.
- Do not weaken existing authentication, authorization, or data-isolation protections.

## 5. Video Engine Requirements

### 5.1 `media_video`

- Used for The AI Brief It.
- Preserve its existing functionality.
- Route eligible generation requests to this engine based on channel configuration.

### 5.2 `animation`

- Shared by Kids, Elders, and future animated channels.
- Do not create separate animation-engine implementations for Kids and Elders.
- Apply Kids-specific safeguards only to Kids.
- Do not automatically apply Kids-specific safeguards to Elders.
- Allow channel-specific configuration without duplicating the shared engine.

## 6. Rendering and Resource Management

- Support Shorts and long-form videos according to channel configuration.
- Default the current machine to one heavy render pipeline at a time.
- Preserve existing resource-management behavior unless the requested phase requires a change.
- Avoid unrelated performance refactors.
- Keep test videos local and private.
- Never automatically upload test videos.

## 7. Implementation Workflow

Before implementation:

1. Read `docs/MASTER_ARCHITECTURE.md`.
2. Review Section 38 for the authoritative content creation mode requirements.
3. Inspect the existing application structure and relevant code.
4. Identify the smallest implementation scope that satisfies the requested phase.
5. Identify relevant tests and existing behavior that must remain intact.

During implementation:

1. Implement only the explicitly requested phase.
2. Reuse existing services, models, engines, and publishing workflows where appropriate.
3. Avoid duplicated channel-specific implementations of shared functionality.
4. Preserve `channel_id` and content relationships throughout the job lifecycle.
5. Keep secrets out of source control, logs, and UI.
6. Add or update focused tests for the changed functionality.

After implementation:

1. Run focused tests for the implemented phase.
2. Fix failures caused by the changes before proceeding.
3. Check for regressions in relevant existing functionality.
4. Review security, channel isolation, and parent-link validation.
5. Report the implementation results using the required completion report.

## 8. Testing Requirements

Test the functionality relevant to each implemented phase, including where applicable:

- Long Video generation.
- Standalone Shorts generation.
- Linked Shorts generation.
- Disabled state when no eligible parent long video exists.
- Parent video selection restricted to the active channel.
- Rejection of cross-channel parent references.
- Persistence of parent and content-family relationships.
- Preservation of `channel_id` throughout generation and upload.
- Correct routing to `media_video` or `animation`.
- Correct handling of unpublished parent videos.
- Automatic insertion of the real parent YouTube URL after publication.
- Safe handling of missing URLs, publishing failures, and retries.
- Channel-specific OAuth and credential isolation.
- Kids-specific safeguards without automatically applying them to Elders.
- Local/private test-video behavior without automatic uploads.
- One-heavy-render-pipeline default.
- Relevant regressions in existing functionality.

Do not claim tests passed unless they were actually executed and passed.

## 9. Required Completion Report

After implementing a phase, report concisely:

1. **Files created/modified:** List the exact paths.
2. **Features implemented:** Describe the completed changes.
3. **Tests run and results:** Include commands and actual outcomes.
4. **Dependencies added:** List new dependencies or state that none were added.
5. **Database/schema changes:** Describe migrations and schema changes, or state that none were required.
6. **API keys/environment variables:** List any variables the user must configure, without exposing secret values.
7. **Configuration/secret file paths:** Give the exact paths used or required by the implementation.
8. **YouTube OAuth steps:** Explain any required setup or changes if OAuth is affected.
9. **How to run/test:** Provide the exact commands and steps needed to verify the feature.
10. **Known limitations/deferred work:** Clearly identify incomplete work and outstanding issues.

## 10. Mandatory Phase Boundaries

- Implement one requested phase at a time.
- Do not proceed to the next phase unless explicitly asked by the user.
- Do not interpret permission to implement one feature as permission to implement the entire master architecture.
- Do not rebuild the application from scratch without explicit approval.
- Preserve existing functionality and avoid unrelated refactors.
- If a required architectural detail is unclear, inspect the master architecture and existing implementation before making assumptions.

## 11. Authoritative Architecture Reference

The authoritative requirements and acceptance criteria for the three mandatory content creation modes are in:

`docs/MASTER_ARCHITECTURE.md` — **Section 38**

Section 38 takes precedence for detailed architecture requirements and acceptance criteria.

This `AGENTS.md` file is the transport copy of the project instructions and must be used together with the master architecture document.

## 12. Definition of Done

A phase is complete only when:

- The requested phase has been implemented without rebuilding the application.
- Existing working functionality is preserved.
- The implementation follows `docs/MASTER_ARCHITECTURE.md`.
- Relevant focused tests have been executed and failures addressed.
- Channel identity is preserved wherever relevant.
- Security and channel-isolation requirements are respected.
- The required completion report has been provided.
- No subsequent phase has been started without explicit authorization.