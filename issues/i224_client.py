import rpyc
from rpyc.utils.registry import TCPRegistryClient


client = TCPRegistryClient('localhost')

client.register(('TEST',), 18812)
client.unregister(18812)

