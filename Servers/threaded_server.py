from Rpyc.Utils.Serving import DEFAULT_PORT, threaded_server, start_discovery_agent_thread


def main(port = DEFAULT_PORT):
    start_discovery_agent_thread(rpyc_port = port)
    threaded_server(port = port)


if __name__ == "__main__":
    main()
