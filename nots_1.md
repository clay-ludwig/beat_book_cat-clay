## Beat Book Process for Beginners (Outline)

### 1) Prerequisites
- Story samples in a JSON file
- GitHub account
- Access to a terminal/Codespace

### 2) Quick Setup for Beginners
- Create a GitHub repository:
  Go to github.com -> Log into your account
	- Click the + icon in the top-right, choose New repository.
	- Name it, set Public or Private, then click Create repository.

- Open Codespace or local terminal in project folder
  - Click Code -> Codespaces -> Create codespace.
	- We'll work locally, so open a terminal in your project folder. [explain this like they have never used a terminal, explain parts of the terminal. keep it concise but detailed. Let the user know how to install copilot]
- Install `uv`
  [I dont remember how to do this, but co-pilot says (- Run: curl -LsSf https://astral.sh/uv/install.sh | sh
	- Then run: export PATH="$HOME/.local/bin:$PATH")
  Initialize your project (optional but helpful):
	- Run: uv init --python 3.12)
- Install `llm` and model plugins (Groq, Gemini, Anthropic, etc.)
  [Describe plugins]
  - Run: `uv add llm install llm-groq` (Here, you can include other models: llm-gemini, llm-anthropic, especially if you have access to their API keys).
  For this process, we'll work with groq.
6. Get a Groq API key:
	- Go to https://console.groq.com
	- Create an account and an API key (click on Create API at the top right corner when you log in to Groq).
  - To set up your Groq API key which should help you access the models, run: uv run llm keys set groq. You'll be prompted to enter your API keys. Bear in mind that you wont see the key, but when you click 'enter/return' it should work.
- Set API key (`uv run llm keys set groq`)
Now you are ready to use open source models on your local computers.

### 3) First: Extract Metadata!
# Step 1
- The first step to taking our archives from json file to beatbook is to extract metadata. Metadata is simply data about the stories we have and to a reason why this step is crucial is: we do not want to dump all of our sensitive data into commercial models. The ope models we use for this task allow us use llms locally on our computers. So we are able to download the weights or brains of the models onto our devices and use them like we would use Word or Excel.
(How to access their APIs?)
To extract metadata, we will need a python script, and this is where our friend copilot comes in. Go into the copilot chat box and craft a prompt asking it to generate a Python script that extracts metadata from your original json file. Your prompt must be detailed, and put into perspective the kind of beatbook you'd like to create.
For instance consider telling copilot that you want a beatbook that looks at the following, if your aim is to generate a thematic beatbook that looks at how occurrences have changed over time:
- Key field groups:
  - **Temporal:** names, season, year, is_weekend
  - **Content classification:** primary/secondary themes, incident type, severity
  - **Geographic:** location, location type
  - **Contextual:** incident time, weather, agencies, outcomes
For a narrative beatbook
- Key field groups:
  - **People:** names,title
  - **Places:** Maryland, Talbot, St Michael's
- Regardless of the type of beatbook, you want to keep quotes and replace full story content with summaries in output. The reason for this extraction is: we do not want to dump our data into commercial models. We want to generate metadata from our json file directly on our devices without pushing it to the internet. So our json files are not exposed, and we have summaries of our stories, which can now serve as the raw materials for our beatbook.
- Exclude bylines, photographer names, and org names

# PRO TIP: When unsure about what prompts/directions to give your AI tool, ask AI!
# [SAMPLE PROMPT: I'd like to generate metadata from articles that will help me create a beat book that looks at public safety issues thematically over time. For example, common issues that occur in the summer vs. the winter. What would the structure of that metadata need to look like?]

Copilot generates the script and saves it in your directory in a file that will end in .p (since it is a pythin script). While the script will mostly not be easy to understand, being a Python script written in code, you need to look over it and read through the prompt contained in the script. These are more likely to be written in plalin text within the script. Check for things that might not align with your intial intention for the beatbook, a step you should not miss, given AI's affinity for halluciantions.

