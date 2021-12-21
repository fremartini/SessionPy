import socket
import os
from util import deserialize, load_router_config


def main():
    yaml = load_router_config()
    host = yaml['host']
    port = yaml['port']
    serve(host, port)


def serve(host, port):
    try:
        addr = (host, port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(addr)
            s.listen()
            print(f"listening on {addr}")
            while True:
                conn, a = s.accept()
                with conn:
                    print(deserialize(conn.recv(1024)))
    except KeyboardInterrupt:
        os._exit(0)


if __name__ == '__main__':
    main()
