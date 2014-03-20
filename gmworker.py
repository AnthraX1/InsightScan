import gearman as gm
import base64
import zlib
import socket
import urllib,urllib2
import re
import sys
import chardet
import time
import json
from multiprocessing import Process, JoinableQueue as Queue,Lock,Manager


THREADS = 100
TIMEOUT=2
GMSERVER=['']
REPORTURL=''
KEY=''

mgr=Manager()
RESULT=mgr.dict()
ERROR=mgr.dict()
lock = Lock()
lockerr=Lock()
def processlist(data):
	res=''
	try:
		res=zlib.decompress(base64.b64decode(data))
	except:
		return False
	return res.split('|')

def getip(domain):
	ip=[]
	try:
		ip=socket.gethostbyname_ex(domain)[2]
	except:
		pass
	return ip

def worker_scan(worker,job):
	print 'Retrieving task...'
	dlist=processlist(job.data)
	if dlist==False:
		print 'No list'
		return 'Error'
	for item in dlist:
		if item=='' or item==None:
			continue
		q.put(item)
		#print 'put item'
	while q.qsize()>THREADS/2:
		time.sleep(0.5)
		#print 'Sleeping...'
	#q.join()
	return 'Done'

def autosend():
	while True:
		#print RESULT
		print 'wait...'
		if len(RESULT)>0:
			processresult()
		if len(ERROR)>0:
			processerr()	
		time.sleep(10)# send back scanned data every 10s

def processresult():
	if len(RESULT)==0:
		return False
	print 'data len:',len(RESULT)
	lock.acquire()
	res=dict(RESULT)
	RESULT.clear()
	lock.release()
	try:
		data=base64.b64encode(zlib.compress(json.dumps(res)))
	except Exception as e:
		print str(e)
		print res
		print 'SEND DATA ERROR'
		return False	
	stat=postback({"type":"data","data":data})
	print 'sent data'

def processerr():
	if len(ERROR)==0:
		return False
	print 'err len:',len(ERROR)
	lockerr.acquire()
	res=dict(ERROR)
	ERROR.clear()
	lockerr.release()
	try:
		data=base64.b64encode(zlib.compress(json.dumps(res)))
	except Exception as e:
		print str(e)
		print res
		print 'SEND ERRDATA ERROR'
		return False
	stat=postback({"type":"error","data":data})
	print 'sent err'

def scanner():
	while True:
		domain=q.get()
		url='http://'+domain
		httpheaders={"Content-type": "application/x-www-form-urlencoded","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8","User-Agent":"Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/20.0.11"}
		req=urllib2.Request(url,headers=httpheaders)
		try:
			r=urllib2.urlopen(req,None,TIMEOUT)
			content=r.read()
			headers=unicode(getheader(r), errors='ignore')
			title=gettitle(content)
			ip=getip(domain)
			data={}
			#data['domain']=domain
			data['ip']=json.dumps(ip)
			data['title']=title
			data['header']=headers
			lock.acquire()
			RESULT[domain]=data
			lock.release()
			#print RESULT
			#print content #debug only
		except Exception as e:
			lockerr.acquire()
			ERROR[domain]=unicode(str(e), errors='ignore')
			lockerr.release()
		q.task_done()



def getheader(handle):
	return json.dumps(dict(handle.info()))
	


def gettitle(content):
	#print content
	tt=re.search("<title.*?>(.*?)</title>",content,re.IGNORECASE|re.DOTALL)
	try:
		title=tt.group(1)
	except:
		return ''
	cc=re.search("<meta.*charset=\"?(.*?)\"",content,re.IGNORECASE)
	charset=None
	try:
		charset=cc.group(1).lower()
	except:
		pass
	#print charset
	if charset==None or charset=='':
		charset=chardet.detect(title).get('encoding','utf-8')
	if charset!='utf-8' or charset!='utf8':
		title=title.decode(charset,'ignore').encode('utf-8')
	return title.strip()
	
'''
def worker_print(worker, job):
	print job.data
	return 'asd'
'''

def postback(postdata):#postdata should be dict
	if len(postdata)==0 or postdata==None:
		return False
	postdata['key']=KEY
	#print postdata #debug
	postdata=urllib.urlencode(postdata)
	httpheaders={"Content-type": "application/x-www-form-urlencoded","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8","User-Agent":"Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/20.0.11"}
	req=urllib2.Request(REPORTURL,postdata,httpheaders)
	try:
		r=urllib2.urlopen(req)
		reply=r.read()
		print 'reply:',reply
#		if reply!='success':
			#print reply
		return True	
	except Exception as e:
		print e
		return False



if __name__ == "__main__":
	worker=gm.GearmanWorker(GMSERVER)
	q=Queue()
	for i in xrange(THREADS):
			t = Process(target=scanner)
			t.daemon=True
			t.start()	
	print 'Threads started'
	worker.register_task("scan1", worker_scan)
	print 'Worker started'
	ts = Process(target=autosend)
	ts.daemon=True
	ts.start()
	print 'Background thread started'
	worker.work()


