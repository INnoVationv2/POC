import json
import uuid
from datetime import datetime

from flask import Flask, request, render_template, session, send_file
import os

import utils
from nifi import Nifi, nifiEnvs, getAllEnvInfo
from exception import NifiException, NormalizeException
from utils import getLatestFile, getFilePathByName

app = Flask(__name__)
app.template_folder = 'template'
app.config['RESOURCE_FOLDER'] = 'resources'
app.config['SECRET_KEY'] = '778899'


@app.route('/', methods=['GET'])
def main():
    utils.resourcePath = app.config['RESOURCE_FOLDER']
    envs = getAllEnvInfo()
    return render_template('main.html', envs=envs)


# Get Host And Username by Instance Name
@app.route("/nifi/instance/<instanceName>", methods=['GET'])
def get_nifi_Instance_info_by_name(instanceName):
    env = nifiEnvs[instanceName]
    session['currentInstance'] = env.toMapWithPwd()
    return json.dumps(env.toMap())


@app.route('/file/upload/excel', methods=['POST'])
def upload_excel():
    utils.save_file("excel")
    return 'Excel upload success!'


@app.route('/file/upload/sql', methods=['POST'])
def upload_sql():
    utils.save_file("sql")
    # 错误时
    return send_file("target/test.txt"), 400
    # return 'SQL upload success!'


@app.route('/file/getCurrentFile')
def getCurrentFile():
    fileInfo = {}

    excelFileInfo = getLatestFile('excel')
    fileInfo['excel'] = None if excelFileInfo is None else excelFileInfo

    sqlFileInfo = getLatestFile('sql')
    fileInfo['sql'] = None if sqlFileInfo is None else sqlFileInfo

    return json.dumps(fileInfo)


@app.route('/file/<filename>')
def downLoad(filename):
    file = getFilePathByName(filename)
    if not os.path.exists(file):
        return "File not Found"
    originName = filename[37:]
    return send_file(file, as_attachment=True, download_name=originName)


@app.route('/nifi/update/<parameterContextId>', methods=['GET'])
def updateParam(parameterContextId):
    user = session['currentInstance'].copy()
    user['parameterContextId'] = parameterContextId
    nifi = Nifi.buildFromMap(user)
    try:
        nifi.checkParameterContextId()
    except NifiException as ex:
        return ex.error_msg
    params = [Param(name='zzz', value='xxx'), Param(name='111', value='xxx')]
    nifi.updateParameter(params)
    return 'Update Success!'

class Param:
    def __init__(self, name, value):
        self.name = name
        self.value = value


if __name__ == '__main__':
    app.run(port=5001, debug=True)
