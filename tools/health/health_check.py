#!/usr/bin/env python3
"""Simple system health check for vps-agent

Checks:
- git status (clean/dirty)
- disk usage (root)
- memory usage
- python version
- DNS/connectivity to api.openai.com:443

Prints a clean CLI report.
"""
import shutil
import subprocess
import sys
import socket
import os


def git_status(repo_path):
    try:
        out = subprocess.check_output(["/usr/bin/git","-C",repo_path,"status","--porcelain"], stderr=subprocess.STDOUT, text=True)
        return "clean" if out.strip()=="" else "dirty"
    except Exception as e:
        return f"error: {e}"


def disk_usage(path="/"):
    try:
        total, used, free = shutil.disk_usage(path)
        return {"total": total, "used": used, "free": free}
    except Exception as e:
        return {"error": str(e)}


def memory_usage():
    # Try /proc/meminfo for portability
    try:
        mem = {}
        with open('/proc/meminfo') as f:
            for line in f:
                parts = line.split(':')
                if len(parts) != 2:
                    continue
                key = parts[0].strip()
                val = parts[1].strip().split()[0]
                mem[key] = int(val)
        return {"MemTotal_kB": mem.get('MemTotal'), "MemAvailable_kB": mem.get('MemAvailable')}
    except Exception as e:
        return {"error": str(e)}


def python_version():
    return sys.version.split('\n')[0]


def can_connect(host='api.openai.com', port=443, timeout=5):
    try:
        addr = socket.getaddrinfo(host, port)[0][4]
        s = socket.socket()
        s.settimeout(timeout)
        s.connect(addr)
        s.close()
        return True
    except Exception as e:
        return False


def report(repo_path):
    r = {}
    r['git_status'] = git_status(repo_path)
    r['disk'] = disk_usage('/')
    r['memory'] = memory_usage()
    r['python'] = python_version()
    r['can_connect_api_openai'] = can_connect()
    return r


def print_report(r):
    print('SYSTEM HEALTH CHECK')
    print('===================')
    print(f"Git status: {r['git_status']}")
    print('')
    d = r['disk']
    if 'error' in d:
        print(f"Disk: error: {d['error']}")
    else:
        print(f"Disk total: {d['total']//(1024*1024)} MB")
        print(f"Disk used: {d['used']//(1024*1024)} MB")
        print(f"Disk free: {d['free']//(1024*1024)} MB")
    print('')
    m = r['memory']
    if 'error' in m:
        print(f"Memory: error: {m['error']}")
    else:
        print(f"MemTotal_kB: {m.get('MemTotal_kB')}")
        print(f"MemAvailable_kB: {m.get('MemAvailable_kB')}")
    print('')
    print(f"Python: {r['python']}")
    print(f"Can connect to api.openai.com:443: {r['can_connect_api_openai']}")


if __name__ == '__main__':
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    repo = os.path.normpath(repo)
    res = report(repo)
    print_report(res)
