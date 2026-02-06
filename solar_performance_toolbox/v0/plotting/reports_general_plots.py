import os
import datetime as dt
import math
import locale
locale.setlocale(locale.LC_TIME, "en_US.UTF-8")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
import seaborn as sns
import dateutil.relativedelta as relativedelta
from sqlalchemy import text, bindparam

from solar_performance_toolbox.v0.data_acquisition.BaseDataAcquisitor import (
    BaseDataAcquisitor,
)
from solar_performance_toolbox.v0.plotting.reference_info import DataColumns as DC
from solar_performance_toolbox.v0.plotting.reference_info import Queries as QRYS

# %% Constants
CHANNEL_REG_IDS = [771, 776, 777, 781, 797, 779, 779, 785, 795, 793, 794, 796]
PLOT_FIGURE_DPI = 120


# %% Helper functions
def proper_float(val, ndigits=3):
    return round(float(val), ndigits)


def calculate_useful_dates(ref_date):
    last_year_month = ref_date - relativedelta.relativedelta(years=1)

    curr_year_start = ref_date.replace(month=1)
    last_year_start = curr_year_start - relativedelta.relativedelta(years=1)

    return [curr_year_start, ref_date, last_year_start, last_year_month]

def get_figure_png(fig: plt.Figure, target_folder: str, filename: str) -> str:
    if not os.path.exists(target_folder):
        os.makedirs(target_folder, exist_ok=True)
    fig_path = os.path.join(target_folder, filename)
    fig.savefig(fig_path, dpi=PLOT_FIGURE_DPI, bbox_inches="tight")
    return fig_path


# %% Data Functions


def get_monthly_data(
    s_farm_id: int,
    date_start: dt.datetime,
    date_end: dt.datetime,
    data_acquisitor: BaseDataAcquisitor,
    source: str = "DB",
    *args,
    **kwargs,
) -> pd.DataFrame:

    if source.upper() == "DB":
        query = QRYS.MONTHLY_DATA_QUERY
        params = {
            "farm_id": s_farm_id,
            "date_start": date_start,
            "date_end": date_end,
            "channel_reg_ids": DC.CHANNEL_REG_IDS,
        }
        query = text(query).bindparams(bindparam("channel_reg_ids", expanding=True))
        df_monthly = data_acquisitor.load_data(query, params=params)

        df_monthly["DESCRIPTION"] = (
            df_monthly["DESCRIPTION"]
            .str.upper()
            .str.replace(r"[^A-Z0-9]+", "_", regex=True)  # symbol → underscore
            .str.replace(r"_+", "_", regex=True)  # collapse multiple underscores
            .str.strip("_")
        )

        mask = df_monthly["CHANNEL_UNIT"].str.fullmatch("kWh", case=False, na=False)

        df_monthly.loc[mask, "VALUE"] = df_monthly.loc[mask, "VALUE"] / 1000
        df_monthly.loc[mask, "CHANNEL_UNIT"] = "MWh"

        df_monthly = df_monthly.pivot_table(
            index="TS", columns="DESCRIPTION", values="VALUE", aggfunc="sum"
        )
        df_monthly.index = pd.to_datetime(df_monthly.index)

        # Calculating other impacts

        df_monthly[DC.AVAILABILITY_IMPACT] = (df_monthly[DC.AVAILABILITY_MEASURED] - df_monthly[DC.AVAILABILITY_BUDGET]) * df_monthly[DC.PRODUCTION_EXPECTED] / 100

        df_monthly[DC.CURTAILMENT_IMPACT] = -(df_monthly[DC.CURTAILMENT_MEASURED] - df_monthly[DC.CURTAILMENT_BUDGET])

        return df_monthly

# %% Summary tables
def get_summary_tables(df_monthly: pd.DataFrame, current_month: dt.datetime):
    summary_tables = {}

    var_col_mapping = {
        "PRODUCTION": "ENERGY_PRODUCED",
        "RESOURCE": "pyrano",
        "SATTELITE": "GHI",
        "CURTAILMENT": "CURTAILMENT",
    }

    curr_year_start, current_month, last_year_start, last_year_month = (
        calculate_useful_dates(current_month)
    )

    for variable, column in var_col_mapping.items():
        if variable not in summary_tables:
            summary_tables[variable] = {
                "MTD": {},
                "YTD": {},
                "LAST_YEAR_MTD": {},
                "LAST_YEAR_YTD": {},
            }

        summary_tables[variable]["MTD"] = proper_float(
            df_monthly.loc[current_month, column]
        )
        summary_tables[variable]["LAST_YEAR_MTD"] = proper_float(
            df_monthly.loc[last_year_month, column]
        )

        summary_tables[variable]["YTD"] = proper_float(
            df_monthly.loc[curr_year_start:current_month, column].sum()
        )
        summary_tables[variable]["LAST_YEAR_YTD"] = proper_float(
            df_monthly.loc[last_year_start:last_year_month, column].sum()
        )

    return summary_tables


