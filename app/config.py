"""Configuration module for FlowBot application."""
from pathlib import Path
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Gemini Studio Settings
    STUDIO_URL: str = "https://gemini.google.com/share/fed2e5f4f4c3?skid=4bd31dae-312d-41d0-96e6-fb0b519ae1c4"
    IMAGE_COUNT: int = 1
    ASPECT_RATIO: str = "9:16"

    # Browser Automation Settings
    BROWSER_PROFILE_DIR: str = "./browser_profile"
    HEADLESS: bool = True
    FLOW_DEBUG: bool = False
    PROXY_SERVER: Optional[str] = "http://31.59.20.176:6754"
    PROXY_USERNAME: Optional[str] = "pgyojheu"
    PROXY_PASSWORD: Optional[str] = "i1z3l2l2mh56"



    GENERATION_TIMEOUT_SECONDS: int = 300
    DOWNLOAD_TIMEOUT_SECONDS: int = 120


    # API Server Settings
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_KEY: str = ""

    # Storage Paths
    OUTPUT_DIR: str = "./generated"
    TEMP_DIR: str = "./temp"
    SCREENSHOT_DIR: str = "./screenshots"
    LOG_DIR: str = "./logs"
    LOG_LEVEL: str = "INFO"

    @property
    def base_path(self) -> Path:
        return Path(__file__).resolve().parent.parent

    @property
    def profile_path(self) -> Path:
        p = Path(self.BROWSER_PROFILE_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def output_path(self) -> Path:
        p = Path(self.OUTPUT_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def temp_path(self) -> Path:
        p = Path(self.TEMP_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def screenshot_path(self) -> Path:
        p = Path(self.SCREENSHOT_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def log_path(self) -> Path:
        p = Path(self.LOG_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()



