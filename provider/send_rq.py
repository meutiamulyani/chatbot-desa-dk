import requests

class ResponseHandler():
    url ="https://api.fonnte.com/send"
    def __init__(self):
        pass

    def sendMsg(self, to, message):
        payload = {
            'target': to,
            'message': message
        }

        files=[]
        headers = {
            'Authorization': '98azMYpnQpZjQJCbiU3A'
        }

        response = requests.request("POST", ResponseHandler.url, headers=headers, data=payload, files=files)
    
    def sendAttach(self, to, url, message):
        payload = {
            'target': to,
            'url': url,
            'message': message
        }

        files=[]
        headers = {
            'Authorization': '98azMYpnQpZjQJCbiU3A'
        }

        response = requests.request("POST", ResponseHandler.url, headers=headers, data=payload, files=files)        