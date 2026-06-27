from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    nlb_app_id: str = ""
    nlb_api_key: str = ""
    catalogue_base_url: str = "https://openweb.nlb.gov.sg/api/v2/Catalogue"
    eresource_base_url: str = "https://openweb.nlb.gov.sg/api/v1/EResource"
    library_base_url: str = "https://openweb.nlb.gov.sg/api/v1/Library"
    recommendation_base_url: str = "https://openweb.nlb.gov.sg/api/v1/Recommendation"
    request_timeout: int = 60
    max_retries: int = 3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def has_credentials(self) -> bool:
        return bool(self.nlb_app_id and self.nlb_api_key)

    @property
    def auth_headers(self) -> dict[str, str]:
        return {
            "X-API-KEY": self.nlb_api_key,
            "X-APP-Code": self.nlb_app_id,
        }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
