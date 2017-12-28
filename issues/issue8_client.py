import rpyc 

conn = rpyc.connect ("localhost", 18861) 

store = conn.root.store 
Order = conn.root.Order 
estrella_levante = conn.root.estrella_levante #beer supplier 
client = conn.root.client 
Product = conn.root.Product 

def show_reserved_products (product):  #callback 
    print 'You have reserved %s' %  product 

#Product.reserveds is the py-notify signal that is thrown when you 
# output a product from thee store 
conn.root.connect (Product.reserveds, show_reserved_products) 

p = store.output ('quinto', estrella_levante) #store.output gives me a Product object
print "@@", type(p), p
order = Order (client) 
order.add_product (p)      #  <---------- this is the interesting moment 
                           #  we pass as argument a Product object 

conn.close ()

