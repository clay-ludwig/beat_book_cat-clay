# Slide Deck Outline: From News Archives to Beatbook

## Slide 1 — Title
- **From News Archives to Beatbook**
- Turning archived stories into a practical, reporter-friendly beat guide

---

## Slide 2 — Prerequisites
- Story archive in a JSON file
- GitHub account
- Terminal/Codespace access (how to access it?)

---

## Slide 3 — Environment Setup
- Create a GitHub repository
- Open Codespace or local terminal in project folder
- Install `uv`
  - `pip install uv`
- (Optional) Initialize project: `uv init --python 3.12`

- Install LLM tooling and plugins
  - `uv add llm`
  - `uv add llm install llm-groq`
- Plugin idea in plain terms: like a Chrome extension for AI tooling
- For this workflow, primary provider is Groq

---

## Slide 5 — API Key Setup
- Create a Groq account and API key at `console.groq.com`
- Set key locally:
  - `uv run llm keys set groq`
- Key is hidden when typed in terminal (normal behavior)

---

## Slide 6 — Why Metadata Extraction Comes First
- Metadata controls what your beatbook can analyze later
- Extracting from raw stories preserves detail before summarization
- Keeps sensitive full-text archives out of commercial model workflows
- Output summaries become safer, lighter “raw material” for beatbook generation

---

## Slide 7 — Prompting Copilot for Extraction Script
- Ask Copilot to generate a Python extraction script
- Be explicit about beatbook goal (thematic vs narrative)
- For thematic-over-time, request fields like:
  - Temporal: names, season, year, weekend
  - Classification: primary/secondary themes, incident type, severity
  - Geographic/context: location, agencies, outcomes, etc.
- Require quote retention and replacing full content with summaries

---

## Slide 8 — Run Metadata Extraction
- Example command:
  - `uv run python metadata.py --model groq/qwen/qwen3-32b --input story_sample.json`
- List available models with:
  - `uv run llm models`
- You can switch open models as needed during long runs

---

## Slide 9 — Common Extraction Problems and how we handled them
- Rate limits (`429`) when processing many stories

How We Handled Rate Limits
- Added **incremental saves** after each processed story
- Script resumes from existing output file
- If a model hits limits, stop with `Ctrl/Cmd + C`, switch model, rerun
- Continue from where extraction stopped instead of restarting

---

## Slide 10 — Verification with SQLite + Datasette
- Load metadata JSON into SQLite:
  - `uv run sqlite-utils insert entities.db stories your_json_file_name --pk docref`
- Install and run Datasette:
  - `uv add datasette`
  - `uv run datasette entities.db`
- Use browser/PORTS to inspect extracted fields and spot errors

---

## Slide 11 — Why Verification Matters
- Validate names, organizations, and outcomes against summaries
- Catch hallucinations, false positives, and missing values
- Check extraction failure patterns before writing beatbook
- Repeat extraction if quality is not acceptable

---

## Slide 12 — Beatbook Generation Script and Command
- Prompt Copilot for a second script (beatbook generator)
- Require:
  - Narrative, reporter-friendly tone
  - Uses pre-extracted summaries/metadata only
  - Trends over time (not only seasons)
  - Follow-up ideas + outdated-data disclaimer

- Example command:
  - `uv run python generate_beatbook.py --model "anthropic/claude-sonnet-4-" --input metadata_stories.json --output my_narrative_beatbook_v2.md`
- Review and iterate until the story flow and accuracy are strong

---

## Slide 13 — Refinement Checklist
- Is the voice for a **new** reporter joining the beat?
- Are story examples woven into narrative (not just stats)?
- Are trends over time clearly explained with concrete examples?
- Are unresolved stories and follow-up angles included?
- Is disclaimer present: data may be outdated?

---

## Slide 14 — Optional Output Formats
- Convert beatbook text into:
  - Timeline
  - Web page
  - Mind map
- Use Copilot to scaffold conversion scripts
- Serve locally and preview via browser/PORTS

---

## Slide 18 — Summary
- Good metadata extraction determines beatbook quality
- Incremental saves make large runs resilient
- Verification is mandatory, not optional
- Beatbook writing is iterative: generate, review, refine
- Final product should be useful to a reporter joining the beat fresh
