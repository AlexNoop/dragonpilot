#!/usr/bin/env python3
import os
import time
from common.params import Params
params = Params()
import cereal.messaging as messaging
from common.realtime import sec_since_boot

def main():
  thermal_sock = messaging.sub_sock('thermal')
  last_ts = 0
  secs = 0
  last_secs = 0
  shutdown_at = 0
  started = False
  usb_online = False
  enabled = False
  last_enabled = False
  while 1:
    cur_time = sec_since_boot()
    if cur_time - last_ts >= 10.:
      enabled = True if params.get("DragonEnableAutoShutdown", encoding='utf8') == '1' else False
      # reset timer when enabled status has changed
      if not last_enabled and enabled:
        shutdown_at = cur_time + secs
      last_enabled = enabled

      if enabled:
        secs = int(params.get("DragonAutoShutdownAt", encoding='utf8')) * 60
        # reset timer when secs num has changed
        if last_secs != secs:
          shutdown_at = cur_time + secs
        last_secs = secs

        msg = messaging.recv_sock(thermal_sock, wait=True)
        started = msg.thermal.started
        with open("/sys/class/power_supply/usb/present") as f:
          usb_online = bool(int(f.read()))

    if enabled:
      if started or usb_online:
        shutdown_at = cur_time + secs
      else:
        if secs > 0 and cur_time >= shutdown_at:
          os.system('LD_LIBRARY_PATH="" svc power shutdown')

    time.sleep(10)

if __name__ == "__main__":
  main()