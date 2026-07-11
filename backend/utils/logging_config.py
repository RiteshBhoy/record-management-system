import sys
from pathlib import Path
from loguru import logger

def configure_logging(base_dir: Path):
    """Configure console and rotating application, error and security logs."""
    log_dir = base_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(log_dir / "application.log", rotation="10 MB", retention="30 days", enqueue=True)
    logger.add(log_dir / "error.log", level="ERROR", rotation="10 MB", retention="60 days", enqueue=True)
    logger.add(log_dir / "security.log", filter=lambda r: r["extra"].get("security", False),
               rotation="10 MB", retention="90 days", enqueue=True)
    return logger
