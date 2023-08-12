import os
from datetime import datetime
from functools import cmp_to_key
from flask import request
import uuid

resourcePath = ''


def save_file(fileType):
    file = request.files['file']
    filename = os.path.join(resourcePath, fileType, "%s_%s" % (str(uuid.uuid4()), file.filename))
    file.save(filename)


def emptyStr(string):
    return string is None or len(string) == 0


def success(msg):
    return {"success": True,
            "msg": msg}


def fail(msg):
    return {"success": False,
            "msg": msg}


def getFilePathByName(filename):
    if filename[-4:] == 'xlsx':
        fileType = 'excel'
    else:
        fileType = 'sql'
    return os.path.join(resourcePath, fileType, filename)


def file_comparator(x, y):
    x_create_time = os.path.getmtime(getFilePathByName(x))
    y_create_time = os.path.getmtime(getFilePathByName(y))
    if x_create_time > y_create_time:
        return 1
    elif x_create_time < y_create_time:
        return -1
    else:
        return 0


def getFileSize(filePath):
    file_size = os.path.getsize(filePath)
    kb = 1024
    mb = kb * 1024
    gb = mb * 1024

    if file_size < kb:
        return f"{file_size} bytes"
    elif file_size < mb:
        size_in_kb = file_size / kb
        return f"{size_in_kb:.2f} KB"
    elif file_size < gb:
        size_in_mb = file_size / mb
        return f"{size_in_mb:.2f} MB"
    else:
        size_in_gb = file_size / gb
        return f"{size_in_gb:.2f} GB"


def time_format(timestamp):
    dt_object = datetime.fromtimestamp(timestamp)
    return dt_object.strftime('%Y-%m-%d %H:%M')


def getLatestFile(fileType):
    filePath = os.path.join(resourcePath, fileType)

    files = os.listdir(filePath)
    if files is None or len(files) == 0:
        return None

    max_file = max(files, key=cmp_to_key(file_comparator))
    filePath = getFilePathByName(max_file)
    return {
        'name': max_file,
        'createTime': time_format(os.path.getmtime(filePath)),
        'size': getFileSize(filePath)
    }
