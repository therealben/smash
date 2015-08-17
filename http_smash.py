#!/usr/bin/python3

"""

 http_smash.py : This script tests a http server  by sending X requests Y times.

 Author: Ben Kelly <kibelan@gmail.com> 
 https://github.com/therealben

 Options:
 
 --url http://hostname.domain 
    http_smash will only query this single URL each iteration
 --urlfile /tmp/file_of_urls
    http_smash will query every URL in this file each iteration
 iterations
    The number of times to query each URL
 smash_threads
    The number of concurrent threads to run

 Licence:

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>

"""




import threading
import argparse
import queue
import urllib.request
import time
import sys


#Setup input queue
input_queue = queue.Queue()

#Define output list
output_list = []




class Smash_Http(threading.Thread):
  """Uses urllib and threading to query a web server
  this class takes no arguments but does require the following
  to be defined globally

  input_queue (queue.Queue) 
  output_list (list)

  Smash_Http does not produce any output, all output from urllib is
  sent to output_list"""
  
  def __init__(self):
    """Assign input_queue and output_list"""
    threading.Thread.__init__(self)
    self.input_queue = input_queue
    self.output_list = output_list
    
  def run(self):
    """Get input from input_queue and queries a URL using urllib.
    Takes no arguments and nothing is returned"""
    while True:
      try:
        host = self.input_queue.get()
        url = urllib.request.urlopen(host)
        #If we got this far without a urllib.error the request was ok
        self.output_list.append("0 OK %s %s" % (host, time.time()))
      except urllib.error.HTTPError:
        #Error from Web server?
        self.output_list.append("1 HTTPError %s %s" % (host, time.time()))
      except urllib.error.URLError:
        #No route to host?
        self.output_list.append("1 URLError %s %s" % (host, time.time()))
      self.input_queue.task_done()




def main(url_list,iterations,smash_threads):
  """Sets up the input queue and calls the Smash_Http class.
  main() requires the following arguments

  url_list (list)
  iterations (int)
  smash_threads (int)
  
  main() does not return anything but it does print output to the console"""
  
  #Record the start time of this script. 
  start_time = time.time()

  #Setup the threads
  for a in range(smash_threads):
    smash_t = Smash_Http()
    smash_t.setDaemon(True)
    smash_t.start()

  #Submit entries into the queue
  for b in range(iterations):
    for single_url in url_list:
      input_queue.put(single_url)

  #Wait for the jobs to finish
  input_queue.join()

  #Record the end time of this script
  end_time = time.time()

  #Work out how many http ok vs http error we captured
  http_ok_response = 0
  http_error_response = 0
  for each_result in output_list:
    if each_result[0] == "0":
      http_ok_response+=1
    elif each_result[0] == "1":
      http_error_response+=1
    else:
      print("Error processing output_list, http_response should be 1 or 0")
      print(each_result[0])
      sys.exit(1)
 
  #Print the output to console
  print("Script ran for %s seconds and sent %s requests." % ((end_time-start_time),len(output_list)))
  print("Rate: %.2f requests per second" % ((len(output_list)/(end_time-start_time))))
  print("Response OK: %s Error: %s" % (http_ok_response,http_error_response))

  #Exit without error
  sys.exit(0)




if __name__ == "__main__":
  #Script is being run on the command line, process arguments, perform basic
  #check of arguments and call main()

  #Setup the arguments
  parser = argparse.ArgumentParser()
  parser.add_argument("--url", help="A single URL you want to test")
  parser.add_argument("--urlfile", help="Parse a file containing URLs instead of specifying a single URL")
  parser.add_argument("iterations", help="The number of time to test the url", type=int)
  parser.add_argument("smash_threads", help="The number of concurrent threads to run", type=int)
  args = parser.parse_args()


  #Check to make sure that --url or --urlfile are called and not both
  if args.url and args.urlfile:
    print("Error you can not specify --url and --urlfile")
    sys.exit(1)
  elif not args.url and not args.urlfile:
    print("Error you need to specify --url or --urlfile")
    sys.exit(1) 
 
  #Put the single url into a list or open the urlfile, read it in
  #and put each url in the file into a list
  url_list = []
  if args.url:
    url_list.append(args.url)
  elif args.urlfile:
    try:
      with open(args.urlfile) as in_file:
        for each in in_file.readlines():
          url_list.append(each)
    except FileNotFoundError:
      print("Error: File %s was not found" % args.urlfile)
      sys.exit(1)

  #Everything is awesome call main
  main(url_list,args.iterations,args.smash_threads)
