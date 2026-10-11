#!/usr/bin/env python3
"""
Aging, Immortality & Lineage Simulator v2
Genetics · House Dynasties · Marriages · Random Events · Deep Lineage Rules
"""

import sys, random, math
from collections import defaultdict, deque
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QGroupBox, QGraphicsView,
    QGraphicsScene, QGraphicsItem, QGridLayout, QCheckBox,
    QTextEdit, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import (
    QBrush, QPen, QColor, QFont, QPainter, QRadialGradient, QPainterPath
)

NAMES = [
    "Aria","Liam","Zoe","Kai","Luna","Orion","Maya","Leo","Ivy","Finn",
    "Ella","Noah","Mila","Ezra","Lily","Oscar","Ruby","Jude","Sage","Wren",
    "Cleo","Atlas","Freya","Rex","Nova","Silas","Iris","Hugo","Eden","Felix",
    "Gaia","Axel","Nora","Soren","Hazel","Jasper","Olive","Luca","Willow","Kian",
    "Cael","Dune","Ember","Flint","Gemma","Hawk","Indie","Bram","Yara","Thane",
]
HOUSE_NAMES = [
    "Stormweaver","Nightbloom","Ironhold","Starfall","Dawnfire","Moonshadow",
    "Wintercrest","Sunblade","Frostborn","Thornwall","Redmoor","Goldwind",
    "Darkwater","Silverthorn","Emberheart","Skywatcher","Deeproot","Highgate",
]
HOUSE_COLORS = [
    QColor(231,76,60),QColor(46,204,113),QColor(52,152,219),QColor(155,89,182),
    QColor(241,196,15),QColor(230,126,34),QColor(26,188,156),QColor(236,112,99),
    QColor(88,214,141),QColor(133,193,233),QColor(187,143,206),QColor(247,220,111),
    QColor(245,176,65),QColor(115,198,182),QColor(210,180,222),QColor(174,214,241),
    QColor(245,183,177),QColor(169,223,191),
]
GEN_Y, SPACING_X, MAX_POP, CORPSE_FADE = 140, 65, 260, 50


class House:
    _idx = 0
    def __init__(self, name=None, color=None):
        n = HOUSE_NAMES[House._idx % len(HOUSE_NAMES)]
        c = HOUSE_COLORS[House._idx % len(HOUSE_COLORS)]
        House._idx += 1
        self.name = name or f"House {n}"
        self.color = color or c
        self.founder = None
        self.prestige = 0.0
        self.extinct = False
    def color_a(self, a=255):
        return QColor(self.color.red(), self.color.green(), self.color.blue(), a)


class Person:
    _ctr = 0
    def __init__(self, a1="i", a2="i", mother=None, father=None, house=None, gen=0):
        Person._ctr += 1
        self.id = Person._ctr
        self.name = random.choice(NAMES)
        self.age = 0.0
        self.is_alive = True
        self.death_age = None
        self.allele1, self.allele2 = a1, a2
        self.blood_type = self._blood()
        self.traits = {k: 0.5 for k in ("longevity","fertility","resilience","charisma")}
        self._inherit(mother, father)
        self.mother, self.father = mother, father
        self.children = []
        self.spouse = None
        self.generation = gen
        self.house = house
        self.max_age = self._max_age()
        self.repro_cd = random.uniform(5, 14)
        self.marry_cd = random.uniform(0, 4)
        self.born_year = 0
        self.x = self.y = self.target_x = self.target_y = 0.0
        self.node = None

    def _blood(self):
        if self.allele1 == "I" and self.allele2 == "I": return "immortal"
        if "I" in (self.allele1, self.allele2): return "carrier"
        return "mortal"

    def _inherit(self, m, f):
        for k in self.traits:
            vals = []
            if m: vals.append(m.traits[k])
            if f: vals.append(f.traits[k])
            avg = sum(vals)/len(vals) if vals else 0.5
            self.traits[k] = max(0.0, min(1.0, avg + random.gauss(0, 0.08)))

    def _max_age(self):
        if self.blood_type == "immortal": return float("inf")
        base = random.uniform(55, 95)
        if self.blood_type == "carrier":
            base *= 1.5 + self.traits["longevity"] * 0.7
        else:
            base *= 0.85 + self.traits["longevity"] * 0.5
        return base

    @property
    def is_immortal(self): return self.blood_type == "immortal"
    @property
    def is_carrier(self): return self.blood_type == "carrier"
    @property
    def is_widowed(self): return self.spouse is not None and not self.spouse.is_alive

    def allele_str(self):
        return "".join(sorted([self.allele1, self.allele2], reverse=True))

    def can_reproduce(self):
        return self.is_alive and 18 <= self.age <= 52 and self.repro_cd <= 0 and len(self.children) < 5

    def can_marry(self, other):
        if self is other or not self.is_alive or not other.is_alive: return False
        if self.spouse and self.spouse.is_alive: return False
        if other.spouse and other.spouse.is_alive: return False
        if self.marry_cd > 0 or other.marry_cd > 0: return False
        if abs(self.age - other.age) > 28: return False
        if abs(self.generation - other.generation) > 2: return False
        if self.age < 16 or other.age < 16: return False
        anc = self._ancestors(3)
        oanc = other._ancestors(3)
        if anc & oanc: return False
        if other.id in anc or self.id in oanc: return False
        return True

    def _ancestors(self, g=3):
        s, q = set(), deque([(self, 0)])
        while q:
            p, d = q.popleft()
            if d >= g: continue
            for pr in (p.mother, p.father):
                if pr: s.add(pr.id); q.append((pr, d+1))
        return s

    def all_ancestors(self):
        s, q = set(), deque([self])
        while q:
            p = q.popleft()
            for pr in (p.mother, p.father):
                if pr and pr.id not in s: s.add(pr.id); q.append(pr)
        return s

    def all_descendants(self):
        s, q = set(), deque([self])
        while q:
            p = q.popleft()
            for c in p.children:
                if c.id not in s: s.add(c.id); q.append(c)
        return s

    def tick(self, dt):
        self.age += dt
        if self.repro_cd > 0: self.repro_cd -= dt
        if self.marry_cd > 0: self.marry_cd -= dt
        if self.blood_type != "immortal" and self.age >= self.max_age:
            self.is_alive = False; self.death_age = self.age

    def color(self):
        if not self.is_alive: return QColor(90,90,90,45)
        if self.is_immortal:
            p = 0.5+0.5*math.sin(self.age*0.1)
            return QColor(int(200+55*p),int(175+40*p),int(20+30*p),240)
        if self.is_carrier:
            p = 0.5+0.5*math.sin(self.age*0.07)
            return QColor(int(130+50*p),int(165+45*p),int(215+40*p),230)
        if self.age < 15: return QColor(100,225,100,225)
        if self.age < 30:
            t = (self.age-15)/15
            return QColor(int(100*(1-t)+60*t),int(225*(1-t)+185*t),int(100*(1-t)+230*t),225)
        if self.age < 55:
            t = (self.age-30)/25
            return QColor(int(60*(1-t)+140*t),int(185*(1-t)+120*t),int(230*(1-t)+210*t),225)
        t = min(1.0,(self.age-55)/40)
        return QColor(int(140*(1-t)+165*t),int(120*(1-t)+135*t),int(210*(1-t)+155*t),max(130,int(225-t*80)))

    def radius(self):
        if not self.is_alive: return 6
        if self.age < 15: return 6+self.age*0.35
        return 15 if self.is_immortal else (14 if self.is_carrier else 13)


