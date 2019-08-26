#!/usr/bin/env python3
#  manalog.py
#  
#  Copyright 2017 Papoteur
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import manatools.ui.common as common
import manatools.ui.basedialog as basedialog
import manatools.services as mnservices
import yui
import time
import gettext
from datetime import date, datetime
from systemd import journal
import os, select, subprocess
import re
import operator

######################################################################
## 
##  Manalog
## 
######################################################################

class MlDialog(basedialog.BaseDialog):
  def __init__(self):
    gettext.install('manatools', localedir='/usr/share/locale', names=('ngettext',))
    if os.getuid() == 0 :
        space = _("System space")
    else :
        space = _("User space")
    self._application_name = _("ManaLog - ManaTools log viewer")
    basedialog.BaseDialog.__init__(self, _("Manatools - log viewer - {}").format(space), "", basedialog.DialogType.POPUP, 80, 10)

  def commands_getstatusoutput(self, cmd):
    """Return (status, output) of executing cmd in a shell."""
    pipe = subprocess.Popen('{ ' + cmd + '; } 2>&1', stdin = subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines = True, shell = True)
    of = pipe.stdout.fileno()
    text = ''
    pipe.stdin.close()
    while True:
        text += os.read(of,8192).decode('utf8')
        status = pipe.poll()
        if status is not None or text == '':
            break
    if text[-1:] == '\n': text = text[:-1]
    return status, text

  def listBoots(self) :
    j = journal.Reader()
    boot_ids = j.query_unique('_BOOT_ID')
    boots = {}
    i=1
    for boot_id in boot_ids:
        j.this_boot(boot_id)
        entry = j.get_next()
        try:
             boots[str(boot_id)]=entry['__REALTIME_TIMESTAMP']
        except:
            pass
        j.flush_matches()
        j.seek_head()
    s_boots = sorted(boots.items(), key=operator.itemgetter(1))
    st_boots = []
    i=1
    for boot_id, tm in s_boots:
        st_boots.append(["{:4d}".format(i),boot_id,datetime.strftime(tm, '%Y-%m-%d %H:%M:%S')])
        i+=1
    return st_boots

  def UIlayout(self, layout):
    '''
    layout to setup UI for Manalog
    '''
    optFactory = yui.YUI.optionalWidgetFactory()
    dialog = self.factory.createVBox(layout)

    lbl1 = self.factory.createLabel(  (dialog), _("A tool to monitor your logs"),True,False)
    cols = self.factory.createHBox(layout)
    col1 = self.factory.createVBox(cols)
    frame = self.factory.createFrame(col1, _("Options"))
    vbox = self.factory.createVBox(col1)
    #### Last Boot
    self.lastBoot = self.factory.createCheckBox(self.factory.createLeft(vbox),_("Last boot"),True)
    self.lastBoot.setNotify(True)
    self.eventManager.addWidgetEvent(self.lastBoot, self.onLastBootEvent)
    #### Tailing mode
    self.tailing = self.factory.createCheckBox(self.factory.createLeft(vbox),_("Tail mode"),False)
    self.tailing.setNotify(True)
    self.eventManager.addWidgetEvent(self.tailing, self.onTailingEvent)
    #### Monotonic display for timestamp
    self.monotonbt = self.factory.createCheckBox(self.factory.createLeft(vbox),_("Monotonic timestamp"),True)

    self.factory.createVSpacing(vbox,0.5)
    row1 = self.factory.createHBox(vbox)
    self.factory.createVSpacing(vbox, 0.5)
    row2 = self.factory.createHBox(vbox)
    self.factory.createVSpacing(vbox, 0.5)
    row3 = self.factory.createHBox(vbox)
    self.factory.createVSpacing(vbox, 0.5)
    row4 = self.factory.createHBox(vbox)
    self.factory.createVSpacing(vbox, 0.5)
    row5 = self.factory.createHBox(vbox)
    self.factory.createVSpacing(vbox, 0.5)
    row6 = self.factory.createHBox(vbox)
    self.factory.createVSpacing(vbox, 0.5)
    row7 = self.factory.createHBox(vbox)
    self.factory.createVSpacing(vbox, 0.5)
    row8 = self.factory.createHBox(vbox)
    self.factory.createVSpacing(vbox, 0.5)
    row9 = self.factory.createHBox(vbox)
    
    #### since and until
    self.sinceFrame = self.factory.createCheckBoxFrame(row1, _("Since"), True)
    self.sinceFrame.setWeight(yui.YD_HORIZ, 1)
    self.sinceFrame.setNotify(True)
    self.eventManager.addWidgetEvent(self.sinceFrame, self.onSinceFrameEvent)
    self.untilFrame = self.factory.createCheckBoxFrame(row2, _("Until"), True)
    self.untilFrame.setWeight(yui.YD_HORIZ, 1)
    self.untilFrame.setNotify(True)
    self.eventManager.addWidgetEvent(self.untilFrame, self.onUntilFrameEvent)
    if (optFactory.hasDateField()):
        hbox1 = self.factory.createHBox(self.sinceFrame)
        self.sinceDate = self.optFactory.createDateField(hbox1, "")
        self.factory.createHSpacing(hbox1, 1.0)
        self.sinceTime = optFactory.createTimeField(hbox1, "");
        sday = date.today().isoformat()
        self.sinceDate.setValue(sday)
        self.sinceTime.setValue("00:00:00")

        hbox1 =  self.factory.createHBox(self.untilFrame)
        self.untilDate = optFactory.createDateField(hbox1, "")
        self.factory.createHSpacing(hbox1, 1.0)
        self.untilTime = optFactory.createTimeField(hbox1, "")
        self.untilDate.setValue(sday)
        self.untilTime.setValue("23:59:59")
    else :
        self.sinceFrame.enable(False)
        self.untilFrame.enable(False)

    #### units
    spacing = self.factory.createHSpacing(row1, 2.0)
    self.unitsFrame = self.factory.createCheckBoxFrame(row3,_("Select a unit"), True)
    self.unitsFrame.setNotify(True)
    self.units = self.factory.createComboBox( self.factory.createLeft(self.unitsFrame), "" )
    
    yui.YUI.app().busyCursor()
    myserv = mnservices.Services()
    list_services = myserv.service_info
    list_units = []
    for unit in list_services.keys() :
        list_units.append(unit)
    list_units.sort()
    dlist = []
    for unit in list_units :
        item = yui.YItem(unit)
        item.this.own(False)
        dlist.append(item)
    itemCollection = yui.YItemCollection(dlist)
    self.units.addItems(itemCollection)
    #### boots
    dlist = []
    self.bootModel = {}
    for boot in self.listBoots() :
        key = boot[0]+' '+boot[2]
        item = yui.YItem(key)
        self.bootModel[key] = boot[1]    #  boot_id
        item.this.own(False)
        dlist.append(item)
    self.bootsFrame = self.factory.createCheckBoxFrame(row4,_("Select a boot"), True)
    self.bootsFrame.setNotify(True)
    if dlist == [] :
        self.eventManager.addWidgetEvent(self.bootsFrame, self.onBootFrameErrorEvent)
    else :
      self.eventManager.addWidgetEvent(self.bootsFrame, self.onBootFrameEvent)      
    self.boots = self.factory.createComboBox( self.factory.createLeft(self.bootsFrame), "" )
    itemCollection = yui.YItemCollection(dlist)
    self.boots.addItems(itemCollection)
    
    #### priority
    # From
    self.factory.createHSpacing(row2, 2.0)
    self.priorityFromFrame = self.factory.createCheckBoxFrame(row5, _("Priority level"), True)
    self.priorityFromFrame.setNotify(True)
    self.priorityFromFrame.setWeight(yui.YD_HORIZ, 1)
    self.priorityFrom = self.factory.createComboBox( self.priorityFromFrame, "" )

    self.pr = ('emerg', 'alert', 'crit', 'err', 'warning', 'notice', 'info', 'debug')
    dlist = []
    for prio in self.pr:
        item = yui.YItem(prio)
        if ( prio == 'debug' ):
            item.setSelected(True)
        item.this.own(False)
        dlist.append(item)
    itemCollection = yui.YItemCollection(dlist)
    self.priorityFrom.addItems(itemCollection)

    #### matching
    self.matchingInputField = self.factory.createInputField(row6, _("Matching"))
    self.factory.createSpacing(row3,1)
    #### not matching
    self.notMatchingInputField =self.factory.createInputField(row7, _("but not matching"))
    self.matchingInputField.setWeight(yui.YD_HORIZ, 1)
    self.notMatchingInputField.setWeight(yui.YD_HORIZ, 1)

    #### search
    self.stopButton = self.factory.createPushButton(self.factory.createRight(row8), _("&Stop"))
    self.eventManager.addWidgetEvent(self.stopButton, self.onStopButton)
    self.stopButton.setDisabled()
    self.findButton = self.factory.createPushButton(self.factory.createRight(row8), _("&Find"))
    self.eventManager.addWidgetEvent(self.findButton, self.onFindButton)
    
    #### create log view object
    self.logView = self.factory.createLogView(cols, _("Log content"), 10, 0)
    self.logView.setWeight(yui.YD_HORIZ, 4)

    self.unitsFrame.setValue(False)
    self.sinceFrame.setValue(False)
    self.untilFrame.setValue(False)
    self.priorityFromFrame.setValue(False)
    self.bootsFrame.setValue(False)

    # buttons on the last line
    align = self.factory.createRight(layout)
    hbox = self.factory.createHBox(align)
    aboutButton = self.factory.createPushButton(hbox, _("&About") )
    self.eventManager.addWidgetEvent(aboutButton, self.onAbout)
    align = self.factory.createRight(hbox)
    hbox     = self.factory.createHBox(align)
    saveButton = self.factory.createPushButton(hbox, _("&Save"))
    self.eventManager.addWidgetEvent(saveButton, self._save)
    quitButton = self.factory.createPushButton(hbox, _("&Quit"))
    self.eventManager.addWidgetEvent(quitButton, self.onQuit)

    # Let's test a cancel event
    self.eventManager.addCancelEvent(self.onCancelEvent)
    
    # End Dialof layout
    

  def onStopButton(self): 
    print ('Button "Stop" pressed')

      #  Active section
  def onFindButton(self) :
    yui.YUI.app().busyCursor()
    j = journal.Reader()
    if self.lastBoot.value() :
         j.this_boot()
         monotonic = self.monotonbt.value()
    else :
        monotonic = False
    if self.unitsFrame.value() :
        if self.units.value() != "" :
            j.add_match("_SYSTEMD_UNIT={}.service".format(self.units.value()))
    if self.bootsFrame.value() :
        monotonic = self.monotonbt.value()
        if self.boots.value() != "" :
            j.this_boot(self.bootModel[self.boots.value()])
    if self.priorityFromFrame.value() :
        level = self.pr.index(self.priorityFrom.value())
        print(level)
        j.log_level(level)
    if self.sinceFrame.value() :
        begin = datetime.strptime(self.sinceDate.value() +" "+self.sinceTime.value(), '%Y-%m-%d %H:%M:%S' )
        j.seek_realtime(begin)
    if self.tailing.value() :
        #   Display in logview all new lines starting from now
        self.stopButton.setEnabled()
        j.seek_tail()
        j.get_previous()
        p = select.poll()
        journal_fd = j.fileno()
        poll_event_mask = j.get_events()
        p.register(journal_fd, poll_event_mask)
        while True:
            ev = self.dialog.pollEvent()
            if ev != None :
                if ev.widget() == self.stopButton :
                    self.stopButton.setDisabled()
                    self.matchingInputField.setEnabled()
                    self.notMatchingInputField.setEnabled()
                    self.lastBoot.setEnabled()
                    break
            if p.poll(250):
                if j.process() == journal.APPEND:
                    for l in j:
                        self.logView.appendLines(self._displayLine(l, monotonic))
    else:
        #   Query for journal lines matching the criteria
        i=0
        lenghtlimit = 100000
        logstr=""
        previousBoot = ""
        if self.untilFrame.value() :
            untilDatetime = datetime.strptime(self.untilDate.value() +" "+self.untilTime.value(), '%Y-%m-%d %H:%M:%S' )
        else :
            untilDatetime = datetime.now()
        matching = self.matchingInputField.value()
        notmatching = self.notMatchingInputField.value()
        matching = matching.replace(' OR ','|')
        if matching == '*' : 
            matching = ''
        if notmatching =='*' : 
            notmatching = '.*'
        neni = not notmatching and not matching
        yeni = notmatching and not matching
        neyi = not notmatching and matching
        yeyi = notmatching and matching
        
        for l in j:
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
            newline=self._displayLine(l,monotonic)
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
        self.logView.setLogText(logstr)
        print("Found {} lines".format(i))
    yui.YUI.app().normalCursor()
    
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
            
  def onLastBootEvent(self) :
      yui.YUI.ui().blockEvents()
      self.sinceFrame.setValue(False)
      self.untilFrame.setValue(False)
      self.monotonbt.setValue(self.lastBoot.value())
      self.bootsFrame.setValue(False)
      yui.YUI.ui().unblockEvents()

  def onBootFrameEvent(self):
      yui.YUI.ui().blockEvents()
      if self.bootsFrame.value() :
          self.lastBoot.setValue(False)
      yui.YUI.ui().unblockEvents()

  def onBootFrameErrorEvent(self):
    # Display error message and ask for journal verification when boots cannot be listed.
    yui.YUI.ui().blockEvents()
    if self.bootsFrame.value() :
      yui.YUI.app().busyCursor()
      if common.askYesOrNo({'title' : _("Boots cannot be listed"),
                            'text' : _("Failed to determine boots: No data available. Do you want to verify the system journal ? (this can take a while)"),
                            'richtext' : True,
                            'default_button' : 2}) == True :
        status,text = self.commands_getstatusoutput("LC_ALL=C journalctl --verify -q")
        yui.YUI.app().normalCursor()
        if status != 0 :
          textToShow = ""
          failedFiles= ""
          for element in text.splitlines(keepends = True) :
            if "FAIL" in element:
              failedFiles += element
              textToShow += failedFiles
          if os.getuid() == 0 :
            textToShow += _("\nDo you want to remove these files ?")
            if common.askYesOrNo({'title' : _("ManaLog - Verify journal"),
                                  'text' : textToShow,
                                  'richText' : True,
                                  'default_button' : 2}) == True :
              for element in failedFiles.splitlines(keepends = False) :
                os.remove(search('\s(.+?)\s', element).group(1))
          else :
            textToShow += _("\nYou must be root to remove these files.")
            common.warningMsgBox ({'title' : _("ManaLog - Verify journal"),
                                   'text' : textToShow,
                                   'richtext' : True})
        else :
          common.infoMsgBox({'title' : _("ManaLog - Verify journal"),
                             'text' : _("No errors have been detected in journal files."),
                             'richtext' : True})
      else :
        yui.YUI.app().normalCursor()
    self.bootsFrame.setValue(False)
    yui.YUI.ui().unblockEvents()

  def onSinceFrameEvent(self) :
      yui.YUI.ui().blockEvents()
      if self.sinceFrame.value() :
          self.lastBoot.setValue(False)
      yui.YUI.ui().unblockEvents()

  def onUntilFrameEvent(self) :
      yui.YUI.ui().blockEvents()
      if self.untilFrame.value() :
          self.lastBoot.setValue(False)
      yui.YUI.ui().unblockEvents()

  def onTailingEvent(self):
      yui.YUI.ui().blockEvents()
      if self.tailing.value() :
            self.sinceFrame.setValue(False)
            self.untilFrame.setValue(False)
            self.priorityFromFrame.setValue(False)
            self.unitsFrame.setValue(False) 
            self.matchingInputField.setValue("")
            self.notMatchingInputField.setValue("")
            self.matchingInputField.setDisabled()
            self.notMatchingInputField.setDisabled()
            self.lastBoot.setDisabled()
            self.sinceFrame.setDisabled()
            self.untilFrame.setDisabled()
            self.unitsFrame.setDisabled()
      else:
           self.lastBoot.setEnabled()
           
      yui.YUI.ui().unblockEvents()
    
  def onCancelEvent(self) :
    print ("Got a cancel event")

  def onQuit(self) :
    print ("Quit button pressed")
    # BaseDialog needs to force to exit the handle event loop 
    self.ExitLoop()

  def onAbout(self) :
      ok = common.AboutDialog({
            'name' : self._application_name,
            'dialog_mode' : common.AboutDialogMode.TABBED,
            'version' : "0.1.0",
            'credits' :"Credits 2017, 2019 Papoteur, Cyril Levet",
            'license' : 'GPLv3',
            'authors' : 'Papoteur &lt;papoteur@mageialinux-online.org&gt;<br />Cyril Levet &lt;cyril.levet0780@orange.fr&gt;',
            'description' : _("Log viewer is a systemd journal viewer"),
      })
  
  def _save(self) :
       yui.YUI.app().busyCursor()
       save_name = yui.YUI.app().askForSaveFileName(os.path.expanduser("~"), "*", _("Save as.."))
       if save_name :
           with open(save_name, 'w') as fd:
                fd.write(self.logView.logText())
      
if __name__ == '__main__':
  ml = MlDialog()
  ml.run()

