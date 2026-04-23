import os
import sys
import pandas as pd
import yaml
from datetime import datetime
from pathlib import Path
from src.exception import FraudException
from src.logger import logging
from src.entity.config_entity import DataValidationConfig
from src.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact

class DataValidation:
    def __init__(self, data_ingestion_artifact: DataIngestionArtifact,
                 data_validation_config: DataValidationConfig):
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config = data_validation_config
            
            # Load schema from yaml
            with open(self.data_validation_config.schema_file_path, 'r') as f:
                self.schema = yaml.safe_load(f)
                
        except Exception as e:
            raise FraudException(e, sys)

    def validate_number_of_columns(self, dataframe: pd.DataFrame) -> bool:
        try:
            # Combine raw and processed column counts from schema
            total_expected = len(self.schema["raw_columns"]) + len(self.schema["processed_columns"])
            status = len(dataframe.columns) == total_expected
            logging.info(f"Column count validation: Expected {total_expected}, Got {len(dataframe.columns)}. Status: {status}")
            return status
        except Exception as e:
            raise FraudException(e, sys)

    def is_column_exist(self, dataframe: pd.DataFrame) -> bool:
        try:
            dataframe_columns = list(dataframe.columns)
            all_expected_columns = {**self.schema["raw_columns"], **self.schema["processed_columns"]}
            
            missing_cols = [col for col in all_expected_columns.keys() if col not in dataframe_columns]
            
            if missing_cols:
                logging.error(f"Missing columns detected: {missing_cols}")
                return False
            return True
        except Exception as e:
            raise FraudException(e, sys)

    def validate_data_types(self, dataframe: pd.DataFrame) -> bool:
        try:
            all_expected_dtypes = {**self.schema["raw_columns"], **self.schema["processed_columns"]}
            for column, expected_type in all_expected_dtypes.items():
                actual_type = str(dataframe[column].dtype)
                
                # Flexible check for floats and ints
                if 'float' in actual_type and 'float' in expected_type: continue
                if 'int' in actual_type and 'int' in expected_type: continue
                if actual_type == expected_type: continue
                
                logging.error(f"Type Mismatch in {column}: Expected {expected_type}, Got {actual_type}")
                return False
            return True
        except Exception as e:
            raise FraudException(e, sys)

    def check_for_nulls(self, dataframe: pd.DataFrame) -> bool:
        try:
            null_count = dataframe.isnull().sum().sum()
            if null_count > 0:
                logging.warning(f"Dataset contains {null_count} null values.")
                return False
            return True
        except Exception as e:
            raise FraudException(e, sys)

    def initiate_data_validation(self) -> DataValidationArtifact:
        try:
            # 1. Load Data
            train_file_path = self.data_ingestion_artifact.trained_file_path
            df = pd.read_json(train_file_path, lines=True)
            
            # 2. Execute Suite of Checks
            logging.info("Starting validation suite...")
            error_msg = ""
            
            col_count_status = self.validate_number_of_columns(df)
            col_exist_status = self.is_column_exist(df)
            data_type_status = self.validate_data_types(df)
            null_check_status = self.check_for_nulls(df)
            
            # Overall Status is True only if ALL checks pass
            overall_status = all([col_count_status, col_exist_status, data_type_status, null_check_status])

            # 3. Create and Save YAML Report
            report_dir = self.data_validation_config.data_validation_dir
            report_dir.mkdir(parents=True, exist_ok=True)
            
            report_path = report_dir / self.data_validation_config.report_file_name
            
            report_content = {
                "validation_status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "data_snapshot": str(train_file_path),
                "metrics": {
                    "record_count": len(df),
                    "column_count_check": "Passed" if col_count_status else "Failed",
                    "column_names_check": "Passed" if col_exist_status else "Failed",
                    "data_types_check": "Passed" if data_type_status else "Failed",
                    "missing_values_check": "Passed" if null_check_status else "Failed"
                }
            }
            
            with open(report_path, "w") as f:
                yaml.dump(report_content, f)

            logging.info(f"Validation report successfully saved to: {report_path}")

            return DataValidationArtifact(
                validation_status=overall_status,
                message="Validation Success" if overall_status else "Validation Failed",
                validation_report_path=report_path
            )

        except Exception as e:
            raise FraudException(e, sys)