class GameEvent:
    PLAGUE="plague"; GOLDEN="golden"; CATASTROPHE="catastrophe"; AWAKEN="awaken"
    BLESS="bless"; MIGRATE="migrate"; FAMINE="famine"; RENAISSANCE="renaissance"
    ICONS = {PLAGUE:"☠",GOLDEN:"✦",CATASTROPHE:"⚡",AWAKEN:"✨",BLESS:"🕊",MIGRATE:"🚶",FAMINE:"🌾",RENAISSANCE:"🎨"}
    def __init__(self, etype, year, desc, dur=0, mag=1.0):
        self.etype, self.year, self.desc = etype, year, desc
        self.duration, self.magnitude, self.remaining = dur, mag, dur
    @property
    def icon(self): return self.ICONS.get(self.etype,"?")
    def tick(self, dt):
        if self.remaining > 0: self.remaining -= dt


class LineageEdge(QGraphicsItem):
    def __init__(self, pp, cp):
        super().__init__(); self.pp=pp; self.cp=cp; self.setZValue(0)
    def boundingRect(self):
        px,py,cx,cy = self.pp.x,self.pp.y,self.cp.x,self.cp.y; m=35
        return QRectF(min(px,cx)-m,min(py,cy)-m,abs(cx-px)+2*m,abs(cy-py)+2*m)
    def paint(self, painter, option, widget):
        px,py,cx,cy = self.pp.x,self.pp.y,self.cp.x,self.cp.y
        rp,rc = self.pp.radius(),self.cp.radius()
        dy=cy-py; sy=py+(rp if dy>0 else -rp); ey=cy-(rc if dy>0 else -rc)
        mid=(sy+ey)/2; path=QPainterPath(); path.moveTo(px,sy); path.cubicTo(px,mid,cx,mid,cx,ey)
        alpha = 90 if self.cp.is_alive else 25
        dimmed = getattr(self.cp,'_dimmed',False)
        if dimmed: alpha = max(8, alpha//4)
        if self.pp.is_immortal or self.cp.is_immortal: col,w = QColor(255,200,50,alpha),2.2
        elif self.pp.is_carrier or self.cp.is_carrier: col,w = QColor(140,175,230,alpha),1.8
        else: col,w = QColor(120,155,210,alpha),1.4
        painter.setRenderHint(QPainter.Antialiasing); painter.setPen(QPen(col,w)); painter.drawPath(path)
        if self.cp.is_alive and not dimmed:
            painter.setBrush(QBrush(col)); painter.setPen(Qt.NoPen); painter.drawEllipse(QPointF(cx,ey),2.5,2.5)
    def sync(self): self.prepareGeometryChange(); self.update()


class MarriageBond(QGraphicsItem):
    def __init__(self, p1, p2):
        super().__init__(); self.p1=p1; self.p2=p2; self.setZValue(1)
    def boundingRect(self):
        x1,y1,x2,y2 = self.p1.x,self.p1.y,self.p2.x,self.p2.y; m=20
        return QRectF(min(x1,x2)-m,min(y1,y2)-m,abs(x2-x1)+2*m,abs(y2-y1)+2*m)
    def paint(self, painter, option, widget):
        x1,y1,x2,y2 = self.p1.x,self.p1.y,self.p2.x,self.p2.y
        r1,r2 = self.p1.radius(),self.p2.radius()
        dx,dy = x2-x1,y2-y1; dist=math.hypot(dx,dy)
        if dist<0.1: return
        ux,uy = dx/dist,dy/dist
        sx,sy = x1+ux*(r1+2),y1+uy*(r1+2); ex,ey = x2-ux*(r2+2),y2-uy*(r2+2)
        alpha = 130 if self.p1.is_alive and self.p2.is_alive else 50
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(255,140,180,alpha),1.8,Qt.DashLine))
        painter.drawLine(QPointF(sx,sy),QPointF(ex,ey))
        mx,my = (sx+ex)/2,(sy+ey)/2
        painter.setPen(Qt.NoPen); painter.setBrush(QBrush(QColor(255,100,140,alpha)))
        sz=4; path=QPainterPath(); path.moveTo(mx,my+sz*0.4)
        path.cubicTo(mx-sz,my-sz*0.5,mx-sz*0.5,my-sz,mx,my-sz*0.4)
        path.cubicTo(mx+sz*0.5,my-sz,mx+sz,my-sz*0.5,mx,my+sz*0.4)
        painter.drawPath(path)
    def sync(self): self.prepareGeometryChange(); self.update()


