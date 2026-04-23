from dataclasses import dataclass
from pathlib import Path
from src.constants import PROJECT_ROOT
import os

@dataclass
class DataIngestionConfig:
    # 1. Local Paths (Your project root folders)
    project_root: Path = PROJECT_ROOT
    data_dir: Path = project_root / "datas"
    
    # Raw data (The simulator output)
    local_raw_path: Path = data_dir / "just_produced" / "transactions.jsonl"
    
    # Processed data (The consumer output)
    local_processed_path: Path = data_dir / "processed" / "features.jsonl"
    
    # 2. S3 Paths (The Warehouse keys)
    s3_raw_key: str = "data/raw/transactions.jsonl"
    s3_processed_key: str = "data/processed/features.jsonl"

    # 3. Training Ingestion (Where to put data when downloading from S3)
    ingested_train_dir: Path = data_dir / "raw"

@dataclass
class DataValidationConfig:
    # Use PROJECT_ROOT to ensure the folder is created in the right place
    data_validation_dir: Path = PROJECT_ROOT / "reports" / "data_validation"
    report_file_name: str = "report.yaml"
    schema_file_path: Path = PROJECT_ROOT / "config" / "schema.yaml"