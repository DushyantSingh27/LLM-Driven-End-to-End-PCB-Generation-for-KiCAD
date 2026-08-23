"""run_context.py - a clean output directory per run.

Stale artifacts silently corrupted three separate measurements during
development: KiCad 9 keeps netclass DEFINITIONS in the .kicad_pro, and
SaveBoard will not overwrite an existing one, so a leftover project file
overrides freshly computed design rules with no warning. Reusing output paths
makes that failure mode possible; a fresh directory per run makes it
impossible. Pure stdlib - importable from either interpreter.
"""
import os
import shutil
import datetime


def new_run_dir(root, name, keep_last=None, clean=True):
    """Return an empty directory for this run: <root>/<name>/<timestamp>/.
    clean=True guarantees emptiness. keep_last=N prunes older runs."""
    # Uniqueness must be structural, not clock-dependent: two runs inside the
    # same second collided on one directory and the second wiped the first.
    base = os.path.join(root, name)
    os.makedirs(base, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path, n = os.path.join(base, stamp), 1
    while os.path.exists(path):
        path = os.path.join(base, "%s-%02d" % (stamp, n))
        n += 1
    os.makedirs(path)

    if keep_last:
        runs = sorted(d for d in os.listdir(base)
                      if os.path.isdir(os.path.join(base, d)))
        for old in runs[:-keep_last]:
            shutil.rmtree(os.path.join(base, old), ignore_errors=True)

    latest = os.path.join(base, "latest.txt")
    with open(latest, "w") as f:
        f.write(path)
    return path


def artifact(run_dir, filename):
    return os.path.join(run_dir, filename)
