
keys = ('method', 'path', 'range', 'lastDir')


class HTTPHeader:
    def __init__(self):
        self.headers = {key: None for key in keys}

    def parse_header(self, line):
        fileds = line.split(' ')
        if fileds[0] == 'GET' or fileds[0] == 'POST' or fileds[0] == 'HEAD':
            self.headers['method'] = fileds[0]
            self.headers['path'] = fileds[1].strip('/')
        if fileds[0] == 'Range:':
            print("yes there is a range")
            temp = fileds[1].split('=')
            self.headers['range'] = temp[1].strip('\r\n')
        if fileds[0] == 'Cookie:':
            cookie = line.strip('Cookie: lastDir=').strip('\r\n').strip('"')
            if cookie == '':
                pass
            else:
                print("find a cookie")
                self.headers['lastDir'] = cookie
                print("this cookie is",cookie)

    def get(self, key):
        return self.headers.get(key)
