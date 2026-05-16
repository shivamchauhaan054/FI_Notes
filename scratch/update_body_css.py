with open(r'c:\Users\HP\Desktop\Fi_assignment\app\static\css\styles.css', 'r', encoding='utf-8') as f:
    content = f.read()

old = """body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.6;
  overflow-x: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}"""

new = """body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.6;
  overflow-x: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
  transition: background-color 0.4s ease, color 0.4s ease;
}"""

if old in content:
    content = content.replace(old, new)
    with open(r'c:\Users\HP\Desktop\Fi_assignment\app\static\css\styles.css', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced")
else:
    # Try with \r\n
    old_rn = old.replace('\n', '\r\n')
    new_rn = new.replace('\n', '\r\n')
    if old_rn in content:
        content = content.replace(old_rn, new_rn)
        with open(r'c:\Users\HP\Desktop\Fi_assignment\app\static\css\styles.css', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Replaced (CRLF)")
    else:
        print("Target not found")
