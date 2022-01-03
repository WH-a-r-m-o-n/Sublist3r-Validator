#!/usr/bin/env python3

import argparse
import concurrent.futures
import datetime
import requests
import sys
import threading
import time
from pathlib import Path


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

def get_urls(file_list, verbose):
	url_list = []
	if len(file_list) > 0:
		for file in file_list:
			print(f'\n[+] Extracting domain names from {file}')
			with open(file, "r") as f:
				for sublist3r_url in f.readlines():
					if verbose == True:
						print(sublist3r_url.strip())
					url_list.append(clean(f'https://{sublist3r_url}'))
		print(f'\n{bcolors.OKGREEN}[+]{bcolors.ENDC} Domain list created.\n')
	else:
		print("The file_list is empty; please try again.")
		sys.exit(0)

	return url_list
	
def clean(url):
	clean_sublist3r_url = url.strip()
	return clean_sublist3r_url

def create_good_site_txt_file(good_sites, output, time_now):
	file_name = f'{output}validated_sites_{time_now}.txt'
	with open(file_name, "a") as w:
		for count, site in enumerate(good_sites, start=1):
				w.write(f'{site}\n')
	print(f'\n{bcolors.OKBLUE}[+] Text file created:{bcolors.ENDC}{count} sites written to {file_name}')

def arg_clean(location):
	if location.endswith("/"):
		return location
	else:
		return f'{location}/'

def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session

def check_site(url):
	global good_sites
	session = get_session()
	try:
		with session.get(url, timeout = 1.0) as response:
			if response.status_code == 200:
				good_sites.append(url)
				print(f'{bcolors.OKGREEN}Successs:{bcolors.ENDC} {response.status_code} from {url}')
			elif response.status_code == 403:
				good_sites.append(url)
				print(f'{bcolors.OKGREEN}Successs:{bcolors.ENDC} {response.status_code} from {url}')
			elif response.status_code == 404:
				if args.verbose:
					print(f'{bcolors.FAIL}Error:{bcolors.ENDC} No connection to {url}')
				else:
					pass
			else:
				if args.verbose:
					print(f'{bcolors.FAIL}Error:{bcolors.ENDC} No connection to {url}')
				else:
					pass
	except Exception as e:
		if args.verbose:
			print(f'{bcolors.FAIL}Error:{bcolors.ENDC} Could not connect to {url}')
		else:
			pass

def pool_all_sites(sites, threads):
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(check_site, sites)

if __name__ == '__main__':
	thread_local = threading.local()
	agent = "Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0"
	good_sites = []
	output = ""
	threads = 5

	parser = argparse.ArgumentParser(
	usage="%(prog)s -i <sublist3r/text/files> <optional arguments> -o output/directory -v ",
	description="Current options are pass directory locations of sublist3r output files and directory for validated results."
	)
	parser.add_argument('-i', '--input', help='Location of sublist3r txt file(s)', required=True)
	parser.add_argument('-o', '--output', help='Output location for validation results', required=False)
	parser.add_argument('-v', '--verbose', help='Shows greater details.', action='store_true', required=False)
	parser.add_argument('-t', '--threads', help='Number of worker threads [default is 5]', required=False)
	args = parser.parse_args()

	banner()
	location = arg_clean(args.input)
	
	if args.output:
		output = arg_clean(args.output)
	files = file_finder(location)
	if args.verbose:
		urls = get_urls(files, verbose=True)
	else:
		urls = get_urls(files, verbose=False)
	if args.threads:
		threads = int(args.threads)
	
	print(f'[+] Starting validation on {len(urls)} domains using {threads} threads.\n')
	start_time = time.time()
	pool_all_sites(urls, threads)
	stop_time = time.time()
	print(f'\n{bcolors.OKGREEN}[+] Validation complete.{bcolors.ENDC}')
	print(f'{bcolors.OKBLUE}Time elapsed:{bcolors.ENDC} {stop_time - start_time : .2f} seconds\n')
	# Get current date-time
	now = datetime.datetime.now()
	time_now = now.strftime("%Y-%m-%d_%H-%M-%S")
	# Add date-time to created text file
	if len(good_sites) > 0:
		print(f'{bcolors.OKGREEN}[+] {bcolors.ENDC}{len(good_sites)} sites can be further enumerated:\n')
		for count, site in enumerate(good_sites, start=1):
			print(f'{count}. {site}')
		create_good_site_txt_file(good_sites, output, time_now)
	else:
		print(f'{bcolors.WARNING}[-] {bcolors.ENDC}No domains were valid.')
	print(f'\n[+] Done!')