# Step 2
Now that the script for the extraction is ready, run this command in the terminal to carry out the extraction:
```bash
uv run python metadata.py --model YOUR MODEL --input story_sample.json
```
In the command above, metadata.py will be replaced with the name of the script copilot generated for you. YOUR MODEL should be replaced eith whatever AI open source model you will be using for your extraction. NOTE that is is very important to use OPEN SOURCE MODELS here, This is the part of beatbook generation that requires extra care and attention. You want to be conscious so that you are not running this prompt with a commercial model.
NOTE also, that earlier, we installed Groq llm. If you are unsure what open source model to use, run:
`uv run llm models`
You will get results in your terminal similar to this:
LLMGroq: groq/groq/compound-mini
LLMGroqWhisper: groq/whisper-large-v3
LLMGroq: groq/qwen/qwen3-32b
LLMGroq: groq/llama-3.1-8b-instant (aliases: groq-llama3.1-8b)
LLMGroq: groq/meta-llama/llama-4-scout-17b-16e-instruct
LLMGroq: groq/canopylabs/orpheus-arabic-saudi
LLMGroq: groq/moonshotai/kimi-k2-instruct-0905
LLMGroq: groq/groq/compound
LLMGroq: groq/openai/gpt-oss-120b
LLMGroq: groq/openai/gpt-oss-safeguard-20b
Any of the models that show up should be fine to run the extraction with. So if you choose to use `groq/qwen/qwen3-32b` and your python script and json file are called metada,py and story_sample.json like mine is in the example above, you should run this command in the terminal: 

`uv run python metadata.py --model groq/qwen/qwen3-32b --input story_sample.json`

# Possible problems with extraction
Although it sounds quite straight forward, many things can go wrong with extraction, and you should not be surprised if you run into errors while carrying out your extraction.
One common reason why you might get an error with this process is rate limits. Rate limits are limits on how many API requests you can make at a given time to the AI model. So if you are working with hundreds of stories you are making hundreds of calls to the AI model. You are likely to run into limits at some point, escpecially if you are using free open source models.
[Image of rate limits error]
When you run into rate limits, the metadata already extracted can be lost.
You can fix rate limits by going again to our friend copilot and asking it to modify your script so that it saves output incrementally. So what happens here is that as your python script extracts the metadata. it saves it directly to a new document. Whenever you encounter rate limits, you can move on immediately to a new miodel. The new model continues from where the older model stopped, instead of starting afresh. So say use used this model: `groq/qwen/qwen3-32b`  and extracted 80 stories out of 500 before reaching your rate limits, you can switch to `groq/meta-llama/llama-4-scout-17b-16e-instruct` simply by interrupting the error messages you are receiving using Cntrl/Cmd + C
The you rerun this command with your new model: `uv run python metadata.py --model ggroq/meta-llama/llama-4-scout-17b-16e-instruct --input story_sample.json`


this process: rate limits -solve with incremental saves


### 4) Why This Step Is Critical
- Metadata quality strongly affects beatbook quality
- Extract from full stories before summarization for richer signals
- Summaries reduce token usage while preserving context

### 5) Reliability Practices
- Save output incrementally after each story
- Handle API rate limits and interruptions
- Process large corpora in batches
- Resume from where processing stopped

### 6) Validate Extraction in SQLite + Datasette
- Load JSON into SQLite:
  - `uv run sqlite-utils insert entities.db stories your_json_file_name --pk docref`
- Install/run Datasette:
  - `uv add datasette`
  - `uv run datasette entities.db`
- Use Datasette to:
  - Inspect extraction quality
  - Check false positives/failed parses
  - Compare extracted fields against summaries and actual stories.

### 7) Iteration Loop
- Review extracted output
- Refine prompts/scripts
- Re-run extraction and validation
- Repeat until metadata quality is acceptable

### 8) Generate the Beatbook
- Use a dedicated script (e.g., `generate_thematic_beatbook.py`)
- Example run:
  - `uv run python generate_thematic_beatbook.py --model "anthropic/claude-sonnet-4-" --input thematic_entities_stories.json --output my_narrative_beatbook_v2.md`

### 9) Beatbook Writing Requirements may include
- Reporter-friendly, business-casual tone
- Short, approachable introduction
- Use pre-extracted data and summaries only
- Include follow-up story ideas + disclaimer that data may be outdated.

### 10) Possible problems and how to fix them
