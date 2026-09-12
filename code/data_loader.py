from pathlib import Path

import pandas as pd


class LoadedData:
    """
    Container for all raw/structured data loaded from the dataset.
    """

    def __init__(
        self,
        requests: pd.DataFrame,
        sample_requests: pd.DataFrame,
        financial_profiles: pd.DataFrame,
        financial_events: pd.DataFrame,
        payment_options: pd.DataFrame,
        exchange_rates: pd.DataFrame,
        messages: pd.DataFrame,
        images: pd.DataFrame,
    ):
        self.requests = requests
        self.sample_requests = sample_requests
        self.financial_profiles = financial_profiles
        self.financial_events = financial_events
        self.payment_options = payment_options
        self.exchange_rates = exchange_rates
        self.messages = messages
        self.images = images


class DataLoader:
    """
    Loads the financial agent dataset from CSV files.
    """

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)

    def _load_csv(self, filename: str) -> pd.DataFrame:
        """
        Load a single CSV file from the dataset directory.
        """
        file_path = self.data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Dataset file not found: {file_path}"
            )

        return pd.read_csv(file_path)

    def load(self) -> LoadedData:
        """
        Load all dataset files and return them as one structured object.
        """

        return LoadedData(
            requests=self._load_csv("requests.csv"),
            sample_requests=self._load_csv("sample_requests.csv"),
            financial_profiles=self._load_csv("financial_profiles.csv"),
            financial_events=self._load_csv("financial_events.csv"),
            payment_options=self._load_csv(
                "request_payment_options.csv"
            ),
            exchange_rates=self._load_csv("exchange_rates.csv"),
            messages=self._load_csv("messages.csv"),
            images=self._load_csv("images.csv"),
        )