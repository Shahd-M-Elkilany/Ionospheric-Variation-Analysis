# Ionospheric VTEC: Low-Cost GNSS Receiver vs Reference Station

Can a low-cost GNSS receiver track the ionosphere as well as a geodetic-grade
station? This project compares vertical total electron content (VTEC) from the
two over four days, 26 to 29 May 2024 (day of year 147 to 150).

| Receiver | File prefix | Role |
| --- | --- | --- |
| Reference GNSS station | `EgSA` | Baseline |
| Low-cost GNSS receiver | `CARO` | Under test |

## Method

1. Each receiver's observations are processed into `.Cmn` files with the
   GPS-TEC analysis program. A `.Cmn` file has one row per satellite per
   epoch: time (Modified Julian Date), PRN, azimuth, elevation, pierce-point
   latitude and longitude, slant TEC, vertical TEC and the S4 index.
2. Times are converted from Modified Julian Date to UTC.
3. VTEC is averaged across all satellites in view at each epoch, giving one
   series per receiver.
4. The two series are compared directly and after a 10-point moving average.
5. The Python script also reports the Pearson correlation, mean bias and RMSE
   between the two series on their shared epochs.

The output is a six-panel figure: raw VTEC for each receiver, VTEC coloured
by pierce-point latitude with the epoch mean overlaid, and the two epoch-mean
series plotted together, raw and smoothed.

## Running it

Put the `.Cmn` files in two folders:

```
data/reference/EgSA147-2024-05-26.Cmn ...
data/lowcost/CARO147-2024-05-26.Cmn ...
```

Python:

```bash
pip install -r requirements.txt
python vtec_comparison.py --reference data/reference --lowcost data/lowcost --out vtec_comparison.png
```

MATLAB (R2022a or later): open `vtec_comparison.m`, set `dataDir` if your
folder is elsewhere, and run it. The MATLAB script produces the figure only.

## Data

The observation files are not included in this repository. VTEC is in TEC
units (1 TECU = 10¹⁶ electrons/m²).

## Files

| File | Purpose |
| --- | --- |
| `vtec_comparison.py` | Loads both receivers, prints agreement statistics, draws the figure |
| `vtec_comparison.m` | Original MATLAB version of the figure |
