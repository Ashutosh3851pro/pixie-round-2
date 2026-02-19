import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.BASE_DIR = Path(__file__).parent.parent.parent

        self.DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Mumbai")
        self.SUPPORTED_CITIES = [
            "Mumbai",
            "Delhi",
            "Bangalore",
            "Hyderabad",
            "Chennai",
            "Pune",
            "Kolkata",
            "Ahmedabad",
            "Jaipur",
            "Kochi",
        ]

        self.GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
        self.GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS", "")  # JSON string

        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
        self.REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
        self.RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", 2))

        self.PLATFORMS = [
            p.strip() for p in os.getenv("PLATFORMS", "district").split(",")
        ]
        self.MARK_EXPIRED_DAYS = int(os.getenv("MARK_EXPIRED_DAYS", 0))

    def get_city_url_mapping(self, platform: str) -> dict:
        if platform == "district":
            return {
                city: "https://www.district.in/events/"
                for city in self.SUPPORTED_CITIES
            }
        return {}

    def validate_city(self, city: str) -> bool:
        return city in self.SUPPORTED_CITIES


config = Config()
