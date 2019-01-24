# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EumeterPipeTool
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
import math
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *

from qgis.utils import *
from qgis.gui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources
#from draw_eumeter_move import *
from drawpiperb import *
# Import the code for the dialog
from eumeter_pipe_tool_dialog import AddEumeterDialog, EditEupipeDialog
import os.path


class EumeterPipeTool:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.unitcode = u''
        self.packer = None
        self.status = 0
        self.editing = False
        self.geom = None
        self.points = []
        self.rb_len = 0.0
        self.gid = 0
        self.unitcode = None
        self.frame_no = u''
        self.type_id = u'0'
        self.std = u'0'
        self.pipe_size = 0
        self.which_dlg = True
        self.assets_or_proj = True
        self.point_xy = ''

        self.rubberband = QgsRubberBand(self.iface.mapCanvas())
        self.rubberband.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.rubberband.setColor(QColor(0, 0, 255, 200))
        self.rubberband.setWidth(2)
        self.rubberband.setVisible(False)

        self.vertex_band = QgsRubberBand(self.iface.mapCanvas())
        self.vertex_band.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.vertex_band.setColor(Qt.magenta)
        self.vertex_band.setIconSize(5)
        self.vertex_band.setVisible(False)

        self.eumeter_pipe_tool_dlg = AddEumeterDialog()
        self.eumeter_pipe_tool_dlg.setWindowTitle(u'新增水表鎖管線')

        self.eumeter_eupipe_tool_dlg = EditEupipeDialog()
        self.eumeter_eupipe_tool_dlg.setWindowTitle(u'新增用戶外線鎖管線')

    def initGui(self):
        self.toolBar = self.iface.addToolBar(u'水表工具')
        self.toolBar.setObjectName('水表工具')
        
        # 新增水表鎖管線
        self.action_add_pipe_snap = QAction(QIcon("C:/Users/tesla/.qgis2/python/plugins/EumeterPipeTool/eumeter_pipe_snap.png"), u"水表工具", self.iface.mainWindow())
        self.action_add_pipe_snap.setCheckable(True)
        self.action_add_pipe_snap.triggered.connect(self.add_eumeter_snap_init)
        self.toolBar.addAction(self.action_add_pipe_snap)

        self.eumeter_pipe_tool_dlg.ui.pushButtonOK.clicked.connect(self.add_eumeter_save)
        self.eumeter_pipe_tool_dlg.ui.pushButtonCancel.clicked.connect(self.add_eumeter_close)
        self.eumeter_pipe_tool_dlg.ui.pushButtonUpdate.clicked.connect(self.get_code_no)
        self.eumeter_pipe_tool_dlg.ui.comboBox_meter_mode.currentIndexChanged.connect(self.meter_mode_changed)
        self.eumeter_pipe_tool_dlg.ui.pushButtonUpdate.clicked.connect(self.get_eum_k)
        self.eumeter_pipe_tool_dlg.ui.plainTextEdit_bh_loc.textChanged.connect(lambda max_length=200: self.bh_loc_changed(max_length))


        # 新增用戶外線鎖管線
        self.action_add_eupipe = QAction(QIcon("C:/Users/tesla/.qgis2/python/plugins/EumeterPipeTool/add_eupipe.png"), u"用戶外線工具", self.iface.mainWindow())
        self.action_add_eupipe.setCheckable(True)
        self.action_add_eupipe.triggered.connect(self.add_eupip_snap_init)
        self.toolBar.addAction(self.action_add_eupipe)

        #self.eumeter_eupipe_tool_dlg.ui.pushButtonOK.clicked.connect(self.add_eupipe_snap_save)
        self.eumeter_eupipe_tool_dlg.ui.pushButtonCancel.clicked.connect(self.add_eupipe_snap_close)
        self.eumeter_eupipe_tool_dlg.ui.plainTextEdit_pipe_doc.textChanged.connect(lambda max_length=100, plain_name='pipe_doc': self.text_changed_eu(max_length, plain_name))
        self.eumeter_eupipe_tool_dlg.ui.plainTextEdit_remark.textChanged.connect(lambda max_length=200, plain_name='remark': self.text_changed_eu(max_length, plain_name))

        # 繪圖圖徵工具
        QObject.connect(self.iface.mapCanvas(), SIGNAL("mapToolSet(QgsMapTool*)"), self.deactivate)

        #self.add_eu_orth_tool = QgsMapToolEmitPoint(self.canvas)
        self.draw_pipe_snap = DrawPipeSnap(self.iface.mapCanvas())
        self.draw_pipe_snap.setAction(self.action_add_pipe_snap)

        self.draw_eupipe_snap = DrawEupipeSnap(self.iface.mapCanvas())
        self.draw_eupipe_snap.setAction(self.action_add_eupipe)
        #self.eu_orth_init = drawpiperb(self.canvas)


    def unload(self):
        self.iface.removeToolBarIcon(self.action_add_pipe_snap)
        self.iface.removePluginMenu(u'新增水表鎖管線', self.action_add_pipe_snap)

        self.iface.removeToolBarIcon(self.action_add_eupipe)
        self.iface.removePluginMenu(u'新增用戶外線鎖管線', self.action_add_eupipe)

        del self.toolBar

    # 新增水表鎖關線 - 啟動點
    def add_eumeter_snap_init(self):
        #print 'add_eumeter_snap_init'

        db_conn = self.get_db_connection()
        query_string = u'SELECT * FROM work_unit'
        query = db_conn.exec_(query_string)

        if query.isActive():
            while query.next():
                self.unitcode = query.value(0)

        self.get_unitcode()
        if len(self.unitcode) > 0:
            if self.layer_check(u'pipe'):
                self.status = 1
                layer = self.iface.activeLayer()
                self.editing = layer.isEditable()
                
                if not self.editing:
                    self.iface.actionToggleEditing().trigger()
                self.iface.mapCanvas().setMapTool(self.draw_pipe_snap)
                self.action_add_pipe_snap.setChecked(True)
                # 繪製完成，執行
                QObject.connect(self.draw_pipe_snap, SIGNAL("drawdown"), self.add_eumeter_snap_geom)
            else:
                QMessageBox.information(self.iface.mainWindow(), u'新增管線', u'管線 圖層尚未開啟!')
        else:
            QMessageBox.information(self.iface.mainWindow(), u'取得廠所代碼', u'廠所代碼不存在!')
    

    # 新增水表鎖關線 - 確認繪製圖徵
    def add_eumeter_snap_geom(self, geom, frame_no):
        #print'add_eumeter_snap_geom'


        reply = QMessageBox.information(self.iface.mainWindow(), u'新增管線', u'確認新增「管線圖徵」! (取消則重新繪製)',
            u'確認', u'取消')
        # 確認 = 0， 取消 = 1

        if reply:
            self.draw_pipe_snap.activate()

        else:
            self.iface.actionPan().trigger()
            self.frame_no = frame_no
            self.geom = geom
            self.points = geom.asPolyline()
            #print self.points
            points_xy = format(self.points[1].x()) + u' ' + format(self.points[1].y())
            self.points_xy = points_xy
            #print '尾端座標 : ' + self.points_xy
            #print u'確認幾何圖形 : ', self.points
            
            # 畫線座標位置
            self.rubberband.setToGeometry(QgsGeometry.fromPolyline(self.points), None)
            # 畫點座標位置
            self.vertex_band.setToGeometry(QgsGeometry.fromPoint(self.points[-1]), None)
            #self.vertex_band.setToGeometry(QgsGeometry.fromPoint(self.points[0]), None)

        # 新增水表 取得 廠所代碼 與 圖框編碼
        self.get_code_no(points_xy)
        if self.frame_no != u'' and self.unitcode != u'':
            # 求止水栓點
            self.packer = self.point_of_division()
            self.eumeter_pipe_tool_dlg_init()
            self.eumeter_pipe_tool_dlg.show()
        else:
            QMessageBox.information(self.iface.mainWindow(), u'新增水表', u'場所代碼 或 圖框編碼 取得失敗')
            # 清除畫線
            if self.rubberband.numberOfVertices():
                self.rubberband.reset()
            # 清除畫點
            if self.vertex_band.numberOfVertices():
                self.vertex_band.reset()
                
    
    # 求分點座標
    def point_of_division(self):
        #print 'point_of_division'
        self.points1_x = self.points[-1].x()
        self.points1_y = self.points[-1].y()

        #print self.points1_x
        #print self.points1_y
        self.points2_x = self.points[-2].x()
        self.points2_y = self.points[-2].y()
        #print self.points2_x
        #print self.points2_y

    
        dist = math.hypot(self.points1_x - self.points2_x, self.points1_y - self.points2_y)
        
        if dist > 2:
            dist_diff = 1.0
        else:
            dist_diff = dist * 0.3
        #print 'dist : ', dist
        #print 'dist_diff : ', dist_diff
        m = dist - dist_diff
        px = ((m * self.points1_x) + (dist_diff * self.points2_x)) / dist
        py = ((m * self.points1_y) + (dist_diff * self.points2_y)) / dist
        #print px
        #print py
        return QgsPoint(px, py)

    
    # 取得 識別碼
    def get_serial_number(self):
        #print 'get_serial_number'

        db_conn = self.get_db_connection()

        # 目前識別碼最大的序號
        serial_number_max = 0
        # 記錄跳號
        serial_number_jump = 0
        # 查詢 unific_id 之字串，由區處編號 + 索引圖碼 + 類別碼 + 種類 + 規格 + 序號
        unific_id = self.unitcode + self.frame_no + u'05' + self.type_id + u'0' + u'%'
        #print unific_id
        # 查詢目前識別碼最大的序號
        #query_string = u'SELECT substring(unific_id, 20, 3) FROM pipe WHERE unific_id LIKE \'{}\' ORDER BY substring(unific_id, 20, 3) DESC LIMIT 1'.format(unific_id)
        query_string = u'SELECT substring(unific_id, 20, 5) FROM eumeter WHERE unific_id LIKE \'{}\' ORDER BY substring(unific_id, 20, 5) DESC LIMIT 1'.format(unific_id)
        #print query_string
        query = db_conn.exec_(query_string)
        if query.isActive():
            # 當 query 有資料時，代表有記錄，若無記錄 serial_number_max 維持 0
            while query.next():
                serial_number_max = int(query.value(0))

        # 資料表欄位已有序號時，該 索引圖框 已有資料了
        if serial_number_max > 0:
            # 要新增的 識別碼 的序號
            serial_number = 0
            # 查詢目前所有的序號，從小到大檢視是否有 跳號
    #			query_string = u'SELECT substring(unific_id, 20, 3) FROM pipe WHERE unific_id LIKE \'{}\' ORDER BY substring(unific_id, 20, 3) ASC'.format(unific_id)
            query_string = u'SELECT substring(unific_id, 20, 5) FROM eumeter WHERE unific_id LIKE \'{}\' ORDER BY substring(unific_id, 20, 5) ASC'.format(unific_id)
            #print query_string
            query = db_conn.exec_(query_string)
            
            if query.isActive():
                # 如果最大的序號 小於、等於 筆數資料，則要新增的序號 等於 現有最大序號加 1
                if serial_number_max <= query.size():
                    serial_number = serial_number_max + 1
                # 如果最大的序號 大於 筆數資料，代表中間存在 跳號
                else:
                    # 暫存 序號
                    i = 1
                    # 連續式 設定新增的序號 等於 現有最大序號加 1
                    serial_number = serial_number_max + 1
                    while query.next():
                        # 欄位的序號 - 暫存續號 大於 0，將 記錄跳號 設為 i
                        if (int(query.value(0)) - i) > 0:
                            serial_number_jump = i
                            break
                        i += 1
        # 代表 serial_number_max == 0，新增為該 索引圖框 第一筆資料
        else:
            serial_number = 1
        
        query.clear()
        db_conn.close()
        
        self.serial_number = unicode(serial_number)
        self.serial_number_jump = unicode(serial_number_jump)

        #print 'self.serial_number,', self.serial_number
        #print 'self.serial_number_jump,', self.serial_number_jump
        self.fill_unific_id()

    # 其它管種編碼 變更下拉選單
    def meter_mode_changed(self):
        #print 'other_mtr_changed : '
        self.type_id = self.eumeter_pipe_tool_dlg.ui.comboBox_meter_mode.currentText().split(', ')[0]
        
        tag = self.eumeter_pipe_tool_dlg.ui.comboBox_meter_mode.currentText().split(', ')[0]
        
        if tag == u'13mm':
            meter_tag = u'13'
            self.type_id = u'2'
        elif tag == u'20mm':
            meter_tag = u'20'
            self.type_id = u'3'
        elif tag == u'25mm':
            meter_tag = u'25'
            self.type_id = u'4'
        elif tag == u'40mm':
            meter_tag = u'40'
            self.type_id = u'5'
        elif tag == u'50mm':
            meter_tag = u'50'
            self.type_id = u'6'
        elif tag == u'80mm':
            meter_tag = u'80'
            self.type_id = u'7'
        else:
            meter_tag = u'M'
            self.type_id = u'8'
        self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_tag.setText(meter_tag)
        self.get_serial_number()

    # 將 識別碼 填入下拉選單
    def fill_unific_id(self):
        #print 'fill_unific_id'
        self.eumeter_pipe_tool_dlg.ui.comboBox_unific_id.clear()
        unific_id = u'連續式 ' + self.unitcode + self.frame_no + u'05' + self.type_id + u'0' + self.serial_number.zfill(5)
        self.eumeter_pipe_tool_dlg.ui.comboBox_unific_id.addItem(unific_id)
            
        if not self.serial_number_jump == u'0':
            unific_id2 = u'跳補式 ' + self.unitcode + self.frame_no + u'05' + self.type_id + u'0' + self.serial_number_jump.zfill(5)
            self.eumeter_pipe_tool_dlg.ui.comboBox_unific_id.addItem(unific_id2)


    # 新增水表鎖關線 - 欄位初始化
    def eumeter_pipe_tool_dlg_init(self):
        #print 'eumeter_pipe_tool_dlg_init'

        self.eumeter_pipe_tool_dlg.show()
        self.eumeter_pipe_tool_dlg.ui.comboBox_unific_id.clear()
        self.eumeter_pipe_tool_dlg.ui.comboBox_meter_mode.setCurrentIndex(-1)
        
        self.eumeter_pipe_tool_dlg.ui.lineEdit_water_no.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_yy.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_no.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_work_area.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_type.clear()

        self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_tag.clear()


        self.eumeter_pipe_tool_dlg.ui.lineEdit_master.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_loc_9mark.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_nine_mark_dsc.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_county_name.clear()

        self.eumeter_pipe_tool_dlg.ui.lineEdit_dist_name.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_vila_name.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_road.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_section.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_lane.clear()

        self.eumeter_pipe_tool_dlg.ui.lineEdit_alley.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_addr_no.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_floor.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_add_2a.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_cust_name.clear()

        self.eumeter_pipe_tool_dlg.ui.lineEdit_cstl_kind.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_kind_desc.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_acep_no.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_empl_date.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_upd_date.clear()

        self.eumeter_pipe_tool_dlg.ui.plainTextEdit_bh_loc.clear()

        # 設置文字輸入框 數字格式
        self.eumeter_pipe_tool_dlg.ui.lineEdit_rt_order1.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_rt_order2.clear()
        
        self.eumeter_pipe_tool_dlg.ui.lineEdit_coord_67x.clear()
        self.eumeter_pipe_tool_dlg.ui.lineEdit_coord_67y.clear()

        self.eumeter_pipe_tool_dlg.ui.lineEdit_coord_97x.setText("{:.3f}".format(self.points[1].x()))
        self.eumeter_pipe_tool_dlg.ui.lineEdit_coord_97y.setText("{:.3f}".format(self.points[1].y()))
        #print format(self.points[-1].x())


    # 新增水表鎖關線 - 儲存
    def add_eumeter_save(self):
        #print 'add_eumeter_save'
        if self.eumeter_pipe_tool_dlg.ui.lineEdit_water_no.text() == u'':
            QMessageBox.information(self.iface.mainWindow(), u'新增水表u', u'必填欄位「水號」請填入資料!')
            return

        db_conn = self.get_db_connection()
        eumeter_gid = None

        # 取得用戶水表最 大gid
        query_string = u'SELECT max(gid) FROM eumeter'
        query = db_conn.exec_(query_string)
        if query.isActive():
            while query.next():
                eumeter_gid = query.value(0)
        # 取得防水栓最大 gid
        query_string = u'SELECT max(gid) FROM packer'
        query = db_conn.exec_(query_string)
        if query.isActive():
            while query.next():
                packer_gid = query.value(0)
        # 取得分水鞍最大 gid
        quer_string = u'SELECT max(gid) FROM saddle'
        query = db_conn.exec_(query_string)
        if query.isActive():
            while query.next():
                saddle_gid = query.value(0)
        # 取得用戶外線最大 gid
        query_string = u'SELECT max(gid) FROM eupipe'
        query = db_conn.exec_(query_string)
        if query.isActive():
            while query.next():
                eupipe_gid = query.value(0)
        # 取得廠區最大gid
        query_string = u'SELECT * FROM work_unit'
        query = db_conn.exec_(query_string)
        if query.isActive():
            while query.next():
                unitcode = query.value(0)


        if eumeter_gid == None or \
            packer_gid == None or \
            saddle_gid == None or \
            eupipe_gid == None:
            QMessageBox.warning(self.iface.mainWindow(), u'新增水表', u'[gid]查詢失敗!')
            query.clear()
            db_conn.close()
            return

        # 處理 comboBox 的欄位
        unific_id = u"'" + self.eumeter_pipe_tool_dlg.ui.comboBox_unific_id.currentText().split(' ')[1] + u"'"
        meter_mode = u"'" + self.eumeter_pipe_tool_dlg.ui.comboBox_meter_mode.currentText().split(', ')[1] + u"'"

        # 處理文字 lineEdit
        water_no = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_water_no.text() + u"'"
        meter_yy = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_yy.text() + u"'"
        meter_no = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_no.text() + u"'"
        work_area = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_work_area.text() + u"'"
        meter_type = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_type.text() + u"'"

        meter_tag = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_tag.text() + u"'"
        master = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_master.text() + u"'"
        loc_9mark = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_loc_9mark.text() + u"'"
        nine_mark_dsc = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_nine_mark_dsc.text() + u"'"
        county_name = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_county_name.text() + u"'"

        dist_name = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_dist_name.text() + u"'"
        vila_name = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_vila_name.text() + u"'"
        road = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_road.text() + u"'"
        section = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_section.text() + u"'"
        lane = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_lane.text() + u"'"

        alley = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_alley.text() + u"'"
        addr_no = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_addr_no.text() + u"'"
        floor = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_floor.text() + u"'"
        add_2a = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_add_2a.text() + u"'"
        cust_name = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_cust_name.text() + u"'"

        cstl_kind = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_cstl_kind.text() + u"'"
        kind_desc = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_kind_desc.text() + u"'"
        acep_no = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_acep_no.text() + u"'"
        empl_date = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_empl_date.text() + u"'"
        upd_date = u"'" + self.eumeter_pipe_tool_dlg.ui.lineEdit_upd_date.text() + u"'"

        bh_loc = u"'" + self.eumeter_pipe_tool_dlg.ui.plainTextEdit_bh_loc.toPlainText() + u"'"

        # 處理數字 lineEdit ，避免 數字 欄位，以空值寫入 資料庫，型態不符所發生之錯誤
        if len(self.eumeter_pipe_tool_dlg.ui.lineEdit_rt_order1.text()) > 0:
            rt_order1 = int(self.eumeter_pipe_tool_dlg.ui.lineEdit_rt_order1.text())
        else:
            rt_order1 = 0

        if len(self.eumeter_pipe_tool_dlg.ui.lineEdit_rt_order2.text()) > 0:
            rt_order2 = int(self.eumeter_pipe_tool_dlg.ui.lineEdit_rt_order2.text())
        else:
            rt_order2 = 0

        if len(self.eumeter_pipe_tool_dlg.ui.lineEdit_coord_67x.text()) > 0:
            coord_67x = float(self.eumeter_pipe_tool_dlg.ui.lineEdit_coord_67x.text())
        else:
            coord_67x = 0.0

        if len(self.eumeter_pipe_tool_dlg.ui.lineEdit_coord_67y.text()) > 0:
            coord_67y = float(self.eumeter_pipe_tool_dlg.ui.lineEdit_coord_67y.text())
        else:
            coord_67y = 0.0

        if len(self.eumeter_pipe_tool_dlg.ui.lineEdit_coord_97x.text()) > 0:
            coord_97x = float(self.eumeter_pipe_tool_dlg.ui.lineEdit_coord_97x.text())
        else:
            coord_97x = 0.0

        if len(self.eumeter_pipe_tool_dlg.ui.lineEdit_coord_97y.text()) > 0:
            coord_97y = float(self.eumeter_pipe_tool_dlg.ui.lineEdit_coord_97y.text())
        else:
            coord_97y = 0.0

        eumeter_gid += 1
        packer_gid += 1
        saddle_gid += 1
        eupipe_gid += 1

        # 座標值轉換幾何座標
        # 水表
        eumeter_geom = self.vertex_band.getPoint(0).toString().replace(',', '')
        # 分水鞍
        packer_geom = self.packer.toString().replace(',', '')
        # 止水栓
        saddle_geom = self.rubberband.getPoint(0, 0).toString().replace(',', '')
        '''
        eupipe_geom = saddle_geom + ', ' + \
            self.rubberband.getPoint(0, 1).toString().replace(',', '') + ', ' + \
            self.rubberband.getPoint(0, 2).toString().replace(',', '') + ', ' + \
            self.rubberband.getPoint(0, 3).toString().replace(',', '') + ', ' + \
            self.rubberband.getPoint(0, 4).toString().replace(',', '') + ', ' + \
            self.rubberband.getPoint(0, 5).toString().replace(',', '') + ', ' + \
            eumeter_geom
        '''
        # 用戶外線
        eupipe_geom = ''
        for p in self.points:
            eupipe_geom += str(p.x()) + ' ' + str(p.y()) + ','
        print eupipe_geom
        '''
        # 分水鞍 角度
        saddle_angle = round(self.rubberband.getPoint(0, 0).azimuth(self.rubberband.getPoint(0, 1)), 2)
        if saddle_angle < 0:
            saddle_angle += 360.00
        
        # 止水栓 角度
        pack_angle = round(self.rubberband.getPoint(0, 0).azimuth(self.rubberband.getPoint(0, 1)), 2)
        if pack_angle < 0:
            pack_angle += 360.00
        '''
        # 分水鞍 角度
        saddle_angle = round(self.points[0].azimuth(self.points[1]), 2)
        if saddle_angle < 0:
            saddle_angle += 360.00
        # 止水栓 角度
        pack_angle = round(self.points[-1].azimuth(self.points[-2]), 2)
        if pack_angle < 0:
            pack_angle += 360.00



        query_string = u"INSERT INTO eumeter (gid, unific_id, meter_mode, water_no, meter_yy, meter_no, work_area, " \
            u"meter_type, meter_tag, master, loc_9mark, nine_mark_dsc, county_name, dist_name, vila_name, road, " \
            u"section, lane, alley, addr_no, floor, add_2a, cust_name, cstl_kind, kind_desc, acep_no, empl_date, " \
            u"upd_date, bh_loc, rt_order1, rt_order2, coord_67x, coord_67y, coord_97x, coord_97y, the_geom) " \
            u"VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, " \
            u"{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, ST_GeomFromText(\'POINT({})\', 4326)); " \
            u"INSERT INTO packer (gid, angle, the_geom) VALUES ({}, {}, ST_GeomFromText(\'POINT({})\', 4326)); " \
            u"INSERT INTO saddle (gid, angle, the_geom) VALUES ({}, {}, ST_GeomFromText(\'POINT({})\', 4326)); " \
            u"INSERT INTO eupipe (gid, system_id, water_no, admin_unit, pipe_unit, pipe_long, trans_sub, the_geom) " \
            u"VALUES ({}, '8030101', {}, '{}', '0', '1', '自來水', ST_GeomFromText(\'MULTILINESTRING(({}))\', 4326)); " \
            u"".format(eumeter_gid, unific_id, meter_mode, water_no, meter_yy, meter_no, work_area, meter_type, meter_tag, 
                master, loc_9mark, nine_mark_dsc, county_name, dist_name, vila_name, road, section, lane, alley, addr_no, 
                floor, add_2a, cust_name, cstl_kind, kind_desc, acep_no, empl_date, upd_date, bh_loc, rt_order1, rt_order2, 
                coord_67x, coord_67y, coord_97x, coord_97y, eumeter_geom, packer_gid, pack_angle, packer_geom, saddle_gid, saddle_angle, saddle_geom, 
                eupipe_gid, water_no, unitcode, eupipe_geom[:-1])
        #print query_string
        query = db_conn.exec_(query_string)
        
        if query.isActive():
            self.eumeter_pipe_tool_dlg.close()
            QMessageBox.information(self.iface.mainWindow(), u'新增水表', u'資料庫寫入完成!')
            if self.rubberband.numberOfVertices():
                self.rubberband.reset()
            if self.vertex_band.numberOfVertices():
                self.vertex_band.reset()
            self.iface.mapCanvas().refreshAllLayers()
        else:
            self.eumeter_pipe_tool_dlg.close()
            QMessageBox.warning(self.iface.mainWindow(), u'新增水表', u'資料庫寫入失敗!')
            if self.rubberband.numberOfVertices():
                self.rubberband.reset()
            if self.vertex_band.numberOfVertices():
                self.vertex_band.reset()
            self.iface.mapCanvas().refreshAllLayers()
        query.clear()
        db_conn.close()

    # 新增水表鎖關線 - 對話框關閉
    def add_eumeter_close(self):
        #print 'add_eumeter_close'

        if self.rubberband.numberOfVertices():
            self.rubberband.reset()

        if self.vertex_band.numberOfVertices():
            self.vertex_band.reset()

        #self.iface.actionPan().trigger()
        self.eumeter_pipe_tool_dlg.close()


    # 檢查整數欄位
    def is_int_try(self, str):
        try:
            int(str)
            return True
        except ValueError:
            return False

    # 新增水表 取得水籍資料
    def get_eum_k(self):
        #print 'get_eum_k'
        water_no = self.eumeter_pipe_tool_dlg.ui.lineEdit_water_no.text()
        if len(water_no) > 0:
            db_conn = self.get_db_connection()
            query_string = u"SELECT * FROM eum_k WHERE water_no LIKE '{}' ORDER BY gid DESC LIMIT 1".format(water_no)
            #print query_string
            query = db_conn.exec_(query_string)
            #select * from eum_k where water_no like '47654120000' order by gid desc
            #select count(water_no), water_no from eum_k group by water_no order by count
        
            # 用戶水表
            if query.isActive():
                #print 'query.size() : ', query.size()
                if query.size() > 0:
                    while query.next():
                        if query.value(4) == None:
                            self.eumeter_pipe_tool_dlg.ui.comboBox_meter_mode.setCurrentIndex(0)
                        else:
                            if self.is_int_try(query.value(4)):
                                meter_mode = int(query.value(4))
                                if meter_mode >= 2:
                                    self.eumeter_pipe_tool_dlg.ui.comboBox_meter_mode.setCurrentIndex(int(query.value(4))-2)
                                else:
                                    self.eumeter_pipe_tool_dlg.ui.comboBox_meter_mode.setCurrentIndex(0)
                            else:
                                self.eumeter_pipe_tool_dlg.ui.comboBox_meter_mode.setCurrentIndex(0)
                        if query.value(1) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_work_area.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_work_area.setText(query.value(1))
                        if query.value(3) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_yy.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_yy.setText(query.value(3))
                        if query.value(5) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_no.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_no.setText(query.value(5))
                        if query.value(6) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_type.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_type.setText(query.value(6))
                        if query.value(7) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_tag.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_meter_tag.setText(query.value(7))
                        if query.value(8) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_master.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_master.setText(query.value(8))
                        if query.value(9) == None:
                            self.eumeter_pipe_tool_dlg.ui.plainTextEdit_bh_loc.setPlainText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.plainTextEdit_bh_loc.setPlainText(query.value(9))
                        if query.value(10) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_county_name.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_county_name.setText(query.value(10))
                        if query.value(11) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_dist_name.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_dist_name.setText(query.value(11))
                        if query.value(12) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_vila_name.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_vila_name.setText(query.value(12))
                        if query.value(13) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_road.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_road.setText(query.value(13))
                        if query.value(14) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_section.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_section.setText(query.value(14))
                        if query.value(15) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_lane.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_lane.setText(query.value(15))
                        if query.value(16) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_alley.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_alley.setText(query.value(16))
                        if query.value(17) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_addr_no.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_addr_no.setText(query.value(17))
                        if query.value(18) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_floor.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_floor.setText(query.value(18))
                        if query.value(19) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_add_2a.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_add_2a.setText(query.value(19))
                        if query.value(20) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_cust_name.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_cust_name.setText(query.value(20))
                        if query.value(21) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_cstl_kind.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_cstl_kind.setText(query.value(21))
                        if query.value(22) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_kind_desc.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_kind_desc.setText(query.value(22))
                        if query.value(23) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_acep_no.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_acep_no.setText(query.value(23))
                        if query.value(24) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_empl_date.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_empl_date.setText(query.value(24))
                        if query.value(25) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_upd_date.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_upd_date.setText(query.value(25))
                        if query.value(26) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_rt_order1.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_rt_order1.setText(unicode(int(query.value(26))))
                        if query.value(27) == None:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_rt_order2.setText(u'')
                        else:
                            self.eumeter_pipe_tool_dlg.ui.lineEdit_rt_order2.setText(unicode(int(query.value(27))))
                else:
                    QMessageBox.information(self.iface.mainWindow(), u'新增水表', u'該水號查無資料!')
            else:
                QMessageBox.information(self.iface.mainWindow(), u'新增水表', u'「水籍資料表」查詢失敗!')
        else:
            QMessageBox.information(self.iface.mainWindow(), u'新增水表', u'「水號」欄位，請填入資料!')

    # plainTextEdit 文字變動時的 SLOT, 控制文字長度
    def bh_loc_changed(self, max_length):
        #print 'bh_loc_changed'
        plain_text_edit = self.eumeter_pipe_tool_dlg.ui.plainTextEdit_bh_loc
        current_length = len(plain_text_edit.toPlainText())
        # 判斷目前文字長度 是否 大於 最大長度
        if current_length > max_length:
            # 如果大於 最大長度，則將文字設為，目前文字資料前 max_length-1 的長度
            plain_text_edit.setPlainText(plain_text_edit.toPlainText()[0:199])
            plain_text_edit.moveCursor(QTextCursor.End)
            QMessageBox.information(self.eumeter_pipe_tool_dlg, u'分表排列', u'輸入文字長度大於資料庫欄位長度!')
            plain_text_edit.setFocus()
    
    # 新增用戶管線 - 啟動點
    def add_eupip_snap_init(self):
        #print 'add_eupip_snap_init'
        db_conn = self.get_db_connection()
        query_string = u'SELECT * FROM work_unit'
        query = db_conn.exec_(query_string)

        if query.isActive():
            while query.next():
                self.unitcode = query.value(0)
        self.get_unitcode()
        if len(self.unitcode) > 0:
            if self.layer_check(u'pipe'):
                self.status = 2
                layer = self.iface.activeLayer()
                self.editing = layer.isEditable()
                
                if not self.editing:
                    self.iface.actionToggleEditing().trigger()
                self.iface.mapCanvas().setMapTool(self.draw_eupipe_snap)
                self.action_add_eupipe.setChecked(True)
                QObject.connect(self.draw_eupipe_snap, SIGNAL("drawdown"), self.eupipe_geom)
            else:
                QMessageBox.information(self.iface.mainWindow(), u'新增用戶外線', u'管線 圖層尚未開啟!')
        else:
            QMessageBox.information(self.iface.mainWindow(), u'取得廠所代碼', u'廠所代碼不存在!')

    # 新增用戶外線 - 鎖管線
    def eupipe_geom(self, geom, frame_no):
        #print'eupipe_geom'


        reply = QMessageBox.information(self.iface.mainWindow(), u'新增用戶外線', u'確認新增「用戶外線圖徵」! (取消則重新繪製)',
            u'確認', u'取消')
        # 確認 = 0， 取消 = 1

        if reply:
            self.draw_eupipe.activate()

        else:
            self.iface.actionPan().trigger()
            self.frame_no = frame_no
            self.geom = geom
            self.points = geom.asPolyline()
            #print self.points
            points_xy = format(self.points[1].x()) + u' ' + format(self.points[1].y())
            self.points_xy = points_xy
            #print '尾端座標 : ' + self.points_xy
            #print u'確認幾何圖形 : ', self.points
            
            # 畫線座標位置
            self.rubberband.setToGeometry(QgsGeometry.fromPolyline(self.points), None)
            # 畫點座標位置
            self.vertex_band.setToGeometry(QgsGeometry.fromPoint(self.points[-1]), None)
            #self.vertex_band.setToGeometry(QgsGeometry.fromPoint(self.points[0]), None)

            self.eumeter_eupipe_tool_dlg_init()
            self.eumeter_eupipe_tool_dlg.show()

    # 新增用戶外線 - 欄位初始化
    def eumeter_eupipe_tool_dlg_init(self):
        #print 'eumeter_eupipe_tool_dlg_init'

        self.eumeter_eupipe_tool_dlg.ui.comboBox_pipe_unit.setCurrentIndex(0)
        self.eumeter_eupipe_tool_dlg.ui.comboBox_oper_phase.setCurrentIndex(0)
        self.eumeter_eupipe_tool_dlg.ui.comboBox_pipe_type.setCurrentIndex(0)
        self.eumeter_eupipe_tool_dlg.ui.comboBox_pipe_status.setCurrentIndex(0)
        self.eumeter_eupipe_tool_dlg.ui.comboBox_use_stat.setCurrentIndex(0)
        self.eumeter_eupipe_tool_dlg.ui.comboBox_pipe_mode.setCurrentIndex(0)

        self.eumeter_eupipe_tool_dlg.ui.lineEdit_water_no.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_unific_id.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_pipe_start.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_pipe_end.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_unific_up.clear()

        self.eumeter_eupipe_tool_dlg.ui.lineEdit_admin_unit.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_unific_pipe.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_pipe_size.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_pipe_high.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_pipe_long.clear()
        
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_pipe_mtr.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_min_depth.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_max_depth.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_start_depth.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_end_depth.clear()

        self.eumeter_eupipe_tool_dlg.ui.lineEdit_saddle_dist.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_dist_ref.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_bury_date.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_pipe_length.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_apply_code.clear()

        self.eumeter_eupipe_tool_dlg.ui.lineEdit_trans_sub.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_geolength.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_const_unit.clear()

        self.eumeter_eupipe_tool_dlg.ui.plainTextEdit_pipe_doc.clear()
        self.eumeter_eupipe_tool_dlg.ui.plainTextEdit_remark.clear()

        self.eumeter_eupipe_tool_dlg.ui.lineEdit_coord_97xs.setText("{:.3f}".format(self.points[0].x()))
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_coord_97ys.setText("{:.3f}".format(self.points[0].y()))
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_coord_97xt.setText("{:.3f}".format(self.points[1].x()))
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_coord_97yt.setText("{:.3f}".format(self.points[1].y()))
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_coord_97zs.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_coord_97zt.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_depth_s.clear()
        self.eumeter_eupipe_tool_dlg.ui.lineEdit_depth_e.clear()

    # 用戶外線 - 儲存
    def add_eupipe_snap_save(self):
        #printprint 'add_eupipe_snap_save'
        '''
        if self.eumeter_eupipe_tool_dlg.ui.lineEdit_water_no.text() == u'':
            QMessageBox.information(self.iface.mainWindow(), u'新增用戶外線', u'必填欄位「水號」請填入資料!')
            return
        '''
        query_string = u'SELECT max(gid) FROM eupipe'
        query = db_conn.exec_(query_string)

        if query.isActive():
            while query.next():
                eupipe_gid = query.value(0)
        query.clear()
        db_conn.close()
        return

        
        # 下拉選單 comboBox
        pipe_unit = u"'" + self.eumeter_eupipe_tool_dlg.comboBox_pipe_unit.currentText().split(' ')[0] + u"'"
        oper_phase = u"'" + self.eumeter_eupipe_tool_dlg.comboBox_oper_phase.currentText().split(' ')[0] + u"'"
        pipe_type = u"'" + self.eumeter_eupipe_tool_dlg.comboBox_pipe_type.currentText().split(' ')[0] + u"'"
        pipe_status = u"'" + self.eumeter_eupipe_tool_dlg.comboBox_type.currentText().split(' ')[0] + u"'"
        use_stat = u"'" + self.eumeter_eupipe_tool_dlg.comboBox_use_stat.currentText().split(' ')[0] + u"'"
        pipe_mode = u"'" + self.eumeter_eupipe_tool_dlg.comboBox_pipe_mode.currentText().split(' ')[0] + u"'"

        # 處理文字 lineEdit
        water_no = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_water_no.text() + u"'"
        unific_id = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_unific_id.text() + u"'"
        pipe_start = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_pipe_start.text() + u"'"
        pipe_end = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_pipe_end.text() + u"'"
        unific_up = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_unific_up.text() + u"'"
        admin_unit = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_admin_unit.text() + u"'"
        unific_pipe = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_unific_pipe.text() + u"'"
        pipe_mtr = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_pipe_mtr.text() + u"'"
        dist_ref = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_dist_ref.text() + u"'"
        bury_date = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_bury_date.text() + u"'"
        apply_code = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_apply_code.text() + u"'"
        trans_sub = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_trans_sub.text() + u"'"
        const_unit = u"'" + self.eumeter_eupipe_tool_dlg.lineEdit_const_unit.text() + u"'"
        pipe_doc = u"'" + self.eumeter_eupipe_tool_dlg.plainTextEdit_pipe_doc.toPlainText() + u"'"
        remark = u"'" + self.eumeter_eupipe_tool_dlg.plainTextEdit_remark.toPlainText() + u"'"

        # 處理數字 lineEdit
        if len(self.eumeter_eupipe_tool_dlg.lineEdit_pipe_size.text()) >= 1:
            pipe_size = int(self.eumeter_eupipe_tool_dlg.lineEdit_pipe_size.text())
        else:
            pipe_size = 0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_pipe_high.text()) >= 1:
            pipe_high = int(self.eumeter_eupipe_tool_dlg.lineEdit_pipe_high.text())
        else:
            pipe_high = 0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_pipe_long.text()) >= 1:
            pipe_long = int(self.eumeter_eupipe_tool_dlg.lineEdit_long.text())
        else:
            pipe_long = 0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_min_depth.text()) >= 1:
            min_depth = int(self.eumeter_eupipe_tool_dlg.lineEdit_min_depth.text())
        else: 
            min_depth = 0.0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_max_depth.text()) >= 1:
            max_depth = int(self.eumeter_eupipe_tool_dlg.lineEdit_max_depth.text())
        else:
            max_depth = 0.0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_start_depth.text()) >= 1:
            start_depth = int(self.eumeter_eupipe_tool_dlg.lineEdit_start_depth.text())
        else:
            start_depth = 0.0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_end_depth.text()) >= 1:
            end_depth = int(self.eumeter_eupipe_tool_dlg.lineEdit_end_depth.text())
        else:
            start_depth = 0.0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_saddle_dist.text()) >= 1:
            saddle_dist = int(self.eumeter_eupipe_tool_dlg.lineEdit_saddle_dist.text())
        else:
            saddle_dist = 0.0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_pipe_length.text()) >= 1:
            pipe_length = int(self.eumeter_eupipe_tool_dlg.lineEdit_pipe_length.text())
        else:
            pipe_length = 0.0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_geomlength.text()) >= 1:
            geomlength = int(self.eumeter_eupipe_tool_dlg.lineEdit_geomlength.text())
        else:
            geomlength = 0.0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_coord_97xs.text()) >= 1:
            coord_97xs = int(self.eumeter_eupipe_tool_dlg.lineEdit_coord_97xs.text())
        else:
            coord_97xs = 0.0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_coord_97zs.text()) >= 1:
            coord_97xs = int(self.eumeter_eupipe_tool_dlg.lineEdit_coord_97zs.text())
        else:
            coord_97xs = 0.0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_coord_97xt.text()) >= 1:
            coord_97xt = int(self.eumeter_eupipe_tool_dlg.lineEdit_coord_97xt.text())
        else:
            coord_97xt = 0.0
            
        if len(self.eumeter_eupipe_tool_dlg.lineEdit_coord_97yt.text()) >= 1:
            coord_97yt = int(self.eumeter_eupipe_tool_dlg.lineEdit_coord_97yt.text())
        else:
            coord_97yt = 0.0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_coord_97zt.text()) >= 1:
            coord_97zt = int(self.eumeter_eupipe_tool_dlg.lineEdit_coord_97zt.text())
        else:
            coord_97zt = 0.0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_depth_s.text()) >= 1:
            start_depth = int(self.eumeter_eupipe_tool_dlg.lineEdit_depth_s.text())
        else:
            start_depth = 0.0

        if len(self.eumeter_eupipe_tool_dlg.lineEdit_depth_e.text()) >= 1:
            end_depth = int(self.eumeter_eupipe_tool_dlg.lineEdit_depth_e.text())
        else:
            end_deoth = 0.0
        
        eupipe_gid += 1

        db_conn = self.get_db_connection()
        query_string = u'INSERT INTO eupipe (gid, system_id, unific_id, pipe_start, pipe_end, unific_up, ' \
            u'admin_unit, unific_pipe, pipe_size, pipe_high, pipe_unit, pipe_long, pipe_mtr, ' \
            u'min_depth, max_depth, start_depth, end_depth, saddle_dist, dist_ref, bury_date, ' \
            u'oper_phase, pipe_length, pipe_type, pipe_status, const_unit, apply_code, water_no, ' \
            u'pipe_doc, trans_sub, use_stat, remark, geolength, coord_97xs, coord_97ys, ' \
            u'coord_97xt, coord_97yt, coord_97zs, coord_97zt, pipe_mode) '\
            u'VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, ' \
            u'{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, ST_GeomFromText(\'POINT({}\', 4326)); '\
            u''.format(eupipe_gid, '8030107', unific_id, pipe_start, pipe_end, unific_up,
                admin_unit, unific_pipe, pipe_size, pipe_high, pipe_unit, pipe_long, pipe_mtr,
                min_depth, max_depth, start_depth, end_depth, saddle_dist, dist_ref, bury_date,
                oper_phase, pipe_length, pipe_type, pipe_status, const_unit, apply_code, water_no,
                pipe_doc, trans_sub, use_stat, remark, geolength, coord_97xs, coord_97ys,
                coord_97xt, coord_97yt, coord_97zs, coord_97zt, pipe_mode)
        #print query_string
        query = db_conn.exec_(query_string)


        if query.isActive():
            QMessageBox.information(self.iface.mainWindow(), u'新增用戶外線', u'新增用戶外線成功!')
            self.iface.mapCanvas().refreshAllLayers()
        else:
            QMessageBox.information(self.iface.mainWindow(), u'新增用戶外線', u'新增用戶外線失敗!')
            if self.rubberband.numberOfVertices():
                self.rubberband.reset()

            if self.vertex_band.numberOfVertices():
                self.vertex_band.reset()

        query.clear()
        db_conn.close()
        self.eumeter_eupipe_tool_dlg.close()

    # 用戶外線 - 對話框關閉
    def add_eupipe_snap_close(self):
        #print 'add_eupipe_snap_close'
        if self.rubberband.numberOfVertices():
            self.rubberband.reset()

        if self.vertex_band.numberOfVertices():
            self.vertex_band.reset()

        self.eumeter_eupipe_tool_dlg.close()

    # edit_pipe_dlg plainTextEdit 文字變動時的 SLOT, 控制文字長度
    def text_changed_eu(self, max_length, plain_name):
        #print 'text_changed_eu'
        if plain_name == 'pipe_doc':
            plain_text_edit = self.eumeter_eupipe_tool_dlg.ui.plainTextEdit_pipe_doc
        elif plain_name == 'remark':
            plain_text_edit = self.eumeter_eupipe_tool_dlg.ui.plainTextEdit_remark
        
        current_length = len(plain_text_edit.toPlainText())
        # 判斷目前文字長度 是否 大於 最大長度
        if current_length > max_length:
            if max_length == 100:
                plain_text_edit.setPlainText(plain_text_edit.toPlainText()[0:99])
                QMessageBox.information(self.eumeter_eupipe_tool_dlg, u'超連結', u'輸入文字長度大於資料庫欄位長度!')
            else:
                plain_text_edit.setPlainText(plain_text_edit.toPlainText()[0:199])
                QMessageBox.information(self.eumeter_eupipe_tool_dlg, u'備註說明', u'輸入文字長度大於資料庫欄位長度!')
            plain_text_edit.moveCursor(QTextCursor.End)
            plain_text_edit.setFocus()

    def deactivate(self):
        QObject.disconnect(self.draw_pipe_snap, SIGNAL('drawdown'), self.add_eumeter_snap_geom)
        self.action_add_pipe_snap.setChecked(False)
        QObject.disconnect(self.draw_eupipe_snap, SIGNAL('drawdown'), self.eupipe_geom)
        self.action_add_eupipe.setChecked(False)

    # 取得區碼
    def get_unitcode(self):
        db_conn = self.get_db_connection()
        query_string = u'SELECT * FROM work_unit'
        query = db_conn.exec_(query_string)

        if query.isActive():
            while query.next():
                self.unitcode = query.value(0)
        else:
            QMessageBox.information(self.iface.mainWindow(), u'取得廠所代碼', u'資料庫連線錯誤!')
            self.unitcode = u''

        query.clear()
        db_conn.close()

    # 新增水表 取得 廠所代碼 與 圖框編碼
    def get_code_no(self, points_xy):
        #print 'get_code_no'
        db_conn = self.get_db_connection()
        query_string = u'SELECT * FROM work_unit'
        query = db_conn.exec_(query_string)

        if query.isActive():
            while query.next():
                self.unitcode = query.value(0)

        query_string = u'SELECT no FROM frame WHERE ST_Contains(the_geom, ST_GeometryFromText(\'POINT({})\', 4326))'.format(points_xy)
        query = db_conn.exec_(query_string)

        if query.isActive():
            while query.next():
                self.frame_no = query.value(0)

        #print u'self.unitcode', self.unitcode
        #print u'self.frame_no', self.frame_no
        # 關閉資料庫連線
        query.clear()
        db_conn.close()

    # 檢查參數圖層是否開啟，若開啟則將該圖層設為作用中的圖層
    def layer_check(self, layer_name):
        layerList = QgsMapLayerRegistry.instance().mapLayersByName(layer_name)
        if layerList:
            self.iface.setActiveLayer(layerList[0])
            if not self.iface.legendInterface().isLayerVisible(layerList[0]):
                self.iface.legendInterface().setLayerVisible(layerList[0], True)
            return True
        else:
            return False

    # 開啟與 資料庫 的連線
    def get_db_connection(self):

        layer = self.canvas.layer(0)
        provider = layer.dataProvider()
        if provider.name() == 'postgres':
            uri = QgsDataSourceURI(provider.dataSourceUri())
            pg_conn = QSqlDatabase.addDatabase('QPSQL')
            if pg_conn.isValid():
                pg_conn.setHostName(uri.host())
                pg_conn.setDatabaseName(uri.database())
                pg_conn.setPort(int(uri.port()))
                pg_conn.setUserName(uri.username())
                pg_conn.setPassword(uri.password())

            if not pg_conn.open():
                err = pg_conn.lastError()
                print err.driverText()
            else:
                return pg_conn