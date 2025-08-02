import argparse
import datetime
import pathlib
from src import importer,analyzer


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input',default=pathlib.PosixPath('data/plant_sensor_uart_full.log'), type=pathlib.PosixPath, required=False)
    parser.add_argument('--mapping_json',default=pathlib.PosixPath('data/device_map_extended.json'), type=pathlib.PosixPath, required=False)
    parser.add_argument('--output', type=str, required=False,default=pathlib.PosixPath('../data/log_analysis'+datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")))
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    importer = importer.Importer(args.mapping_json,args.input)
    importer.run()
    analyzer = analyzer.run(importer.garden_config,importer.database)



