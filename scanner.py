#coding:utf-8
#!/usr/bin/env python

'''
 ______                              __      __      
/\__  _\                  __        /\ \    /\ \__   
\/_/\ \/     ___     ____/\_\     __\ \ \___\ \ ,_\  
   \ \ \   /' _ `\  /',__\/\ \  /'_ `\ \  _ `\ \ \/  
    \_\ \__/\ \/\ \/\__, `\ \ \/\ \L\ \ \ \ \ \ \ \_ 
    /\_____\ \_\ \_\/\____/\ \_\ \____ \ \_\ \_\ \__\
    \/_____/\/_/\/_/\/___/  \/_/\/___L\ \/_/\/_/\/__/
                                  /\____/            
                                  \_/__/             
 __                __                
/\ \              /\ \               
\ \ \         __  \ \ \____    ____  
 \ \ \  __  /'__`\ \ \ '__`\  /',__\ 
  \ \ \L\ \/\ \L\.\_\ \ \L\ \/\__, `\
   \ \____/\ \__/.\_\\ \_,__/\/\____/
    \/___/  \/__/\/_/ \/___/  \/___/ 
                                     
'''

 
import platform
import sys
import socket as sk
import httplib
from subprocess import Popen, PIPE
import re
from optparse import OptionParser
import threading
from threading import Thread
from Queue import Queue

NUM = 50
PORTS=[21,22,23,25,80,81,110,135,139,389,443,445,873,1433,1434,1521,2433,3306,3307,3389,5800,5900,8080,22222,22022,27017,28017]
URLS=['','phpinfo.php','phpmyadmin/','xmapp/','zabbix/','jmx-console/','.svn/entries','nagios/','index.action','login.action']
# convert an IP address from its dotted-quad format to its
# 32 binary digit representation
def ip2bin(ip):
  b = ""
	inQuads = ip.split(".")
	outQuads = 4
	for q in inQuads:
		if q != "":
			b += dec2bin(int(q),8)
			outQuads -= 1
	while outQuads > 0:
		b += "00000000"
		outQuads -= 1
	return b

# convert a decimal number to binary representation
# if d is specified, left-pad the binary number with 0s to that length
def dec2bin(n,d=None):
	s = ""
	while n>0:
		if n&1:
			s = "1"+s
		else:
			s = "0"+s
		n >>= 1
	if d is not None:
		while len(s)<d:
			s = "0"+s
	if s == "": s = "0"
	return s

# convert a binary string into an IP address
def bin2ip(b):
	ip = ""
	for i in range(0,len(b),8):
		ip += str(int(b[i:i+8],2))+"."
	return ip[:-1]

# print a list of IP addresses based on the CIDR block specified
def listCIDR(c):
	cidrlist=[]
	parts = c.split("/")
	baseIP = ip2bin(parts[0])
	subnet = int(parts[1])
	# Python string-slicing weirdness:
	# "myString"[:-1] -> "myStrin" but "myString"[:0] -> ""
	# if a subnet of 32 was specified simply print the single IP
	if subnet == 32:
		print bin2ip(baseIP)
	# for any other size subnet, print a list of IP addresses by concatenating
	# the prefix with each of the suffixes in the subnet
	else:
		ipPrefix = baseIP[:-(32-subnet)]
		for i in range(2**(32-subnet)):
			cidrlist.append(bin2ip(ipPrefix+dec2bin(i, (32-subnet))))
		return cidrlist	

# input validation routine for the CIDR block specified
def validateCIDRBlock(b):
	# appropriate format for CIDR block ($prefix/$subnet)
	p = re.compile("^([0-9]{1,3}\.){0,3}[0-9]{1,3}(/[0-9]{1,2}){1}$")
	if not p.match(b):
		print "Error: Invalid CIDR format!"
		return False
	# extract prefix and subnet size
	prefix, subnet = b.split("/")
	# each quad has an appropriate value (1-255)
	quads = prefix.split(".")
	for q in quads:
		if (int(q) < 0) or (int(q) > 255):
			print "Error: quad "+str(q)+" wrong size."
			return False
	# subnet is an appropriate value (1-32)
	if (int(subnet) < 1) or (int(subnet) > 32):
		print "Error: subnet "+str(subnet)+" wrong size."
		return False
	# passed all checks -> return True
	return True
	
def pinger():
	global pinglist
	while True:
		ip=q.get()
		if platform.system()=='Linux':
			p=Popen(['ping','-c 2',ip],stdout=PIPE)
			m = re.search('(.*)\srecieved', p.stdout.read())
			if m!=0:
				pinglist.append(ip)
		if platform.system()=='Windows':
			p=Popen('ping -n 2 ' + ip, stdout=PIPE)
			m = re.search('TTL', p.stdout.read())
			if m:
				pinglist.append(ip)
		q.task_done()

