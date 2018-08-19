#!/usr/bin/env python3
#
# Author: Fred C.
# https://github.com/0x9900/whitelist/blob/master/whitelist.py
# Mod: LittleKaosLilly
#
from __future__ import print_function
from collections import defaultdict

import sys
import re
import dnsq
from netaddr import IPNetwork, cidr_merge

MAX_RECURSION = 5


def debug(thing):
    global isDebug
    if isDebug:
        print(thing)  # , file=sys.stderr)


def warning(thing):
    global isWarning
    if isWarning:
        print(thing, file=sys.stderr)


def dns_txt(domain):
    try:
        resp = dnsq.query_dns(domain, "TXT")
    except DNS.ServerError as err:
        debug("No TXT records for: " + domain + ": " + str(err))
        return None
    except dns.exception.DNSException as err:
        debug("No TXT records for: " + domain + ": " + str(err))
        return None

    # debug(resp)
    response = []
    for r in resp:
        response.append("".join([x for x in str(r).split('"') if x.strip()]))
    return response


def dns_parse(txt_records, domain):
    resp = defaultdict(set)
    for record in txt_records:
        debug("TXT record for: " + domain + ": " + str(record))
        fields = record.split(" ")
        if re.match(r"v=spf1", fields[0]):
            # warning("TXT record for:" + domain + ":" + str(record))
            for field in fields:
                tresp = parse_mechanism(field, domain)
                for t in tresp:
                    for tt in tresp.get(t, set()):
                        resp[t].add(tt)

    return resp


# Parse the given mechansim, and dispatch it accordintly
# well secu.lu read the RFC strangly
# TXT record for:secu.lu:v=spf1 +include:pt.lu +a +ip4:194.154.200.229 +ip4:80.90.47.128/29 ~all
def parse_mechanism(mechanism, domain):
    res = defaultdict(set)

    mechanism = mechanism.strip()
    if mechanism.startswith("+"):
        mechanism = mechanism.replace("+", '')

    if re.match(r"^a$", mechanism):
        res = convert_domain_to_ipv46(domain)
        return res

    elif re.match(r"^mx$", mechanism):
        debug("MX found for " + domain + ":" + mechanism)
        res = convert_mx_to_ipv46(domain)
        return res

    elif re.match(r"^a:.*$", mechanism):
        match = re.match(r"^a:(.*)$", mechanism)
        res = convert_domain_to_ipv46(match.group(1))
        return res

    elif re.match(r"^mx:.*$", mechanism):
        match = re.match(r"^mx:(.*)$", mechanism)
        res = convert_mx_to_ipv46(match.group(1))
        return res

    elif re.match(r"^ip4:.*$", mechanism):
        match = re.match(r"^ip4:(.*)$", mechanism)
        debug("IPv4 address found for " + domain + ": " + match.group(1))
        res["ip4"].add(match.group(1))
        return res

    elif re.match(r"^ip6:.*$", mechanism):
        match = re.match(r"^ip6:(.*)$", mechanism)
        debug("IPv6 address found for " + domain + ": " + match.group(1))
        res["ip6"].add(match.group(1))
        return res

    elif re.match(r"^ptr.*$", mechanism):
        warning("PTR found for " + domain + ": " + mechanism)

    elif re.match(r"^exists:$", mechanism):
        warning("Exists found for " + domain + ": " + mechanism)

    elif re.match(r"^exists:.*$", mechanism):
        warning("Exists found for " + domain + ": " + mechanism)

    elif re.match(r"^redirect(?:[=:]) ?(.*)$", mechanism):
        debug("Redirect found for " + domain + ": " + mechanism)
        match = re.match(r"^redirect(?:[=:]) ?(.*)", mechanism)
        res["redirect"].add(match.group(1))
        return res

    elif re.match(r"^exp:$", mechanism):
        warning("EXP found for " + domain + ": " + mechanism)

    # elif re.match(r"^.all$", mechanism):
    #    if domain == root_domain or all_mechanism == "":
    #        match = re.match(r"^(.all)$", mechanism)
    #        debug("All found for", domain, ":", match.group(1))
    #        all_mechanism = " " + str(match.group(1))

    elif re.match(r"^include:.*$", mechanism):
        match = re.match(r"^include:(.*)", mechanism)
        res["include"].add(match.group(1))
        return res

    elif mechanism == '':
        pass
    elif re.match(r"v=spf1", mechanism):
        pass
    elif re.match(r"(~|\-|\+|\?)all", mechanism):
        pass

    else:
        warning("Unkown pattern found for " + domain + ": " + mechanism)

    return res


