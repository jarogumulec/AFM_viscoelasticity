import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

SEG_NAMES = {0: "approach", 1: "hold", 2: "retract"}

def autodetect(df: pd.DataFrame):
    if "time_s" not in df or "segment" not in df:
        raise ValueError("CSV must contain 'time_s' and 'segment'.")
    fcols = [c for c in df.columns if c.startswith("force_")]
    icols = [c for c in df.columns if c.startswith("indentation_")]
    if not fcols:
        raise ValueError("No force_* column found (e.g., force_nN or force_N).")
    if not icols:
        raise ValueError("No indentation_* column found (e.g., indentation_nm or indentation_m).")
    return fcols[0], icols[0]

def pretty_ylabel(colname: str, default_label: str):
    if "_" in colname:
        base, unit = colname.split("_", 1)
        return f"{base} [{unit}]"
    return default_label

def plot_by_segments(x, y, seg, xlabel, ylabel, title):
    fig, ax = plt.subplots()
    for s in sorted(pd.unique(seg.dropna())):
        mask = (seg == s)
        name = SEG_NAMES.get(int(s), f"segment {int(s)}")
        ax.plot(x[mask], y[mask], label=name)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig

def plot_hold_dualy(t, f, d, title, force_label, ind_label):
    fig, axF = plt.subplots()
    axD = axF.twinx()
    lnF = axF.plot(t, f, color="tab:blue", label=force_label)[0]
    lnD = axD.plot(t, d, color="tab:orange", label=ind_label)[0]
    axF.set_xlabel("time [s]")
    axF.set_ylabel(force_label, color="tab:blue")
    axD.set_ylabel(ind_label, color="tab:orange")
    axF.tick_params(axis="y", colors="tab:blue")
    axD.tick_params(axis="y", colors="tab:orange")
    axF.set_title(title)
    axF.grid(True, alpha=0.3)
    lines = [lnF, lnD]
    labels = [ln.get_label() for ln in lines]
    axF.legend(lines, labels, loc="best")
    fig.tight_layout()
    return fig

def main():
    ap = argparse.ArgumentParser(description="Plot 4 charts from exported AFM CSV (time/force/indentation).")
    ap.add_argument("csv", help="Input CSV (from export_one_curve.py)")
    ap.add_argument("--save-prefix", help="If set, saves 4 PNGs with this prefix; otherwise shows windows.")
    args = ap.parse_args()

    path = Path(args.csv)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    df = pd.read_csv(path)
    force_col, ind_col = autodetect(df)

    # 1) time vs force
    fig1 = plot_by_segments(df["time_s"], df[force_col], df["segment"],
                            "time [s]", pretty_ylabel(force_col, "force"),
                            f"{path.name} — time vs {force_col}")

    # 2) time vs indentation
    fig2 = plot_by_segments(df["time_s"], df[ind_col], df["segment"],
                            "time [s]", pretty_ylabel(ind_col, "indentation"),
                            f"{path.name} — time vs {ind_col}")

    # 3) hold-only dual Y
    hold = df[df["segment"] == 1]
    if hold.empty:
        fig3, ax = plt.subplots()
        ax.set_title(f"{path.name} — HOLD (segment==1) not found")
        ax.set_xlabel("time [s]")
        ax.set_ylabel("value")
        ax.grid(True, alpha=0.3)
        fig3.tight_layout()
    else:
        fig3 = plot_hold_dualy(hold["time_s"], hold[force_col], hold[ind_col],
                               f"{path.name} — HOLD (segment==1)",
                               pretty_ylabel(force_col, "force"),
                               pretty_ylabel(ind_col, "indentation"))

    # 4) force vs indentation
    fig4 = plot_by_segments(df[ind_col], df[force_col], df["segment"],
                            pretty_ylabel(ind_col, "force"),
                            pretty_ylabel(force_col, "indentation"),
                            f"{path.name} — {ind_col} vs {force_col}")

    if args.save_prefix:
        stem = Path(args.save_prefix).with_suffix("")
        fig1.savefig(f"{stem}_time_vs_force.png", dpi=200)
        fig2.savefig(f"{stem}_time_vs_indentation.png", dpi=200)
        fig3.savefig(f"{stem}_hold_dualy.png", dpi=200)
        fig4.savefig(f"{stem}_force_vs_indentation.png", dpi=200)
        print("Saved 4 figures with prefix:", stem)
    else:
        plt.show()

if __name__ == "__main__":
    main()
