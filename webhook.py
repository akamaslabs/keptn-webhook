import logging
import sys
import time
from flask import Flask, request
import subprocess
import threading
import requests
import json
import os
import base64

# Config logging
logging.basicConfig(stream=sys.stdout,
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

app = Flask(__name__)


@app.route("/v1/study-run", methods=['POST'])
def get_request():    
    def check_study():
        studyStatus = get_study_status(body["study-id"])
        while studyStatus != "FINISHED":
            app.logger.info(f"Waiting for study completion. Status: {studyStatus}")
            time.sleep(30)
            studyStatus = get_study_status(body["study-id"]) 

        app.logger.info("Study is over")
        send_finished(body)
    
    body, user, pwd = parse_request()

    if init() != 0:
        return "The connection to Akamas can not be established, check the services.", 500

    if login(user, pwd) != 0:
        return "User/password combination is wrong", 401
    
    #get_best_configuration(body['study-id'])
    
    if launch_study(body["study-id"]) == 1:
        return "Study is already running, wait for completion", 422

    threading.Thread(target=check_study).start()
    
    return "Request parsed"

def parse_request():
    app.logger.info("Request received")
    params = dict(request.args)
    app.logger.debug(f"parameters: {params}")

    body = request.get_json()
    app.logger.debug(f"json body: {body}")

    # Decode password from Basic Access authentication
    userPwd = request.headers['Authorization'].lstrip(' ').lstrip('Basic ')
    userPwd = base64.b64decode(userPwd).decode("utf-8").split(':')
    user = userPwd[0]
    password = userPwd[1]
    app.logger.debug(f"user: {user}")

    return body, user, password

def init():
    # Config & login
    configReq = "akamas init config -a http://kong:8000 -w default"
    launch_command(configReq)

    testReq = "akamas status"
    out, returnCode = launch_command(testReq)
    if (returnCode != 0):
        app.logger.info(f"The connection to Akamas can not be established")
        return returnCode

    return 0
    
def login(user, password):        
    loginReq = f"akamas login -u {user} -p {password}"
    out, returnCode = launch_command(loginReq)

    return returnCode

def launch_study(studyId):
    if get_study_status(studyId) == "RUNNING":
        return 1

    launch_study = f"yes y | akamas start study {studyId}"
    launch_command(launch_study)

    return 0

def get_study_status(studyId):
    statusRequest = f'akamas list -o json studies'
    output, statusCode = launch_command(statusRequest)

    studies_json = json.loads(output)

    for study in studies_json:
        if (study["id"] == studyId):
            app.logger.info(f"Study: {study}")
            app.logger.info(f"Study status: {study['status']}")

            return study["status"]

    return 1
 
def launch_command(request):
    run = subprocess.run(request, shell=True, capture_output=True, text=True)
    app.logger.debug(f"return code: {run.returncode}\nstdout:\n{run.stdout}")

    if run.returncode != 0:
        app.logger.error(run.stderr)

    return run.stdout, run.returncode

def get_parameters():
    return dict(request.args)

def send_finished(body):
    send_event("finished", body)

def send_event(eventState, body):
    # According to the keptn documentation:
    # 'This custom data will be automatically appended to every remaining triggered task event in the sequence. The data must be passed in an attribute with the name of the task.'
    # Thus the results are stored in the data.optimize key
    data = {
      "project": body['project'],
      "stage": body['stage'],
      "service": body['service'],
      "status": "succeeded",
      "result": "pass",
      "optimize": get_best_configuration(body['study-id'])
    }

    reply = {
        "source": "akamas",
        "data": data,
        "specversion": "1.0",
        "type": f"{body['type'].rsplit('.', 1)[0]}.{eventState}",
        "shkeptncontext": body['shkeptncontext'],
        "triggeredid": body['triggeredid']
    }

    reply = json.dumps(reply)

    app.logger.debug(f"reply: {reply}")

    headers = {
        'Content-type': 'application/json',
        'accept': 'application/json',
        'x-token': os.environ['KEPTN_TOKEN']
    }

    response = requests.post(f"{os.environ['KEPTN_URL'].rstrip('/')}/api/v1/event", headers=headers, data=reply, verify=False)

    return reply

def get_best_configuration(studyId):
    studyRequest = f'akamas describe -o json study {studyId}'
    output, statusCode = launch_command(studyRequest)

    study = json.loads(output)

    app.logger.debug(f'Status code: {statusCode}')
    app.logger.debug(f"Study: {study}")
    app.logger.info(f'Best configuration: {study["best configuration"]}')

    return study['best configuration']

