import json
import os

import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler


class Dataset:
    @staticmethod
    def load_data(folder_path: str, preprocess: bool = True) -> pd.DataFrame:
        meta_data = []
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".json"):
                file_path = os.path.join(folder_path, file_name)
                with open(file_path, "r") as f:
                    data = json.load(f)
                    meta = data.get("meta", {})[0]
                    meta_data.append(meta)

        df = pd.DataFrame(meta_data)
        # Replace "Infinity" with -1 in all columns
        df.replace("Infinity", -1, inplace=True)

        if preprocess:
            df = Dataset._preprocess_data(df)

        return df

    @staticmethod
    def _preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
        scaler = MinMaxScaler()
        df = pd.DataFrame(scaler.fit_transform(df), columns=df.columns)
        return df
