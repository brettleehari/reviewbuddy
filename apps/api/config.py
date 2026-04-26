from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    github_client_id: str = ""
    github_client_secret: str = ""
    allowed_origins: str = "https://brettleehari.github.io"
    cache_dir: str = "/tmp/smartreview-cache"
    clone_dir: str = "/tmp/smartreview-clones"
    max_repo_size_mb: int = 100
    max_files_per_pr: int = 50
    analysis_timeout_seconds: int = 90
    rate_limit_per_hour: int = 20
    rate_limit_per_day: int = 60

    class Config:
        env_prefix = "SMARTREVIEW_"


settings = Settings()
