#!/usr/bin/env python3

import subprocess
import sys
import threading
from time import sleep

from dnslib import QTYPE, RR, RCODE, dns
from dnslib.server import DNSServer, DNSRecord, BaseResolver

from slimDNS import SlimDNSServer

class SlimDNSResolver:
    def __init__(self,server):
        self._server = server
    def resolve(self,hostname):
        ip_bytes = self._server.resolve_mdns_address(hostname)
        if not ip_bytes:
            return None
        address = ".".join(str(i) for i in ip_bytes) 
        return address # XXX.XXX.XXX.XXX
        
class AvahiResolver:
    def resolve(self,hostname,timeout=1):
        try:
            result = subprocess.check_output(["avahi-resolve", "--name", "-4", hostname], timeout=timeout)
            [_, address] = result.decode("UTF-8").strip("\n").split("\t")
            return address # XXX.XXX.XXX.XXX
        except subprocess.TimeoutExpired:
            return None
        except BaseException:
            raise

class MulticastDNSProxyResolver(BaseResolver):
    def __init__(self,mdns_resolver=None,dns_address='8.8.8.8',dns_port=53,timeout=1):
        self._mdns_resolver = mdns_resolver
        self.address = dns_address
        self.port = dns_port
        self.timeout = timeout

    def resolve(self,request,handler):
        if request.q.qtype != QTYPE.A: # Only IPv4 is supported
            reply = request.reply()
            reply.header.rcode = getattr(RCODE,'NXDOMAIN')
            return reply       
        hostname = str(request.q.qname)
        if hostname.endswith(".local."):
            reply = request.reply()
            address = address = self._mdns_resolver.resolve(hostname)
            if address:
                rr = RR(
                    rname=request.q.qname,
                    rtype=request.q.qtype,
                    rdata=dns.A(address),
                    ttl=300
                )
                reply.add_answer(rr)
            else:
                reply.header.rcode = getattr(RCODE,'NXDOMAIN')
            return reply 
        else:
            try:
                if handler.protocol == 'udp':
                    proxy_r = request.send(self.address,self.port,timeout=self.timeout)
                else:
                    proxy_r = request.send(self.address,self.port,tcp=True,timeout=self.timeout)
                reply = DNSRecord.parse(proxy_r)
            except socket.timeout:
                reply = request.reply()
                reply.header.rcode = getattr(RCODE,'NXDOMAIN')
            return reply              
        
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: {} hostname address'.format(sys.argv[0]))
        sys.exit(1)

    if len(sys.argv) >= 3:
        hostname = sys.argv[1]
        address = sys.argv[2]

    dns_address = '208.67.222.222'
    dns_port = 5353
    
    print("Hostname: {}".format(hostname))
    print("Address: {}".format(address))
    print("DNS Address: {}".format(dns_address))
    print("DNS port: {}".format(dns_port))
    
    avahi_coex = False # TODO enable/disable coexist with avahi-daemon
    
    if avahi_coex:
        print("Using AvahiResolver")
        mdns_resolver = AvahiResolver()
    else:
        print("Using SlimDNSResolver")
        mdns_server = SlimDNSServer(address, hostname)
        mdns_resolver = SlimDNSResolver(mdns_server)
        print("Publishing hostname on multicast DNS")
        mdns_server_thread = threading.Thread(target=mdns_server.run_forever) # TODO Stop thread properly
        mdns_server_thread.start()

    resolver = MulticastDNSProxyResolver(mdns_resolver, dns_address, dns_port)
    
    servers = [
        DNSServer(resolver=resolver, port=53, address='127.0.0.1', tcp=False)
        #DNSServer(resolver=resolver, port=53, address=address, tcp=False) # TODO enable/disable listen on address
    ]
    
    for s in servers:
        s.start_thread()
  
    try:
        while True:
            sleep(10)
            sys.stderr.flush()
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        for s in servers:
            s.stop()
