import os
import re
import sys
import requests

# Set up API configuration
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    print("❌ No OPENROUTER_API_KEY found in environment secrets. Exiting.")
    sys.exit(1)

# Detect repository details
REPO = os.getenv("REPO", "Global-Earthquake-Tracker-for-Home-Assistant")
PROJECT_NAME = REPO.split("/")[-1].replace("-", " ").replace("_", " ").title()

print(f"🤖 Starting AI Self-Repair Agent for {PROJECT_NAME}...")

# Check for common CI log files generated during testing
LOG_FILES = [
    "pytest_log.txt",
    "pytest.log",
    "test_results.log",
    "ruff_log.txt",
    "error_log.txt",
]
error_log_content = ""
found_log = None

for log_file in LOG_FILES:
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    error_log_content = content
                    found_log = log_file
                    break
        except Exception as e:
            print(f"⚠️ Failed to read log file {log_file}: {e}")

if not error_log_content:
    print("✅ No test failure logs detected. Assuming build is clean! Exiting.")
    sys.exit(0)

print(f"🔍 Analyzing error log from: {found_log}")

# Try to extract the failing file path using common python traceback patterns
target_file = None
file_match = re.search(r'File "([^"]+\.py)", line \d+', error_log_content)
if file_match:
    target_file = file_match.group(1)
else:
    # Fallback to scanning for common integration/app file structures if traceback parsing is ambiguous
    for root, _, files in os.walk("."):
        if (
            "ai_engineer" in root
            or ".github" in root
            or ".git" in root
            or "venv" in root
        ):
            continue
        for file in files:
            if file.endswith(".py") and file != "repair.py":
                # Look for mentions of files in the error logs
                if file in error_log_content:
                    target_file = os.path.join(root, file)
                    break
        if target_file:
            break

if not target_file or not os.path.exists(target_file):
    print(
        "❌ Could not identify which source file caused the failure from the log traceback."
    )
    sys.exit(1)

print(f"🎯 Target file identified for repair: {target_file}")

try:
    with open(target_file, "r", encoding="utf-8") as f:
        original_code = f.read()
except Exception as e:
    print(f"❌ Failed to load target file {target_file}: {e}")
    sys.exit(1)

# Construct a detailed prompt to instruct the model to fix the code
BACKTICKS = "`" * 3
prompt = f"""
You are the AI Staff Engineer for '{PROJECT_NAME}'. Your persona is Snoop Dogg.
A unit test or quality linting check has failed on our code base, and your job is to analyze the failure, diagnose the bug, and write the corrected version of the file.

Target File to Fix: {target_file}

Here is the current broken code of the file:
{BACKTICKS}python
{original_code}
{BACKTICKS}

Here is the error log/traceback showing why it failed:
{BACKTICKS}
{error_log_content}
{BACKTICKS}

CRITICAL INSTRUCTIONS:
1. Return ONLY the fully rewritten and corrected Python code for the file.
2. Do NOT wrap your response in triple backticks ({BACKTICKS}) or a code block. Output the raw text directly.
3. Make sure the code is syntactically perfect, handles the error correctly, and passes the tests.
4. Keep the code style intact.
"""

openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/" + REPO,
    "X-Title": f"{PROJECT_NAME} Self-Healing Agent",
}
payload = {
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": prompt}],
}

fixed_code = ""
max_retries = 5
delay = 1

for attempt in range(max_retries):
    try:
        print(f"Sending request to OpenRouter (Attempt {attempt + 1}/{max_retries})...")
        response = requests.post(
            openrouter_url, headers=headers, json=payload, timeout=45.0
        )
        if response.status_code == 200:
            result = response.json()
            fixed_code = result["choices"][0]["message"]["content"].strip()
            break
        else:
            print(f"API Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Attempt failed with network exception: {e}")

    if attempt < max_retries - 1:
        time_to_sleep = delay
        print(f"Retrying in {time_to_sleep}s...")
        import time

        time.sleep(time_to_sleep)
        delay *= 2

if not fixed_code:
    print("❌ Failed to get a response from OpenRouter after maximum retries.")
    sys.exit(1)

# Strip code block decorators if the model returned them
pattern = rf"^{BACKTICKS}(?:python)?\n|\n{BACKTICKS}$"
fixed_code = re.sub(pattern, "", fixed_code).strip()

try:
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(fixed_code)
    print(f"✅ Successfully wrote the repaired code back to {target_file}!")
except Exception as e:
    print(f"❌ Failed to write repaired code to file: {e}")
    sys.exit(1)

# Write the explanation for the pull request body so the workflow can use it
pr_prompt = f"""
You are the AI Staff Engineer for '{PROJECT_NAME}'. Your persona is Snoop Dogg.
You just successfully fixed a test suite crash in {target_file}!

Here was the error:
{error_log_content[:500]}

Explain in a smooth, professional, Snoop Dogg-styled way what went wrong and how you fixed it. Keep it under 3 paragraphs.
DO NOT use code blocks or backticks.
"""

try:
    pr_payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": pr_prompt}],
    }
    response = requests.post(
        openrouter_url, headers=headers, json=pr_payload, timeout=25.0
    )
    if response.status_code == 200:
        explanation = response.json()["choices"][0]["message"]["content"].strip()
        with open("pr_body.txt", "w", encoding="utf-8") as f:
            f.write(explanation)
        print("📝 Saved PR description metadata successfully!")
except Exception as e:
    # Non-blocking failure: write fallback PR description
    with open("pr_body.txt", "w", encoding="utf-8") as f:
        f.write(
            f"The AI Staff Engineer has applied a self-healing fix to resolve test suite failures in {target_file}."
        )
    print(f"⚠️ Explanatory meta generation failed: {e}. Saved fallback description.")
