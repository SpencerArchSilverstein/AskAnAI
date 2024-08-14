#
# Uploads a PDF to S3
# Inserts a new job record in the database
# Sends the job id back to the client.
#

import json
import boto3
import os
import uuid
import base64
import pathlib
import datatier

from configparser import ConfigParser
from pypdf import PdfReader

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: upload PDF**")

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

    #
    # the user has sent us two parameters:
    #  1. filename of their file
    #  2. raw file data in base64 encoded string
    #
    # The parameters are coming through web server 
    # (or API Gateway) in the body of the request
    # in JSON format.
    #
    print("**Accessing request body**")

    if "body" not in event:
      raise Exception("event has no body")

    body = json.loads(event["body"]) # parse the json

    if "filename" not in body:
      raise Exception("event has a body but no filename")
    if "data" not in body:
      raise Exception("event has a body but no data")

    filename = body["filename"]
    datastr = body["data"]

    print("filename:", filename)
    print("datastr (first 10 chars):", datastr[0:10])

    #
    # open connection to the database:
    #
    print("**Opening connection**")

    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

    #
    # Decode PDF
    #
    base64_bytes = datastr.encode()        # string -> base64 bytes
    bytes = base64.b64decode(base64_bytes) # base64 bytes -> raw bytes

    #
    # write raw bytes to local filesystem for upload:
    #
    print("**Writing local data file**")
    #
    # write binary to local data file
    #
    local_filename = "/tmp/data.pdf"
    outfile = open(local_filename, "wb")
    outfile.write(bytes)
    outfile.close()

    #
    # for each page, extract text, split into words,
    # and see which words are numeric values:
    #
    reader = PdfReader(local_filename)
    number_of_pages = len(reader.pages)
    pdf_text = ""
    for i in range(0, number_of_pages):
      page = reader.pages[i]
      text = page.extract_text()
      pdf_text += text
      pdf_text += " "


    # Add Job to Database 
    sql = """
      INSERT INTO jobs(status, originaldatafile, txtfilekey)
                  VALUES(%s, %s, %s);
    """

    random_uuid = str(uuid.uuid4())
    textfilekey = "Alpha/" + filename + "/" + random_uuid +".txt"
    datatier.perform_action(dbConn, sql, ["pending", filename, textfilekey])

    # Retrieve the JOB ID
    sql = "SELECT LAST_INSERT_ID();"

    row = datatier.retrieve_one_row(dbConn, sql)

    jobid = row[0]

    print("jobid:", jobid)

    # write the extracted text to a local file 
    local_text_file = "/tmp/data.txt"
    with open(local_text_file, "w") as outfile:
        outfile.write(pdf_text)

    # upload the text file to S3 bucket
    bucket.upload_file(local_text_file,
                       textfilekey,
                       ExtraArgs={
                           'ACL': 'public-read',
                           'ContentType': 'text/plain'
                       })

    print(f"**Finished uploading text file, text is now at {textfilekey}**")
    
    #
    # respond in an HTTP-like way, i.e. with a status
    # code and body in JSON format:
    #
    print("**DONE, returning jobid**")

    return {
      'statusCode': 200,
      'body': json.dumps({'jobid':str(jobid), 'bucketkey':textfilekey})
    }

  except Exception as err:
    print("**ERROR**")
    print(str(err))

    return {
      'statusCode': 400,
      'body': json.dumps(str(err))
    }
