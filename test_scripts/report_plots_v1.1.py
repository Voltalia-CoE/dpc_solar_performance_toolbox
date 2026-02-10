# %%
import datetime as dt

import pandas as pd
import dateutil.relativedelta as relativedelta
from sqlalchemy import text, bindparam

from solar_performance_toolbox.v0.data_acquisition.DBDataAcquisitor import DBDataAcquisitor
from solar_performance_toolbox.v0.plotting.reference_info import DataColumns as DC
from solar_performance_toolbox.v0.plotting.reference_info import Queries as QRYS

import solar_performance_toolbox.v0.plotting.reports_general_plots as rgp

# %%
s_farm_id = 1

target_year = 2026
target_month = 1

plots_folder = "test_scripts\\test_files"

# %%
data_acquisitor = DBDataAcquisitor("PT")

target_date = dt.datetime(target_year, target_month, 1)
date_start = dt.datetime(target_year, 1, 1) - relativedelta.relativedelta(years=1)
date_end = target_date + relativedelta.relativedelta(months=1) - dt.timedelta(seconds=1)

all_paths = []

# %%
df_monthly = rgp.get_monthly_data(s_farm_id=s_farm_id, date_start=date_start, date_end=date_end, data_acquisitor=data_acquisitor)

# %%
summ_tbl = rgp.get_summary_tables2(df_monthly, target_date)
summ_tbl = pd.DataFrame(summ_tbl).T
print(summ_tbl)

# %%
fig = rgp.plot_waterfall(target_date, df_monthly)
all_paths.append(rgp.get_figure_png(fig, plots_folder, f"{s_farm_id}_waterfall_{target_date.strftime('%Y-%m')}.png"))

# %%
for x in ["production", "irradiation", "availability", "curtailment"]:
    fig = rgp.plot_comparison_ytd(df_monthly, target_date, target=x)
    all_paths.append(rgp.get_figure_png(fig, plots_folder, f"{s_farm_id}_comparison_{target_date.strftime('%Y-%m')}_{x}_1.png"))

# %%
for x in ["production", "irradiation"]:
    fig = rgp.plot_comparison_ytd(df_monthly, target_date, target=x, percentage=True, cumulative=True)
    all_paths.append(rgp.get_figure_png(fig, plots_folder, f"{s_farm_id}_comparison_{target_date.strftime('%Y-%m')}_{x}_2.png"))