class PersonNode(QGraphicsItem):
    def __init__(self, person, on_select=None):
        super().__init__(); self.person=person; self.on_select=on_select
        self.highlighted=False; self.dimmed=False; self._hover=False
        self.setAcceptHoverEvents(True); self.setZValue(10); self.setPos(person.x,person.y)
    def hoverEnterEvent(self, e): self._hover=True; self.update(); self.setZValue(20)
    def hoverLeaveEvent(self, e): self._hover=False; self.update(); self.setZValue(10)
    def mousePressEvent(self, e):
        if self.on_select: self.on_select(self.person)
        super().mousePressEvent(e)
    def boundingRect(self):
        r=self.person.radius(); e=30 if self.person.is_immortal else 18
        return QRectF(-r-e,-r-e,2*(r+e),2*(r+e)+42)
    def paint(self, painter, option, widget):
        p=self.person; r=p.radius(); c=p.color(); painter.setRenderHint(QPainter.Antialiasing)
        dim = self.dimmed and not self.highlighted
        if dim: c = QColor(c.red(),c.green(),c.blue(),max(15,c.alpha()//4))
        # House ring
        if p.house and p.is_alive and not dim:
            hcol = p.house.color_a(100 if not self.highlighted else 210)
            painter.setPen(QPen(hcol,3.5)); painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(-r-4,-r-4,2*(r+4),2*(r+4)))
        # Highlight glow
        if self.highlighted:
            g=QRadialGradient(0,0,r*3); g.setColorAt(0,QColor(255,255,200,60)); g.setColorAt(1,QColor(255,255,200,0))
            painter.setBrush(QBrush(g)); painter.setPen(Qt.NoPen); painter.drawEllipse(QRectF(-r*3,-r*3,r*6,r*6))
        # Immortal glow
        if p.is_immortal and p.is_alive and not dim:
            pulse=0.5+0.5*math.sin(p.age*0.1)
            g=QRadialGradient(0,0,r*2.8); a=int(25+20*pulse)
            g.setColorAt(0,QColor(255,215,0,a)); g.setColorAt(0.5,QColor(255,180,0,a//3)); g.setColorAt(1,QColor(255,150,0,0))
            painter.setBrush(QBrush(g)); painter.setPen(Qt.NoPen); painter.drawEllipse(QRectF(-r*2.8,-r*2.8,r*5.6,r*5.6))
            rp=0.6+0.4*math.sin(p.age*0.08)
            painter.setPen(QPen(QColor(255,215,0,int(130+80*rp)),1.8,Qt.DashDotLine)); painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(-r-6,-r-6,2*(r+6),2*(r+6)))
            # Century badges
            for m in [100,250,500,1000,2500]:
                if p.age>=m:
                    br=5; bx,by=r+3,-r-3
                    painter.setBrush(QBrush(QColor(255,80,80,180))); painter.setPen(QPen(QColor(255,200,200,200),0.8))
                    painter.drawEllipse(QPointF(bx,by),br,br)
                    painter.setPen(QColor(255,255,255,220)); painter.setFont(QFont("Segoe UI",4,QFont.Bold))
                    painter.drawText(QRectF(bx-8,by-5,16,10),Qt.AlignCenter,f"{m//100}c"); bx+=12
        # Carrier shimmer
        elif p.is_carrier and p.is_alive and not dim:
            pulse=0.5+0.5*math.sin(p.age*0.07)
            g=QRadialGradient(0,0,r*2); a=int(15+10*pulse)
            g.setColorAt(0,QColor(150,190,255,a)); g.setColorAt(1,QColor(100,150,230,0))
            painter.setBrush(QBrush(g)); painter.setPen(Qt.NoPen); painter.drawEllipse(QRectF(-r*2,-r*2,r*4,r*4))
            painter.setPen(QPen(QColor(140,180,255,int(80+40*pulse)),1.2,Qt.DotLine)); painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(-r-4,-r-4,2*(r+4),2*(r+4)))
        # Body
        grad=QRadialGradient(-r*0.15,-r*0.15,r*1.1)
        grad.setColorAt(0,c.lighter(140)); grad.setColorAt(0.75,c); grad.setColorAt(1,c.darker(130))
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(c.darker(150),1.0) if p.is_alive else QPen(QColor(70,70,70,30),0.6))
        painter.drawEllipse(QRectF(-r,-r,2*r,2*r))
        # Allele badge
        if p.is_alive and r>7 and not dim:
            badge=p.allele_str(); bc=QColor(255,215,0,180) if "I" in badge else QColor(160,160,160,120)
            painter.setPen(QPen(bc,0.5)); painter.setBrush(QBrush(QColor(20,20,40,160)))
            bw,bh=16,10; painter.drawRoundedRect(QRectF(r*0.2,-r-bh-2,bw,bh),2,2)
            painter.setPen(bc); painter.setFont(QFont("Consolas",6,QFont.Bold))
            painter.drawText(QRectF(r*0.2,-r-bh-2,bw,bh),Qt.AlignCenter,badge)
        # Age
        if p.is_alive and r>=9 and not dim:
            painter.setPen(QColor(255,255,255,190)); painter.setFont(QFont("Segoe UI",max(6,int(r*0.5)),QFont.Bold))
                        # Age text (continued from paint method)
            painter.drawText(QRectF(-r,-r*0.45,2*r,r*0.8),Qt.AlignCenter,str(int(p.age)))
        # Name + info
        show = self._hover or self.highlighted
        if (show or (p.is_alive and r>9)) and not dim:
            a = 230 if show else 140
            painter.setPen(QColor(220,220,220,a))
            painter.setFont(QFont("Segoe UI",7,QFont.Bold if show else QFont.Normal))
            painter.drawText(QRectF(-48,r+2,96,13),Qt.AlignCenter,p.name)
            painter.setFont(QFont("Segoe UI",6))
            if p.is_immortal: st="∞ Immortal"
            elif p.is_carrier: st=f"◇ Carrier (×{p.max_age/80:.1f})"
            elif not p.is_alive: st=f"✝ Died {int(p.death_age or p.age)}"
            else: st=f"Gen {p.generation}"
            painter.setPen(QColor(180,180,200,a))
            painter.drawText(QRectF(-48,r+13,96,11),Qt.AlignCenter,st)
            if p.house and show:
                painter.setPen(p.house.color_a(min(255,a+40)))
                painter.drawText(QRectF(-48,r+23,96,11),Qt.AlignCenter,p.house.name)
        # Trait mini-bars on hover
        if show and p.is_alive and not dim:
            bx,by,bw,bh = r+10,-20,30,4
            for i,(k,v) in enumerate(p.traits.items()):
                yy=by+i*(bh+3)
                painter.setPen(Qt.NoPen); painter.setBrush(QColor(40,40,60,180))
                painter.drawRoundedRect(QRectF(bx,yy,bw,bh),1,1)
                tc = QColor(100,200,100,180) if v>0.6 else QColor(200,200,100,180) if v>0.3 else QColor(200,100,100,180)
                painter.setBrush(tc); painter.drawRoundedRect(QRectF(bx,yy,int(bw*v),bh),1,1)
                painter.setPen(QColor(180,180,200,150)); painter.setFont(QFont("Segoe UI",4))
                painter.drawText(QRectF(bx+bw+2,yy-1,50,bh+2),Qt.AlignVCenter|Qt.AlignLeft,k[:3])
        # Death X
        if not p.is_alive and not dim:
            painter.setPen(QPen(QColor(200,40,40,100),2)); d=r*0.5
            painter.drawLine(QPointF(-d,-d),QPointF(d,d)); painter.drawLine(QPointF(d,-d),QPointF(-d,d))

    def sync(self):
        self.prepareGeometryChange(); self.setPos(self.person.x,self.person.y); self.update()


class GenLabel(QGraphicsItem):
    def __init__(self, gen, y):
        super().__init__(); self.gen=gen; self.y_pos=y; self.setZValue(-5)
    def boundingRect(self): return QRectF(-6000,self.y_pos-50,12000,GEN_Y)
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        c = QColor(255,255,255,6) if self.gen%2==0 else QColor(255,255,255,3)
        painter.fillRect(QRectF(-6000,self.y_pos-50,12000,GEN_Y),c)
        painter.setPen(QColor(255,215,0,45)); painter.setFont(QFont("Segoe UI",8,QFont.Bold))
        painter.drawText(QPointF(-5950,self.y_pos),f"GEN {self.gen}")


