import os
from openai import OpenAI

# 1. Read the diff of the merged PR
try:
    with open("merged_diff.txt", "r") as f:
        diff_text = f.read()
except FileNotFoundError:
    print("No diff found. Exiting.")
    exit(0)

if not diff_text.strip() or len(diff_text) < 10:
    print("Diff is too small or empty. Exiting.")
    exit(0)

# 2. Engage OpenRouter
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("No API key found. Exiting.")
    exit(0)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

prompt = f"""
You are an AI Staff Engineer maintaining a Home Assistant integration. 
A Pull Request was just merged. Read the diff and write ONE single, highly robust `pytest` function that covers a new edge case introduced by this code.

Your response MUST exactly follow this plain text format:
FILEPATH: tests/test_auto_generated.py
CODE:
<paste the full python test code here including imports>

Do not include any other text or markdown blocks.

Diff:
{diff_text}
"""

print("Analyzing merged code and generating test...")
try:
    completion = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct:free",
        messages=[dict(role="user", content=prompt)]
    )
    
    response_text = completion.choices[0].message.content.strip()
    
    # 3. Parse the custom text format
    lines = response_text.splitlines()
    file_path = None
    code_lines = []
    is_code = False
    
    for line in lines:
        if line.startswith("FILEPATH:"):
            file_path = line.replace("FILEPATH:", "").strip()
        elif line.startswith("CODE:"):
            is_code = True
        elif is_code:
            # Clean up markdown if the LLM hallucinated it
            if not line.startswith("```"):
                code_lines.append(line)
                
    new_code = "\n".join(code_lines)
    
    # 4. Save the new test to the disk
    if file_path and new_code:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(new_code)
        print(f"Successfully wrote new test to {file_path}")
    else:
        print("Could not parse the LLM response correctly.")
        
except Exception as e:
    print(f"Failed to generate test: {e}")