#
# Summarize pdf using model specified by user
#

import json
import boto3
import os
import uuid
import base64
import pathlib
import datatier
import urllib.parse
import string
import openai

from configparser import ConfigParser
from pypdf import PdfReader

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: summarize pdf**")

    bucketkey_results_file = ""

    #
    # setup AWS based on config file:
    #
    config_file = 'config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file

    configur = ConfigParser()
    configur.read(config_file)

    #
    # configure for S3 access:
    #
    s3_profile = 's3readwrite'
    boto3.setup_default_session(profile_name=s3_profile)

    bucketname = configur.get('s3', 'bucket_name')

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucketname)

    #
    # configure for RDS access
    #
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')

    # get bucketkey
    if "bucketkey" in event:
      bucketkey = event["bucketkey"]
    elif "pathParameters" in event:
      if "bucketkey" in event["pathParameters"]:
        bucketkey = event["pathParameters"]["bucketkey"]
      else:
        raise Exception("requires bucketkey parameter in pathParameters")
    else:
        raise Exception("requires bucketkey parameter in event")

    print("bucketkey:", bucketkey)

    # get model
    if "model" in event:
      model = event["model"]
    elif "pathParameters" in event:
      if "model" in event["pathParameters"]:
        model = event["pathParameters"]["model"]
      else:
        raise Exception("requires model parameter in pathParameters")
    else:
        raise Exception("requires model parameter in event")

    print("model:", model)

    bucketkey_results_file = bucketkey[0:-4] + "_summary.txt"

    print("bucketkey results file:", bucketkey_results_file)

    #
    # download text file from S3 to LOCAL file system:
    #
    print("**DOWNLOADING '", bucketkey, "'**")

    local_text_file = "/tmp/data.txt"

    bucket.download_file(bucketkey, local_text_file)

    #
    # read the local text file:
    #
    print("**PROCESSING local text file**")

    with open(local_text_file, "r") as infile:
      text = infile.read()

    #
    # update status column in DB for this job,
    # change the value to "processing - starting". Use the
    # bucketkey --- stored as datafilekey in the table ---
    # to identify the row to update. Use the datatier.
    #
    # open connection to the database:
    #
    print("**Opening DB connection**")
    #
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    #
    sql = """
    UPDATE jobs SET status = 'processing - starting' WHERE txtfilekey = %s;
    """
    row = datatier.perform_action(dbConn, sql, [bucketkey])

    if row == 0:
      raise Exception("existing row has not been modified")

    #
    # analysis complete, write the results to local results file:
    #
    local_results_file = "/tmp/results.txt"

    print("local results file:", local_results_file)

    if model == 'ChatGPT':
      openai.api_key = 'OPEN_AI_API_KEY'
      response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system",
            "content": "You are an assistant that summarizes large texts"
        }, {
            "role": "user",
            "content": f"Summarize the following text: {text}"
        }])

      outfile = open(local_results_file, "w")
      outfile.write("**ChatGPT summary**\n")
      outfile.write(response.choices[0].message['content'].strip())
      outfile.close()

    elif model == 'Gemini':
      google_api_key = "GEMINI_API_KEY"
      genai.configure(api_key=google_api_key)
      model = genai.GenerativeModel('gemini-1.5-flash')
      response = model.generate_content("Summarize this text:" +  text)
      outfile = open(local_results_file, "w")
      outfile.write("**Gemini summary**\n")
      outfile.write(response.text)
      outfile.close

    elif model == 'Claude':
      API_KEY = "CLAUDE_API_KEY"
      API_URL = "https://api.anthropic.com/v1/messages"

      payload = {
          "model": "claude-3-sonnet-20240229", 
          "max_tokens": 1000, 
          "temperature": 0.3,
          "messages": [{ "role": "user", "content": f"Summarize this text: {text}" }]
      }

      headers = {
          "Content-Type": "application/json",
          "X-API-Key": API_KEY,
          "anthropic-version": "2023-06-01"
      }

      response = requests.post(API_URL, headers=headers, json=payload)

      if response.status_code == 200:
          result = response.json()
          summary = result['content'][0]['text']
          print("Summary:")
          print(summary)
      else:
          print(f"Error: {response.status_code}")
          print(json.dumps(response.json(), indent=2))

    #
    # upload the results file to S3:
    #
    print("**UPLOADING to S3 file", bucketkey_results_file, "**")

    bucket.upload_file(local_results_file,
                       bucketkey_results_file,
                       ExtraArgs={
                         'ACL': 'public-read',
                         'ContentType': 'text/plain'
                       })

    # 
    # The last step is to update the database to change
    # the status of this job, and store the results
    # bucketkey for download:
    #
    sql = """
    UPDATE jobs SET status = 'completed', responsefilekey = %s WHERE txtfilekey = %s;
    """
    datatier.perform_action(dbConn, sql, [bucketkey_results_file, str(bucketkey)])


    #
    # done!
    #
    # respond in an HTTP-like way, i.e. with a status
    # code and body in JSON format:
    #
    print("**DONE, returning success**")

    return {
      'statusCode': 200,
      'body': json.dumps("success")
    }

  #
  # on an error, try to upload error message to S3:
  #
  except Exception as err:
    print("**ERROR**")
    print(str(err))

    local_results_file = "/tmp/results.txt"
    outfile = open(local_results_file, "w")

    outfile.write(str(err))
    outfile.write("\n")
    outfile.close()

    if bucketkey_results_file == "": 
      #
      # we can't upload the error file:
      #
      pass
    else:
      # 
      # upload the error file to S3
      #
      print("**UPLOADING**")
      #
      bucket.upload_file(local_results_file,
                         bucketkey_results_file,
                         ExtraArgs={
                           'ACL': 'public-read',
                           'ContentType': 'text/plain'
                         })

    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    #
    sql = """
    UPDATE jobs SET status = 'error', responsefilekey = %s WHERE txtfilekey = %s;
    """
    datatier.perform_action(dbConn, sql, [bucketkey_results_file, bucketkey])

    #
    # done, return:
    #    
    return {
      'statusCode': 400,
      'body': json.dumps(str(err))
    }
