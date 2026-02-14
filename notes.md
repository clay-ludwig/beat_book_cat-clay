## Beat book process 02/14/2026

Before we proceed with this task, users should:
    -Have story samples in a json file
    -Have a Github account
If these requirements are met, the next thing is to set up our environment. Note: we will be using Groq models for this process, but users can feel free to install other models.
## Quick setup for beginners
First create a repository: 
1. Go to github.com -> Log into your account
	- Click the + icon in the top-right, choose New repository.
	- Name it, set Public or Private, then click Create repository.
2. Open your codespace or terminal:
	- Click Code -> Codespaces -> Create codespace.
	- We'll work locally, so open a terminal in your project folder.
3. Install uv (Python tool runner):
	- Run: curl -LsSf https://astral.sh/uv/install.sh | sh
	- Then run: export PATH="$HOME/.local/bin:$PATH"
4. Initialize your project (optional but helpful):
	- Run: uv init --python 3.12
5. Install llm:
	- Run: uv add llm
    - Run: uv add llm install llm-groq (Here, you can include other models: llm-gemini, llm-anthropic, especially if you have access to their API keys).
6. Get a Groq API key:
	- Go to https://console.groq.com
	- Create an account, then create an API key (click on Create API at the top right corner when you log in to Groq).
    - To set up your Groq API key which should help you access the models, run: uv run llm keys set groq. You'll be prompted to enter your API keys. Bear in mind that you wont see the key, but when you click 'enter/return' it should work.

    [Next: extract entities. You choose what groq model to use]