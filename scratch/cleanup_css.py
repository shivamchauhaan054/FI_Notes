with open(r'c:\Users\HP\Desktop\Fi_assignment\app\static\css\styles.css', 'r', encoding='utf-16' if open(r'c:\Users\HP\Desktop\Fi_assignment\app\static\css\styles.css', 'rb').read(2) == b'\xff\xfe' else 'utf-8') as f:
    content = f.read()

content = content.replace('\x00', '')

# Remove the old toggle switch styles
import re
content = re.sub(r'/\* Toggle Switch \*/.*?user-select: none;\}', '', content, flags=re.DOTALL)

# Add new active toggle styles
active_styles = """
.theme-toggle.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
  box-shadow: 0 0 15px var(--primary-glow);
}
"""

if ".theme-toggle.active" not in content:
    content += active_styles

with open(r'c:\Users\HP\Desktop\Fi_assignment\app\static\css\styles.css', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated CSS")
