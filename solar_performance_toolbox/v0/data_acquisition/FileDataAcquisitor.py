import pandas as pd

from .BaseDataAcquisitor import BaseDataAcquisitor

class FileDataAcquisitor(BaseDataAcquisitor):

    def load_data(self, filepath, filetype:str="csv", *args, **kwargs):

        filetype = filetype.lower()
        
        match filetype:
            case "csv":
                data:pd.DataFrame = pd.read_csv(filepath, *args, **kwargs)

            case _:
                return super().load_data(*args, **kwargs)
            
        data = self._treat_column_names(data)

        return data
    
    def _treat_column_names(self, data:pd.DataFrame):

        data.columns = data.columns.astype(str).str.lstrip()
        data.columns = data.columns.astype(str).str.rstrip()
        data.columns = data.columns.astype(str).str.replace(" ", "_")

        return data        