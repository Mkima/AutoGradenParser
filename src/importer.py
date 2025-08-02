import json,re
import logging

import pandas as pd


class Importer:
    def __init__(self, map_json, data_file):
        self.map_json = map_json
        self.data_file = data_file
        self.garden_config = {}
        self.columns = ['timestamp', 'level', 'type', 'sensor_id', 'value']
        self.database = pd.DataFrame(columns=self.columns)
        self.logger = logging.getLogger('importer')
    def import_data(self):
        with open(self.map_json, 'r') as f:
            self.garden_config = json.load(f)


        with open(self.data_file, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                try:

                    match = re.match(
                        r'\[([\d-]+ [\d:.]+)\]\s+(\w+)\s+(\w+)(?:\[id=(\d+)\])?:?\s+Initialized sensor', line)
                    if match is not None:
                        #First handle init case
                        self.database = pd.concat(
                            [self.database, pd.DataFrame([[pd.to_datetime(match.group(1)), match.group(2),
                                                           match.group(3), match.group(4),
                                                           'Init']], columns=self.columns)])
                    else:
                        #handle general data
                        match = re.match(r'^\[([\d-]+ [\d:.]+)\]\s+(\w+)\s+(\w+)(?:\[id=(\d+)\])?:\s*\w+=(\d+(?:\.\d+)?)', line)
                        if match is not None:
                            self.database = pd.concat([self.database, pd.DataFrame([[pd.to_datetime(match.group(1)),  match.group(2),
                                                              match.group(3),  match.group(4),
                                                              float(match.group(5))]], columns=self.columns)])
                        else:
                            #handle pump data [2025-07-31 06:06:45.000] ERROR PumpCtrl[id=2002]: Pump failure on init
                            match = re.match(
                                r'\[(\d{4}-\d{2}-\d{2} [\d:.]+)\]\s+(\w+)\s+(\w+)(?:\[id=(\d+)\])?:\s*(.+)',
                                line)
                            if match is not None:
                                self.database = pd.concat(
                                    [self.database, pd.DataFrame([[pd.to_datetime(match.group(1)), match.group(2),
                                                                   match.group(3), match.group(4),
                                                                   match.group(5)]], columns=self.columns)])


                except Exception as e:
                    self.logger.error(f'Error parsing line {line}:',e)

    def apply_mapping(self):
        try:
            self.database['name'] = self.database['sensor_id'].map(lambda x: self.garden_config['sensors'].get(x, {}).get('name'))
            self.database['model'] = self.database['sensor_id'].map(lambda x: self.garden_config['sensors'].get(x, {}).get('model'))
        except Exception as e:
            self.logger.error('Mapping error: ',e)
    def run(self):
        self.import_data()
        self.logger.info('Data imported successfully')
        self.apply_mapping()