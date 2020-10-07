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

class MulticastDNSProxyResolver(BaseResolver):
    def __init__(self,mdns_resolver=None,dns_address='8.8.8.8',dns_port=53,timeout=1):
        self._mdns_resolver = mdns_resolver
        self.address = dns_address
        self.port = dns_port
        self.timeout = timeout

    def resolve(self,request,handler):
        if request.q.qtype != QTYPE.A: # Only IPv4 is supported
            reply = request.reply()
            reply.header.rcode = RCODE.NOERROR
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
                reply.header.rcode = RCODE.NXDOMAIN
            return reply
        if handler.protocol == 'udp':
            proxy_r = request.send(self.address,self.port,timeout=self.timeout)
        else:
            proxy_r = request.send(self.address,self.port,tcp=True,timeout=self.timeout)
        reply = DNSRecord.parse(proxy_r)
        return reply

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        local_address = sys.argv[1]
        hostname = sys.argv[2]
    elif len(sys.argv) >= 2:
        local_address = sys.argv[1]
        hostname = None
    else:
        print('Usage: {} LOCAL_ADDRESS [HOSTNAME]'.format(sys.argv[0]))
        sys.exit(1) 

    dns_address = '208.67.222.222'
    dns_port = 443

    print("Local IP: {}".format(local_address))
    print("Hostname: {}".format(hostname))
    print("Upstream DNS IP: {}".format(dns_address))
    print("Upstream DNS port: {}".format(dns_port))

    mdns_server = SlimDNSServer(local_address, hostname)
    mdns_resolver = SlimDNSResolver(mdns_server)

    mdns_server_thread = threading.Thread(target=mdns_server.run_forever) # TODO Stop thread properly
    mdns_server_thread.start()

    resolver = MulticastDNSProxyResolver(mdns_resolver, dns_address, dns_port)

    servers = [
        DNSServer(resolver=resolver, port=53, address="0.0.0.0", tcp=False)
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

