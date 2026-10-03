"""Compare ionospheric VTEC from a reference GNSS station and a low-cost receiver.

Reads .Cmn files (the per-satellite TEC output of the GPS-TEC analysis
program), averages VTEC across satellites at each epoch for both receivers,
plots the two series, and reports how closely they agree.

Usage:
    python vtec_comparison.py --reference data/reference --lowcost data/lowcost
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Column layout of a .Cmn file, after its 5 header lines.
COLUMNS = ["mjd", "time_ut", "prn", "az", "ele", "lat", "lon", "stec", "vtec", "s4"]
HEADER_LINES = 5


def load_cmn(folder):
    """Load every .Cmn file under `folder` into one DataFrame with a UTC time column."""
    files = sorted(Path(folder).rglob("*.Cmn"))
    if not files:
        raise FileNotFoundError(f"No .Cmn files found under {folder}")
    frames = [
        pd.read_csv(f, sep=r"\s+", skiprows=HEADER_LINES, header=None,
                    names=COLUMNS, usecols=range(len(COLUMNS)))
        for f in files
    ]
    data = pd.concat(frames, ignore_index=True)
    # Modified Julian Date -> Julian Date -> timestamp
    data["time"] = pd.to_datetime(data["mjd"] + 2400000.5, origin="julian", unit="D")
    return data


def epoch_mean_vtec(data, freq="1min"):
    """Mean VTEC across all satellites in view, per time bin."""
    return data.groupby(data["time"].dt.floor(freq))["vtec"].mean()


def agreement(reference, lowcost):
    """Agreement statistics on the epochs both receivers recorded."""
    both = pd.concat([reference, lowcost], axis=1, keys=["ref", "low"]).dropna()
    diff = both["low"] - both["ref"]
    return {
        "n_epochs": len(both),
        "pearson_r": float(both["ref"].corr(both["low"])),
        "bias_tecu": float(diff.mean()),
        "rmse_tecu": float(np.sqrt((diff**2).mean())),
    }


def plot(ref, low, ref_mean, low_mean, smooth_window, out_path):
    import matplotlib.pyplot as plt

    fig, axs = plt.subplots(3, 2, figsize=(15, 10))

    axs[0, 0].plot(ref["time"], ref["vtec"], "b", linewidth=0.5)
    axs[0, 0].set_title("Reference station: VTEC, all satellites")
    axs[0, 1].plot(low["time"], low["vtec"], "r", linewidth=0.5)
    axs[0, 1].set_title("Low-cost receiver: VTEC, all satellites")

    for ax, data, mean, title in (
        (axs[1, 0], ref, ref_mean, "Reference station: VTEC by pierce-point latitude"),
        (axs[1, 1], low, low_mean, "Low-cost receiver: VTEC by pierce-point latitude"),
    ):
        sc = ax.scatter(data["time"], data["vtec"], c=data["lat"], cmap="jet",
                        s=10, vmin=20, vmax=40)
        fig.colorbar(sc, ax=ax, label="Latitude (deg)")
        ax.plot(mean.index, mean.values, "k-", linewidth=1.5, label="Epoch mean")
        ax.set_title(title)
        ax.legend()

    axs[2, 0].plot(ref_mean.index, ref_mean.values, "b-", linewidth=1.5, label="Reference")
    axs[2, 0].plot(low_mean.index, low_mean.values, "r-", linewidth=1.5, label="Low-cost")
    axs[2, 0].set_title("Epoch-mean VTEC")
    axs[2, 0].legend()

    ref_smooth = ref_mean.rolling(smooth_window, min_periods=1).mean()
    low_smooth = low_mean.rolling(smooth_window, min_periods=1).mean()
    axs[2, 1].plot(ref_smooth.index, ref_smooth.values, "b-", linewidth=1.5, label="Reference")
    axs[2, 1].plot(low_smooth.index, low_smooth.values, "r-", linewidth=1.5, label="Low-cost")
    axs[2, 1].set_title(f"Epoch-mean VTEC, {smooth_window}-point moving average")
    axs[2, 1].legend()

    for ax in axs.flat:
        ax.set_xlabel("Time (UTC)")
        ax.set_ylabel("VTEC (TECU)")
        ax.grid(True)

    fig.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=150)
        print(f"Figure saved to {out_path}")
    else:
        plt.show()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reference", required=True,
                        help="folder of .Cmn files from the reference station")
    parser.add_argument("--lowcost", required=True,
                        help="folder of .Cmn files from the low-cost receiver")
    parser.add_argument("--freq", default="1min", help="time bin for averaging (default 1min)")
    parser.add_argument("--smooth", type=int, default=10,
                        help="moving-average window in bins (default 10)")
    parser.add_argument("--out", default=None,
                        help="save the figure here instead of showing it")
    parser.add_argument("--no-plot", action="store_true", help="print statistics only")
    args = parser.parse_args(argv)

    ref = load_cmn(args.reference)
    low = load_cmn(args.lowcost)
    ref_mean = epoch_mean_vtec(ref, args.freq)
    low_mean = epoch_mean_vtec(low, args.freq)

    stats = agreement(ref_mean, low_mean)
    print(f"Matched epochs : {stats['n_epochs']}")
    print(f"Pearson r      : {stats['pearson_r']:.3f}")
    print(f"Mean bias      : {stats['bias_tecu']:+.2f} TECU (low-cost minus reference)")
    print(f"RMSE           : {stats['rmse_tecu']:.2f} TECU")

    if not args.no_plot:
        plot(ref, low, ref_mean, low_mean, args.smooth, args.out)


if __name__ == "__main__":
    main()