# Convert A/AAAA records to IPs and adds them to the SPF master list
def convert_domain_to_ipv46(domain):
    res = defaultdict(set)
    try:
        a_records = dnsq.query_dns(domain, "A")
        for ip in a_records:
            debug("A record for" + domain + ":" + str(ip))
            res["ip4"].add(str(ip))
    except dns.exception.DNSException:
        pass

    try:
        aaaa_records = dnsq.query_dns(domain, "AAAA")
        for ip in aaaa_records:
            debug("A record for" + domain + ":" + str(ip))
            res["ip6"].add(str(ip))
    except dns.exception.DNSException:
        pass
    return res


# Convert MX records to IPs and adds them to the SPF master list
def convert_mx_to_ipv46(domain):
    res = defaultdict(set)
    try:
        mx_records = dnsq.query_dns(domain, "MX")
    except dns.exception.DNSException:
        import pdb

        pdb.set_trace()
        return

    for record in mx_records:
        mx = str(record).split(" ")
        debug("MX record found for " + domain + ": " + mx[1])
        tres = convert_domain_to_ipv46(mx[1])
        for t in tres:
            for tt in tres[t]:
                res[t].add(tt)
    return res


def process(domain):
    domains = [domain]
    ip_addresses = set()
    for cnt in range(MAX_RECURSION):
        includes = set()
        for dom in domains:
            txt = dns_txt(dom)
            if not txt:
                continue
            spf = dns_parse(txt, dom)
            ip_addresses |= spf.get("ip4", set())
            ip_addresses |= spf.get("ip6", set())
            includes |= spf.get("include", set())
            includes |= spf.get("redirect", set())
        if not includes:
            break
        domains = includes
    return ip_addresses


if __name__ == "__main__":
    global isDebug
    global isWarning
    isDebug = 0
    isWarning = 0
    whitelist = set()
    domainlist = set()
    with open(sys.argv[1]) as fd:
        for line in fd:
            line = line.strip()
            if line == "":
                continue
            domainlist.add(line)
            for ip in process(line):
                whitelist.add(IPNetwork(ip))

    ip_list = list()
    for ip in whitelist:
        found = False
        for ipl in ip_list:
            if ip in ipl:
                found = True
        if found is True:
            continue
        ip_list.append(ip)

    to_remove = set()
    for ondex in range(len(ip_list)):
        ip = ip_list[ondex]
        found = False
        for index in range(ondex + 1, len(ip_list)):
            if ip in ip_list[index]:
                found = True
        if found is True:
            to_remove.add(ip)
            continue

    for ip in to_remove:
        ip_list.remove(ip)

    cidr_merge(ip_list)

    warning(len(ip_list))
    warning(len(whitelist))

    print(
        """# Permit local clients
127.0.0.0/8 permit
192.168.46.0/24 permit
# RFC 1918
192.168.0.0/16       reject
172.16.0.0/12        reject
10.0.0.0/8           reject"""
    )

    print("")
    for dom in sorted(domainlist):
        print("# " + dom)

    print("")
    # for ip in sorted(whitelist):
    for ip in sorted(ip_list):
        if ip.version == 4:
            print(str(ip.cidr) + "   permit")