class PopChart(QWidget):
    def __init__(self):
        super().__init__(); self.setMinimumHeight(140); self.setMaximumHeight(200); self.data=[]
    def set_data(self, d): self.data=d; self.update()
    def paintEvent(self, event):
        painter=QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        w,h = self.width(),self.height(); m=35
        painter.fillRect(self.rect(),QColor(18,18,35))
        if len(self.data)<2:
            painter.setPen(QColor(120,120,150)); painter.setFont(QFont("Segoe UI",9))
            painter.drawText(self.rect(),Qt.AlignCenter,"Collecting data..."); painter.end(); return
        mx = max(max(d[1],d[2],d[3]) for d in self.data); mx=max(mx,1)
        cw,ch = w-2*m, h-2*m
        painter.setPen(QPen(QColor(60,60,80),0.5))
        for i in range(5):
            y=m+ch*i/4; painter.drawLine(m,int(y),w-m,int(y))
            painter.setPen(QColor(100,100,130)); painter.setFont(QFont("Segoe UI",6))
            painter.drawText(2,int(y)-4,m-4,12,Qt.AlignRight|Qt.AlignVCenter,str(int(mx*(1-i/4))))
            painter.setPen(QPen(QColor(60,60,80),0.5))
        def dl(idx,col):
            painter.setPen(QPen(col,1.5)); path=QPainterPath()
            for i,d in enumerate(self.data):
                x=m+cw*i/(len(self.data)-1); y=m+ch*(1-d[idx]/mx)
                path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
            painter.drawPath(path)
        dl(1,QColor(80,170,230)); dl(2,QColor(140,180,255)); dl(3,QColor(255,215,0))
        painter.setFont(QFont("Segoe UI",7)); lx=m+5
        for lb,co in [("Mortals",QColor(80,170,230)),("Carriers",QColor(140,180,255)),("Immortals",QColor(255,215,0))]:
            painter.setPen(Qt.NoPen); painter.setBrush(co); painter.drawEllipse(lx,5,6,6)
            painter.setPen(QColor(180,180,200)); painter.drawText(lx+9,5,60,12,Qt.AlignVCenter|Qt.AlignLeft,lb); lx+=75
        painter.end()


