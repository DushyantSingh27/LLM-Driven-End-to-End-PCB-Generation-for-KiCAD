"""routing.py - the autorouting bridge (DSN out, Freerouting, SES back in).

Runs under KiCad's bundled Windows python.exe. Verified facts this rests on:
  - pcbnew.ExportSpecctraDSN(board, path) / ImportSpecctraSES(board, path) exist
    and round-trip: import grew a board 38->105 tracks, 38->44 vias, and KiCad's
    own connectivity count matched the router's report exactly.
  - Freerouting 2.2.4 logs to STDOUT and exits 0 on success.
  - java is discoverable via shutil.which under Windows python.exe.

Nothing here is hardcoded to one machine: the jar comes from FREEROUTING_JAR or
a short list of conventional locations, and java from PATH. Both failures are
loud and name the fix.
"""
import os
import re
import shutil
import subprocess

import pcbnew

DEFAULT_JAR_LOCATIONS = (
    os.path.join(os.path.expanduser("~"), "pcbgen_tools", "freerouting-2.2.4.jar"),
    "C:\\Program Files\\freerouting\\freerouting.jar",
)

ROUTER_TIMEOUT_S = 900          # 15 min; the benchmark routes in ~10s


def find_java():
    exe = shutil.which("java") or shutil.which("java.exe")
    if not exe:
        raise RuntimeError(
            "java not found on PATH. Freerouting needs a Java runtime "
            "(JRE 25 for 2.2.4). Install it or add it to PATH.")
    return exe


def find_jar():
    env = os.environ.get("FREEROUTING_JAR")
    if env:
        if not os.path.exists(env):
            raise RuntimeError("FREEROUTING_JAR points at a missing file: %r" % env)
        return env
    for cand in DEFAULT_JAR_LOCATIONS:
        if os.path.exists(cand):
            return cand
    raise RuntimeError(
        "freerouting jar not found. Set FREEROUTING_JAR to its path, or place "
        "it at one of: %s" % ", ".join(DEFAULT_JAR_LOCATIONS))


def export_dsn(board, dsn_path, router_clearance_mm=None, scratch_path=None):
    """Write a Specctra DSN for the router.

    router_clearance_mm inflates the exported netclass clearance so that
    satisfying copper-to-copper also satisfies KiCad's hole-to-copper rule,
    which the DSN does not carry (measured: 14+ hole violations without it).

    The inflation is applied IN MEMORY and reverted immediately after export,
    so the board's real design rules are untouched and DRC stays honest.
    A scratch FILE cannot be used: KiCad 9 stores netclass definitions in the
    .kicad_pro, so a save/reload round-trip through a temp path loses them
    (measured: scratch board came back with no classes and KiCad's 0.2mm
    default). scratch_path is accepted but unused, kept for call compatibility.
    """
    ns = board.GetDesignSettings().m_NetSettings
    saved = {}
    if router_clearance_mm is not None:
        for key in list(ns.GetNetclasses().keys()):
            name = str(key)
            nc = ns.GetNetClassByName(name)
            saved[name] = nc.GetClearance()
            nc.SetClearance(pcbnew.FromMM(router_clearance_mm))
        d = ns.GetDefaultNetclass()
        saved["__default__"] = d.GetClearance()
        d.SetClearance(pcbnew.FromMM(router_clearance_mm))
        ns.RecomputeEffectiveNetclasses()

    try:
        if not pcbnew.ExportSpecctraDSN(board, dsn_path):
            raise RuntimeError("ExportSpecctraDSN failed for %r" % dsn_path)
    finally:
        if saved:
            for name, val in saved.items():
                if name == "__default__":
                    ns.GetDefaultNetclass().SetClearance(val)
                else:
                    ns.GetNetClassByName(name).SetClearance(val)
            ns.RecomputeEffectiveNetclasses()
    return dsn_path


def parse_router_log(text):
    """Structured result from Freerouting's stdout."""
    out = {"started_unrouted": None, "final_unrouted": None, "passes": 0,
           "unrouted_nets": [], "saved": False, "warnings": []}
    m = re.search(r"started with (\d+) unrouted nets", text)
    if m:
        out["started_unrouted"] = int(m.group(1))
    m = re.search(r"final score:\s*[\d.]+\s*\((\d+) unrouted\)", text)
    if m:
        out["final_unrouted"] = int(m.group(1))
    out["passes"] = len(re.findall(r"Auto-router pass #(\d+)", text))
    out["unrouted_nets"] = [(n, int(c)) for n, c in
                            re.findall(r"Net '([^']+)' \((\d+) unrouted", text)]
    out["saved"] = bool(re.search(r"Saving '", text))
    out["warnings"] = re.findall(r"WARN\s+\S*\s*(.+)", text)
    return out


def run_freerouting(dsn_path, ses_path, exclude_nets=(),
                    timeout_s=ROUTER_TIMEOUT_S, jar=None, java=None):
    """Route headlessly. Returns (ok, stats, raw_log).
    exclude_nets: nets the router must not touch - typically plane nets that
    have already been stitched, since routing them would duplicate that work."""
    java = java or find_java()
    jar = jar or find_jar()
    cmd = [java, "-jar", jar, "-de", dsn_path, "-do", ses_path]
    if exclude_nets:
        cmd += ["-inc", ",".join(exclude_nets)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return False, {"error": "router timed out after %ss" % timeout_s}, ""
    log = (r.stdout or "") + (r.stderr or "")
    stats = parse_router_log(log)
    ok = (r.returncode == 0 and stats["saved"] and os.path.exists(ses_path))
    stats["returncode"] = r.returncode
    return ok, stats, log


def import_ses(board, ses_path):
    """Import routed copper. Returns (traces, vias) counts after import.
    Verified non-destructive: pre-existing stitching survives."""
    before_t = len([t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T])
    before_v = len([t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T])
    if not pcbnew.ImportSpecctraSES(board, ses_path):
        raise RuntimeError("ImportSpecctraSES failed for %r" % ses_path)
    after_t = len([t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T])
    after_v = len([t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T])
    if after_t < before_t or after_v < before_v:
        raise RuntimeError(
            "SES import destroyed existing copper: tracks %d->%d, vias %d->%d"
            % (before_t, after_t, before_v, after_v))
    return after_t, after_v
