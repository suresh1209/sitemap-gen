import os
import sys
import json
import argparse

import crawler

parser = argparse.ArgumentParser(description='Sitemap-Generator')
parser.add_argument('--config', action="store", default=None, help="config file in json format")

arg = parser.parse_args()
# Read the config file
if arg.config is not None:
	try:
		config_data=open(arg.config,'r')
		config = json.load(config_data)
		config_data.close()
	except Exception as e:
		config = {}
else:
	print("Please pass the json config file as argument, --config")
	sys.exit()

crawl = crawler.Crawler(**config)
crawl.run()
