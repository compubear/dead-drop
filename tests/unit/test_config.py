"""Dead Drop — Initial test suite to verify project setup."""

import pytest

from pipeline.config import Settings


class TestConfig:
    """Test configuration loading."""

    def test_default_settings(self):
        """Test that default settings load correctly."""
        s = Settings(
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5432,
            POSTGRES_DB="deaddrop_test",
            POSTGRES_USER="test",
            POSTGRES_PASSWORD="test",
        )
        assert s.POSTGRES_DB == "deaddrop_test"
        assert s.APP_ENV == "development"
        assert s.LOG_LEVEL == "INFO"

    def test_database_url(self):
        """Test database URL construction."""
        s = Settings(
            POSTGRES_HOST="db.example.com",
            POSTGRES_PORT=5433,
            POSTGRES_DB="mydb",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="pass",
        )
        assert s.database_url == "postgresql://user:pass@db.example.com:5433/mydb"

    def test_pipeline_schedule_default(self):
        """Test default pipeline schedule cron."""
        s = Settings()
        assert s.PIPELINE_SCHEDULE_CRON == "0 6 * * *"


class TestPipelineImport:
    """Test that pipeline modules import correctly."""

    def test_pipeline_version(self):
        """Test pipeline version is set."""
        import pipeline

        assert pipeline.__version__ == "0.1.0"

    def test_pipeline_main_import(self):
        """Test main module imports."""
        from pipeline.main import main, setup_logging, run_pipeline

        assert callable(main)
        assert callable(setup_logging)
        assert callable(run_pipeline)

    def test_submodule_imports(self):
        """Test all submodule packages import."""
        import pipeline.sources
        import pipeline.gap_detection
        import pipeline.content_gen
        import pipeline.verification
        import pipeline.publishers
        import pipeline.db
