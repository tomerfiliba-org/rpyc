import rpyc
from rpyc.utils.registry import UDPRegistryClient


client = UDPRegistryClient('localhost')
client.register(('TEST',), 18812)
client.register(('TEST',), 18813)
client.register(('TEST',), 18814)
client.register(('TEST',), 18815)


