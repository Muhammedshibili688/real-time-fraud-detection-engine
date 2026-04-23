import sys
import os
from pathlib import Path

# Standard Imports
from src.logger import logging
from src.exception import FraudException

# Entities
from src.entity.config_entity import DataIngestionConfig, DataValidationConfig
from src.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact

# Components
from src.components.data.data_ingestion import DataIngestion
from src.components.data.data_validation import DataValidation

def main():
    try:
        logging.info("--- Starting Demo End-to-End Pipeline ---")

        # ---------------------------------------------------------
        # STAGE 1: DATA INGESTION
        # ---------------------------------------------------------
        logging.info(">>> Stage: Data Ingestion Initiated")
        
        ingestion_config = DataIngestionConfig()
        ingestion = DataIngestion(config=ingestion_config)
        
        # A. Sync local produced data to S3 (Warehouse Update)
        logging.info("Step 1.1: Syncing local features to S3 Warehouse (Sliding Window)...")
        ingestion.sync_data_to_s3()
        
        # B. Download the snapshot from S3 for training
        logging.info("Step 1.2: Pulling fresh training snapshot from S3...")
        train_file_path = ingestion.initiate_data_ingestion()
        
        # C. Create Artifact for the next stage
        ingestion_artifact = DataIngestionArtifact(
            trained_file_path=Path(train_file_path)
        )
        logging.info(f"Ingestion Stage Complete. Artifact: {ingestion_artifact.trained_file_path}")


        # ---------------------------------------------------------
        # STAGE 2: DATA VALIDATION
        # ---------------------------------------------------------
        logging.info(">>> Stage: Data Validation Initiated")
        
        validation_config = DataValidationConfig()
        validation = DataValidation(
            data_ingestion_artifact=ingestion_artifact,
            data_validation_config=validation_config
        )
        
        validation_artifact = validation.initiate_data_validation()
        
        if not validation_artifact.validation_status:
            logging.error(f"Pipeline Halted: {validation_artifact.message}")
            print(f"❌ Validation Failed. Check logs for details.")
            return
        
        logging.info(f"Validation Stage Complete: {validation_artifact.message}")
        print(f"✅ Pipeline Success! Data is valid and ready at: {ingestion_artifact.trained_file_path}")

        # ---------------------------------------------------------
        # STAGE 3: DATA TRANSFORMATION (Next Step)
        # ---------------------------------------------------------
        # logging.info(">>> Stage: Data Transformation Initiated")
        # ... stay tuned ...

    except Exception as e:
        # Our custom exception captures Filename and Line Number automatically
        raise FraudException(e, sys)

if __name__ == "__main__":
    main()