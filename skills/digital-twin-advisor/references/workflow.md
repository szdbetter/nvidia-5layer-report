# Digital Twin Advisor Workflow

## Goal
Build a useful advisor-style digital twin from real public material, then standardize the method for repeated use.

## Step-by-step

### Step 0. Clarify the ask
Capture:
- who the subject is
- why this twin is being built
- what kinds of questions the user wants to ask later
- whether the target is a consultant, product advisor, investment advisor, operator, teacher, or commentator

### Step 1. Define source boundary
Record:
- source types: articles / interviews / podcasts / tweets / talks / books / notes
- date range
- known missing sources
- knowledge cutoff date

Rule: the cutoff date is part of the deliverable, not a side note.

### Step 2. Clean the corpus
Transform raw HTML, exports, transcripts, or scraped text into clean Markdown.

Minimum structure per source item:
- title
- date
- source link (if any)
- body

Cleaning rules:
- remove menus, button labels, repeated catalogs, footer clutter
- keep image references only when the image changes meaning
- preserve headings and lists where they encode logic
- preserve quoted prompts, frameworks, checklists, and examples

### Step 3. Extract the 5 layers

#### 1) Corpus boundary
What the twin knows and the confidence level of that knowledge.

#### 2) Persona
Extract stable patterns such as:
- values
- tastes
- recurring likes/dislikes
- default emotional stance
- what the subject respects / mocks / avoids

#### 3) Capability
Extract what the subject repeatedly demonstrates real edge in:
- problem types solved often
- methods used repeatedly
- evidence of practical success
- domains with repeated specificity

#### 4) Decision logic
Extract how the subject judges:
- good vs bad opportunities
- speed vs quality
- leverage vs labor
- build vs buy
- tool A vs tool B
- short-term win vs long-term moat

#### 5) Expression
Extract how the subject sounds:
- sentence rhythm
- punchiness vs nuance
- use of metaphors
- use of binaries / contrasts
- use of examples, lists, or slogans

### Step 4. Merge into an advisor card
Do not split “人物画像” and “思维模型/决策规则” into separate outputs by default.
Merge them into one operational artifact: the advisor card.

The advisor card must answer:
- who this twin is useful for
- what problems it should be asked
- what problems it should not be asked
- how it usually thinks
- how it usually talks
- how far its authority should be trusted

### Step 5. Generate the avatar prompt
Turn the advisor card into a reusable system prompt.

Mandatory constraints:
- do not claim knowledge beyond the cutoff date
- do not invent private conversations, unpublished opinions, or recent events
- answer within the advisor role, not as a universal oracle
- if the question falls outside competence, say so in-character but clearly

### Step 6. Package for scale
When the user wants repeatability:
- save the SOP
- save templates
- save a generic skill
- keep case-specific files separate from the generic method

## Review checklist
Before calling the twin usable, verify:
- cutoff date is recorded
- advisor role is explicit
- suitable / unsuitable questions are listed
- at least 5-10 decision rules are extracted where possible
- expression style has concrete evidence, not vague adjectives
- prompt has clear boundary clauses

## Failure modes
- Overfitting to one article
- Confusing style imitation with judgment imitation
- Treating hype statements as stable principles
- Ignoring source gaps
- Letting the twin answer outside its real edge

## Preferred operating principle
Useful > flattering.
The twin should be a decision aid with clear boundaries, not a cosplay shell.
