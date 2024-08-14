#
# Client-side python app for our final project
# It is a set of lambda functions in AWS through API Gateway
#
# Authors:
#   Aryaman, Archie, Eric
#

import requests
import json

import uuid
import pathlib
import logging
import sys
import os
import base64

from configparser import ConfigParser
from getpass import getpass

############################################################
# prompt - model
def prompt_model():
  """
  Prompts the user to input the desired model

  Parameters
  ----------
  None

  Returns
  -------
  Name of model chosen by user
  """

  print()
  print(">> Enter Model:")
  print("   1 => ChatGPT")
  print("   2 => Gemini")
  print("   3 => Claude")
  cmd = input()

  if cmd == "1":
    return "ChatGPT"
  elif cmd == "2":
    return "Gemini"
  elif cmd == "3":
    return "Claude"
  else:
    print("Invalid response")
    sys.exit(0)

############################################################
# prompt - function
def prompt_function():
  """
  Prompts the user to enter 

  Parameters
  ----------
  None

  Returns
  -------
  Command number entered by user (0/1)
  """
  print()
  print(">> Enter a command:")
  print("   0 => end")
  print("   1 => upload pdf, select model, display response")

  cmd = input()

  if cmd == "":
    cmd = -1
  elif not cmd.isnumeric():
    cmd = -1
  else:
    cmd = int(cmd)
  return cmd

############################################################
# upload pdf and summarize using chosen model
def upload_pdf(baseurl):
  """
  Prompts the user for a local filename and uploads that PDF to S3
  Then displays the summary of the PDF using chosen model

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  # get local PDF
  print("Enter PDF filename>")
  local_filename = input()
  print("Uploading PDF to S3...")

  if not pathlib.Path(local_filename).is_file():
    print("PDF file '", local_filename, "' does not exist...")
    return

  if not local_filename.endswith(".pdf"):
    print(local_filename, "is not a PDF...")
    return
  
  try:
    # build data packet
    infile = open(local_filename, "rb")
    bytes = infile.read()
    infile.close()

    # encode pdf as base64
    data = base64.b64encode(bytes)
    datastr = data.decode()
    data = {"filename": local_filename, "data": datastr}

    # call web service:
    api = '/pdf'
    url = baseurl + api
    res = requests.post(url, json=data)

    # failure
    if res.status_code != 200:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      print(res.json())
      return

    # success
    body = res.json()
    jobid = body['jobid']
    bucketkey = body['bucketkey']
    print("PDF uploaded, job id =", jobid)

    # prompt user for the model
    model = prompt_model()
    print("Generating response...")

    # call web service with chosen model
    if model == "ChatGPT":
      api = "/cgpt-pdf-summarize"
    elif model == "Claude":
      api = "/claude-pdf-summary"
    elif model == "Gemini":
      api = "/gemini-pdf-summary"
    else:
      sys.exit(0)
    
    url = baseurl + api

    data = {"bucketkey":bucketkey}
    res = requests.post(url, json=data)

    # failure
    if res.status_code != 200:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      print(res.json())
      print(res)
      return

    # success
    body = res.json()

    # now display text by downloading from s3
    print()
    print("Summary using", model, ":")
    print(body['response'])

  except Exception as e:
    logging.error("upload() failed:")
    logging.error(e)
    return


############################################################
# main
def main():

  try:
    print('** Welcome to ALPHA LLM **')
    print()

    # eliminate traceback so we just get error message:
    sys.tracebacklimit = 0

    # config file
    config_file = 'pdf-parser-config.ini'

    # ensure config file exists
    if not pathlib.Path(config_file).is_file():
      print("**ERROR: config file '", config_file, "' does not exist, exiting")
      sys.exit(0)

    # setup base URL to web service:
    configur = ConfigParser()
    configur.read(config_file)
    baseurl = configur.get('client', 'webservice')

    #
    # make sure baseurl does not end with /, if so remove:
    #
    if len(baseurl) < 16:
      print("**ERROR: baseurl '", baseurl, "' is not nearly long enough...")
      sys.exit(0)

    if baseurl == "https://YOUR_GATEWAY_API.amazonaws.com":
      print("**ERROR: update config file with your gateway endpoint")
      sys.exit(0)

    if baseurl.startswith("http:"):
      print("**ERROR: your URL starts with 'http', it should start with 'https'")
      sys.exit(0)

    lastchar = baseurl[len(baseurl) - 1]
    if lastchar == "/":
      baseurl = baseurl[:-1]

    # main processing loop:
    cmd = prompt_function()
    while cmd != 0:
      #
      if cmd == 1:
        upload_pdf(baseurl)
      else:
        print("** Unknown command, try again...")
      cmd = prompt_function()

    # done
    print()
    print('** done **')
    sys.exit(0)

  except Exception as e:
    logging.error("**ERROR: main() failed:")
    logging.error(e)
    sys.exit(0)

if __name__ == "__main__":
  main()