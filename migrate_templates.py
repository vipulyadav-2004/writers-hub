import glob, re

for f in glob.glob('project/templates/*.html'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # regex matches: {{ url_for('static', filename='FOLDER/' + VARIABLE) }}
    # or {{ url_for('static', filename='FOLDER/' + VARIABLE ) }} - with spaces
    new_content = re.sub(
        r"\{\{\s*url_for\('static',\s*filename='(profile_pics|post_pics|message_pics)/'\s*\+\s*([^}]+?)\)\s*\}\}",
        r"{{ get_image_url(\2, '\1') }}",
        content
    )
    
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Updated {f}")
