import json

import requests
import yaml

from exception import NifiException


def loadNifiConf():
    confFilePath = 'conf/nifi.yaml'
    with open(confFilePath) as data:
        nifiConf = yaml.safe_load(data)
    envs = {}
    for env in nifiConf.items():
        detail = NifiSecretInfo(env[0], env[1])
        envs[env[0]] = detail
    return envs


class NifiSecretInfo:
    def __init__(self, envName, conf):
        self.envName = envName
        self.host = conf['host']
        self.username = conf['username']
        self._pwd = conf['pwd']

    def getHost(self):
        if self.host is not None:
            return '%s/nifi-api' % self.host
        return None

    def getPwd(self):
        return self._pwd

    def toMap(self):
        return {'envName': self.envName,
                'host': self.host,
                'username': self.username}

    def toMapWithPwd(self):
        map = self.toMap()
        map['host'] = self.getHost()
        map['pwd'] = self._pwd
        return map


class Nifi:
    def __init__(self):
        self._host = None
        self.username = None
        self.pwd = None
        self.parameterContextId = None

        self.accessToken = None
        self.requestToken = None
        self.headers = {'Connection': 'keep - alive'}
        self.httpCode = [201, 200]

    @staticmethod
    def buildFromMap(infoMap):
        nifi = Nifi()
        nifi._host = infoMap['host']
        nifi.username = infoMap['username']
        nifi.pwd = infoMap['pwd']
        nifi.parameterContextId = infoMap['parameterContextId']
        nifi._login()
        return nifi

    def checkParameterContextId(self):
        url = '%s/parameter-contexts/%s?includeInheritedParameters=true' % (self._host, self.parameterContextId)
        headers = self._getHeaders()
        response = requests.get(url=url, headers=headers, verify=False)
        if response.status_code not in self.httpCode:
            raise NifiException('ParameterContext: %s is not Exist!' % self.parameterContextId)
        return True

    def _getCookies(self):
        cookies = None
        if self.accessToken is not None:
            cookies = self.accessToken + ';'
        if self.requestToken is not None:
            cookies += self.requestToken
        return cookies

    def _getHeaders(self, headerMap=None):
        header = self.headers.copy()
        if headerMap is not None:
            header.update(headerMap)
        cookies = self._getCookies()
        if cookies is not None:
            header['Cookie'] = cookies
        if self.requestToken is not None:
            header['Request-Token'] = self.requestToken.split('=')[1]
        return header

    def _checkResponseStatus(self, path, response):
        if response.status_code not in self.httpCode:
            return path + response.text

    def updateRequestToken(self, headers):
        if not headers.__contains__('Set-Cookie'):
            return
        for string in headers['Set-Cookie'].split(';'):
            if string.__contains__('__Secure-Request-Token'):
                self.requestToken = string.strip()

    def _login(self):
        if self._host is None \
                or self.username is None \
                or self.pwd is None:
            raise NifiException('username or pwd is not set')

        url = '%s/access/token' % self._host
        payload = {'username': self.username,
                   'password': self.pwd}
        headers = self._getHeaders({'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})

        response = requests.post(url=url, data=payload, headers=headers, verify=False)
        self.updateRequestToken(response.headers)
        self._checkResponseStatus(response=response, path='[NIFI-Login()]')
        if response.status_code not in [200, 201]:
            raise NifiException("Log in Failed, Check your username&password")

        for string in response.headers['Set-Cookie'].split(';'):
            if string.__contains__('__Secure-Authorization-Bearer'):
                if string.__contains__('SameSite'):
                    for split in string.split(','):
                        if split.__contains__('__Secure-Authorization-Bearer'):
                            self.accessToken = split.strip()
                            break
                else:
                    self.accessToken = string.strip()
                    break
        return 'Login Success'

    def _getParameterDetail(self):
        url = '%s/parameter-contexts/%s?includeInheritedParameters=true' % (self._host, self.parameterContextId)
        headers = self._getHeaders()
        response = requests.get(url=url, headers=headers, verify=False)
        self.updateRequestToken(response.headers)
        self._checkResponseStatus(response=response, path='[NIFI-updateParameter()]')
        return json.loads(response.text)

    @staticmethod
    def _buildParameter(name, value):
        return {'parameter': {
            'name': name,
            'value': value,
            'description': '',
            'sensitive': False
        }}

    @staticmethod
    def _buildUpdateMap(oldParamMap):
        return {
            'revision': oldParamMap['revision'],
            'id': oldParamMap['id'],
            'uri': oldParamMap['uri'],
            'permissions': oldParamMap['permissions'],
            'component': {
                'parameters': [],
                'id': oldParamMap['id'],
                'name': oldParamMap['component']['name']
            }
        }

    def updateParameter(self, newParamMap):
        parameterDetail = self._getParameterDetail()
        updateMap = self._buildUpdateMap(parameterDetail)
        for param in newParamMap:
            updateMap['component']['parameters'].append(self._buildParameter(param.name, param.value))
        url = '%s/parameter-contexts/%s/update-requests' % (self._host, self.parameterContextId)
        headers = self._getHeaders({'Content-Type': 'application/json'})
        response = requests.post(url=url, data=json.dumps(updateMap), headers=headers, verify=False)
        self.updateRequestToken(response.headers)
        if response.status_code not in self.httpCode:
            raise NifiException("Update Failed: " + response.text)
        return "Update Success!"


class Param:
    def __init__(self, name, value):
        self.name = name
        self.value = value


def getAllEnvInfo():
    return nifiEnvs


nifiEnvs = loadNifiConf()

if __name__ == '__main__':
    loadNifiConf()
    # nifi = Nifi(host='https://127.0.0.1:8443', username='69b60a39-e69d-4f6b-a169-d4053fdbc594',
    #             pwd='0b5nb''/tOVp5f7lBxpQqQUtBFAsCZXqyT', parameterContextId='e4df7022-0189-1000-1f3f-cf433850aaae')
    # print(nifi.login())
    # params = [Param(name='zzz', value='xxx'), Param(name='111', value='xxx')]
    # print(nifi.updateParameter(params))
