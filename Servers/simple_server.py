from Rpyc.Utils.Serving import serve_socket, create_listener_socket, DEFAULT_PORT


def main(port = DEFAULT_PORT):
    sock = create_listener_socket(port)
    while True:
        newsock, name = sock.accept()
        serve_socket(newsock)

if __name__ == "__main__":
    main()

    