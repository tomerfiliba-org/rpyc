import rpyc
from rpyc.utils.registry import UDPRegistryClient
from rpyc.utils.factory import connect_by_service

client = UDPRegistryClient('localhost')
client.register(('TEST',), 18820)


connect_by_service('TEST')

