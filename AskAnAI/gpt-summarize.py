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
    print("**lambda: summarize pdf using ChatGPT**")

    # 
    # in case we get an exception, initial this filename
    # so we can write an error message if need be:
    #

    bucketkey_results_file = ""

    if "body" not in event:
      raise Exception("event has no body")
    body = json.loads(event["body"]) # parse the json

    if "bucketkey" not in body:
      raise Exception("event has a body but no bucketkey")

    bucketkey = body["bucketkey"]
    print(bucketkey)

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

    extension = pathlib.Path(bucketkey).suffix

    # changed .pdf to .txt
    if extension != ".txt" : 
      raise Exception("expecting S3 document to have .txt extension")

    bucketkey_results_file = bucketkey[0:-4] + "response" + ".txt" # added response, changed .pdf to .txt
    
    print("**READING TEXT FILE FROM S3**")
    obj = s3.Object(bucketname, bucketkey)
    text_content = obj.get()['Body'].read().decode('utf-8')


    #
    # Feed the text content of the pdf file into GPT
    #
    print("gpt processing start")
    openai.api_key = 'OPEN_AI_KEY'
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[{
          "role": "system",
          "content": "You are an assistant that summarizes large texts"
      }, {
          "role": "user",
          "content": f"Summarize the following text: {text_content}"
      }])


    local_results_file = "/tmp/results.txt"
    print("local results file:", local_results_file)

    with open(local_results_file, "w") as outfile:
        outfile.write("**ChatGPT summary**\n")
        outfile.write(response.choices[0].message['content'].strip())

    print("GPT processing end")

    print("**UPLOADING to S3 file", bucketkey_results_file, "**")
    bucket.upload_file(local_results_file,
                       bucketkey_results_file,
                       ExtraArgs={
                           'ACL': 'public-read',
                           'ContentType': 'text/plain'
                       })

   
    print("**DONE, returning success**")

    return {
        'statusCode': 200,
        'body': bucketkey_results_file
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
    return {'statusCode': 400, 'body': json.dumps({'error': 'error'})}