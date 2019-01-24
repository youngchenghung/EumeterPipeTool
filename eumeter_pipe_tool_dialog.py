# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EumeterPipeToolDialog
                                 A QGIS plugin
 EumeterPipeTool
                             -------------------
        begin                : 2019-01-02
        git sha              : $Format:%H$
        copyright            : (C) 2019 by  
        email                :  
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import *
from qgis.core import *
from qgis.utils import *

from ui_add_eumeter import Ui_AddEumeter
from ui_edit_eupipe import Ui_EditEupipe

class AddEumeterDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self, iface.mainWindow())
        self.ui = Ui_AddEumeter()
        self.ui.setupUi(self)

class EditEupipeDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self, iface.mainWindow())
        self.ui = Ui_EditEupipe()
        self.ui.setupUi(self)