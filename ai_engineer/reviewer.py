import os
import requests
from openai import OpenAI

# 1. Read the diff to see what changed
try:
    with open("pr_diff.txt", "r") as f:
        diff_text = f.read()
except FileNotFoundError:
    print("No diff found, exiting.")
    exit(0)

# If diff is empty or too small, skip
if len(diff_text.strip()) < 10:
    print("Empty diff, skipping review.")
    exit(0)

# 2. Engage the LLM with HA-specific context
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("No API key found. Skipping AI review.")
    exit(0)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

prompt = f"""
You are an expert Home Assistant Core maintainer reviewing a pull request for the 'Global Earthquake Tracker' custom integration.
Review the following code diff. 

Look specifically for these common Home Assistant integration mistakes:
1. 'sensor.py': Ensure new entities define a proper `_attr_unique_id` or `_attr_has_entity_name`.
2. 'coordinator.py': Ensure no blocking I/O calls (like `requests.get`) are made directly; they must be wrapped in `await hass.async_add_executor_job` or use `aiohttp`.
3. 'config_flow.py': Look for missing string translations.
4. General: Check for overly broad exception handling (e.g., bare `except:`).

If the code looks perfect, respond ONLY with "APPROVED".
If there are issues, write a short, polite GitHub PR comment highlighting the specific files and line numbers, and suggest the fix.

Diff:
{diff_text}
"""

completion = client.chat.completions.create(
    model="meta-llama/llama-3-8b-instruct:free",  # Completely free model!
    messages=[{"role": "user", "content": prompt}],
)

review_comment = completion.choices[0].message.content.strip()

# 3. Post the comment back to GitHub
if review_comment != "APPROVED":
    print("Issues found. Posting comment to PR...")

    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")
    token = os.getenv("GITHUB_TOKEN")

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"body": f"🤖 **AI Maintainer Review:**\n\n{review_comment}"}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print("Comment posted successfully!")
    else:
        print(f"Failed to post comment: {response.text}")
else:
    print("Code looks good! No comment needed.")
