#!/usr/bin/python3

import subprocess
import tempfile
import shutil
import os
import time
import tarfile
import xmlrpc.client as xmlrpc
import netifaces
import ssl
import n4d.server.core as n4dcore
import n4d.responses
from n4d.utils import get_backup_name

class Hostname:
	
	# Some Hostname Values
	HOSTNAME_FILE = "/etc/hostname"
	HOSTS_FILE = "/etc/hosts"
	HOSTNAME_BINARY = "/bin/hostname"
	HOSTNAME_CLIENT_ORPHAN = "client-sense-ip"
	XMLRPC_SERVER = "server"
	
	def __init__(self):
		
		self.core=n4dcore.Core.get_core()
		self.backup_files=["/etc/hostname", "/etc/hosts"]
	
	#def init
	
	def startup(self,options):
		'''
		This function set the hostname at startup, only works on 
		classroom model.
			* Desktop -> /etc/hostname -> n4d
			* Client -> /etc/hostname <- n4d
			* Server -> Nothing 
		'''
		# If is a boot time then make the things
		if options["boot"]:

			# get the name at n4d-vars
			list_variables={}

			# get the current name
			tmp=self.get_hostname_file()
			if tmp["status"]==0:
				current_name=tmp["return"]
			else:
				current_name="Unknown"
			
			list_variables["HOSTNAME"]=current_name
			
			# Get the version to make the correct actions 
			# Client actions
			#Old n4d: llxver=objects['LliurexVersion'].lliurex_version()[1].split(", ")
			llxver=self.core.get_plugin('LliurexVersion').lliurex_version().get('return',None).split(", ")

			if "client" in llxver or "client-lite" in llxver:
				#Old n4d: list_variables['HOSTNAME'] = objects['VariablesManager'].get_variable('HOSTNAME')
				list_variables['HOSTNAME'] = self.core.get_variable('HOSTNAME').get('return',None)
				if list_variables["HOSTNAME"] != type(str):
					list_variables["HOSTNAME"]=None
				if list_variables['HOSTNAME'] == None:
					#Old n4d: objects['VariablesManager'].init_variable('HOSTNAME',{'hostname':'client-sense-registrar'})
					list_variables["HOSTNAME"]=current_name
				
				dns_name=None
				status=False
				
				# Connect to server to get the name
				try:
					# GET THE MAC ON THE SERVER 
					# get the internal ethernet card on servers
					addrs=netifaces.ifaddresses('eth0')
					mac=addrs[netifaces.AF_LINK][0]['addr']
					context=ssl._create_unverified_context()
					server = xmlrpc.ServerProxy("https://"+Hostname.XMLRPC_SERVER+":9779",context=context)

					# Connect with server and make stuff
					try:
						#status,dns_name = server.has_name("","Dnsmasq",mac)
						ret=server.has_name("","DnsmasqManager",mac)
						if ret["status"]==0:
							status=True
							dns_name=ret["return"]

					except Exception as e:
						# If Server ===||===> n4d
						# default >> n4d
						# default >> /etc/hostname
						self.set_hostname_n4d(current_name)
						#Old n4d: return {'status':True, 'msg':'[Hostanme] Server is unreachable and client is not registered'}
						return n4d.responses.build_successful_call_response('','[Hostname] Server is unreachable and client is not registered')

					# If server is connected but not name for this machine 
					if not status:
						# If Server ======> n4d (Not Registered)
						# default >> n4d
						# default >> /etc/hostname
						self.set_hostname_n4d(list_variables["HOSTNAME"])
						#Old n4d:return {'status':True, 'msg':'[Hostanme] Client is not registered'}
						return n4d.responses.build_successful_call_response('','[Hostname] Client is not registered')
						
					if current_name == dns_name:
						# All is done and correct
						# N4D == /etc/hostname == DNSMASQ
						#Old n4d: return {'status':True, 'msg':'[Hostanme] All is in place'}
						return n4d.responses.build_successful_call_response('','[Hostname] All is in place')
						
					elif current_name != dns_name:
						# If server != /etc/hostname 
						# server >> /etc/hostname
						# server >> n4d
						self.set_hostname_n4d(dns_name)
						self.set_hostname_file(dns_name)
						#Old n4d: return {'status':True, 'msg':'[Hostanme] hostname is setted : server != /etc/hostname'}
						return n4d.responses.build_successful_call_response( '','[Hostname] hostname is setted : server != /etc/hostname')
						
						
					
					elif current_name != list_variables['HOSTNAME']:
						# If n4d != /etc/hostname
						# n4d >>  /etc/hostname
						self.set_hostname_file(current_name)
						#Old n4d:return {'status':True, 'msg':'[Hostanme] hostname is setted: n4d != /etc/hostname '}
						return n4d.responses.build_successful_call_response('','[Hostname] hostname is setted: n4d != /etc/hostname ')

				except Exception as e:
					print(e)
					#Old n4d: return {'status':False, 'msg':'[Hostanme] ERROR:'+str(e)}
					return n4d.responses.build_failed_call_response('','[Hostname] ERROR:'+str(e))

				
			# end if "client"
			
			elif "server" in llxver or "server-lite" in llxver:
				# If /etc/hostname ==||==> n4d is null
				# then /etc/hostname -> n4d
				#Old n4d: list_variables['HOSTNAME'] = objects['VariablesManager'].get_variable('HOSTNAME')
				list_variables['HOSTNAME'] = self.core.get_variable('HOSTNAME').get('return',None)

				if list_variables['HOSTNAME'] == None:
					self.set_hostname_n4d(current_name)
				
			# end if "server"
			elif "desktop" in llxver or "desktop-lite" in llxver:
				# If /etc/hostname -> n4d 
				if current_name != list_variables['HOSTNAME']:
					self.set_hostname_n4d(current_name)
			# end if desktop
			else:
				
				if (list_variables['HOSTNAME'] == None):
					#Old n4d:status,list_variables['HOSTNAME'] = objects['VariablesManager'].init_variable('HOSTNAME',{'HOSTNAME':'client-sense-registrar'})
					ret=self.core.set_variable("HOSTNAME",'client-sense-registrar')
					list_variables=ret.get('return',None)
					if ret.get('status',None)==0:
						status=True
					else:
						status=False
					
	#def startup

	def info(self):
		'''
		Show basic info about this plugin
		'''	
		#Old n4d: return {'status':True, 'msg':'[Hostanme] Manage machine hostname'}
		return n4d.responses.build_successful_call_response('','[Hostname] Manage machine hostname')

		
	#def apt
	
	# service test and backup functions #
	
	def test(self):

		pass
		
	#def test
	
	
	def set_hostname_n4d(self,hostname):
		'''
		Set the hostname value on the vars everywhere
		'''
		try:
			# Put the variables on the dictionary
			#Old n4d:
			#objects['VariablesManager'].init_variable('HOSTNAME',{'hostname':hostname})
			#return {'status': True, 'msg':'[Hostname] is setted at n4d to '+hostname+' n4d-vars '}
			self.core.set_variable("HOSTNAME",hostname)
			return n4d.responses.build_successful_call_response('','[Hostname] is setted at n4d to '+hostname+' n4d-vars ')
			
		except Exception as e:
			print(str(e))
			#Old n4d: return {'status': False, 'msg':'[Hostname] is not setted at n4d to '+hostname+' '}
			return n4d.responses.build_failed_call_response('','[Hostname] is not setted at n4d to '+hostname+' ')
		
	#def set_hostname_n4d(self,hostname)
	
	def set_hostname_file(self,hostname):
		'''
		Set the hostname for a machine
		'''
		
		try:
			# First set at file
			f=open(Hostname.HOSTNAME_FILE,"w")
			f.write(hostname+"\n")
			f.close()
			#subprocess.check_output(["hostname","-F",Hostname.HOSTNAME_FILE])
			#subprocess.check_output(["systemctl","restart","hostname.service"])
			#Old n4d: return {'status': True, 'msg':'[Hostname] is setted by n4d to '+hostname+'  at '+ Hostname.HOSTNAME_FILE}
			return n4d.responses.build_successful_call_response('','[Hostname] is setted by n4d to '+hostname+'  at '+ Hostname.HOSTNAME_FILE)

		except Exception as e:
			#Old n4d:return {'status': False, 'msg':'[Hostname] Hostname not setted :'+ str(e)}
			return n4d.responses.build_failed_call_response('','[Hostname] Hostname not setted :'+ str(e))

	#def set_hostname_file
	
	def set_hosts_file(self, hostname):
		try:
			f = open(Hostname.HOSTS_FILE,'r')
			lines = f.readlines()
			f.close()
			f = open(Hostname.HOSTS_FILE,'w')
			for x in lines:
				aux = x.strip(" ")
				if aux.startswith('127.0.1.1'):
					f.write("127.0.1.1\t"+hostname+"\n")
				else:
					f.write(x)
			f.close()
			#return {'status': True, 'msg':hostname + ' is updated on /etc/hosts'}	
			return n4d.responses.build_successful_call_response('',hostname + ' is updated on /etc/hosts')	

		except Exception as e:
			#Old n4d: return {'status': False, 'msg':str(e)}
			return n4d.responses.build_failed_call_response('',str(e))

	#def set_hosts_file
	
	
	def get_hostname_n4d(self):
		
		'''
		Get the hostname value at n4d values
		'''
		try: 
			list_variables={}
			#Old n4d:
			#list_variables['HOSTNAME'] = objects['VariablesManager'].get_variable('HOSTNAME')
			#return {'status': True,'HOSTNAME':list_variables['HOSTNAME']}
			list_variables['HOSTNAME']=self.core.get_variable('HOSTNAME').get('return',None)
			return n4d.responses.build_successful_call_response(list_variables['HOSTNAME'])
		
		except Exception as e:
			
			#Old n4d: return {'status': False, 'msg':'[Hostname] Hostname not set at n4d : '+ str(e)}
			return n4d.responses.build_failed_call_response('','[Hostname] Hostname not set at n4d : '+ str(e))

	#def get_n4d_hostname(self):

	def get_hostname_file(self):
		'''
		Get the current hostname at file /etc/hostname
		'''
		try:
			# Get Hostname from 
			f=open(Hostname.HOSTNAME_FILE,"r")
			hostname=f.read()
			f.close()
			#Old n4d: return {'status': True, 'HOSTNAME':hostname.rstrip()}
			return n4d.responses.build_successful_call_response(hostname.rstrip())


	
		except Exception as e:
		
			#Old n4d:return {'status': False, 'msg':'[Hostname] Hostname not getted '+ str(e)}
			return n4d.responses.build_failed_call_response('','[Hostanme] Hostname not getted :'+ str(e) )
	
	#def get_hostname_file(self):
	
	def makedir(self,dir_path=None):
		
		if not os.path.isdir(dir_path):
			os.makedirs(dir_path)
		
		return [True]
		
	# def created	
	
	
	def backup(self,dir_path="/backup"):
		
		
		try:
		
			self.makedir(dir_path)
			
			#get_backup_name es una funcion que esta definida en n4d
			file_path=dir_path+"/"+get_backup_name("Hostname")
			
				
			tar=tarfile.open(file_path,"w:gz")
			
			for f in self.backup_files:
				if os.path.exists(f):
					tar.add(f)
					
			#for
			
			tar.close()
			
			#Old n4d: return [True,file_path]
			return n4d.responses.build_successful_call_response(file_path)
			
			
		except Exception as e:
				print("Backup failed", str(e))
				#Old n4d: return [False,str(e)]
				return n4d.responses.build_failed_call_response('',str(e))

	#def backup
	
	
	def restore(self,file_path=None):
		
				
		
		#Ordeno de manera alfabetica el directorio y busco el fichero que tiene mi cadena
		if file_path==None:
			dir_path="/backup"
			for f in sorted(os.listdir(dir_path),reverse=True):
			
				if "Hostname" in f:
					file_path=dir_path+"/"+f
					break
			
		#Descomprimo el fichero y solo las cadenas que espero encontrar son las que restauro, reiniciando el servicio
		
		
		try:
			if os.path.exists(file_path):
				
				tmp_dir=tempfile.mkdtemp()
				tar=tarfile.open(file_path)
				tar.extractall(tmp_dir)
				tar.close
				
				for f in self.backup_files:
						tmp_path=tmp_dir+f
						if os.path.exists(tmp_path):
							shutil.copy(tmp_path,f)
							
				
				
			
			#print("File is restored in %s" % self.backup_files)
			#Old n4d: return [True,""]
			return n4d.responses.build_successful_call_response()

		
		except Exception as e:
			
			print ("Restored failed", str(e))
			#return [False,str(e)]
			return n4d.responses.build_failed_call_response('',str(e))

		
		pass
		
	#def restore

#Hostname
