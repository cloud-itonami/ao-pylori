#!/usr/bin/env python3
"""pylori-pharmacy evidence: read-only measurement of local catalogue state.

No network calls (cron runs unattended and terminal HTTP is denied).
Measurement of record for pylori-pharmacy. The agent must not re-measure.
On any failure print a REFUSED banner and UNMEASURED lines and exit 0:
a measurement we could not take must never look like a clean measurement.
"""
import json
import os
import time

NAME = "pylori-pharmacy"
PROFILE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.join(PROFILE, "workspace")
CATALOG = os.path.join(WS, "catalogs", "pharmacy-catalog.edn")
SOURCES = os.path.join(WS, "sources.edn")
LEDGER = os.path.join(WS, "ledger.jsonl")


def count_tokens(path, token):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return sum(1 for line in fh
                       if token in line and not line.lstrip().startswith(";"))
    except OSError:
        return None


def age_hours(path):
    try:
        return round((time.time() - os.path.getmtime(path)) / 3600.0, 2)
    except OSError:
        return None


def main():
    problems = []
    for path in (CATALOG, SOURCES):
        if not os.path.isfile(path):
            problems.append("missing:" + os.path.basename(path))
    if problems:
        print("REFUSED: cannot measure (" + ", ".join(problems) + ")")
        for key in ("catalog_entries", "sources", "ledger_rows", "newest_catalog_age_hours"):
            print("UNMEASURED\t%s.%s\t%s" % (NAME, key, ";".join(problems)))
        return 0

    entries = count_tokens(CATALOG, ":entry/id")
    sources = count_tokens(SOURCES, ":source/id")
    rows = count_tokens(LEDGER, '"ts"')
    age = age_hours(CATALOG)
    m = {
        "catalog_entries": entries,
        "sources": sources,
        "ledger_rows": rows if rows is not None else 0,
        "newest_catalog_age_hours": age,
    }
    for key in ("catalog_entries", "sources", "ledger_rows", "newest_catalog_age_hours"):
        value = m[key]
        print("MEASURE\t%s.%s\t%s" % (NAME, key, value if value is not None else "UNMEASURED"))
    print("STATUS\tok")
    try:
        with open(LEDGER, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                 "bot": NAME, "m": m}, sort_keys=True) + "\n")
    except OSError as exc:
        print("UNMEASURED\t%s.ledger_append\t%s" % (NAME, exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
