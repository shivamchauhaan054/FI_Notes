with open(r'c:\Users\HP\Desktop\Fi_assignment\app\static\css\styles.css', 'r', encoding='utf-16' if open(r'c:\Users\HP\Desktop\Fi_assignment\app\static\css\styles.css', 'rb').read(2) == b'\xff\xfe' else 'utf-8') as f:
    content = f.read()

# Remove the garbage if any (from previous echo commands)
content = content.replace('\x00', '')

# Append the new styles cleanly if not already there
styles = """
/* Toggle Switch */
.toggle-switch {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
}
.toggle-switch input {
  display: none;
}
.toggle-slider {
  width: 34px;
  height: 18px;
  background: var(--border);
  border-radius: 20px;
  position: relative;
  transition: 0.3s;
}
.toggle-slider::before {
  content: '';
  position: absolute;
  width: 14px;
  height: 14px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: 0.3s;
}
.toggle-switch input:checked + .toggle-slider {
  background: var(--primary);
}
.toggle-switch input:checked + .toggle-slider::before {
  transform: translateX(16px);
}
.toggle-label {
  user-select: none;
}
"""

if ".toggle-switch" not in content:
    content += styles

with open(r'c:\Users\HP\Desktop\Fi_assignment\app\static\css\styles.css', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated CSS")
