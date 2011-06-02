#server: please, pay attention at line 'print type(product)' inside 
#Order in method add_product 
#we will see Order and not Product class 
#------------------------------------- 
from itertools import count 
from datetime import datetime 
from notify.all import * 
import rpyc 

class Supplier(object): 
    def __init__(self, name): 
        self.name = name 

    def __repr__(self): 
        return 'Supplier: %s' % self.name 

class Product(object): 
    reserveds = Signal() #when a product is set reserved, we throw this signal 
    exposed_reserveds = reserveds 

    def __init__(self, name, supplier, id): 
        self.name = name 
        self.supplier = supplier 
        self.id = id 
        self.reserved = 'N' 

    def set_reserved (self): 
        self.reserved = 'Y' 
        Product.reserveds(self)  #notify the observers 

    def __repr__(self): 
        return '<Product: %s, %s, Id: %s>' % (self.name, self.supplier, self.id) 

class Store(object): 
    def __init__(self, name): 
        self.name = name 
        self._products = [] 

    def input (self, product): 
        self._products.append(product) 

    def output (self, product_name, supplier): 
        for i, p in enumerate(self._products): 
            if p.name == product_name and p.supplier == supplier: 
                ret = self._products.pop(i) 
                ret.set_reserved() 
                return ret 
        raise Exception('There is no: %s, %s' % (product_name, supplier)) 

    exposed_output = output 

    def __repr__(self): 
        ret = 'Store: %s\n' % self.name 
        for p in self._products: 
            ret += '%s\n' % p 
        return ret 

class Client(object): 
    def __init__(self, name): 
        self.name = name 

    def __repr__(self): 
        return 'Client: %s' % self.name 

class Order(object): 
    new_id = count() 

    def __init__(self, client): 
        self.id = Order.new_id.next() 
        self.client = client 
        self.products = [] 
        self.datetime = datetime.now() 

    def add_product(self, product): 
        print type(product)        #  <--------- look at the output: it is not Product but Order class
        print "!!", product 
        self.products.append(product) 

    exposed_add_product = add_product 

    def __repr__(self): 
        ret = ['<Order: %d, %s, Date: %s>' % (self.id, self.client, 
                         self.datetime.strftime('%d-%m-%Y %H:%M'))] 
        for p in self.products: 
            ret.append('\t%s' % p) 
        return '\n'.join(ret) 

#creating some objects 

estrella_levante = Supplier('Estrella Levante') 
store = Store('Trastienda') 
client = Client('Miguel Angel') 

for i in range(5): 
    store.input(Product('quinto', estrella_levante, '#%d' % i)) 
    store.input(Product('tercio', estrella_levante, '#%d' % i)) 

class MyService(rpyc.Service): 
    exposed_store = store 
    exposed_Order = Order 
    exposed_estrella_levante = estrella_levante 
    exposed_client = client 
    exposed_Product = Product 

    def __init__(self, *args): 
        rpyc.Service.__init__(self, *args) 
        self.signal_handler = []        #when registering signal of py-notify with the handler 

    def on_disconnect(self): 
        for s, h in self.signal_handler: 
            s.disconnect(h) 

    # we register py-notify signal with the handler this way, so when 
    # closing we disconnect every connection 
    def exposed_connect(self, signal, handler): 
        handler =  rpyc.async(handler) 
        self.signal_handler.append((signal, handler)) 
        signal.connect(handler) 

    def exposed_disconnect(self, signal, handler): 
        handler =  rpyc.async(handler) # py-notify disconnects passing 
                                       # as argument the handler object, as we connected 
        try: 
            self.signal_handler.remove((signal, handler)) 
            signal.disconnect(handler) 
        except: 
            pass 

if __name__ == "__main__": 
    from rpyc.utils.server import ThreadedServer 
    t = ThreadedServer(MyService, port = 18861) 
    t.start()

