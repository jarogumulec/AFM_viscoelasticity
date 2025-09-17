import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def autodetect_columns(df: pd.DataFrame):
    if "time_s" not in df.columns:
        raise ValueError("CSV must contain 'time_s'.")
    if "segment" not in df.columns:
        raise ValueError("CSV must contain 'segment'.")

    force_cols = [c for c in df.columns if c.startswith("force_")]
    ind_cols = [c for c in df.columns if c.startswith("indentation_")]

    return force_cols[0] if force_cols else None, ind_cols[0] if ind_cols else None


def pretty_ylabel(colname: str, default_label: str):
    if not colname:
        return default_label
    if "_" in colname:
        base, unit = colname.split("_", 1)
        return f"{base} [{unit}]"
    return default_label


def main():
    ap = argparse.ArgumentParser(
        description="Plot HOLD segment (segment==1) with dual Y axes (force + indentation)."
    )
    ap.add_argument("csv", help="Input CSV (from export_one_curve.py)")
    ap.add_argument("--save", help="Optional PNG output (otherwise show interactively)")
    args = ap.parse_args()

    path = Path(args.csv)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    df = pd.read_csv(path)
    force_col, ind_col = autodetect_columns(df)

    hold = df[df["segment"] == 1].copy()
    if hold.empty:
        raise SystemExit("No rows with segment==1 (hold) found in the CSV.")

    t = hold["time_s"]

    fig, ax_main = plt.subplots()

    if force_col and ind_col:
        # Dual Y: force on left, indentation on right
        axF = ax_main
        axD = ax_main.twinx()

        lnF = axF.plot(t, hold[force_col], color="tab:blue", label=force_col)[0]
        lnD = axD.plot(t, hold[ind_col], color="tab:orange", label=ind_col)[0]

        axF.set_xlabel("time [s]")
        axF.set_ylabel(pretty_ylabel(force_col, "force"), color="tab:blue")
        axD.set_ylabel(pretty_ylabel(ind_col, "indentation"), color="tab:orange")

        axF.tick_params(axis="y", colors="tab:blue")
        axD.tick_params(axis="y", colors="tab:orange")

        lines = [lnF, lnD]
    elif ind_col:
        # Only indentation available
        lnD = ax_main.plot(t, hold[ind_col], color="tab:orange", label=ind_col)[0]
        ax_main.set_xlabel("time [s]")
        ax_main.set_ylabel(pretty_ylabel(ind_col, "indentation"), color="tab:orange")
        lines = [lnD]
    elif force_col:
        # Only force available
        lnF = ax_main.plot(t, hold[force_col], color="tab:blue", label=force_col)[0]
        ax_main.set_xlabel("time [s]")
        ax_main.set_ylabel(pretty_ylabel(force_col, "force"), color="tab:blue")
        lines = [lnF]
    else:
        raise SystemExit("Neither force_* nor indentation_* columns found in CSV.")

    ax_main.set_title(f"{path.name} — HOLD (segment==1)")
    ax_main.grid(True, alpha=0.3)
    ax_main.legend(lines, [ln.get_label() for ln in lines], loc="best")

    fig.tight_layout()

    if args.save:
        fig.savefig(args.save, dpi=200)
        print(f"Saved: {args.save}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
