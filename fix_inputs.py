import os
import re

template_dir = r"d:\Projects\exam\Exam-Management-Automation-System\templates"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    bad_classes = [
        "shadow-md shadow-slate-200/50 hover:shadow-lg transition-all duration-300",
        "shadow-md shadow-slate-200/50 hover:shadow-lg",
        "shadow-md hover:shadow-lg transition-all duration-300"
    ]
    
    def replacer(match):
        tag = match.group(0)
        for bad in bad_classes:
            tag = tag.replace(bad, "shadow-sm transition-colors")
        return tag

    new_content = re.sub(r'<(input|select|textarea)\b[^>]*>', replacer, content, flags=re.IGNORECASE)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, _, files in os.walk(template_dir):
    for file in files:
        if file.endswith('.html'):
            process_file(os.path.join(root, file))

print("Done fixing inputs.")