def scanipport():
	global lock
	while True:
		host,port=sq.get()
		sd=sk.socket(sk.AF_INET, sk.SOCK_STREAM)
		try:
			sd.connect((host,port))
			if options.genlist==True:
				if port not in ipdict:
					ipdict[port]=[]
					ipdict[port].append(host)
				else:
					ipdict[port].append(host)
			else:
				lock.acquire()
				print "%s:%d OPEN" % (host, port)
				lock.release()
			sd.close()
			if options.downpage==True and port in [80,81,1080,8080]:				
				dlpage(ip,port)
		except:
			pass
		sq.task_done()		

def dlpage(ip,port):
	global page,lock
	page+='<h1>'+ip+':'+str(port)+'</h1><br>'
	for url in URLS:
		c=httplib.HTTPConnection(ip+':'+str(port))
		c.request('GET','/'+url)
		r=c.getresponse()
		#print url,r.status
		if r.status in [200,301,302]:
			if url=='':
				url='Homepage'
			lock.acquire()
			print ip+':'+str(port),url,'exists'
			page+='<h2>'+url+'</h2><br>'+r.read()
			lock.release()
		c.close()

	
	
		
if __name__ == "__main__":
	usage="usage: InsightScan.py <hosts[/24|/CIDR]> [start port] [end port] -t threads\n\nExample: InsightScan.py 192.168.0.0/24 1 1024 -t 20"
	parser = OptionParser(usage=usage)
	parser.add_option("-t", "--threads", dest="NUM",help="Maximum threads, default 50")
	parser.add_option("-p", "--portlist", dest="PORTS",help="Customize port list, separate with ',' example: 21,22,23,25 ...")
	parser.add_option("-N", '--noping', action="store_true", dest="noping",help="Skip ping sweep, port scan whether targets are alive or not")
	parser.add_option("-P", '--pingonly', action="store_true", dest="noscan",help="Ping scan only,disable port scan")
	parser.add_option("-d", '--downpage', action="store_true", dest="downpage",help="Download and save HTML pages from HTTP ports(80,81,8080), also detects some web apps")
	parser.add_option("-l", '--genlist', action="store_true", dest="genlist",help="Output a list, ordered by port number,for THC-Hydra IP list")
	parser.add_option("-L", '--genfile', action="store_true", dest="genfile",help="Put the IP list in separate files named by port number. Implies -l option.\nExample: IPs with port 445 opened will be put into 445.txt")
	(options, args) = parser.parse_args()
	if options.NUM !=None and options.NUM!=0:
		NUM=int(options.NUM)
		print 'Scanning with',NUM,'threads...'
	if len(args)<1:
		parser.print_help()
		sys.exit()
	if options.noping== True and options.noscan == True:
		print 'ERROR: Cannot use -N and -P together'
		sys.exit()
	iplist=[]	
	ipaddr=args[0]
	if len(args)==2:
		print 'Must specify end port'
		sys.exit()
	try:
		sk.inet_aton(ipaddr)
		iplist.append(ipaddr)
	except:		
		if not validateCIDRBlock(ipaddr):
			print 'IP address not valid!'
			sys.exit()
		else:
			iplist=listCIDR(ipaddr)
	if len(args)==3:
		startport=int(args[1])
		endport=int(args[2])
		if startport>endport:
			print 'start port must be smaller or equal to end port'
			sys.exit()
		PORTS=[]
		for i in xrange(startport,endport+1):
			PORTS.append(i)
	if options.PORTS!= None:
		PORTS=[int(pn) for pn in options.PORTS.split(',') ]
	global page		
	page=''
#start ping threads
	if options.noping != True:
		print "Scanning for live machines...\n"
		global pinglist
		q=Queue()
		pinglist=[]
		for i in range(NUM):
			t = Thread(target=pinger)
			t.setDaemon(True)
			t.start()	
		
		for ip in iplist:
			q.put(ip)
		q.join()
	else:
		pinglist=iplist
	#print pinglist
	if options.noscan == True:
		for host in pinglist:
			print host,
		sys.exit()
	if len(pinglist)==0:
		print 'No live machines detected. Try again with -N switch'
		sys.exit()
	print "Scanning ports...\n"
	sq=Queue()
	lock = threading.Lock()
	if options.genfile==True:
		options.genlist=True
	if options.genlist==True:
		global ipdict
		ipdict={}
	for i in range(NUM):
		st = Thread(target=scanipport)
		st.setDaemon(True)
		st.start()	
		
	for scanip in pinglist:
		for port in PORTS:			
			sq.put((scanip,port))
	sq.join()
	
	if options.genlist==True:
		for port,iplist in ipdict.items():
			if options.genfile==True:
				 file=open(str(port)+'.txt', "w")
			else:	 
				print "\n========Port",port,'========'
			for ip in iplist:
				if options.genfile==True:
					file.write(ip+"\n")
				else:	
					print ip
	
	if options.downpage==True and page!='':
		f = open('page.html', 'w')
		f.write(page)
		f.close()
		print 'page dumped to page.html'
		
