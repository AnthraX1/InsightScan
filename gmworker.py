import gearman as gm
import base64
import zlib
import socket
import urllib,urllib2
import re
import threading
import sys
import chardet
import time
import json
from threading import Thread
from Queue import Queue


THREADS = 20
TIMEOUT=5
GMSERVER=['']
REPORTURL=''
KEY=''
RESULT={}
lock = threading.Lock()

#For python2.4 Queue class...
if sys.version_info[1]==4:
	class Queue(Queue):
		def __init__(self, maxsize=0):
			self.maxsize = maxsize
			self._init(maxsize)
			self.mutex = threading.Lock()
			self.not_empty = threading.Condition(self.mutex)
			self.not_full = threading.Condition(self.mutex)
			self.all_tasks_done = threading.Condition(self.mutex)
			self.unfinished_tasks = 0

		def task_done(self):
			self.all_tasks_done.acquire()
			try:
				unfinished = self.unfinished_tasks - 1
				if unfinished <= 0:
					if unfinished < 0:
						raise ValueError('task_done() called too many times')
					self.all_tasks_done.notifyAll()
				self.unfinished_tasks = unfinished
			finally:
				self.all_tasks_done.release()

		def join(self):
			self.all_tasks_done.acquire()
			try:
				while self.unfinished_tasks:
					self.all_tasks_done.wait()
			finally:
				self.all_tasks_done.release()
		def put(self, item, block=True, timeout=None):
			self.not_full.acquire()
			try:
				if self.maxsize > 0:
					if not block:
						if self._qsize() == self.maxsize:
							raise Full
					elif timeout is None:
						while self._qsize() == self.maxsize:
							self.not_full.wait()
					elif timeout < 0:
						raise ValueError("'timeout' must be a positive number")
					else:
						endtime = _time() + timeout
						while self._qsize() == self.maxsize:
							remaining = endtime - _time()
							if remaining <= 0.0:
								raise Full
							self.not_full.wait(remaining)
				self._put(item)
				self.unfinished_tasks += 1
				self.not_empty.notify()
			finally:
				self.not_full.release()	




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

	dlist=processlist(job.data)
	if dlist==False:
		print 'No list'
		return 'Error'
	for i in xrange(THREADS):
			t = Thread(target=scanner)
			t.daemon=True
			t.start()	
	for item in dlist:
		if item=='' or item==None:
			continue
		q.put(item)
	q.join()
	return 'Done'

def autosend():
	while True:
		#print 'wait...'
		if len(RESULT)>0 and q.empty():
			lock.acquire()
			processresult()
			lock.release()
		time.sleep(30)# send back scanned data every 30s

def processresult():
	if len(RESULT)==0:
		return False
	data=base64.b64encode(zlib.compress(json.dumps(RESULT)))
	stat=postback({"type":"data","data":data})
	if stat!=False:
		RESULT.clear()


def scanner():
	while True:
		domain=q.get()
		if len(domain)<3:
			q.task_done()
			continue
		url='http://'+domain
		#print url
		httpheaders={"Content-type": "application/x-www-form-urlencoded","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8","User-Agent":"Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/20.0.11"}
		req=urllib2.Request(url,headers=httpheaders)
		try:
			ip=getip(domain)
			r=urllib2.urlopen(req,timeout=TIMEOUT)
			content=r.read()
			headers=getheader(r)
			title=gettitle(content)
			data={}
			#data['domain']=domain
			data['ip']=json.dumps(ip)
			data['title']=title
			data['header']=headers
			RESULT[domain]=data
			#print RESULT
			#print content #debug only
		except Exception as e:
			errdata=base64.b64encode(zlib.compress(json.dumps({"domain":domain,"exception":str(e)})))
			errmsg={"type":"error","data":errdata}
			#print errmsg
			postback(errmsg)
		if len(RESULT)>=THREADS:
			lock.acquire()
			processresult()
			lock.release()
		q.task_done()



def getheader(handle):
	return json.dumps(dict(handle.info()))
	


def gettitle(content):
	#print content
	tt=re.search("<.*>(.*?)</title>",content,re.IGNORECASE|re.DOTALL)
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
	if charset==None:
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
		#print reply
		if reply!='success':
			print reply
		return True	
	except Exception as e:
		print str(e)
		return False



if __name__ == "__main__":
	worker=gm.GearmanWorker(GMSERVER)
	q=Queue()
	worker.register_task("scan1", worker_scan)
	print 'Worker started'
	ts = Thread(target=autosend)
	ts.daemon=True
	ts.start()
	print 'Background thread started'
	worker.work()


