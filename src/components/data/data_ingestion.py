import os
import sys
import json
import pandas as pd
import shutil
from pathlib import Path
from src.exception import FraudException
from src.logger import logging
from src.entity.config_entity import DataIngestionConfig
from src.configuration.aws_connection import S3Connection
from src.constants import TRAINING_BUCKET_NAME, MIN_RECORDS_FOR_TRAINING, MAX_RECORDS_TO_KEEP

class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        try:
            self.config = config
            self.s3 = S3Connection()
        except Exception as e:
            raise FraudException(e, sys)

    def _move_root_files_to_data_dir(self):
        """
        Cleanup: If simulator/consumer accidentally output to project root,
        move them to the paths defined in the config.
        """
        try:
            # 1. Handle Raw Transactions
            root_raw = self.config.project_root / "transactions.jsonl"
            if root_raw.exists():
                self.config.local_raw_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(root_raw), str(self.config.local_raw_path))
                logging.info(f"Relocated {root_raw.name} to {self.config.local_raw_path}")

            # 2. Handle Processed Features
            root_features = self.config.project_root / "features.jsonl"
            if root_features.exists():
                self.config.local_processed_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(root_features), str(self.config.local_processed_path))
                logging.info(f"Relocated {root_features.name} to {self.config.local_processed_path}")
        
        except Exception as e:
            raise FraudException(e, sys)

    def _merge_with_s3_window(self, local_df: pd.DataFrame) -> pd.DataFrame:
        """
        Implements the Sliding Window:
        Downloads from data/processed/ (S3), merges, dedups, and trims.
        """
        try:
            temp_file = "s3_current_window.jsonl"
            
            try:
                logging.info(f"Downloading existing window from S3: {self.config.s3_processed_key}")
                self.s3.s3_client.download_file(
                    TRAINING_BUCKET_NAME, 
                    self.config.s3_processed_key, 
                    temp_file
                )
                s3_df = pd.read_json(temp_file, lines=True)
                combined_df = pd.concat([s3_df, local_df], ignore_index=True)
                if os.path.exists(temp_file): os.remove(temp_file)
            except Exception:
                logging.info("S3 processed key not found. Starting a new window.")
                combined_df = local_df

            # Deduplicate by transaction ID (The 'Double-Run' protection)
            combined_df.drop_duplicates(subset=['tx_id'], keep='first', inplace=True)

            # Sliding Window Trim
            if len(combined_df) > MAX_RECORDS_TO_KEEP:
                logging.info(f"Trimming window to newest {MAX_RECORDS_TO_KEEP} records.")
                combined_df = combined_df.tail(MAX_RECORDS_TO_KEEP)

            return combined_df

        except Exception as e:
            raise FraudException(e, sys)

    def sync_data_to_s3(self):
        """
        Main synchronization logic:
        1. Local datas/just_produced/ -> S3 data/raw/
        2. Local datas/processed/ -> S3 data/processed/ (via sliding window)
        """
        try:
            logging.info("Initiating Data Sync to S3...")
            self._move_root_files_to_data_dir()

            # --- PART 1: RAW DATA SYNC ---
            if self.config.local_raw_path.exists():
                logging.info(f"Uploading raw data to S3: {self.config.s3_raw_key}")
                self.s3.s3_client.upload_file(
                    str(self.config.local_raw_path), 
                    TRAINING_BUCKET_NAME, 
                    self.config.s3_raw_key
                )

            # --- PART 2: PROCESSED DATA SYNC (SLIDING WINDOW) ---
            if self.config.local_processed_path.exists():
                local_df = pd.read_json(self.config.local_processed_path, lines=True)
                
                # Apply the smart merge logic
                final_processed_df = self._merge_with_s3_window(local_df)

                # Save merged data locally to the processed path before upload
                final_processed_df.to_json(
                    str(self.config.local_processed_path), 
                    orient='records', 
                    lines=True
                )

                logging.info(f"Uploading merged window to S3: {self.config.s3_processed_key}")
                self.s3.s3_client.upload_file(
                    str(self.config.local_processed_path), 
                    TRAINING_BUCKET_NAME, 
                    self.config.s3_processed_key
                )
                logging.info(f"Sync complete. Window size: {len(final_processed_df)}")
            else:
                logging.warning("No local processed features found to sync.")

        except Exception as e:
            raise FraudException(e, sys)

    def initiate_data_ingestion(self) -> str:
        """
        The Trigger for Training:
        Downloads data from S3 data/processed/ to local datas/raw/
        """
        try:
            logging.info("Ingesting training data from S3 Warehouse...")
            
            # Ensure the datas/raw directory exists
            self.config.ingested_train_dir.mkdir(parents=True, exist_ok=True)
            
            export_file_path = self.config.ingested_train_dir / "train_snapshot.jsonl"

            self.s3.s3_client.download_file(
                TRAINING_BUCKET_NAME,
                self.config.s3_processed_key,
                str(export_file_path)
            )

            logging.info(f"Ingestion successful. Data saved to: {export_file_path}")
            return str(export_file_path)

        except Exception as e:
            raise FraudException(e, sys)