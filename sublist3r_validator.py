#!/usr/bin/env python3

import datetime
import io
import os
import sys
import queue
import requests
import threading
import urllib3

AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0"
THREADS = 20

def banner():
	print("######################################################################################")
	print("#                               Sublist3r URL Validator                              #")
	print("#                                   by Will Harmon                                   #")
	print("#                                                                                    #")
	print("######################################################################################")
	print("\n")
# function to take care of the directory walking
def step_gather(path):
	file_list = []
	for root, dir_names, file_names in os.walk(path):
		for file in file_names:
			# Only add specific file to file_list if the extension matches
			if file.rsplit(".")[-1] == "txt":
				file_list.append(os.path.join(root, file))
	print(f'[+] Discovered {len(file_list)} sublist3r output files:\n')
	for file in file_list:
		print(file)
	return file_list

def get_urls(file_list):
	url_list = []
	urls = queue.Queue()
	if len(file_list) > 0:
		for file in file_list:
			with open(file, "r") as f:
				for sublist3r_url in f.readlines():
					urls.put(clean(sublist3r_url))
					url_list.append(clean(sublist3r_url))
	else:
		print("The file_list is empty; please try again.")
		sys.exit(0)

	return urls

def url_validate(urls):
	http = urllib3.PoolManager(timeout=0.5)
	urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
	headers = {'User-Agent': AGENT}

    # Open each sublist3r file in file_list and extract the URLs
    # If URLs return a an http status, add to the good_list

	while not urls.empty():
		url = f'{urls.get()}'
		try:
			r_http = http.request(f'GET', f'https://{url}')
		except Exception as e:
			#sys.stderr.write('x');sys.stderr.flush()
			continue
		if r_http.status == 200:
			print(f'Success {r_http.status}: {url}')
			with open('sublist3r_validation.txt', 'a') as results:
				results.write(f'https://{url}\n')
		elif r_http.status == 403:
			print(f'Success {r_http.status}: {url}')
			with open('sublist3r_validation.txt', 'a') as results:
				results.write(f'https://{url}\n')
		elif r_http.status == 404:
			continue
		else:
			#print(f'{r.status_code} => {url}')
			#print(f'{r_http.status} => {url}')
			continue

def clean(url):
	clean_sublist3r_url = url.strip()
	return clean_sublist3r_url

def cleanup(time):
	current_directory = os.getcwd()
	old_name = f'{current_directory}/sublist3r_validation.txt'
	new_name = f'{current_directory}/sublist3r_validation_{time}'
	os.rename(old_name, new_name)
	print(f'\n[+] Results can be found in {new_name}.\n')

if __name__ == '__main__':
	threads = []
	banner()
	location = input("Enter the location of sublist3r output files.\n")
	files = step_gather(location)
	urls = get_urls(files)
	#sys.stdin.readline()
	print("\n[+] Starting validation...\n")
	for _ in range(THREADS):
		t = threading.Thread(target=url_validate, args=(urls,))
		threads.append(t)
		t.start()
	for x in threads:
		x.join()
	# Get current date-time
	now = datetime.datetime.now()
	time = now.strftime("%Y-%m-%d_%H:%M:%S")
	# Add date-time to resulting text file
	cleanup(time)
	print(f'[+] Done!')