def get_summary_tables2(df_monthly: pd.DataFrame, current_month: dt.datetime) -> dict:
    summary_tables = {}

    curr_year_start, current_month, last_year_start, last_year_month = (
        calculate_useful_dates(current_month)
    )

    for column in df_monthly.columns:
        summary_tables[column] = {
            "MTD": proper_float(df_monthly.loc[current_month, column]),
            "LAST_YEAR_MTD": proper_float(df_monthly.loc[last_year_month, column]),
            "YTD": proper_float(
                df_monthly.loc[curr_year_start:current_month, column].sum()
            ),
            "LAST_YEAR_YTD": proper_float(
                df_monthly.loc[last_year_start:last_year_month, column].sum()
            ),
        }

    return summary_tables


# %% Waterfall plot
def plot_waterfall(
    date,
    data0,
    # budget_srs,
    # resource_srs,
    # curtailment_srs,
    # availability_srs,
    # prod_srs,
    # ax=None,
):

    # data2 = pd.concat(
    #     [budget_srs, resource_srs, -curtailment_srs, availability_srs], axis=1
    # )  #
    # # Small hack to properly label production bar. Setting the measured bottom to 0.0 completes this
    # final_total = data2.sum(axis=1)
    # data2["Black Box"] = final_total - prod_srs
    # data2["Measured"] = prod_srs

    data2 = data0[
        [
            DC.PRODUCTION_BUDGET,
            DC.RESOURCE_IMPACT,
            DC.CURTAILMENT_IMPACT,
            DC.AVAILABILITY_IMPACT,
            DC.BLACKBOX_MEASURED,
            DC.PRODUCTION_MEASURED,
        ]
    ].copy()

    # data2.iloc[:, 1:-1] = data2.iloc[:, 1:-1] * -1

    data2.columns = [
        "Budget",
        "Irradiation Δ",
        "Curtailment Δ",
        "Availability Δ",
        "BlackBox",
        "Measured",
    ]

    data2 = data2.loc[[date]]

    bottom = data2.cumsum(axis=1).shift(1, axis=1).fillna(0.0)
    bottom["Measured"] = 0.0

    data2 = data2.iloc[0]
    bottom = bottom.iloc[0]

    # ymin = bottom[1:-1].min() * 0.95
    ymin = 0
    ymax = bottom.max() * 1.1

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor="white", dpi=120)

    colors = (
        ["blue"]
        + ["green" if val >= 0 else "red" for val in data2.values[1:-1]]
        + ["blue"]
    )
    data2.plot.bar(
        bottom=bottom,
        ax=ax,
        color=colors,
        alpha=0.8,
        edgecolor="black",
        layout="compressed",
    )
    ax.tick_params(axis="x", labelrotation=0)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.set_ylabel(f"Energy [MWh]")
    ax.set_ylim(ymin, ymax)
    ax.set_title("Energy Waterfall")

    for iii in range(1, len(data2) - 1):
        ax.hlines(bottom.iloc[iii], iii - 1, iii, color="black", ls="dashed", alpha=0.5)
    # Connecting to production bar, since the bottom is 0.0
    ax.hlines(data2["Measured"], iii, iii + 1, color="black", ls="dashed", alpha=0.5)

    container = ax.containers[0]

    labels = [
        f"{v:.2f}" if i != 0 and i != len(data2) - 1 else f"{abs(v):.0f}"
        for i, v in enumerate(data2.values)
    ]

    ax.bar_label(
        container,
        labels,
        padding=3,
        fontsize=9,
    )

    # fig.tight_layout()

    if fig is not None:
        return fig


