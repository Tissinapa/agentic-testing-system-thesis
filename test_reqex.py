import re

requirements = open("docs/requirements_java.md").read()

# Try different patterns
match1 = re.search(r'Bearer\s+(\S+)', requirements)
match2 = re.search(r'Token value:\s*(\S+)', requirements)

print("Bearer match:", match1.group(1) if match1 else None)
print("Token value match:", match2.group(1) if match2 else None)