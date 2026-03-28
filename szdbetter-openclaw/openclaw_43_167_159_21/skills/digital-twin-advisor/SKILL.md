---
name: digital-twin-advisor
description: Build digital twin advisors from KOL/expert public content. Use /digital-twin-advisor to invoke.
disable-model-invocation: true
---

# Digital Twin Advisor

Build a digital twin as an **advisor**, not a roleplay toy.

The default output is a 3-part package:
1. `*_raw.md` — clean corpus in Markdown
2. `*_advisor_profile.md` — merged advisor card
3. `*_avatar_prompt.md` — reusable system prompt

If the user asks to productize the method, also create or update a reusable SOP / skill.

## Workflow

### 1) Lock the modeling protocol before execution
Confirm or define:
- Subject name
- Source boundary
- Knowledge cutoff date
- Intended advisor role
- Primary question categories the twin should answer
- Excluded domains / hard boundaries

Do not skip this step. If the user says “先思考，再执行”, start by showing the modeling frame before doing file conversion.

### 2) Convert source material into clean Markdown
Normalize the corpus into readable Markdown.
Keep:
- title
- author / source if available
- publish time
- canonical link if available
- body text

Remove or minimize:
- navigation chrome
- duplicate menus / TOCs
- decorative markup
- irrelevant UI text
- repeated image boilerplate unless it carries meaning

### 3) Build the advisor card
Merge persona and reasoning into a single advisor profile.
Always cover:
- one-line positioning
- advisor role
- high-ROI scenarios
- thinking model
- decision rules
- expression style
- suitable questions
- unsuitable questions
- answer boundaries and confidence notes

Use the template in `references/deliverables.md`.

### 4) Generate the avatar prompt
Turn the advisor card into a reusable prompt that makes the assistant answer:
- with the subject’s judgment style
- within the subject’s competence boundary
- without overclaiming facts after the cutoff date
- without pretending private knowledge

Use the template in `references/prompt-template.md`.

### 5) Productize when requested
If the user wants the method reused across multiple people:
- save a generic SOP
- save templates
- create or update a reusable skill

## Quality bar

A useful digital twin must satisfy all 5 layers:
1. **Corpus boundary** — what the twin knows, and until when
2. **Persona** — values, preferences, recurring stances
3. **Capability** — what problems the subject is actually good at
4. **Decision logic** — how the subject makes tradeoffs
5. **Expression** — tone, framing, rhythm, favorite contrasts

If one layer is weak, say so explicitly instead of faking confidence.

## Default naming convention

Use kebab-case or snake_case consistently. Recommended files:
- `<subject>_raw.md`
- `<subject>_advisor_profile.md`
- `<subject>_avatar_prompt.md`

If building a reusable package, save templates and SOP in a project folder and keep the skill generic.

## References

Read these files as needed:
- `references/workflow.md` — full end-to-end process and guardrails
- `references/deliverables.md` — advisor card and corpus structure templates
- `references/prompt-template.md` — universal avatar prompt template
