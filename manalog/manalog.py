#!/usr/bin/python3 -O
#  manalog.py
#  
#  Copyright 2017 Papoteur
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
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
import os

######################################################################
## 
##  Manalog
## 
######################################################################

class MlDialog(basedialog.BaseDialog):
  def __init__(self):
    basedialog.BaseDialog.__init__(self, "Manatools - log viewer", "", basedialog.DialogType.POPUP, 80, 10)
    
  def UIlayout(self, layout):
    '''
    layout to setup UI for Manalog
    '''
    optFactory = yui.YUI.optionalWidgetFactory()
    dialog = self.factory.createVBox(layout)

    lbl1 = self.factory.createLabel(  (dialog), _("A tool to monitor your logs"),True,False)
    frame = self.factory.createFrame(layout, _("Options"))
    vbox = self.factory.createVBox(frame)
    self.lastBoot = self.factory.createCheckBox(self.factory.createLeft(vbox),_("Last boot"),True)
    self.lastBoot.setNotify(True)
    self.eventManager.addWidgetEvent(self.lastBoot, self.onLastBootEvent)
    self.factory.createVSpacing(vbox,0.5)
    row1 = self.factory.createHBox(vbox)
    self.factory.createVSpacing(vbox, 0.5)
    row2 = self.factory.createHBox(vbox)
    self.factory.createVSpacing(vbox, 0.5)
    row3 = self.factory.createHBox(vbox)
    self.factory.createVSpacing(vbox, 0.5)
    row4 = self.factory.createHBox(vbox)
    
    #### since and until
    self.sinceFrame = self.factory.createCheckBoxFrame(row1, _("Since"), True)
    self.sinceFrame.setNotify(True)
    self.eventManager.addWidgetEvent(self.sinceFrame, self.onSinceFrameEvent)
    self.untilFrame = self.factory.createCheckBoxFrame(row2, _("Until"), True)
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

    self.unitsFrame = self.factory.createCheckBoxFrame(row1,_("Select a unit"), True)
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
    yui.YUI.app().normalCursor()

    #### priority
    # From
    self.factory.createHSpacing(row2, 2.0)
    self.priorityFromFrame = self.factory.createCheckBoxFrame(row2, _("From priority"), True)
    self.priorityFromFrame.setNotify(True)
    self.priorityFromFrame.setWeight(yui.YD_HORIZ, 1)
    priorityFrom = self.factory.createComboBox( self.priorityFromFrame, "" )

    pr = ('emerg', 'alert', 'crit', 'err', 'warning', 'notice', 'info', 'debug')
    dlist = []
    for prio in pr:
        item = yui.YItem(prio)
        if ( prio == 'emerg' ):
            item.setSelected(True)
        item.this.own(False)
        dlist.append(item)
    itemCollection = yui.YItemCollection(dlist)
    priorityFrom.addItems(itemCollection)

    self.factory.createHSpacing( row2, 2.0 )
    # To
    self.priorityToFrame = self.factory.createCheckBoxFrame(row2, _("To priority"), True)
    self.priorityToFrame.setNotify(True)
    self.priorityToFrame.setWeight(yui.YD_HORIZ, 1)
    priorityTo = self.factory.createComboBox( self.priorityToFrame, "" )

    dlist = []
    for prio in pr:
        item = yui.YItem(prio)
        if ( prio == 'debug' ):
            item.setSelected(True)
        item.this.own(False)
        dlist.append(item)
    itemCollection = yui.YItemCollection(dlist)
    priorityTo.addItems(itemCollection)

    #### matching
    self.matchingInputField = self.factory.createInputField(row3, _("Matching"))
    self.factory.createSpacing(row3,1)
    #### not matching
    self.notMatchingInputField =self.factory.createInputField(row3, _("but not matching"))
    self.matchingInputField.setWeight(yui.YD_HORIZ, 2)
    self.notMatchingInputField.setWeight(yui.YD_HORIZ, 2)

    #### search
    findButton = self.factory.createPushButton(self.factory.createRight(row4), _("&Find"))
    self.eventManager.addWidgetEvent(findButton, self.onFindButton)
    
    #### create log view object
    self.logView = self.factory.createLogView(layout, _("Log content"), 10, 0)


    ### NOTE CheckBoxFrame doesn't honoured his costructor checked value for his children
    self.unitsFrame.setValue(False)
    self.sinceFrame.setValue(False)
    self.untilFrame.setValue(False)
    self.priorityFromFrame.setValue(False)
    self.priorityToFrame.setValue(False)

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
    
  def onFindButton(self) :
    print ('Button "Find" pressed')
    yui.YUI.app().busyCursor()
    j = journal.Reader()
    if self.lastBoot.value() :
         j.this_boot()
    if self.unitsFrame.value() :
        if self.units.value() != "" :
            j.add_match("_SYSTEMD_UNIT={}.service".format(self.units.value()))
    if self.priorityFromFrame.value() :
        level = self.priorityFromFrame.value()
        if self.priorityToFrame.value() :
            level += self.priorityToFrame.value()
        j.log_level(level)
    if self.sinceFrame.value() :
        begin = datetime.strptime(self.sinceDate.value() +" "+self.sinceTime.value(), '%Y-%m-%d %H:%M:%S' )
        j.seek_realtime(begin)
    i=0
    logstr=""
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
        i+=1
        try:
            newline="{} {}[{}]: {}\n".format( datetime.strftime(l['__REALTIME_TIMESTAMP'], '%Y-%m-%d %H:%M:%S' ), l['SYSLOG_IDENTIFIER'],l['_PID'], l['MESSAGE'])
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
        except:
            for key in l.keys() :
                logstr += ("{}: {}\n".format(key,l[key]))
    self.logView.setLogText(logstr)
    yui.YUI.app().normalCursor()
    
  def onLastBootEvent(self) :
      yui.YUI.ui().blockEvents()
      self.sinceFrame.setValue(False)
      self.untilFrame.setValue(False)
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

  def onPriorityFromFrameEvent(self):
      yui.YUI.ui().blockEvents()
      if self.priorityToFrame.value() and not self.priorityFromFrame.value():
          self.priorityToFrame.setValue(False)
      yui.YUI.ui().unblockEvents()
   
  def onPriorityToFrameEvent(self):
      yui.YUI.ui().blockEvents()
      if self.priorityToFrame.value() and not self.priorityFromFrame.value():
          self.priorityFromFrame.setValue(True)
      yui.YUI.ui().unblockEvents()

  def onCancelEvent(self) :
    print ("Got a cancel event")

  def onQuit(self) :
    print ("Quit button pressed")
    # BaseDialog needs to force to exit the handle event loop 
    self.ExitLoop()

  def onAbout(self) :
      ok = common.infoMsgBox({'title':"About", 'text':"Log viewer is a systemd journal viewer\nWork in progress"})

  def _save(self) :
       yui.YUI.app().busyCursor()
       save_name = yui.YUI.app().askForSaveFileName(os.path.expanduser("~"), "*", _("Save as.."))
       if save_name :
           with open(save_name, 'w') as fd:
                fd.write(self.logView.logText())
      
if __name__ == '__main__':
  gettext.install('manatools', localedir='/usr/share/locale', names=('ngettext',))
  ml = MlDialog()
  ml.run()

