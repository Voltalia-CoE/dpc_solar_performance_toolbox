from pandas import DataFrame

class BaseDataAcquisitor:

    def __init__(self):
        pass

    def load_data(*args, **kwargs) -> DataFrame:
        raise NotImplementedError()
    
    