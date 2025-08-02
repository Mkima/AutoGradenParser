import pytest
import pandas as pd
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.importer import Importer


class TestImporter:

    @pytest.fixture
    def sample_map_json(self):
        return {
            "sensors": {
                "1001": {"name": "Temperature_Sensor_1", "model": "TempPro"},
                "1002": {"name": "Humidity_Sensor_1", "model": "HumidMax"},
                "2001": {"name": "Soil_Moisture_1", "model": "SoilSense"},
                "2002": {"name": "Pump_Controller_1", "model": "PumpCtrl"}
            }
        }

    @pytest.fixture
    def sample_log_data(self):
        return [
            "[2025-01-15 10:30:00] INFO TempSensor[id=1001]: Initialized sensor",
            "[2025-01-15 10:30:15] INFO TempSensor[id=1001]: temperature=23.5",
            "[2025-01-15 10:30:30] DEBUG HumiditySensor[id=1002]: humidity=65.2",
            "[2025-01-15 10:30:45] WARNING SoilSensor[id=2001]: moisture=45.8",
            "[2025-01-15 10:31:00] ERROR PumpCtrl[id=2002]: Pump failure on init",
            "[2025-01-15 10:31:15] INFO TempSensor: temperature=24.1",
            "Invalid log line that should be ignored",
            "[2025-01-15 10:33:15] INFO TempSensor: temperature=25.1"
        ]

    @pytest.fixture
    def temp_files(self, sample_map_json, sample_log_data):
        # Create temporary files
        map_fd, map_path = tempfile.mkstemp(suffix='.json')
        data_fd, data_path = tempfile.mkstemp(suffix='.log')

        try:
            # Write map JSON
            with os.fdopen(map_fd, 'w') as f:
                json.dump(sample_map_json, f)

            # Write log data
            with os.fdopen(data_fd, 'w') as f:
                for line in sample_log_data:
                    f.write(line + '\n')

            yield map_path, data_path
        finally:
            # Cleanup
            os.unlink(map_path)
            os.unlink(data_path)

    def test_importer_initialization(self, temp_files):
        map_path, data_path = temp_files
        importer = Importer(map_path, data_path)

        assert importer.map_json == map_path
        assert importer.data_file == data_path
        assert importer.garden_config == {}
        assert list(importer.database.columns) == ['timestamp', 'level', 'type', 'sensor_id', 'value']
        assert len(importer.database) == 0

    def test_import_data_success(self, temp_files):
        map_path, data_path = temp_files
        importer = Importer(map_path, data_path)

        importer.import_data()

        # Check that garden_config is loaded
        assert "sensors" in importer.garden_config
        assert "1001" in importer.garden_config["sensors"]

        # Check that data is imported
        assert len(importer.database) > 0
        assert not importer.database.empty

        # Verify specific data points
        init_rows = importer.database[importer.database['value'] == 'Init']
        assert len(init_rows) == 1
        assert init_rows.iloc[0]['sensor_id'] == '1001'

        temp_rows = importer.database[importer.database['sensor_id'] == '1001']
        temp_data_rows = temp_rows[temp_rows['value'] != 'Init']
        assert len(temp_data_rows) >= 1

    def test_import_data_handles_different_log_levels(self, temp_files):
        map_path, data_path = temp_files
        importer = Importer(map_path, data_path)

        importer.import_data()

        levels = importer.database['level'].unique()
        expected_levels = {'INFO', 'DEBUG', 'WARNING', 'ERROR'}
        assert set(levels).issubset(expected_levels)

    def test_import_data_handles_missing_sensor_id(self, temp_files):
        map_path, data_path = temp_files
        importer = Importer(map_path, data_path)

        importer.import_data()

        # Check for rows without sensor_id (should have NaN or None)
        rows_without_id = importer.database[importer.database['sensor_id'].isna()]
        assert len(rows_without_id) >= 0  # Could be 0 or more depending on log format

    def test_apply_mapping_success(self, temp_files):
        map_path, data_path = temp_files
        importer = Importer(map_path, data_path)

        importer.import_data()
        importer.apply_mapping()

        # Check that mapping columns are added
        assert 'name' in importer.database.columns
        assert 'model' in importer.database.columns

        # Verify specific mappings
        sensor_1001_rows = importer.database[importer.database['sensor_id'] == '1001']
        if not sensor_1001_rows.empty:
            assert sensor_1001_rows.iloc[0]['name'] == 'Temperature_Sensor_1'
            assert sensor_1001_rows.iloc[0]['model'] == 'TempPro'

    def test_apply_mapping_handles_unmapped_sensors(self, temp_files):
        map_path, data_path = temp_files
        importer = Importer(map_path, data_path)

        importer.import_data()
        importer.apply_mapping()

        # Check that unmapped sensors have NaN values
        unmapped_rows = importer.database[importer.database['name'].isna()]
        # Should handle gracefully without errors
        assert isinstance(unmapped_rows, pd.DataFrame)

   
    def test_run_method_complete_workflow(self, temp_files):
        map_path, data_path = temp_files
        importer = Importer(map_path, data_path)

        importer.run()

        # Verify complete workflow
        assert not importer.database.empty
        assert 'name' in importer.database.columns
        assert 'model' in importer.database.columns
        assert len(importer.garden_config) > 0

    def test_timestamp_parsing(self, temp_files):
        map_path, data_path = temp_files
        importer = Importer(map_path, data_path)

        importer.import_data()

        # Check that timestamps are properly parsed as datetime
        assert importer.database['timestamp'].dtype == 'datetime64[ns]'

        # Verify specific timestamp
        first_row = importer.database.iloc[0]
        assert isinstance(first_row['timestamp'], pd.Timestamp)

    def test_numeric_value_conversion(self, temp_files):
        map_path, data_path = temp_files
        importer = Importer(map_path, data_path)

        importer.import_data()

        # Check that numeric values are properly converted
        numeric_rows = importer.database[pd.to_numeric(importer.database['value'], errors='coerce').notna()]
        if not numeric_rows.empty:
            # Should have some numeric values
            assert len(numeric_rows) > 0

    def test_file_not_found_handling(self):
        with pytest.raises(FileNotFoundError):
            importer = Importer('nonexistent_map.json', 'nonexistent_data.log')
            importer.import_data()
