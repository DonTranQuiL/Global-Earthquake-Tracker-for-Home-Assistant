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
LOG_FILES = ["pytest_log.txt", "pytest.log", "test_results.log", "ruff_log.txt", "error_log.txt"]
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

# 1. Gather all potential .py files mentioned in the logs
candidates = []
# Standard Python pattern -> File "path/to/file.py", line 12
for match in re.finditer(r'File "([^"]+\.py)", line \d+', error_log_content):
    candidates.append(match.group(1))
# Pytest pattern -> path/to/file.py:12 (with or without trailing text)
for match in re.finditer(r'([\w/._-]+\.py):(\d+)', error_log_content):
    candidates.append(match.group(1))

# Clean paths (remove runner environment prefixes) and verify they actually exist locally
existing_candidates = []
for c in candidates:
    clean_path = c.split(f"{REPO.split('/')[-1]}/")[-1]  # Strip absolute runner paths
    if os.path.exists(clean_path) and os.path.isfile(clean_path):
        if "ai_engineer" not in clean_path and ".github" not in clean_path:
            existing_candidates.append(clean_path)

# De-duplicate candidate list
existing_candidates = list(dict.fromkeys(existing_candidates))

# 2. Prioritize fixing actual source files over test files
target_file = None
if existing_candidates:
    non_test_candidates = [c for c in existing_candidates if "test" not in c.lower()]
    if non_test_candidates:
        target_file = non_test_candidates[0]
        print(f"🎯 Code file prioritized for repair: {target_file}")
    else:
        target_file = existing_candidates[0]
        print(f"🎯 Test file prioritized for repair: {target_file}")

# Fallback: Scan root if log parser completely failed
if not target_file:
    print("⚠️ Ambiguous traceback. Scanning workspace for candidate files mentioned in log...")
    for root, _, files in os.walk("."):
        if "ai_engineer" in root or ".github" in root or ".git" in root or "venv" in root:
            continue
        for file in files:
            if file.endswith(".py") and file != "repair.py":
                if file in error_log_content:
                    target_file = os.path.join(root, file)
                    break
        if target_file:
            break

if not target_file or not os.path.exists(target_file):
    print("❌ Could not safely identify which local python file to target for repair.")
    sys.exit(1)

print(f"🎯 Target file verified: {target_file}")

try:
    with open(target_file, "r", encoding="utf-8") as f:
        original_code = f.read()
except Exception as e:
    print(f"❌ Failed to load target file {target_file}: {e}")
    sys.exit(1)

# Construct prompt instructing the AI
BACKTICKS = "`" * 3
prompt = f"""
You are the AI Staff Engineer for '{PROJECT_NAME}'. Your persona is Snoop Dogg.
A unit test or quality linting check has failed on our codebase. Analyze the failure, diagnose the bug in '{target_file}', and output the corrected code.

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
1. You must output the entire corrected Python file inside a single standard markdown code block starting with {BACKTICKS}python and ending with {BACKTICKS}.
2. Do NOT write conversational explanations, comments, or raps INSIDE that code block. Keep it strictly as runnable python.
3. You can write your smooth Snoop Dogg commentary and explanation OUTSIDE of the code block (either before or after).
4. Keep the original style, structure, and imports of the code intact except for the specific bug fix.
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
        print(f"Sending repair request to OpenRouter (Attempt {attempt + 1}/{max_retries})...")
        response = requests.post(openrouter_url, headers=headers, json=payload, timeout=45.0)
        if response.status_code == 200:
            result = response.json()
            fixed_code = result["choices"][0]["message"]["content"].strip()
            break
        else:
            print(f"API Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Attempt failed with network exception: {e}")
    
    if attempt < max_retries - 1:
        print(f"Retrying in {delay}s...")
        import time
        time.sleep(delay)
        delay *= 2

if not fixed_code:
    print("❌ Failed to get a response from OpenRouter after maximum retries.")
    sys.exit(1)

# Extract python code securely if the AI wrapped it in markdown code blocks
match = re.search(rf"{BACKTICKS}python\s*(.*?)\s*{BACKTICKS}", fixed_code, re.DOTALL | re.IGNORECASE)
if match:
    fixed_code = match.group(1).strip()
else:
    # Fallback to general code block
    match = re.search(rf"{BACKTICKS}\s*(.*?)\s*{BACKTICKS}", fixed_code, re.DOTALL)
    if match:
        fixed_code = match.group(1).strip()

# Clean up remaining markdown artifacts
pattern = rf"^{BACKTICKS}(?:python)?\n|\n{BACKTICKS}$"
fixed_code = re.sub(pattern, "", fixed_code).strip()

# ⚠️ CRITICAL UPGRADE: Python Syntax Compilation Shield
try:
    compile(fixed_code, target_file, 'exec')
    print("✅ Fixed code compiled successfully! Valid python syntax verified.")
except SyntaxError as e:
    print(f"❌ Syntax validation FAILED on the code returned by AI: {e}")
    print("Aborting file overwrite and PR creation to prevent broken code from being committed.")
    sys.exit(1)

try:
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(fixed_code)
    print(f"✅ Successfully wrote the repaired code back to {target_file}!")
except Exception as e:
    print(f"❌ Failed to write repaired code to file: {e}")
    sys.exit(1)

# Write explanation for the Pull Request description
pr_prompt = f"""
You are the AI Staff Engineer for '{PROJECT_NAME}'. Your persona is Snoop Dogg.
You successfully fixed a test suite crash in {target_file}!

Here was the error:
{error_log_content[:400]}

Explain in a smooth, professional, Snoop Dogg-styled way what went wrong and how you fixed it. Keep it under 3 paragraphs.
DO NOT use code blocks or backticks.
"""

try:
    pr_payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": pr_prompt}],
    }
    response = requests.post(openrouter_url, headers=headers, json=pr_payload, timeout=25.0)
    if response.status_code == 200:
        explanation = response.json()["choices"][0]["message"]["content"].strip()
        with open("pr_body.txt", "w", encoding="utf-8") as f:
            f.write(explanation)
        print("📝 Saved PR description metadata successfully!")
except Exception as e:
    with open("pr_body.txt", "w", encoding="utf-8") as f:
        f.write(f"The AI Staff Engineer has applied a self-healing fix to resolve test suite failures in {target_file}.")
    print(f"⚠️ Explanatory meta generation failed: {e}. Saved fallback description.")
