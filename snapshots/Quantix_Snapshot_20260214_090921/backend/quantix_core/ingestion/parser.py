import pandas as pd
import io

class OHLCVParser:
    def parse_csv_file(self, path):
        return pd.read_csv(path).to_dict("records")

    def parse_csv_content(self, content):
        return pd.read_csv(io.StringIO(content)).to_dict("records")

