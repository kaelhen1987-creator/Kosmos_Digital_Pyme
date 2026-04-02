import os
import re

mappings = {
    'ft.alignment.top_left': 'ft.Alignment(-1.0, -1.0)',
    'ft.alignment.top_center': 'ft.Alignment(0.0, -1.0)',
    'ft.alignment.top_right': 'ft.Alignment(1.0, -1.0)',
    'ft.alignment.center_left': 'ft.Alignment(-1.0, 0.0)',
    'ft.alignment.center': 'ft.Alignment(0.0, 0.0)',
    'ft.alignment.center_right': 'ft.Alignment(1.0, 0.0)',
    'ft.alignment.bottom_left': 'ft.Alignment(-1.0, 1.0)',
    'ft.alignment.bottom_center': 'ft.Alignment(0.0, 1.0)',
    'ft.alignment.bottom_right': 'ft.Alignment(1.0, 1.0)'
}

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    new_content = content
    for old, new in mappings.items():
        new_content = new_content.replace(old, new)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Patched {filepath}")

for root, dirs, files in os.walk('app'):
    for file in files:
        if file.endswith('.py'):
            process_file(os.path.join(root, file))
            
process_file('main.py')
