import os
import json
import requests
from openai import OpenAI

# 1. Grab issue data from GitHub Actions environment
issue_title = os.getenv("ISSUE_TITLE", "")
issue_body = os.getenv("ISSUE_BODY", "")
issue_number = os.getenv("ISSUE_NUMBER")
repo = os.getenv("GITHUB_REPOSITORY")
token = os.getenv("GITHUB_TOKEN")
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    print("No OpenRouter API key found. Exiting safely.")
    exit(0)

# 2. Engage OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

prompt = f"""
You are an AI maintainer for a Home Assistant integration called "Global Earthquake Tracker".
A user just opened a new GitHub issue. 

Title: {issue_title}
Body: {issue_body}

Your job is to analyze the issue and return a JSON object with two keys:
1. "labels": A list of strings. Choose from: ["bug", "enhancement", "question", "needs-info"]. 
2. "comment": A polite string responding to the user. 
   - If it seems like a bug but they didn't provide error logs or their Home Assistant version, ask for them nicely.
   - If it's a feature request, thank them for the idea.
   - If they provided everything needed, just say "Thanks for opening this! The AI maintainer has flagged it for review."
   - Keep it short and friendly.

Return ONLY valid JSON. Do not include markdown formatting or explanations.
{{
    "labels": ["bug", "needs-info"],
    "comment": "your response here"
}}
"""

print("Analyzing issue...")
try:
    completion = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct:free",
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = completion.choices[0].message.content.strip()
    
    # Strip markdown if the AI accidentally included it
    if response_text.startswith("```json"):
        response_text = response_text[7:-3]
    elif response_text.startswith("```"):
        response_text = response_text[3:-3]
        
    triage_data = json.loads(response_text)
    labels = triage_data.get("labels", [])
    comment = triage_data.get("comment", "")
    
except Exception as e:
    print(f"Failed to analyze issue: {e}")
    exit(1)

# 3. Setup GitHub API Auth
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json"
}

# 4. Apply the Labels to the Issue
if labels:
    print(f"Applying labels: {labels}")
    label_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/labels"
    requests.post(label_url, headers=headers, json={"labels": labels})

# 5. Post the Reply Comment
if comment:
    print("Posting comment...")
    comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    requests.post(comment_url, headers=headers, json={"body": f"🤖 **AI Triage:**\n\n{comment}"})

print("Triage complete!")