class ZoomView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene); self._z=0
        self.setRenderHints(QPainter.Antialiasing|QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    def wheelEvent(self, e):
        f=1.15
        if e.angleDelta().y()>0: self.scale(f,f); self._z+=1
        else: self.scale(1/f,1/f); self._z-=1
    def fit_all(self):
        r=self.scene().itemsBoundingRect().adjusted(-80,-50,80,50)
        if r.width()>0 and r.height()>0: self.fitInView(r,Qt.KeepAspectRatio)
        self._z=0


# ── Simulation Engine ────────────────────────────────────────────────
class Engine:
    def __init__(self):
        self.people=[]; self.houses=[]; self.events=[]; self.year=0.0
        self.repro_rate=0.012; self.marry_rate=0.03
        self.total_births=0; self.total_deaths=0; self.total_marriages=0
        self.effects=[]; self.log=[]; self.pop_hist=[]; self._last_snap=-5

    def create_house(self, name=None, color=None):
        h=House(name,color); self.houses.append(h); return h

    def add_person(self, a1="i", a2="i", mother=None, father=None, house=None, gen=0):
        if sum(1 for p in self.people if p.is_alive)>=MAX_POP: return None
        p=Person(a1,a2,mother,father,house,gen); p.born_year=self.year
        if mother: mother.children.append(p)
        if father: father.children.append(p)
        self.people.append(p); self.total_births+=1
        if house and house.extinct: house.extinct=False
        self.layout(); return p

    def layout(self):
        gens=defaultdict(list)
        for p in self.people: gens[p.generation].append(p)
        for gn in sorted(gens.keys()):
            ppl=gens[gn]
            def sk(p):
                mid=0
                if p.mother and p.father: mid=(p.mother.target_x+p.father.target_x)/2
                elif p.mother: mid=p.mother.target_x
                elif p.father: mid=p.father.target_x
                return (mid, p.id)
            ppl.sort(key=sk)
            # place spouses adjacent
            placed,seen=[],set()
            for p in ppl:
                if p.id in seen: continue
                placed.append(p); seen.add(p.id)
                if (p.spouse and p.spouse.is_alive and p.spouse.generation==gn
                        and p.spouse.id not in seen and p.spouse in ppl):
                    placed.append(p.spouse); seen.add(p.spouse.id)
            n=len(placed); sx=-(n-1)*SPACING_X/2
            for i,p in enumerate(placed):
                p.target_x=sx+i*SPACING_X; p.target_y=gn*GEN_Y+60

    def step(self, dt):
        prev_alive=sum(1 for p in self.people if p.is_alive)
        self.year+=dt
        # tick effects
        for eff in self.effects[:]:
            eff[2]-=dt
            if eff[2]<=0: self.effects.remove(eff)
        # tick events
        for ev in self.events[:]:
            ev.tick(dt)
            if ev.remaining<=0 and ev.duration>0: self.events.remove(ev)
        # tick people
        for p in self.people: p.tick(dt)
        now_alive=sum(1 for p in self.people if p.is_alive)
        self.total_deaths+=prev_alive-now_alive
        # Ancestral resonance
        imm_ids={p.id for p in self.people if p.is_immortal and p.is_alive}
        for p in self.people:
            if p.is_alive and not p.is_immortal:
                cnt=sum(1 for aid in p.all_ancestors() if aid in imm_ids)
                p.traits["longevity"]=min(1.0,p.traits["longevity"]+cnt*0.00015*dt)
                if p.blood_type!="immortal": p.max_age=p._max_age()
        # Marriage & Reproduction
        self._marriages(dt); self._reproduction(dt)
        # Smooth positions
        for p in self.people:
            p.x+=(p.target_x-p.x)*0.1; p.y+=(p.target_y-p.y)*0.1
        # Events
        self._check_events()
        # Snapshot
        if self.year-self._last_snap>=3: self._snapshot(); self._last_snap=self.year

    def _eff_mult(self, key):
        m=1.0
        for e in self.effects:
            if e[0]==key: m*=(1+e[1]) if e[1]>0 else (1+e[1])
        return max(0.01,m)

    def _marriages(self, dt):
        unmar=[p for p in self.people if p.is_alive and (not p.spouse or p.is_widowed)
               and p.age>=16 and p.marry_cd<=0]
        random.shuffle(unmar); done=set()
        rate=self.marry_rate*self._eff_mult("fertility_boost")
        for p in unmar:
            if p.id in done: continue
            if random.random()>rate*dt*(0.5+p.traits["charisma"]): continue
            best,bs=None,float("inf")
            for q in unmar:
                if q.id in done or q.id==p.id: continue
                if not p.can_marry(q): continue
                s=abs(p.age-q.age)*2+abs(p.generation-q.generation)*15
                if p.house and q.house and p.house is q.house: s-=5
                if q.is_immortal or q.is_carrier: s-=3
                if s<bs: bs=s; best=q
            if best:
                p.spouse=best; best.spouse=p; done.add(p.id); done.add(best.id)
                p.marry_cd=5; best.marry_cd=5; self.total_marriages+=1
                if p.house and best.house and p.house is not best.house:
                    w,l = (p.house,best.house) if p.house.prestige>=best.house.prestige else (best.house,p.house)
                    best.house=w; w.prestige+=1
                    self._log(f"🏠 Houses {w.name} & {l.name} united by marriage!")

    def _reproduction(self, dt):
        done=set()
        for p in self.people:
            if p.id in done or not p.can_reproduce(): continue
            if p.spouse and p.spouse.is_alive and p.spouse.can_reproduce():
                sp=p.spouse; done.add(p.id); done.add(sp.id)
                rate=self.repro_rate*(0.5+p.traits["fertility"])*(0.5+sp.traits["fertility"])
                rate*=self._eff_mult("fertility_boost")*self._eff_mult("fertility_penalty")
                if p.is_immortal or sp.is_immortal: rate*=0.3
                if random.random()<rate*dt:
                    ch=self._child(p,sp)
                    if ch: p.repro_cd=random.uniform(6,16); sp.repro_cd=random.uniform(6,16)
            elif not p.spouse or (p.spouse and not p.spouse.is_alive):
                rate=self.repro_rate*0.08*(0.5+p.traits["fertility"])*self._eff_mult("fertility_boost")*self._eff_mult("fertility_penalty")
                if random.random()<rate*dt:
                    ch=self._child(p,None)
                    if ch: p.repro_cd=random.uniform(8,20)

    def _child(self, p1, p2):
        a1=random.choice([p1.allele1,p1.allele2])
        if p2:
            a2=random.choice([p2.allele1,p2.allele2]); gn=max(p1.generation,p2.generation)+1
        else:
            a2=random.choice(["i","i","I"]); gn=p1.generation+1
        # Mutation (0.3%)
        for _ in range(2):
            if random.random()<0.003:
                v=a1 if random.random()<0.5 else a2
                if v=="i": a1,a2 = (a1.replace("i","I") if a1==v else a1), (a2.replace("i","I") if a2==v else a2)
                else: a1,a2 = (a1.replace("I","i") if a1==v else a1), (a2.replace("I","i") if a2==v else a2)
        house=p1.house or (p2.house if p2 else None) or self.create_house()
        ch=self.add_person(a1,a2,mother=p1,father=p2,house=house,gen=gn)
        if ch:
            house.prestige+=0.1
            for e in self.effects:
                if e[0]=="trait_boost":
                    for k in ch.traits: ch.traits[k]=min(1.0,ch.traits[k]+e[1]*0.05)
                    ch.max_age=ch._max_age()
        return ch

    def _check_events(self):
        ch=0.0008+self.year*0.000005
        ac=sum(1 for p in self.people if p.is_alive)
        if ac>50: ch*=1.5
        if ac>100: ch*=1.3
        if random.random()<ch: self._trigger()

    def _trigger(self):
        et=random.choices(
            [GameEvent.PLAGUE,GameEvent.GOLDEN,GameEvent.CATASTROPHE,GameEvent.AWAKEN,
             GameEvent.BLESS,GameEvent.MIGRATE,GameEvent.FAMINE,GameEvent.RENAISSANCE],
            weights=[12,20,8,4,10,12,10,14])[0]
        alive=[p for p in self.people if p.is_alive]
        if not alive: return

        if et==GameEvent.PLAGUE:
            k=0
            for p in alive:
                sc=0.4+p.traits["resilience"]*0.5
                if p.is_carrier: sc+=0.15
                if p.is_immortal: sc=1.0
                if random.random()>sc: p.is_alive=False; p.death_age=p.age; k+=1
            dur=random.uniform(10,25); self.effects.append(["fertility_penalty",-0.3,dur])
            self.events.append(GameEvent(et,self.year,f"Plague! {k} died. Fertility −30% for {int(dur)}y.",dur))
            self._log(f"☠ PLAGUE — {k} perished! Fertility −30% for {int(dur)}y.")

        elif et==GameEvent.GOLDEN:
            dur=random.uniform(15,35); mag=random.uniform(0.3,0.6)
            self.effects.append(["fertility_boost",mag,dur])
            self.events.append(GameEvent(et,self.year,f"Golden Age! Fertility +{int(mag*100)}% for {int(dur)}y.",dur,mag))
            self._log(f"✦ GOLDEN AGE — Fertility +{int(mag*100)}% for {int(dur)}y!")

        elif et==GameEvent.CATASTROPHE:
            k=0
            for p in alive:
                if p.age<40 and not p.is_immortal and random.random()<0.15:
                    p.is_alive=False; p.death_age=p.age; k+=1
            self.events.append(GameEvent(et,self.year,f"Catastrophe! {k} young lost."))
            self._log(f"⚡ CATASTROPHE — {k} young adults died!")

        elif et==GameEvent.AWAKEN:
            morts=[p for p in alive if p.blood_type=="mortal"]
            if morts:
                c=random.choice(morts); old=c.allele_str()
                c.allele1="I"; c.allele2="I"; c.blood_type="immortal"; c.max_age=float("inf")
                self.events.append(GameEvent(et,self.year,f"{c.name} awakens Immortal! ({old}→II)"))
                self._log(f"✨ AWAKENING — {c.name} becomes IMMORTAL!")

        elif et==GameEvent.BLESS:
            if self.houses:
                h=random.choice(self.houses); dur=random.uniform(20,40)
                self.effects.append(["trait_boost",0.3,dur]); h.prestige+=5
                self.events.append(GameEvent(et,self.year,f"House {h.name} blessed! Traits + for {int(dur)}y.",dur))
                self._log(f"🕊 BLESSING — House {h.name} gains divine favor!")

        elif et==GameEvent.MIGRATE:
            n=random.randint(1,3)
            for _ in range(n):
                h=self.create_house()
                a1,a2=random.choice(["I","i","i","i"]),random.choice(["I","i","i","i"])
                p=self.add_person(a1,a2,house=h,gen=0)
                if p: p.x=p.target_x; p.y=p.target_y; h.founder=p
            self.events.append(GameEvent(et,self.year,f"{n} migrants found new houses!"))
            self._log(f"🚶 MIGRATION — {n} newcomers arrive!")

        elif et==GameEvent.FAMINE:
            dur=random.uniform(10,20); self.effects.append(["fertility_penalty",-0.4,dur])
            self.events.append(GameEvent(et,self.year,f"Famine! Fertility −40% for {int(dur)}y.",dur))
            self._log(f"🌾 FAMINE — Fertility −40% for {int(dur)}y!")

        elif et==GameEvent.RENAISSANCE:
            dur=random.uniform(15,30)
            self.effects.append(["trait_boost",0.4,dur]); self.effects.append(["fertility_boost",0.2,dur])
            self.events.append(GameEvent(et,self.year,f"Renaissance! Traits & fertility boosted for {int(dur)}y.",dur))
            self._log(f"🎨 RENAISSANCE — All boosted for {int(dur)}y!")

    def _log(self, t):
        self.log.append((int(self.year),t))
        if len(self.log)>200: self.log=self.log[-200:]

    def _snapshot(self):
        al=[p for p in self.people if p.is_alive]
        self.pop_hist.append((self.year,
            sum(1 for p in al if p.blood_type=="mortal"),
            sum(1 for p in al if p.is_carrier),
            sum(1 for p in al if p.is_immortal)))
        if len(self.pop_hist)>300: self.pop_hist=self.pop_hist[-300:]

    def stats(self):
        al=[p for p in self.people if p.is_alive]
        im=[p for p in al if p.is_immortal]; ca=[p for p in al if p.is_carrier]; mo=[p for p in al if p.blood_type=="mortal"]
        mg=max((p.generation for p in self.people),default=0)
        aa=sum(p.age for p in al)/max(1,len(al))
        ah={h for h in self.houses if any(p.is_alive and p.house is h for p in self.people)}
        return dict(year=self.year,total=len(self.people),alive=len(al),dead=len(self.people)-len(al),
            immortals=len(im),carriers=len(ca),mortals=len(mo),avg_age=aa,
            oldest=max((p.age for p in self.people),default=0),
            oldest_imm=max((p.age for p in im),default=0),
            oldest_car=max((p.age for p in ca),default=0),
            max_gen=mg,births=self.total_births,deaths=self.total_deaths,
            marriages=self.total_marriages,houses_active=len(ah),
            houses_extinct=len(self.houses)-len(ah))

    def reset(self):
        self.people.clear(); self.houses.clear(); self.events.clear()
        self.effects.clear(); self.log.clear(); self.pop_hist.clear()
        self.year=0; self.total_births=0; self.total_deaths=0; self.total_marriages=0
        self._last_snap=-5; Person._ctr=0; House._idx=0


# ── Main Window ──────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aging, Immortality & Lineage v2 — Genetics · Houses · Events")
        self.setMinimumSize(1300,820); self.resize(1540,920)
        self.eng=Engine(); self.running=False; self.speed=1.0
        self.nodes={}; self.mar_edges={}; self.lin_edges={}; self.gen_lbls={}
        self.auto_fit=True; self.sel_person=None; self._last_log=0; self._notifs=[]
        self._build_ui(); self._apply_theme(); self._seed()
        self.timer=QTimer(self); self.timer.timeout.connect(self._tick); self.timer.setInterval(50)

    def _build_ui(self):
        cw=QWidget(); self.setCentralWidget(cw); root=QHBoxLayout(cw)
        root.setContentsMargins(4,4,4,4); root.setSpacing(4)

        # LEFT
        left=QWidget(); left.setFixedWidth(265); ll=QVBoxLayout(left)
        ll.setContentsMargins(0,0,0,0); ll.setSpacing(3)
        t=QLabel("⏳ Aging & Lineage\n     Simulator v2")
        t.setStyleSheet("font-size:15px;font-weight:bold;color:#ffd700;padding:2px;"); ll.addWidget(t)

        cg=QGroupBox("⚙ Controls"); cl=QVBoxLayout(cg)
        self.btn_play=QPushButton("▶  Start"); self.btn_play.setCheckable(True)
        self.btn_play.clicked.connect(self._toggle); cl.addWidget(self.btn_play)
        self.btn_step=QPushButton("⏭  Step +2y")
        self.btn_step.clicked.connect(lambda:self._do_step(2.0)); cl.addWidget(self.btn_step)
        rw=QHBoxLayout()
        self.btn_reset=QPushButton("🔄 Reset"); self.btn_reset.clicked.connect(self._reset); rw.addWidget(self.btn_reset)
        self.btn_fit=QPushButton("🔍 Fit"); self.btn_fit.clicked.connect(self._fit); rw.addWidget(self.btn_fit)
        cl.addLayout(rw)
        cl.addWidget(QLabel("Speed:"))
        self.sl_sp=QSlider(Qt.Horizontal); self.sl_sp.setRange(1,80); self.sl_sp.setValue(10)
        self.sl_sp.valueChanged.connect(self._sp_chg); cl.addWidget(self.sl_sp)
        self.lb_sp=QLabel("1.0×"); cl.addWidget(self.lb_sp)
        cl.addWidget(QLabel("Reproduction:"))
        self.sl_rp=QSlider(Qt.Horizontal); self.sl_rp.setRange(1,60); self.sl_rp.setValue(12)
        self.sl_rp.valueChanged.connect(self._rp_chg); cl.addWidget(self.sl_rp)
        self.lb_rp=QLabel("1.2 %"); cl.addWidget(self.lb_rp)
        self.chk_fit=QCheckBox("Auto-fit"); self.chk_fit.setChecked(True)
        self.chk_fit.toggled.connect(lambda v:setattr(self,'auto_fit',v)); cl.addWidget(self.chk_fit)
        ll.addWidget(cg)

        ag=QGroupBox("👥 Add Founders"); al=QVBoxLayout(ag)
        for lb,al_pair in [("🧑 Mortal (ii)",("i","i")),("◇ Carrier (Ii)",("I","i")),("✨ Immortal (II)",("I","I"))]:
            b=QPushButton(lb); b.clicked.connect(lambda c,a=al_pair:self._add_founder(a[0],a[1])); al.addWidget(b)
        b3=QPushButton("🌱 Seed Population"); b3.clicked.connect(self._seed); al.addWidget(b3)
        ll.addWidget(ag)

        sg=QGroupBox("📊 Statistics"); sl=QGridLayout(sg); self._st={}
        for i,(k,lb) in enumerate([
            ("year","Year"),("total","Total Born"),("alive","Alive"),("dead","Dead"),
            ("immortals","Immortals (II)"),("carriers","Carriers (Ii)"),("mortals","Mortals (ii)"),
            ("avg_age","Avg Age"),("oldest","Oldest Ever"),("oldest_imm","Oldest Immortal"),
            ("oldest_car","Oldest Carrier"),("max_gen","Max Generation"),("births","Births"),
            ("deaths","Deaths"),("marriages","Marriages"),("houses_active","Active Houses"),
            ("houses_extinct","Extinct Houses")]):
            sl.addWidget(QLabel(lb+":"),i,0); v=QLabel("0")
            v.setStyleSheet("color:#ffd700;font-weight:bold;font-size:10px;"); sl.addWidget(v,i,1); self._st[k]=v
        ll.addWidget(sg)

        lg=QGroupBox("📋 Legend"); lgl=QVBoxLayout(lg)
        for tx,co in [("● Young mortal (0-15)","#64e064"),("● Adult mortal (15-55)","#3cb8e6"),
            ("● Elder mortal (55+)","#7868c8"),("◇ Carrier (Ii) shimmer","#8cb4ff"),
            ("✨ Immortal (II) golden glow","#ffd700"),("✝ Dead grey faded","#5a5a5a"),
            ("— Lineage parent→child","#7899d2"),("— Marriage bond ♥","#ff8cb4"),
            ("◯ House dynasty ring","#aaaaaa"),("Badge: allele pair (Ii)","#ffd700")]:
            l=QLabel(tx); l.setStyleSheet(f"color:{co};font-size:9px;"); lgl.addWidget(l)
        ll.addWidget(lg); ll.addStretch(); root.addWidget(left)

        # CENTER
        self.scene=QGraphicsScene(); self.scene.setBackgroundBrush(QBrush(QColor(12,12,24)))
        self.view=ZoomView(self.scene); root.addWidget(self.view,1)

        # RIGHT
        right=QWidget(); right.setFixedWidth(285); rl=QVBoxLayout(right)
        rl.setContentsMargins(0,0,0,0); rl.setSpacing(3)
        tabs=QTabWidget()

        # Inspector
        iw=QWidget(); il=QVBoxLayout(iw)
        self.insp_title=QLabel("Click a person to inspect")
        self.insp_title.setStyleSheet("color:#ffd700;font-size:13px;font-weight:bold;")
        self.insp_title.setWordWrap(True); il.addWidget(self.insp_title)
        self.insp_det=QTextEdit(); self.insp_det.setReadOnly(True)
        self.insp_det.setStyleSheet("background:#1a1a2e;color:#d0d0e0;border:1px solid #333355;font-size:10px;")
        il.addWidget(self.insp_det)
        bl=QPushButton("🔗 Highlight Lineage"); bl.clicked.connect(self._hl_lineage); il.addWidget(bl)
        bc=QPushButton("❌ Clear Highlight"); bc.clicked.connect(self._clr_hl); il.addWidget(bc)
        tabs.addTab(iw,"👤 Inspector")

        # Event log
        lw=QWidget(); lol=QVBoxLayout(lw)
        self.ev_disp=QTextEdit(); self.ev_disp.setReadOnly(True)
        self.ev_disp.setStyleSheet("background:#1a1a2e;color:#d0d0e0;border:1px solid #333355;font-size:10px;")
        lol.addWidget(self.ev_disp); tabs.addTab(lw,"📜 Events")

        # Chart
        chw=QWidget(); cvl=QVBoxLayout(chw)
        self.pop_chart=PopChart(); cvl.addWidget(self.pop_chart)
        self.eff_lbl=QLabel("No active effects"); self.eff_lbl.setStyleSheet("color:#ff9966;font-size:10px;")
        self.eff_lbl.setWordWrap(True); cvl.addWidget(self.eff_lbl)
        tabs.addTab(chw,"📈 Chart")

        rl.addWidget(tabs); root.addWidget(right)

        # Year overlay
        self.year_item=self.scene.addText("Year: 0",QFont("Segoe UI",15,QFont.Bold))
        self.year_item.setDefaultTextColor(QColor(255,215,0,170)); self.year_item.setZValue(100)

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow{background:#1a1a2e;}
            QGroupBox{color:#e0e0e0;border:1px solid #333355;border-radius:5px;
                      margin-top:8px;padding-top:12px;font-weight:bold;font-size:10px;}
            QGroupBox::title{subcontrol-origin:margin;left:8px;padding:0 4px;}
            QLabel{color:#c0c0d0;font-size:10px;}
            QPushButton{background:#2a2a4a;color:#e0e0f0;border:1px solid #444466;
                        border-radius:4px;padding:5px 10px;font-size:10px;font-weight:bold;}
            QPushButton:hover{background:#3a3a6a;} QPushButton:pressed{background:#4a4a8a;}
            QPushButton:checked{background:#5a3a8a;border-color:#8a5abf;}
            QSlider::groove:horizontal{height:5px;background:#2a2a4a;border-radius:2px;}
            QSlider::handle:horizontal{background:#6a6aaa;width:14px;margin:-5px 0;border-radius:7px;}
            QCheckBox{color:#c0c0d0;font-size:10px;}
            QTabWidget::pane{border:1px solid #333355;background:#1a1a2e;}
            QTabBar::tab{background:#2a2a4a;color:#c0c0d0;padding:5px 8px;
                         border:1px solid #333355;border-bottom:none;border-radius:4px 4px 0 0;font-size:10px;}
            QTabBar::tab:selected{background:#3a3a6a;color:#ffd700;}
            QTextEdit{font-size:10px;}
        """)

    def _add_founder(self, a1, a2):
        h=self.eng.create_house(); p=self.eng.add_person(a1,a2,house=h,gen=0)
        if p:
            h.founder=p; p.x=p.target_x; p.y=p.target_y
            self._mk_node(p); self._upd_gen()
            if self.auto_fit: self._fit()

    def _seed(self):
        for a1,a2 in [("I","I"),("I","I"),("I","i"),("I","i"),("i","i"),("i","i"),("i","i")]:
            h=self.eng.create_house(); p=self.eng.add_person(a1,a2,house=h,gen=0)
            if p: h.founder=p; p.x=p.target_x; p.y=p.target_y; self._mk_node(p)
        self._upd_gen(); self._fit()

    def _mk_node(self, person):
        n=PersonNode(person,on_select=self._sel); self.scene.addItem(n); self.nodes[person.id]=n
        for par in [person.mother,person.father]:
            if par and par.id in self.nodes:
                k=(par.id,person.id); e=LineageEdge(par,person)
                self.scene.addItem(e); self.lin_edges[k]=e
        if person.spouse and person.spouse.id in self.nodes:
            self._mk_mar(person,person.spouse)

    def _mk_mar(self, p1, p2):
        k=(min(p1.id,p2.id),max(p1.id,p2.id))
        if k not in self.mar_edges:
            e=MarriageBond(p1,p2); self.scene.addItem(e); self.mar_edges[k]=e

    def _upd_gen(self):
        mg=max((p.generation for p in self.eng.people),default=0)
        for g in range(mg+1):
            if g not in self.gen_lbls:
                l=GenLabel(g,g*GEN_Y+60); self.scene.addItem(l); self.gen_lbls[g]=l
            else: self.gen_lbls[g].y_pos=g*GEN_Y+60; self.gen_lbls[g].update()

    def _sel(self, person):
        self.sel_person=person; self._upd_insp()

    def _upd_insp(self):
        p=self.sel_person
        if not p:
            self.insp_title.setText("Click a person to inspect"); self.insp_det.clear(); return
        st="✨ IMMORTAL" if p.is_immortal else ("◇ Carrier" if p.is_carrier else ("✝ Deceased" if not p.is_alive else "● Mortal"))
        self.insp_title.setText(f"{p.name} — {st}")
        hn=p.house.name if p.house else "None"
        hc=p.house.color.name() if p.house else "#888"
        ma="∞" if p.is_immortal else f"{p.max_age:.1f}"
        par=[]
        if p.mother: par.append(f"  Parent 1: {p.mother.name} ({p.mother.allele_str()})")
        if p.father: par.append(f"  Parent 2: {p.father.name} ({p.father.allele_str()})")
        sp=f"{p.spouse.name} ({p.spouse.allele_str()})" if p.spouse and p.spouse.is_alive else ("Widowed" if p.is_widowed else "Single")
        ch=", ".join(f"{c.name}({c.allele_str()})" for c in p.children[:8])
        if len(p.children)>8: ch+=f" +{len(p.children)-8}"
        sib=[c for pr in [p.mother,p.father] if pr for c in pr.children if c is not p and c not in sib] if p.mother or p.father else []
        sib=list({c.id:c for c in [c for pr in [p.mother,p.father] if pr for c in pr.children if c is not p]}.values())
        stxt=", ".join(s.name for s in sib[:6]) or "None"
        anc=len(p.all_ancestors()); des=len(p.all_descendants())
        imm_ids={pp.id for pp in self.eng.people if pp.is_immortal and pp.is_alive}
        ia=sum(1 for a in p.all_ancestors() if a in imm_ids)
        tb=""
        for k,v in p.traits.items():
            f=int(v*10); tb+=f"  {k:10s} {'█'*f}{'░'*(10-f)} {v:.2f}\n"
        text=f"""╔═══ Identity ═══════════════════╗
  Age:       {p.age:.1f} / {ma}
  Born:      Year {int(p.born_year)}
  Generation: {p.generation}
  Alleles:   {p.allele1}|{p.allele2}  ({p.allele_str()})
  Blood:     {p.blood_type.upper()}

╔═══ House ════════════════════════╗
  Name:      {hn}
  Prestige:  {p.house.prestige:.1f}
  Extinct:   {"Yes" if p.house.extinct else "No"}

╔═══ Traits ══════════════════════╗
{tb}
╔═══ Family ══════════════════════╗
  Spouse:    {sp}
  Children:  {len(p.children)}  {ch}
  Siblings:  {len(sib)}  {stxt}
  Ancestors: {anc} total
  Descendants: {des} total
  Living Immortal Ancestors: {ia}
"""
        if p.death_age:
            text+=f"""
╔═══ Death ═══════════════════════╗
  Died at age: {p.death_age:.1f}
  Death year:  {int(p.born_year+p.death_age)}
"""
        self.insp_det.setPlainText(text)

    def _hl_lineage(self):
        p=self.sel_person
        if not p: return
        ids={p.id}|p.all_ancestors()|p.all_descendants()
        for pid in list(ids):
            pp=self._find_p(pid)
            if pp and pp.spouse: ids.add(pp.spouse.id)
        for nid,n in self.nodes.items():
            if nid in ids: n.highlighted=True; n.dimmed=False; n.setZValue(15)
            else: n.highlighted=False; n.dimmed=True; n.setZValue(5)
            n.sync()

    def _clr_hl(self):
        for n in self.nodes.values():
            n.highlighted=False; n.dimmed=False; n.setZValue(10); n.sync()

    def _find_p(self, pid):
        for p in self.eng.people:
            if p.id==pid: return p
        return None

    def _toggle(self, checked):
        self.running=checked
        if checked: self.btn_play.setText("⏸  Pause"); self.timer.start()
        else: self.btn_play.setText("▶  Start"); self.timer.stop()

    def _sp_chg(self, v): self.speed=v/10.0; self.lb_sp.setText(f"{self.speed:.1f}×")
    def _rp_chg(self, v): self.eng.repro_rate=v/1000.0; self.lb_rp.setText(f"{self.eng.repro_rate*100:.1f} %")
    def _fit(self): self.view.fit_all()

    def _reset(self):
        self.running=False; self.btn_play.setChecked(False); self.btn_play.setText("▶  Start"); self.timer.stop()
        self.scene.clear(); self.nodes.clear(); self.mar_edges.clear()
        self.lin_edges.clear(); self.gen_lbls.clear(); self._notifs.clear()
        self.sel_person=None; self.eng.reset(); self._last_log=0
        self.year_item=self.scene.addText("Year: 0",QFont("Segoe UI",15,QFont.Bold))
        self.year_item.setDefaultTextColor(QColor(255,215,0,170)); self.year_item.setZValue(100)
        self.insp_title.setText("Click a person to inspect"); self.insp_det.clear()
        self.ev_disp.clear(); self.pop_chart.set_data([]); self._seed()

    def _do_step(self, dt):
        self.eng.step(dt*self.speed)
        for p in self.eng.people:
            if p.id not in self.nodes:
                if p.mother: p.x,p.y=p.mother.x,p.mother.y
                elif p.father: p.x,p.y=p.father.x,p.father.y
                else: p.x,p.y=p.target_x,p.target_y
                self._mk_node(p)
        for p in self.eng.people:
            if p.spouse:
                k=(min(p.id,p.spouse.id),max(p.id,p.spouse.id))
                if k not in self.mar_edges: self._mk_mar(p,p.spouse)
        self._prune(); self._upd_gen(); self._sync()

    def _tick(self): self._do_step(0.5)

    def _prune(self):
        rm=[]
        for p in self.eng.people:
            if not p.is_alive and p.death_age and (p.age-p.death_age)>CORPSE_FADE: rm.append(p.id)
        for pid in rm:
            if pid in self.nodes:
                for k in [k for k in self.lin_edges if k[0]==pid or k[1]==pid]:
                    self.scene.removeItem(self.lin_edges[k]); del self.lin_edges[k]
                for k in [k for k in self.mar_edges if k[0]==pid or k[1]==pid]:
                    self.scene.removeItem(self.mar_edges[k]); del self.mar_edges[k]
                self.scene.removeItem(self.nodes[pid]); del self.nodes[pid]

    def _sync(self):
        for p in self.eng.people:
            if p.id in self.nodes: self.nodes[p.id].sync()
        for e in self.lin_edges.values(): e.sync()
        for e in self.mar_edges.values(): e.sync()
        s=self.eng.stats()
        self.year_item.setPlainText(f"Year: {int(s['year'])}")
        self.year_item.setPos(self.view.mapToScene(15,10))
        for k,l in self._st.items():
            v=s.get(k,0); l.setText(f"{v:.1f}" if isinstance(v,float) else str(v))
        if self.sel_person: self._upd_insp()
        if self.eng.log:
            lt="\n".join(f"[Y{y}] {t}" for y,t in self.eng.log[-50:])
            self.ev_disp.setPlainText(lt)
            sb=self.ev_disp.verticalScrollBar(); sb.setValue(sb.maximum())
        self.pop_chart.set_data(self.eng.pop_hist)
        if self.eng.effects:
            pts=[]
            for e in self.eng.effects:
                n=e[0].replace("_"," ").title()
                pts.append(f"• {n}: {e[1]:+.0%} ({e[2]:.0f}y)")
            self.eff_lbl.setText("\n".join(pts))
        else: self.eff_lbl.setText("No active effects")
        # Notifications
        ll=len(self.eng.log)
        if ll>self._last_log:
            for _,t in self.eng.log[self._last_log:][-3:]: self._notif(t)
        self._last_log=ll
        # House extinction
        for h in self.eng.houses:
            if not any(p.is_alive and p.house is h for p in self.eng.people) and not h.extinct:
                h.extinct=True; self.eng._log(f"💀 House {h.name} has gone EXTINCT!")
        if self.auto_fit and random.random()<0.02: self.view.fit_all()

    def _notif(self, text):
        it=self.scene.addText(text,QFont("Segoe UI",11,QFont.Bold))
        it.setDefaultTextColor(QColor(255,200,100,200)); it.setZValue(200)
        yo=len(self._notifs)*30; it.setPos(self.view.mapToScene(15,40+yo))
        self._notifs.append(it); QTimer.singleShot(4000,lambda i=it:self._rm_notif(i))

    def _rm_notif(self, it):
        if it in self._notifs: self._notifs.remove(it)
        if it.scene()==self.scene: self.scene.removeItem(it)

    def keyPressEvent(self, e):
        if e.key()==Qt.Key_Space: self.btn_play.toggle(); self._toggle(self.btn_play.isChecked())
        elif e.key()==Qt.Key_F: self._fit()
        elif e.key()==Qt.Key_R: self._reset()
        elif e.key()==Qt.Key_H: self._hl_lineage()
        elif e.key()==Qt.Key_Escape: self._clr_hl()
        super().keyPressEvent(e)


if __name__=="__main__":
    app=QApplication(sys.argv); app.setStyle("Fusion")
    win=MainWindow(); win.show()
    QTimer.singleShot(100,win._fit)
    sys.exit(app.exec())