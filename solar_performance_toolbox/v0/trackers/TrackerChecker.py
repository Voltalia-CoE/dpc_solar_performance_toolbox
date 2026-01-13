import pandas as pd

class TrackerChecker:

    def __init__(self):
        pass

    def get_angle_mae(
        self,
        df_ang: pd.DataFrame,
        df_setpoint: pd.DataFrame,
        interval: str = "D",
    ):

        abs_error = (df_setpoint - df_ang).abs()

        if interval == "D":
            df_mae = (
                abs_error
                .resample("D")
                .mean()
                .reset_index()
            )

        elif interval == "all":
            df_mae = abs_error.mean()

        return df_mae
