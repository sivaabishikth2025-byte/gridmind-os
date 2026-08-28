from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./gridmind.db"
    redis_url: str = "redis://localhost:6380/0"
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    site_latitude: float = 40.7128
    site_longitude: float = -74.0060
    site_name: str = "Manhattan Campus Microgrid"
    electricity_maps_zone: str = "US-NY-NYC"
    open_meteo_url: str = "https://api.open-meteo.com/v1/forecast"
    api_prefix: str = "/api/v1"


settings = Settings()
