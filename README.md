InsightScan
===========

A single file multithread portscanner in python

Usage: InsightScan.py <hosts[/24|/CIDR]> [start port] [end port] -t threads

Example: InsightScan.py 192.168.0.0/24 1 1024 -t 20

Options:
-h, --help show this help message and exit

-t NUM, --threads=NUM
Maximum threads, default 50
-p PORTS, --portlist port,port1,port2

Customize port list, separate with ‘,’ example:
21,22,23,25 …

-N, --noping Skip ping sweep, port scan whether targets are alive or not

-P, –-pingonly Ping scan only,disable port scan

-d, –-downpage Download and save HTML pages from HTTP
ports(80,81,8080), also detects some web apps

-l, –-genlist Output a list, ordered by port number,for THC-Hydra IP
list

-L, –-genfile Put the IP list in separate files named by port number. Implies -l option. Example: IPs with port 445
opened will be put into 445.txt
