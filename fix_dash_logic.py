import os, re
import subprocess

# get the original dashboard.html
raw = subprocess.check_output(["git", "show", "origin/main~4:dashboard.html"], text=True)

# extract the script block (we only want the content inside <script>)
# Note: dashboard.html has only one <script> block at the bottom.
match = re.search(r'<script>(.*?)</script>', raw, re.DOTALL)
if match:
    dash_script = match.group(1).strip()
    # In dashboard.html, the script had `const D=window.DASH;` at the top.
    # In app.html, the theme toggle `#theme` is already defined by Explorer, 
    # but the dashboard used `#theme` too. I renamed it to `#theme-dash` in app.html.
    # Let's fix that.
    dash_script = dash_script.replace("$('#theme').onclick", "$('#theme-dash').onclick")
    
    # read app.html
    app_html = open("app.html", "r", encoding="utf-8").read()
    
    # insert dash_script before the closing </script> tag
    new_app = app_html.replace("</script>\n</body>", "\n" + dash_script + "\n</script>\n</body>")
    
    open("app.html", "w", encoding="utf-8").write(new_app)
    print("Injected dashboard logic into app.html")
else:
    print("Could not find script block")
