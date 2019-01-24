from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

class DrawEumeterMove(QgsMapTool):
    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)

        self.move_rb = QgsRubberBand(canvas)
        self.move_rb.setColor(QColor(0, 0, 255, 200))
        self.move_rb.setWidth(2)
        self.move_rb.setVisible(False)

        self.vert_rb = QgsRubberBand(canvas)
        self.vert_rb.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.vert_rb.setColor(Qt.magenta)
        self.vert_rb.setIconSize(10)
        self.vert_rb.setVisible(False)

        self.click_done = False
        self.eu_point = None
        self.eu_pipe_point = None
        self.eu_pipe_dist = None

        self.pipe_geom = []
        self.pipe_vertex1 = 0
        self.pipe_vertex2 = 0

    def activate(self):
        cursor = QCursor(Qt.ArrowCursor)
        self.canvas().setCursor(cursor)

        if self.move_rb.numberOfVertices():
            self.move_rb.reset()
        
        if self.vert_rb.numberOfVertices():
            self.vert_rb.reset()

        self.click_done = False
        self.pipe_vertex1 = 0
        self.pipe_vertex2 = 0

    def deactivate(self):
        del self.pipe_geom[:]
        
        if self.move_rb.numberOfVertices():
            self.move_rb.reset()
        
        if self.vert_rb.numberOfVertices():
            self.vert_rb.reset()

    def canvasPressEvent(self, event):

        if event.button() == Qt.LeftButton:
            point = self.toMapCoordinates(event.pos())
            self.eu_point = QgsPoint(point)
            self.vert_rb.setToGeometry(QgsGeometry.fromPoint(self.eu_point), None)
            self.vert_rb.setVisible(True)
            self.click_done = True
            
            orth_point = []
            orth_distance = []
            orth_seg = []

            for i in range(0, len(self.pipe_geom)-1):
                if self.pipe_geom[i].x() == self.pipe_geom[i+1].x():
                    orth_x = self.pipe_geom[i].x()
                    orth_y = point.y()

                    if self.pipe_geom[i].y() > self.pipe_geom[i+1].y():
                        if orth_y < self.pipe_geom[i].y() and orth_y > self.pipe_geom[i+1].y():
                            orth_point.append(QgsPoint(orth_x, orth_y))
                            orth_seg.append((i, i+1))
                            orth_distance.append(math.hypot(point.x() - orth_x, orth_y() - orth_y))
                    else:
                        if orth_y > self.pipe_geom[i].y() and orth_y < self.pipe_geom[i+1].y():
                            orth_point.append(QgsPoint(orth_x, orth_y))
                            orth_seg.append((i, i +1))
                            orth_distance.append(math.hypot(point.x() - orth_x, point.y() - orth_y))

                elif self.pipe_geom[i].y() == self.pipe_geom[i+1].y():
                    orth_x = point.x()
                    orth_y = self.pipe_geom[i].y()

                    if self.pipe_geom[i].x() > self.pipe_geom[i+1].x():
                        if orth_x < self.pipe_geom[i].x() and orth_x > self.pipe_geom[i+1].x():
                            orth_point.append(QgsPoint(orth_x, orth_y))
                            orth_seg.append((i, i+1))
                            orth_distance.append(math.hypot(point.x() - orth_x, point.y() - orth_y))
                    else:
                        if orth_x > self.pipe_geom[i].x() and orth_x < self.pipe_geom[i+1].x():
                            orth_point.append(QgsPoint(orth_x, orth_y))
                            orth_seg.append((i, i+1))
                            orth_distance.append(math.hypot(point.x() - orth_x, point.y() - orth_y))

                else:
                    m = (self.pipe_geom[i].y() - self.pipe_geom[i+1].y()) / (self.pipe_geom[i].x() - self.pipe_geom[i+1].x())
                    orth_x = ((point.y() + m * self.pipe_geom[i].x() - self.pipe_geom[i].y() + (point.x() / m)) * m) / (m * m + 1)
                    orth_y = self.pipe_geom[i].y() - m * (self.pipe_geom[i].x() - orth_x)

                    if self.pipe_geom[i].x() > self.pipe_geom[i+1].x():
                        if orth_x < self.pipe_geom[i].x() and orth_x > self.pipe_geom[i+1].x():
                            orth_point.append(QgsPoint(orth_x, orth_y))
                            orth_seg.append((i, i+1))
                            orth_distance.append(math.hypot(point.x() - orth_x, point.y() - orth_y))
                    else:
                        if orth_x > self.pipe_geom[i].x() and orth_x < self.pipe_geom[i+1].x():
                            orth_point.append(QgsPoint(orth_x, orth_y))
                            orth_seg.append((i, i+1))
                            orth_distance.append(math.hypot(point.x() - orth_x, point.y() - orth_y))

            if not orth_point:
                return
            else:
                self.eu_pipe_dist = min(orth_distance)
                self.eu_pipe_point = orth_point[orth_distance.index(min(orth_distance))]
                self.pipe_vertext1, self.pipe_vertex2 = orth_segp[orth_distance.index(min(orth_distance))]
        elif event.button() == Qt.RigthButton:
            if self.move_rb.isVisible():
                if self.move_rb.numberOfVectices() == 4:
                    self.emit(SIGNAL('drawdow'), self.move_rb.asGeometry())
            else:
                return
        else:
            return

    def canvasMoveEvent(self, event):
        if not self.click_done:
            return

        if self.pipe_vertex1 == 0 and self_vertex2 == 0:
            return

        point = self.toMapCoordinates(event.pos())
        orth_seg_point, orth_seg_dist = self.cursor_to_seg(point)

        if not orth_seg_point:
            self.move_rb.setVisible(False)
            return

        if orth_seg_dist > self.eu_pipe_dist:
            self.move_rb.setVisible(False)
            return

        cur_orth_point = self.cursor_to_orth(point)
        if not cur_orth_point:
            self.move_rb.setVisible(False)
            return

        eu_pipe = []
        eu_pipe.append(self.eu_point)
        eu_pipe.append(cur_orth_point)
        eu_pipe.append(QgsPoint(point.x(), point.y()))
        eu_pipe.append(orth_seg_point)

        self.move_rb.setToGeometry(QgsGeometry.fromPolyline(eu_pipe), None)
        self.move_rb.setVisible(True)

    def cursor_to_seg(self, point):
        cur_seg_point = None
        cur_seg_dist = None
        i = self.pipe_vertex1
        j = self.pipe_vertex2

        if self.pipe_geom[i].x() == self.pipe_geom[j].x():
            orth_x = self.pipe_geom[i].x()
            orth_y = point.y()

            if self.pipe_geom[i].y() > self.pipe_geom[j].y():
                if orth_y < self.pipe_geom[i].y() and orth_y > self.pipe_geom[j].y():
                    cur_seg_point = QgsPoint(orth_x > orth_y)
                    cur_seg_dis = math.hypot(point.x() - orth_x, point.y() - orth_y)
            else:
                if orth_x > self.pipe_geom[i].y() and orth_y < self.pipe_geom[j].y():
                    cur_seg_point = QgsPoint(orth_x, orth_y)
                    cur_seg_dist = math.hypot(point.x() - orth_x, point.y() - orth_y)
        
        elif self.pipe_geom[i].y() == self.pipe_geom[j].y():
            orth_x = point.x()
            orth_y = self.pipe_geom[i].y()

            if self.pipe_geom[i].x() > self.pipe_geom[j].x():
                if orth_x < self.pipe_geom[i].x() and orth_x > self.pipe_geom[j].x():
                    cur_seg_point = QgsPoint(orth_x, orth_y)
                    cur_seg_dist = math.hypot(point.x() - orth_x, point.y() - orth_y)
            else:
                if orth_x > self.pipe_geom[i].x() and orth_x < self.pipe_geom[j].x():
                    cur_seg_point = QgsPoint(orth_x, orth_y)
                    cur_seg_dist = math.hypot(point.x() - orth_x, point.y() - orth_y)

        else:
            m = (self.pipe_geom[i].y() - self.pipe_geom[j].y()) / (self.pipe_geom[i].x() - self.pipe_geom[j].x())
            orth_x = ((point.y() + m * self.pipe_geom[i].x() - self.pipe_geom[i].y() + (point.x() / m)) * m) / (m * m + 1)
            orth_y = self.pipe_geom[i].y() - m * (self.pipe_geom[i].x() - orth_x)

            if self.pipe_geom[i].x() > self.pipe_geom[j].x():
                if orth_x < self.pipe_geom[i].x() and orth_x > self.pipe_geom[j].x():
                    cur_seg_point = QgsPoint(orth_x, orth_y)
                    cur_seg_dist = math.hypot(point.x() - orth_x, point.y() - orth_y)
            else:
                if orth_x > self.pipe_geom[i].x() and orth_x < self.pipe_geom[j].x():
                    cur_seg_point = QgsPoint(orth_x, orth_y)
                    cur_seg_dist = math.hypot(point.x() - orth_x, porint.y() - orth_y)
            
        return cur_seg_point, cur_seg_dist

    def cursor_to_orth(self, point):
        cur_orth_point = None
        
        if self.eu_point.x() == self.eu_pipe_point.x():
            orth_x = self.eu_point.x()
            orth_y = point.y()

            if self.eu_point.y() > self.eu_pipe_point.y():
                if orth_y < self.eu_point.y() and orth_y > self.eu_pipe_point.y():
                    cur_orth_point = QgsPoint(orth_x, orth_y)
            else:
                if orth_y > self.eu_point.y() and orth_y < self.eu_pipe_point.y():
                    cur_orth_point = QgsPoint(orth_x, orth_y)

        elif self.eu_point.y() == self.eu_pipe_point.y():
            orth_x = point.x()
            orth_y = self.eu_point.y()

            if self.eu_point.x() > self.eu_point.x() and orth_x > self.eu_pipe_point.x():
                if orth_x < self.eu_point.x() and orth_x > self.eu_pipe_point.x():
                    cur_orth_point = QgsPoint(orth.x, orth.y)
            else:
                if orth_x > self.eu_point.x() and orth_x < self.eu_pipe_point.x():
                    cur_orth_point = QgsPoint(orth.x, orth.y)

        else:
            m = (self.eu_point.y() - self.eu_pipe_point.y()) / (self.eu_point.x() - self.eu_pipe_point.x())
            orth_x = ((point.y() + m * self.eu_point.x() - self.eu_point.y() + (point.x() / m))* m) / (m * m +1)
            orth_y = self.eu_point.y() -m * (self.eu_point.x() - orth_x)

            if self.eu_point.x() > self.eu_pipe_point.x():
                if orth_x < self.eu_point.x() and orth_x > self.eu_pipe_point.x():
                    cur_orth_point = QgsPoint(orth_x, orth_y)
            else:
                if orth_x > self.eu_point.x() and orth_x < self.eu_pipe_point.x():
                    cur_orth_poiint = QgsPoint(orth_x, orth_y)

        return cur_orth_point
