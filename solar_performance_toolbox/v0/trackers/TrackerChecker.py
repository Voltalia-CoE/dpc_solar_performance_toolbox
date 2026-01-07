import pandas as pd

class TrackerChecker:

    def __init__(self):
        pass

    def get_angle_mae(self, df_ang:pd.DataFrame, df_setpoint:pd.DataFrame):

        df_error = df_setpoint - df_ang   

        df_abs_error = df_error.abs()

        df_mae = df_abs_error.mean()

        return df_mae
