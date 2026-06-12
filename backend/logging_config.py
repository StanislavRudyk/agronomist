import sys
from loguru import logger

logger.remove()

logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>  <level>{message}</level>",
    level="INFO",
    colorize=True,
)

logger.add(
    "logs/agronomist.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line}  {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="30 days",
    compression="gz",
    encoding="utf-8",
)

logger.add(
    "logs/security.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="INFO",
    rotation="5 MB",
    retention="90 days",
    compression="gz",
    encoding="utf-8",
    filter=lambda record: record["extra"].get("security", False),
)

security_logger = logger.bind(security=True)