# %% YTD comparison plots
def _plot_production_comparison_ytd(
    df_monthly: pd.DataFrame, current_month: dt.datetime, percentage: bool = False, cumulative: bool = False
):
    fig, ax = plt.subplots(facecolor="white", layout="compressed", figsize=(9, 5.5))

    width = dt.timedelta(days=9)
    font = 12
    font2 = 9

    curr_year_start, current_month, last_year_start, last_year_month = (
        calculate_useful_dates(current_month)
    )

    df_m_ytd = df_monthly.loc[curr_year_start:current_month]

    totals = df_m_ytd[DC.PRODUCTION_MEASURED] + df_m_ytd[DC.CURTAILMENT_MEASURED]

    cum_str = " (Cumulative)" if cumulative else ""

    # Creating bars
    if percentage:
        bars1 = ax.bar(
            df_m_ytd.index,
            totals / df_m_ytd[DC.PRODUCTION_BUDGET] * 100,
            width=width,
            label=f"Production Index",
            color="orange",
        )

        ax.bar_label(bars1, fmt="%.2f", padding=3, fontsize=font2, zorder=20)

        ax.hlines(100, xmin=df_m_ytd.index.min() - dt.timedelta(weeks=5), xmax=df_m_ytd.index.max() + dt.timedelta(weeks=5), color="black", linestyle="--", zorder=10, alpha=0.3)

    else:
        bars1 = ax.bar(
            df_m_ytd.index - 5 * width / 8,
            df_m_ytd[DC.PRODUCTION_BUDGET],
            width=width,
            label=f"Expected Production",
            color="b",
        )
        bars2 = ax.bar(
            df_m_ytd.index + 5 * width / 8,
            df_m_ytd[DC.PRODUCTION_MEASURED],
            width=width,
            label=f"Measured Production",
            color="orange",
        )
        bars3 = ax.bar(
            df_m_ytd.index + 5 * width / 8,
            df_m_ytd[DC.CURTAILMENT_MEASURED],
            bottom=df_m_ytd[DC.PRODUCTION_MEASURED],
            width=width,
            label=f"Curtailment",
            color="yellowgreen",
        )
    

        # Labeling bars
        ax.bar_label(bars1, fmt="%.0f", padding=3, fontsize=font2, zorder=20)
        ax.bar_label(
            bars2, fmt="%.0f", label_type="center", fontsize=font2, rotation=90, zorder=20
        )
        ax.bar_label(
            bars3, fmt="%.0f", label_type="center", fontsize=font2, rotation=90, zorder=20
        )
        ax.bar_label(
            bars3,
            labels=[f"{t:.0f}" for t in totals],
            padding=3,
            fontsize=font2,
        )

    # Plotting PXXs
    if not percentage:
        ax.plot(
            df_m_ytd.index,
            df_m_ytd[DC.PRODUCTION_P50],
            label="P50",
            color="turquoise",
            linestyle="--",
            linewidth=2,
            marker="o",
            markersize=5,
        )

    # Plotting last year measurements
    df_m_last_ytd = df_monthly.loc[last_year_start:last_year_month]
    df_m_last_ytd.index = df_m_last_ytd.index + pd.DateOffset(years=1)

    if percentage:
        ax.plot(
            df_m_last_ytd.index,
            (df_m_last_ytd[DC.PRODUCTION_MEASURED] + df_m_last_ytd[DC.CURTAILMENT_MEASURED]) / df_m_last_ytd[DC.PRODUCTION_BUDGET] * 100,
            label=f"{last_year_start.year} Production Index",
            color="orangered",
            linestyle="--",
            linewidth=2,
            marker="o",
            markersize=5,
        )

    else:
        ax.plot(
            df_m_last_ytd.index,
            df_m_last_ytd[DC.PRODUCTION_MEASURED],
            label=f"{last_year_start.year} Measured",
            color="orangered",
            linestyle="--",
            linewidth=2,
            marker="o",
            markersize=5,
        )

    ax.legend(fontsize=font)
    y_unit = "[%]" if percentage else "[MWh]"
    ax.set_ylabel(f"Energy Production {y_unit}", fontsize=font)
    ax.tick_params(axis="both", labelsize=font2)

    ax.set_xlim(df_m_ytd.index.min() - 2*width, df_m_ytd.index.max() + 2*width)
    ax.set_xticks(df_m_ytd.index)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))  # Jan/2025, Feb/2025, Mar...
    ax.set_title(f"YTD Production Measured vs. Expected{cum_str}", fontsize=font)
    return fig


