InsightScan
===========

A single file multithread port scanner with service detection in python

Usage: InsightScan.py <hosts[/24|/CIDR]> [start port] [end port] -t threads

Example: InsightScan.py 192.168.0.0/24 1 1024 -t 20

Options:
  -h, --help            show this help message and exit
  
  -t NUM, --threads=NUM
                        Maximum threads, default 50
                        
  -T TIMEOUT, --timeout=TIMEOUT
                        Scan timeout, per thread
                        
  -n NETWORK, --network=NETWORK
                       Quick Network discovery, find reachable networks.
                       Local IP range only. 
                       A=10.0.0.0-10.255.255.255
                       B=172.16.0.0-172.31.255.255
                       C=192.168.0.0-192.168.255.255 
                       Example: -n B will try Class B addresses                       
                        
  -p PORTS, --portlist=PORTS
                        Customize port list, separate with ',' example:
                        21,22,23,25 ...
                        
  -N, --noping          Skip ping sweep, port scan whether targets are alive
                        or not
                        
  -P, --pingonly        Ping scan only,disable port scan
  
  -S, --service         Service detection, using banner and signature
  
  -d, --downpage        Detects interesting stuff on HTTP ports(80,80,8080),
                        when used with -S , will try all ports with HTTP
                        service. Grab and save to HTML pages if found
                        anything.
                        
  -l, --genlist         Output a list, ordered by port number(service, with -S
                        option),for THC-Hydra IP list
                        
  -L, --genfile         Put the IP list in separate files named by port
                        number(service, with -S option). Implies -l option.
                        Example: IPs with port 445 opened will be put into
                        445.txt
                        
                        
