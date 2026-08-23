"""Probe: can layout_pipeline.py (Windows python.exe) launch Freerouting?
Checks java discovery, exit codes, and whether stdout/stderr are capturable -
all needed before the router becomes an unattended pipeline stage."""
import subprocess, shutil, os

JAR = "C:\\Users\\Dushyant\\pcbgen_tools\\freerouting-2.2.4.jar"
print("jar exists:", os.path.exists(JAR))

print("=== java discovery ===")
for name in ("java", "java.exe"):
    print("  shutil.which(%r): %r" % (name, shutil.which(name)))

print("=== can we run it and capture output? ===")
try:
    r = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=60)
    print("  rc:", r.returncode)
    print("  stdout:", repr(r.stdout[:80]))
    print("  stderr:", repr(r.stderr[:80]))
except Exception as e:
    print("  FAILED:", repr(e))

print("=== does the jar respond, and what exit code? ===")
try:
    r = subprocess.run(["java", "-jar", JAR, "-help"],
                       capture_output=True, text=True, timeout=120)
    print("  rc:", r.returncode, "| stdout bytes:", len(r.stdout),
          "| stderr bytes:", len(r.stderr))
    print("  first line:", (r.stdout or r.stderr).splitlines()[:1])
except Exception as e:
    print("  FAILED:", repr(e))
