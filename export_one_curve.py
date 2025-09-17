from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import afmformats as af

def pick_curve(group, idx=None, row=None, col=None):
    if idx is not None:
        return idx, group[idx]
    # výběr podle [row, col] z 2D mřížky
    if row is not None and col is not None:
        # většina map má pořadí "x rychle", tj. idx = row*nx + col
        # metadatům věříme pro grid shape
        md0 = getattr(group[0], "metadata", {}) or {}
        nx = md0.get("grid shape x") or md0.get("grid_shape_x") or None
        ny = md0.get("grid shape y") or md0.get("grid_shape_y") or None
        if nx is None or ny is None:
            raise ValueError("Grid shape not in metadata; use --idx instead.")
        idx = row * nx + col
        return idx, group[idx]
    raise ValueError("Specify either --idx or both --row and --col.")

def compute_indentation(curve):
    # deflection d = measured - piezo
    z_piezo = curve["height (piezo)"]
    d = curve["height (measured)"] - z_piezo
    delta = z_piezo - d
    return delta

def main():
    ap = argparse.ArgumentParser(description="Export time–force & time–indentation for one curve")
    ap.add_argument("infile", help=".jpk-force-map")
    gsel = ap.add_mutually_exclusive_group(required=True)
    gsel.add_argument("--idx", type=int, help="curve index (0..N-1)")
    gsel.add_argument("--row", type=int, help="grid row (use with --col)")
    ap.add_argument("--col", type=int, help="grid col (use with --row)")
    ap.add_argument("--out", default="", help="optional CSV output filename")
    ap.add_argument("--units", choices=["SI","nm-nN"], default="SI",
                    help="output units: SI (m,N) or nm-nN")
    args = ap.parse_args()

    infile = Path(args.infile)
    group = af.AFMGroup(str(infile))
    idx, curve = pick_curve(group, idx=args.idx, row=args.row, col=args.col)

    # metadata (bez výpisu obrovských struktur – jen to podstatné)
    md = getattr(curve, "metadata", {}) or {}
    k = md.get("spring constant")
    sens = md.get("sensitivity")
    segcount = md.get("segment count")
    mode = md.get("imaging mode")
    date = md.get("date")
    row = md.get("grid index y")
    col = md.get("grid index x")

    print(f"\nFile: {infile.name}")
    print(f"Selected curve idx={idx} (row={row}, col={col})")
    print(f"Mode: {mode} | Date: {date} | Segments: {segcount}")
    print(f"Spring k: {k} N/m | Sensitivity: {sens} m/V (if present)")

    t = curve["time"]           # [s]
    F = curve["force"]          # [N]
    delta = compute_indentation(curve)  # [m]
    seg = curve["segment"] if "segment" in curve.columns else np.full_like(t, np.nan)

    if args.units == "nm-nN":
        scale_F = 1e9
        scale_d = 1e9
        F_out = F * scale_F
        d_out = delta * scale_d
        F_name = "force_nN"
        d_name = "indentation_nm"
    else:
        F_out = F
        d_out = delta
        F_name = "force_N"
        d_name = "indentation_m"

    df = pd.DataFrame({
        "time_s": t,
        F_name: F_out,
        d_name: d_out,
        "segment": seg
    })

    print("\nHead of data:")
    print(df.head())

    if args.out:
        df.to_csv(args.out, index=False)
        print(f"\nSaved: {args.out}")

if __name__ == "__main__":
    main()