def _plot_resource_comparison_ytd(df_monthly: pd.DataFrame, current_month: dt.datetime, percentage: bool = False, cumulative: bool = False):
    fig, ax = plt.subplots(facecolor="white", layout="compressed", figsize=(9, 5.5))

    width = dt.timedelta(days=9)
    font = 12
    font2 = 9

    curr_year_start, current_month, last_year_start, last_year_month = (
        calculate_useful_dates(current_month)
    )

    df_m_ytd = df_monthly.loc[curr_year_start:current_month]

    cum_str = " (Cumulative)" if cumulative else ""

    # Creating bars
    if percentage:
        bars1 = ax.bar(
            df_m_ytd.index,
            df_m_ytd[DC.RESOURCE_MEASURED] / df_m_ytd[DC.RESOURCE_BUDGET] * 100,
            width=width,
            label="Resource Index",
            color="orange",
        )

        ax.bar_label(bars1, fmt="%.2f", padding=3, fontsize=font2, zorder=20)
        ax.hlines(100, xmin=df_m_ytd.index.min() - dt.timedelta(weeks=5), xmax=df_m_ytd.index.max() + dt.timedelta(weeks=5), color="black", linestyle="--", zorder=10, alpha=0.3)

    else:
        bars1 = ax.bar(
            df_m_ytd.index - 5 * width / 8,
            df_m_ytd[DC.RESOURCE_BUDGET],
            width=width,
            label="Budget",
            color="b",
        )
        bars2 = ax.bar(
            df_m_ytd.index + 5 * width / 8,
            df_m_ytd[DC.RESOURCE_MEASURED],
            width=width,
            label="Measured",
            color="orange",
        )

        # Labeling bars
        ax.bar_label(bars1, fmt="%.0f", padding=3, fontsize=font2, zorder=20)
        ax.bar_label(bars2, fmt="%.0f", fontsize=font2, zorder=20)

    # # Plotting PXXs
    # ax.plot(
    #     df_m_ytd.index,
    #     df_budget.loc[curr_year_start:current_month]["GHI"],
    #     label="Budget",
    #     color="turquoise",
    #     linestyle="--",
    #     linewidth=2,
    # )

    # Plotting last year measurements
    df_m_last_ytd = df_monthly.loc[last_year_start:last_year_month]
    df_m_last_ytd.index = df_m_last_ytd.index + pd.DateOffset(years=1)
    if percentage:
        ax.plot(
            df_m_last_ytd.index,
            df_m_last_ytd[DC.RESOURCE_MEASURED] / df_m_last_ytd[DC.RESOURCE_BUDGET] * 100,
            label=f"{last_year_start.year} Resource Index",
            color="orangered",
            linestyle="--",
            linewidth=2,
            marker="o",
            markersize=5,
        )

    else:
        ax.plot(
            df_m_last_ytd.index,
            df_m_last_ytd[DC.RESOURCE_MEASURED],
            label=f"{last_year_start.year} Measured",
            color="orangered",
            linestyle="--",
            linewidth=2,
            marker="o",
            markersize=5,
        )

    ax.legend(fontsize=font)
    y_unit = "[%]" if percentage else "[kWh/m²]"
    ax.set_ylabel(f"Irradiation {y_unit}", fontsize=font)
    ax.tick_params(axis="both", labelsize=font2)

    ax.set_xlim(df_m_ytd.index.min() - 2*width, df_m_ytd.index.max() + 2*width)
    ax.set_xticks(df_m_ytd.index)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))
    ax.set_title(f"YTD Irradiation{cum_str}", fontsize=font)

    return fig


def _plot_curtailment_comparison_ytd(
    df_monthly: pd.DataFrame, current_month: dt.datetime
):
    fig, ax = plt.subplots(facecolor="white", layout="compressed", figsize=(9, 5.5))

    width = dt.timedelta(days=9)
    font = 12
    font2 = 9

    curr_year_start, current_month, last_year_start, last_year_month = (
        calculate_useful_dates(current_month)
    )

    # Current year YTD
    df_m_ytd = df_monthly.loc[curr_year_start:current_month]

    # Bars: Curtailment (current year)
    bars = ax.bar(
        df_m_ytd.index + 5 * width / 8,
        df_m_ytd[DC.CURTAILMENT_MEASURED],
        width=width,
        label="Curtailment",
        color="yellowgreen",
    )

    # Labeling bars (absolute values on top)
    ax.bar_label(
        bars,
        labels=[f"{abs(v):.0f}" for v in df_m_ytd[DC.CURTAILMENT_MEASURED]],
        padding=3,
        fontsize=font2,
        zorder=20,
    )

    # Budget line
    ax.plot(
        df_m_ytd.index,
        df_m_ytd[DC.CURTAILMENT_BUDGET],
        label="Budget",
        color="turquoise",
        linestyle="--",
        linewidth=2,
        marker="o",
        markersize=5,
    )

    # Last year YTD
    df_m_last_ytd = df_monthly.loc[last_year_start:last_year_month].copy()
    df_m_last_ytd.index = df_m_last_ytd.index + pd.DateOffset(years=1)

    ax.plot(
        df_m_last_ytd.index,
        df_m_last_ytd[DC.CURTAILMENT_MEASURED],
        label=f"{last_year_start.year} Measured",
        color="darkgreen",
        linestyle="--",
        linewidth=2,
        marker="o",
        markersize=5,
    )

    # Formatting
    ax.legend(fontsize=font)
    ax.set_ylabel("Curtailment [MWh]", fontsize=font)
    ax.tick_params(axis="both", labelsize=font2)
    ax.set_xticks(df_m_ytd.index)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))
    ax.set_title("YTD Curtailment", fontsize=font)

    # Y-limits (keep zero visible and leave room for labels)
    ymax = max(
        df_m_ytd[DC.CURTAILMENT_MEASURED].max(),
        df_m_ytd[DC.CURTAILMENT_BUDGET].max(),
    )
    ax.set_ylim(min(-3, df_m_ytd[DC.CURTAILMENT_MEASURED].min()) * 1.1, ymax * 1.15)

    return fig


