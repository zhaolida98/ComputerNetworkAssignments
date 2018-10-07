import os, asyncio, mimetypes, urllib.parse, traceback
from parse_header import HTTPHeader


async def dispatch(reader, writer):
    header = HTTPHeader()
    while True:
        data = await reader.readline()
        if data ==b'':
            break
        message = data.decode()
        header.parse_header(message)
        if data == b'\r\n':
            break
    method = header.get('method')
    print("method:", method)
    if (method != 'GET') and (method != 'HEAD'):
        writer.writelines([
            b'HTTP/1.1 405 OK\r\n',
            b'Content-Type:text/html; charset=utf-8\r\n',
            b'Connection: close\r\n',
            b'\r\n',
            b'<html><body>405 Method Not Allowed.<body></html>\r\n',
            b'\r\n'
        ])
    try:
        headerPath = urllib.parse.unquote(header.get('path'))
        print("header.get('path'):", headerPath)
        # 不带有附属，这是主页
        if header.get('path') == '':
            fullPath = os.path.abspath('.')
            sequence = writeSequence(fullPath, headerPath)
            writer.writelines(sequence)
        # 如果带有随后的子目录
        else:
            fullPath = './' + headerPath
            print("fullpath:", fullPath)
            # 如果是目录
            if os.path.isdir(fullPath):
                sequence = writeSequence(fullPath,headerPath)
                writer.writelines(sequence)
            # 如果是文件
            elif os.path.isfile(fullPath):
                size = str(os.path.getsize(fullPath))
                mime = mimetypes.guess_type(fullPath)[0]
                if mime is None:
                    mime = 'application/octet-stream'
                print("the mimetype is",mime)
                mime = mime.encode()
                range = header.get('range')
                if range is None:
                    print("range == none")
                    f = open(fullPath, 'rb').read()
                    writer.writelines([
                        b'HTTP/1.1 200 OK\r\n',
                        b'Content-Type:',
                        mime,
                        b'\r\ncharset=utf-8\r\n',
                        b'Connection: close\r\n',
                        b'Content-Length: ',
                        size.encode(),
                        b'\r\n',
                        b'\r\n',
                        f,
                        b'\r\n'
                    ])
                else:
                    print("range != none")
                    ranges = range.split('-')
                    range_begin = int(ranges[0])
                    hasNoEnd = (ranges[1] == '')
                    print("range[1] is:", ranges[1], hasNoEnd)
                    range_end = int(size if hasNoEnd else ranges[1])
                    print("range end is:",range_end)
                    print("range begin is:",range_begin)
                    length = range_end - range_begin
                    f = open(fullPath, 'rb')
                    f.seek(range_begin)
                    f = f.read() if hasNoEnd else f.read(range_end)
                    range = (str(range_begin)+'-'+str(range_end - 1)+'/'+str(size)).encode()
                    writer.writelines([
                        b'HTTP/1.1 206 Partial Content\r\n',
                        b'Content-Type:',
                        mime,
                        b'\r\ncharset=utf-8\r\n',
                        b'Connection: close\r\n',
                        # b'Transfer-Encoding: chunked\r\n',
                        b'Content-Length: ',
                        str(length).encode(),
                        b'\r\nContent-Range: bytes ',
                        range,
                        b'\r\n',
                        b'\r\n',
                        f,
                        b'\r\n'
                    ])
            # 不是目录不是文件就什么都不是
            else:
                writer.writelines([
                    b'HTTP/1.1 404 OK\r\n',
                    b'Content-Type:text/html; charset=utf-8\r\n',
                    b'Connection: close\r\n',
                    b'\r\n',
                    b'<html><body>404 Not Found<body></html>\r\n',
                    b'\r\n'
                ])
        await writer.drain()
        writer.close()
    except Exception as e:
        # traceback.print_exc()
        pass


def writeSequence(filename, subpath):
    sequencePre = [
        b'HTTP/1.1 200 OK\r\n',
        b'Content-Type:text/html; charset=utf-8\r\n',
        b'Connection: close\r\n',
        b'\r\n',
        b'<html><head><title>Index of .//</title></head> '
        b'<body bgcolor="white"> <h1>Index of .//</h1><hr> '
        b'<pre> '
        b'<a href="../">../</a><br>']
    sequenceSuffix = [b'</pre>'
                      b'<hr>'
                      b'</body></html> \r\n',
                      b'\r\n']
    currentList = os.listdir(filename)
    for i in currentList:
        if subpath != '':
            i = '<a href="/' + os.path.join(subpath +'/'+ i) + '">' + i + '</a><br>'
        else:
            i = '<a href="/' + i + '">' + i + '</a><br>'
        sequencePre.append(i.encode())
    for j in sequenceSuffix:
        sequencePre.append(j)
    return sequencePre


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(dispatch, '127.0.0.1', 8080, loop=loop)
    server = loop.run_until_complete(coro)

    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
