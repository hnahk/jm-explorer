import re

text = open("app.html", "r", encoding="utf-8").read()

# Wrap dashboard logic
text = text.replace("const D=window.DASH;", "(() => {\nconst D=window.DASH;")

# Wrap explorer logic
text = text.replace("// Explorer Logic\n\nconst D = window.JM", "})();\n\n// Explorer Logic\n(() => {\nconst D = window.JM")

# Close explorer logic and chop off the junk at the bottom
# We look for `header();buildFilters();render();`
idx = text.find("header();buildFilters();render();")
if idx != -1:
    idx += len("header();buildFilters();render();")
    text = text[:idx] + "\n})();\n</script>\n</body>\n</html>\n"
else:
    print("Could not find the end of explorer logic")
    exit(1)

open("app.html", "w", encoding="utf-8").write(text)
print("app.html fixed")