def _plot_energy_availability_ytd(df_monthly: pd.DataFrame, current_month: dt.datetime):
    fig, ax = plt.subplots(facecolor="white", layout="compressed", figsize=(9, 5.5))

    width = dt.timedelta(days=9)
    font = 12
    font2 = 9

    curr_year_start, current_month, last_year_start, last_year_month = (
        calculate_useful_dates(current_month)
    )

    # Current year YTD
    df_m_ytd = df_monthly.loc[curr_year_start:current_month]

    # Bars: Availability (current year)
    bars2 = ax.bar(
        df_m_ytd.index - 5 * width / 8,
        df_m_ytd[DC.AVAILABILITY_BUDGET],
        width=width,
        label="Budget",
        color="b",
    )
    bars = ax.bar(
        df_m_ytd.index + 5 * width / 8,
        df_m_ytd[DC.AVAILABILITY_MEASURED],
        width=width,
        label="Availability",
        color="orange",
    )

    # Labeling bars
    ax.bar_label(
        bars,
        fmt="%.0f",
        padding=3,
        fontsize=font2,
        zorder=20,
    )
    ax.bar_label(
        bars2,
        fmt="%.0f",
        padding=3,
        fontsize=font2,
        zorder=20,
    )

    # Last year YTD
    df_m_last_ytd = df_monthly.loc[last_year_start:last_year_month].copy()
    df_m_last_ytd.index = df_m_last_ytd.index + pd.DateOffset(years=1)

    ax.plot(
        df_m_last_ytd.index,
        df_m_last_ytd[DC.AVAILABILITY_MEASURED],
        label=f"{last_year_start.year} Measured",
        color="orangered",
        linestyle="--",
        linewidth=2,
        marker="o",
        markersize=5,
    )

    # Formatting
    ax.legend(fontsize=font, loc="best")
    ax.set_ylabel("Availability [%]", fontsize=font)
    ax.tick_params(axis="both", labelsize=font2)
    ax.set_xticks(df_m_ytd.index)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))
    ax.set_title("YTD Energy Availability Impact", fontsize=font)

    # Y-limits with headroom for labels
    ymax = max(
        df_m_ytd[DC.AVAILABILITY_MEASURED].max(),
        df_m_last_ytd[DC.AVAILABILITY_MEASURED].max(),
    )
    ax.set_ylim(0, ymax * 1.15)

    return fig


def plot_comparison_ytd(
    df_monthly: pd.DataFrame,
    current_month: dt.datetime,
    target: str,
    percentage: bool = False,
    cumulative: bool = False,
):
    
    if cumulative:
        df_monthly = df_monthly.sort_index().groupby(pd.Grouper(freq="YS")).cumsum()

    match target.lower():
        case "production":
            return _plot_production_comparison_ytd(df_monthly, current_month, percentage, cumulative)
        case "irradiation":
            return _plot_resource_comparison_ytd(df_monthly, current_month, percentage, cumulative)
        # case "poa":
        #     return _plot_poa_comparison_ytd(df_monthly, current_month)
        # case "poa_gain":
        #     return _plot_poa_gain_comparison_ytd(df_monthly, current_month)
        case "curtailment":
            return _plot_curtailment_comparison_ytd(
                df_monthly, current_month
            )
        case "availability":
            return _plot_energy_availability_ytd(df_monthly, current_month)
        case _:
            raise NotImplementedError(f"Comparison plot for '{target}' not implemented")
