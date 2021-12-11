#!/usr/bin/env python3

import argparse
import datetime
import io
import os
import sys
import queue
import requests
import shutil
import threading
import urllib3
from pathlib import Path

parser = argparse.ArgumentParser(
	usage="%(prog)s <optional arguments>",
	description="Current options are pass directory locations of sublist3r output files and directory for validated results."
)
parser.add_argument('-i', '--input', help='Location of sublist3r txt file(s)', required=True)
parser.add_argument('-o', '--output', help='Output location for validation results', required=False)
args = parser.parse_args()

AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0"
THREADS = 10
CONFIRMED_URLS = 0

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def banner():
	print("######################################################################################")
	print("#                               Sublist3r URL Validator                              #")
	print("#                                   by Will Harmon                                   #")
	print("#                                                                                    #")
	print("######################################################################################")
	print("\n")
# function to take care of the directory walking
def file_finder(location):
	file_list = []
	print("[+] Looking for txt files...")
	working_directory = Path(location)
	for file in working_directory.iterdir():
		if str(file).endswith('.txt'):
			file_list.append(file)
	if len(file_list) > 0:
		print(f'{bcolors.OKGREEN}[+]{bcolors.ENDC} Discovered {len(file_list)} sublist3r output files:\n')
	else:
		print(f'{bcolors.WARNING}[-]{bcolors.ENDC} {len(file_list)} sublist3r output files found.\n')
		print("Ensure that you have sublist3r output txt files in the proper directory and try again.")
		sys.exit(0)
	return file_list

def get_urls(file_list):
	url_list = []
	urls = queue.Queue()
	if len(file_list) > 0:
		for file in file_list:
			print(f'\n[+] Extracting domain names from {file}')
			with open(file, "r") as f:
				for sublist3r_url in f.readlines():
					print(sublist3r_url.strip())
					urls.put(clean(sublist3r_url))
					url_list.append(clean(sublist3r_url))
		print(f'\n{bcolors.OKGREEN}[+]{bcolors.ENDC} Domain list created.\n')
	else:
		print("The file_list is empty; please try again.")
		sys.exit(0)

	return urls

def url_validate(urls, output):
	global CONFIRMED_URLS
	http = urllib3.PoolManager(timeout=2.0)
	#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
	headers = {'User-Agent': AGENT}

    # Open each sublist3r file in file_list and extract the URLs
    # If URLs return a an http status, add to the good_list

	while not urls.empty():
		url = urls.get()
		
		try:
			r_http = http.request(f'GET', f'https://{url}')
		except Exception as e:
			#sys.stderr.write('e');sys.stderr.flush()
			print(f'{bcolors.WARNING}Failure [no connection]{bcolors.ENDC}: {url}')
			#print(e)

			continue
		if r_http.status == 200:
			CONFIRMED_URLS += 1
			print(f'{bcolors.OKGREEN}Success {r_http.status}{bcolors.ENDC}: {url}')
			with open(f'{output}sublist3r_validation.txt', 'a') as results:
				results.write(f'https://{url}\n')
		elif r_http.status == 403:
			CONFIRMED_URLS += 1
			print(f'{bcolors.OKGREEN}Success {r_http.status}{bcolors.ENDC}: {url}')
			with open(f'{output}sublist3r_validation.txt', 'a') as results:
				results.write(f'https://{url}\n')
		elif r_http.status == 404:
			print(f'{bcolors.WARNING}Failure {r_http.status}{bcolors.ENDC}: {url}')
			continue
		else:
			print(f'{bcolors.WARNING}Failure {r_http.status}{bcolors.ENDC}: {url}')
			continue
	
def clean(url):
	clean_sublist3r_url = url.strip()
	return clean_sublist3r_url

def arg_clean(location):
	if location.endswith("/"):
		return location
	else:
		return f'{location}/'

def cleanup(time, output):
	old_name = f'{output}sublist3r_validation.txt'
	new_name = f'{output}sublist3r_validation_{time}.txt'
	shutil.move(old_name, new_name)
	
	#old_name = 'sublist3r_validation.txt'
	#new_name = f'sublist3r_validation_{time}.txt'
	#os.rename(old_name, new_name)
	print(f'\n[+] Results can be found in {new_name}.\n')

if __name__ == '__main__':
	threads = []
	banner()
	location = arg_clean(args.input)
	output = ""
	if args.output:
		output = arg_clean(args.output)
	files = file_finder(location)
	urls = get_urls(files)
	#sys.stdin.readline()
	print("\n[+] Starting validation...\n")
	for _ in range(THREADS):
		t = threading.Thread(target=url_validate, args=(urls, output,))
		threads.append(t)
		t.start()
	for x in threads:
		x.join()
	# Get current date-time
	now = datetime.datetime.now()
	time = now.strftime("%Y-%m-%d_%H:%M:%S")
	# Add date-time to resulting text file
	if CONFIRMED_URLS > 0:
		print(f'{bcolors.OKGREEN}[+] {bcolors.ENDC}{CONFIRMED_URLS} domains can be further enumerated.')
		cleanup(time, output)
	else:
		print(f'{bcolors.WARNING}[-] {bcolors.ENDC}No domains were valid.')
	print(f'[+] Done!')
