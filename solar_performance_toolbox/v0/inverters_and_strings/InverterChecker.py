import pandas as pd


class InverterChecker:

    def __init__(self, agg_func: str = "median"):
        self.agg_func = agg_func

    def calculate_production_deltas(
        self,
        target_eqp: str,
        data: pd.DataFrame,
        one_to_x: str = "one",
        resample: None | str = None,
        agg_func: None | str = "mean",
        *args,
        **kwargs,
    ):

        data0 = data.copy()

        if resample is not None:
            data0 = data0.resample(resample).agg(agg_func)

        match one_to_x:
            case "one":
                return self._calculate_deltas_one_to_one(target_eqp, data0)
            case "rest":
                return self._calculate_deltas_one_to_rest(target_eqp, data0)
            case _:
                NotImplementedError()

    def _calculate_deltas_one_to_one(self, target_eqp: str, data: pd.DataFrame):

        data_new = data.copy()
        for eqp in data.columns:

            data_new[eqp] = ((data[eqp] / data[target_eqp]) - 1) * 100

        data_new["REFERENCE_EQP"] = target_eqp

        return data_new

    def _calculate_deltas_one_to_rest(self, target_eqp: str, data: pd.DataFrame):

        data_new = data.copy()

        equips_to_compare = list(data.columns).copy()
        equips_to_compare.remove(target_eqp)

        others_data = data_new[equips_to_compare].agg(self.agg_func, axis=1)

        data_new = ((data_new[target_eqp] / others_data) - 1) * 100

        data_new = data_new.rename(target_eqp)

        return data_new

    def calculate_availability(
        self,
        inv_data: pd.DataFrame | pd.Series,
        irrad_data: pd.DataFrame,
        interval: str = "D",
    ):

        data2 = inv_data.copy()
        data2 = data2.reindex(irrad_data.index)
        data2 = data2.loc[irrad_data > 50]

        if isinstance(data2, pd.Series):
            return self._calculate_time_availability_series(data2, interval)
        
        elif isinstance(data2, pd.DataFrame):
            return self._calculate_time_availability_df(data2, interval)
    
    def _calculate_time_availability_series(self, inv_srs:pd.Series, interval:str):

        valid = (inv_srs > 1000)

        if interval == "D":
            time_avail = (
                valid
                .resample("D")
                .mean()
                .rename("VALUE")
                # .reset_index(name="TS")
            )

        elif interval == "all":
            time_avail = valid.mean()

        return time_avail

    def _calculate_time_availability_df(self, inv_df:pd.Series, interval:str):

        valid = inv_df > 1000

        if interval == "D":
            time_avail = (
                valid
                .resample("D")
                .mean()
                .reset_index()
            )

        elif interval == "all":
            time_avail = valid.mean()

        return time_avail

    def calculate_efficiency(self, ac_df: pd.DataFrame, dc_df: pd.DataFrame, interval: str = "D"):

        eff = ac_df / dc_df

        if interval == "D":
            eff_df = (
                eff
                .resample("D")
                .mean()
                .reset_index()
            )

        elif interval == "all":
            eff_df = eff.mean()

        return eff_df
