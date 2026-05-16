with open(r'c:\Users\HP\Desktop\Fi_assignment\app\static\css\styles.css', 'rb') as f:
    content = f.read()

# Find the start of the garbled text
# It likely starts after "border: 1px solid #e2e8f0;\n}"
target = b'border: 1px solid #e2e8f0;\r\n}'
idx = content.find(target)
if idx != -1:
    clean_content = content[:idx + len(target)]
    clean_content += b'\n\nbody.light-mode .note-card {\n  background: white;\n  border-color: #e2e8f0;\n  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);\n}\n\nbody.light-mode .note-card:hover {\n  border-color: var(--primary);\n  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);\n}\n'
    with open(r'c:\Users\HP\Desktop\Fi_assignment\app\static\css\styles.css', 'wb') as f:
        f.write(clean_content)
    print("Fixed")
else:
    print("Target not found")
