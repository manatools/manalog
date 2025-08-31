
from systemd import journal
from datetime import datetime

import os, select, subprocess

class Logviewer():
  def __init__(self):
    self.j = journal.Reader()
    
  def query(self, lastboot, monotonic, units, boot, sinceDatetime, untilDatetime, matching, notmatching, level) :
    #   Query for journal lines matching the criteria
    if lastboot:
         self.j.this_boot()
    else :
        monotonic = False
    if units :
            self.j.add_match(f"_SYSTEMD_UNIT={units}.service")
    if boot :
            self.j.this_boot(boot)
    if level :
        self.j.log_level(level)
    if sinceDatetime :
        self.j.seek_realtime(sinceDatetime)
    i=0
    lenghtlimit = 100000
    logstr=""
    previousBoot = ""
    neni = not notmatching and not matching
    yeni = notmatching and not matching
    neyi = not notmatching and matching
    yeyi = notmatching and matching
        
    for l in self.j:
            if previousBoot != l['_BOOT_ID'] :
                if previousBoot != "" :
                    logstr += "=== {} ===\n".format(_("Reboot"))
                previousBoot = l['_BOOT_ID']
            if untilDatetime < l['__REALTIME_TIMESTAMP'] :
                break
            if i>lenghtlimit :
               logstr += _("Limit of {} lines reached. Please add some filters.\n").format(lenghtlimit) 
               break
            i+=1
            newline=self._displayLine(l, monotonic)
            if neni : # not notmatching and not matching
                    logstr += newline
            if yeni : #notmatching and not matching
                if not (notmatching in newline) :
                    logstr += newline
            if neyi :  #not notmatching and matching
                if matching in newline :
                    logstr += newline
            if yeyi : # notmatching and matching
                if not (notmatching in newline) and (matching in newline):
                    logstr += newline
    return logstr, i

  def tail(self, monotonic):
        #   Display in logview all new lines starting from now
        self.j.seek_tail()
        self.j.get_previous()
        p = select.poll()
        journal_fd = self.j.fileno()
        poll_event_mask = self.j.get_events()
        p.register(journal_fd, poll_event_mask)
        while True:
            # ev = self.dialog.pollEvent()
            if False :
                if ev.widget() == self.stopButton :
                    self.stopButton.setDisabled()
                    self.matchingInputField.setEnabled()
                    self.notMatchingInputField.setEnabled()
                    self.lastBoot.setEnabled()
                    break
            if p.poll(250):
                if self.j.process() == journal.APPEND:
                    for l in self.j:
                        pass
                        # send (self._displayLine(l, monotonic))

  def _displayLine(self, entry, monotonic = False):
      if monotonic :
         timeStr = "[{:.3f}]".format(entry['__MONOTONIC_TIMESTAMP'].timestamp.total_seconds())
      else :
          timeStr = datetime.strftime(entry['__REALTIME_TIMESTAMP'], '%Y-%m-%d %H:%M:%S' )
      try:
              pid = "[{}]".format(entry['_PID'])
      except :
             pid = ""
      if 'SYSLOG_IDENTIFIER' in entry.keys() :
           rline = "{} {}{}: {}\n".format(timeStr ,entry['SYSLOG_IDENTIFIER'], pid, entry['MESSAGE'])
      else:
        try:
              rline = "{} {}{}: {}\n".format( timeStr,entry['_COMM'],pid, entry['MESSAGE'])
        except:
            rline=""
            for key in entry.keys() :
                rline += ("{}: {}\n".format(key,entry[key]))
      return rline
