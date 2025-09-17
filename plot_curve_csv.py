import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


SEG_NAMES = {0: "approach", 1: "hold", 2: "retract"}


def auto_columns(df: pd.DataFrame):
    """
    Najdi názvy sloupců síly a indentace podle hlaviček.
    Očekává 'time_s', 'segment' a dále:
      - síla: sloupce začínající 'force_' (např. force_nN nebo force_N)
      - indentace: sloupce začínající 'indentation_' (např. indentation_nm nebo indentation_m)
    """
    if "time_s" not in df or "segment" not in df:
      raise ValueError("CSV musí obsahovat sloupce 'time_s' a 'segment'.")

    force_cols = [c for c in df.columns if c.startswith("force_")]
    ind_cols = [c for c in df.columns if c.startswith("indentation_")]

    if not force_cols:
        raise ValueError("Nenašel jsem sloupec síly (očekávám např. 'force_nN' nebo 'force_N').")
    if not ind_cols:
        raise ValueError("Nenašel jsem sloupec indentace (např. 'indentation_nm' nebo 'indentation_m').")

    # vezmi první nalezený
    return force_cols[0], ind_cols[0]


def plot_segments(ax, t, y, seg, ylabel, title):
    unique = sorted(pd.unique(seg.dropna()))
    for s in unique:
        mask = (seg == s)
        name = SEG_NAMES.get(int(s), f"segment {int(s)}")
        ax.plot(t[mask], y[mask], label=name)
    ax.set_xlabel("time [s]")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)


def main():
    ap = argparse.ArgumentParser(description="Plot time–force and time–indentation from exported CSV")
    ap.add_argument("csv", help="input CSV (e.g., curve_045.csv)")
    ap.add_argument("--save", help="optional path to save PNG (otherwise shows window)")
    args = ap.parse_args()

    path = Path(args.csv)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    df = pd.read_csv(path)
    force_col, ind_col = auto_columns(df)

    fig1, ax1 = plt.subplots()
    plot_segments(ax1, df["time_s"], df[force_col], df["segment"],
                  ylabel=f"{force_col.replace('force_','force [').replace('N]','N]').replace('nN','nN')}",
                  title=f"{path.name} — time vs {force_col}")

    fig2, ax2 = plt.subplots()
    plot_segments(ax2, df["time_s"], df[ind_col], df["segment"],
                  ylabel=f"{ind_col.replace('indentation_','indentation [').replace('m]','m]').replace('nm','nm')}",
                  title=f"{path.name} — time vs {ind_col}")

    fig1.tight_layout()
    fig2.tight_layout()

    if args.save:
        out1 = Path(args.save)
        stem = out1.with_suffix("").as_posix()
        fig1.savefig(stem + "_force.png", dpi=200)
        fig2.savefig(stem + "_indentation.png", dpi=200)
        print(f"Saved: {stem}_force.png, {stem}_indentation.png")
    else:
        plt.show()


if __name__ == "__main__":
    main()
