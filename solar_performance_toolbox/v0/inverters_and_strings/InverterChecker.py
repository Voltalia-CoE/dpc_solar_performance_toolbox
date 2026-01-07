import pandas as pd


class InverterChecker:

    def __init__(self, agg_func:str = "median"):
        self.agg_func = agg_func

    def calculate_production_deltas(
        self,
        target_eqp: str,
        data: pd.DataFrame,
        one_to_x: str = "one",
        resample: None | str = None,
        agg_func: None | str = "mean",
        *args,
        **kwargs
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

    
    def _calculate_deltas_one_to_one(self, target_eqp:str, data:pd.DataFrame):

        data_new = data.copy()
        for eqp in data.columns:

            data_new[eqp] = ((data[eqp] / data[target_eqp]) - 1) * 100

        return data_new
    
    def _calculate_deltas_one_to_rest(self, target_eqp:str, data:pd.DataFrame):

        data_new = data.copy()
        
        equips_to_compare = list(data.columns).copy()
        equips_to_compare.remove(target_eqp)

        others_data = data_new[equips_to_compare].agg(self.agg_func, axis=1)

        data_new = ((data_new[target_eqp] / others_data) - 1) * 100

        return data_new

    def calculate_availability(self, inv_df:pd.DataFrame, irrad_df:pd.DataFrame):

        data2 = inv_df.copy()
        data2 = data2.reindex(irrad_df.index)
        data2:pd.DataFrame = data2.loc[irrad_df > 50]

        data3 = data2.loc[(data2 > 1000)].dropna() # | (data2.isna())

        time_avail = len(data3) / len(data2)

        return time_avail
    
    def calculate_efficiency(self, ac_df:pd.DataFrame, dc_df:pd.DataFrame):

        eff_df = ac_df / dc_df

        eff_df = eff_df.mean()

        return eff_df
    