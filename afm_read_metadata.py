# Minimal JPK metadata check
# Requires: afmformats (pip install afmformats)


from pathlib import Path
from pprint import pprint
import sys

import afmformats as af

# --- 1) PUT YOUR FILE HERE ---
JPK_PATH = r"PC-3-2029-bleb-25-dish1-data-2025.09.05-10.47.17.093.jpk-force-map"
# -----------------------------

def main():
    p = Path(JPK_PATH)
    if not p.exists():
        sys.exit(f"Input not found: {p}")

    group = af.AFMGroup(str(p))
    n = len(group)
    print(f"\nFile: {p.name}")
    print(f"Curves in map: {n}")

    if n == 0:
        sys.exit("No curves found in this file.")

    # Use the first curve as representative for experiment metadata
    curve0 = group[0]

    print("\n--- Available data columns in first curve ---")
    print(list(curve0.columns))

    # Some afmformats builds expose .metadata; keep this robust:
    md = getattr(curve0, "metadata", None)
    if md:
        print("\n--- Experiment / acquisition metadata (first curve) ---")
        # Pretty-print a few commonly useful sections if present
        for key in ["instrument", "calibration", "imaging", "position", "settings"]:
            if key in md:
                print(f"\n[{key}]")
                pprint(md[key])
        # Anything else that might be present:
        other = {k: v for k, v in md.items() if k not in {"instrument","calibration","imaging","position","settings"}}
        if other:
            print("\n[other]")
            pprint(other)
    else:
        print("\nNo structured metadata dict exposed on this curve. "
              "afmformats still provides columns/units; try other curves or update afmformats.")

    print("\nDone.")

if __name__ == "__main__":
    main()
