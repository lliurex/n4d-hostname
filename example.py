#!/usr/bin/python
import xmlrpclib

server_ip = "zen"

c = xmlrpclib.ServerProxy("https://"+server_ip+":9779")
user = ("aberlanas","lliurex")
print c.get_methods("Hostname")

# Get the n4d value of Hostname
print(c.get_hostname_n4d("","Hostname"))
# Get the file value of Hostname
print(c.get_hostname_file("","Hostname"))

# Set the n4d value of Hostname
#print(c.set_hostname_n4d(user,"Hostname",hostname_new))

# Set the file value of Hostname
#print(c.set_hostname_file(user,"Hostname",hostname_new))