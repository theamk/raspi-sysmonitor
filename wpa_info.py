#!/usr/bin/python3 -B
import sys
import os
import subprocess
import time
import collections

WifiResult = collections.namedtuple(
    'WifiResult', [
        'status', # connection status, or None if all connected
        'ip',     # associated IP or None
        'mac',    # MAC of wireless card
        'ssid',   # name wireless network we connected to
        'bssid',  # MAC of wireless AP we connected to
        'freq',   # frequency
        'linkspeed', # Link speed, Mb/sec
        'rssi',   # signal strength, dBm (-100 ... -10 range or so)
        'parse_info', # debugging only:  unused fields
    ])


_nologin_gone = True

def has_nologin():
    """Return True if we are in early boot and logins are not allowed yet"""
    global _nologin_gone
    if _nologin_gone:
        return False
    try:
        os.stat('/run/nologin')
        return True
    except FileNotFoundError:
        _nologin_gone = True
        return False


class WifiWPAInfo():
    """get info about wifi connection by talking to "wpa_supplicated" daemoin"""
    def __init__(self, iface="wlan0"):
        self._cmd_prefix = ['wpa_cli','-i', iface]
        
    def poll(self):
        ss = self._status_command('status')
        # Pop unused status fields so they do not show up in parse_info
        ss.pop('id', None)  # 0
        ss.pop('pairwise_cipher', None)  # 'CCMP'
        ss.pop('group_cipher', None) # 'CCMP'
        ss.pop('key_mgmt', None) # 'WPA2',
        ss.pop('mode', None) # 'station', 
        ss.pop('p2p_device_address', None) #  same as mac,
        ss.pop('uuid', None) #  network card UUID
        
        sp = self._status_command('signal_poll')
        sp.pop('NOISE', None) #  9999,
        sp.pop('FREQUENCY', None) # same as 'freq'

        status = ss.pop('wpa_state', '????')
        if status == 'COMPLETED':
            if not ss.get('ip_address'):
                status = 'DHCP'
            elif has_nologin():
                # wifi is ready, but login is prohibited
                status = 'WAIT-NOLOGIN'
            else:
                # All ready!
                status = ''
            
        result = WifiResult(
            status=status,
            ip=ss.pop('ip_address', None),
            mac=ss.pop('address', None),
            ssid=ss.pop('ssid', None),
            bssid=ss.pop('bssid', None),
            freq=ss.pop('freq', None),            
            linkspeed=sp.pop('LINKSPEED', None),
            rssi=sp.pop('RSSI', None),
            parse_info=tuple(
                ['ss_%s=%s' % (k, v) for k, v in sorted(ss.items())] +
                ['sp_%s=%s' % (k, v) for k, v in sorted(sp.items())] 
            ) or None)

        return result
                
    def _status_command(self, cmd):
        out, err = self._exec_command(cmd)
        rv = dict()
        if err:
            rv['ERR_PROCESS'] = err
        for lnum, line in enumerate(out.splitlines()):
            if '=' not in line:
                rv['ERR_' + str(lnum + 1)] = line
            else:
                k, v = line.split('=', 1)
                rv[k] = v
        return rv        

    def _exec_command(self, cmd):
        """exec wpa_cli command, return output as string"""
        # TODO: use "wpa_cli" in interactive mode to avoid all the execs
        proc = subprocess.run(self._cmd_prefix + [cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err = proc.stderr.decode('utf-8')
        if proc.returncode != 0:
            err += '\n(returncode %r)\n' % (proc.returncode, )
        return  proc.stdout.decode('utf-8'), err
            


def main():
    wifi_info = WifiWPAInfo()
    while True:
        stat = wifi_info.poll()
        print(stat)
        time.sleep(1.0)
    
    
if __name__ == '__main__':
    main()


