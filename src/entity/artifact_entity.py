from dataclasses import dataclass
from pathlib import Path

@dataclass
class DataIngestionArtifact:
    trained_file_path: Path
    # We track this so the next component knows where to find the data

@dataclass
class DataValidationArtifact:
    validation_status: bool
    message: str
    validation_report_path: Path