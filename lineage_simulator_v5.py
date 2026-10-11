#!/usr/bin/env python3
"""
Aging, Immortality & Lineage Simulator v5
Genetics · House Dynasties · Marriages · Random Events · Deep Lineage Rules
v3: Search, Save/Load, Filters, House Rankings, Context Menu, Gene Frequency, Pause-on-Event
v4: Drag-and-drop, Timeline Scrubber, Personality/Traits, Achievements, Mini-map, Pop Pyramid, Wars
v5: ★ ADVANCED AI ★ — Relationships, Skills, Dynamic Roles, Personality Behaviors,
    House Strategy (Alliances/Trade), Memory System, Mentoring, Influence Propagation,
    Network-Aware Marriage, Smarter Reproduction
"""

import sys, random, math, json, os
from collections import defaultdict, deque
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QGroupBox, QGraphicsView,
    QGraphicsScene, QGraphicsItem, QGridLayout, QCheckBox,
    QTextEdit, QTabWidget, QLineEdit, QMenu, QFileDialog,
    QComboBox, QHeaderView, QTableWidget, QTableWidgetItem,
    QDialog, QDialogButtonBox, QMessageBox, QSplitter,
    QFrame, QSizePolicy, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal, Property
from PySide6.QtGui import (
    QBrush, QPen, QColor, QFont, QPainter, QRadialGradient, QPainterPath,
    QAction, QKeySequence, QPixmap, QImage
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

PERSONALITIES = ["Ambitious","Wise","Creative","Ruthless","Pious",
                 "Charismatic","Cunning","Nurturing","Reckless","Stoic"]
PERSONALITY_COLORS = {
    "Ambitious": QColor(255,100,100), "Wise": QColor(180,160,255),
    "Creative": QColor(255,200,100), "Ruthless": QColor(200,50,50),
    "Pious": QColor(255,255,180), "Charismatic": QColor(255,150,200),
    "Cunning": QColor(150,200,150), "Nurturing": QColor(150,220,255),
    "Reckless": QColor(255,130,50), "Stoic": QColor(160,170,180),
}

SKILL_NAMES = ["combat","diplomacy","scholarship","craft","leadership","survival"]
SKILL_COLORS = {
    "combat": QColor(255,80,80), "diplomacy": QColor(100,200,255),
    "scholarship": QColor(200,160,255), "craft": QColor(255,200,100),
    "leadership": QColor(255,215,0), "survival": QColor(100,220,100),
}

REL_FRIENDSHIP = "friendship"
REL_RIVALRY = "rivalry"
REL_MENTORSHIP = "mentorship"
REL_COLORS = {
    REL_FRIENDSHIP: QColor(100,220,100,60),
    REL_RIVALRY: QColor(255,60,60,60),
    REL_MENTORSHIP: QColor(180,160,255,60),
}

ACHIEVEMENTS = {
    "first_birth": ("First Birth", "Witness the first birth"),
    "pop_50": ("Growing Village", "Reach 50 living"),
    "pop_100": ("Thriving Town", "Reach 100 living"),
    "pop_200": ("Bustling City", "Reach 200 living"),
    "gen_5": ("Five Generations", "Reach generation 5"),
    "gen_10": ("Deep Roots", "Reach generation 10"),
    "immortal_dynasty": ("Immortal Dynasty", "3+ living immortals"),
    "house_extinct": ("Fallen House", "A house goes extinct"),
    "survive_plague": ("Plague Survivor", "Survive a plague"),
    "first_awakening": ("First Awakening", "Witness an awakening"),
    "centenarian": ("Centenarian", "Mortal reaches age 100"),
    "golden_age": ("Golden Era", "Experience a golden age"),
    "house_war": ("House War", "Witness a house war"),
    "prestige_10": ("Prestigious", "House reaches 10 prestige"),
    "diverse_gene": ("Gene Diversity", "All 3 blood types alive"),
    "marriage_50": ("50 Marriages", "Witness 50 marriages"),
    "first_alliance": ("Diplomatic Bond", "Houses form an alliance"),
    "master_craftsman": ("Master Artisan", "Craft skill 0.9+"),
    "legendary_warrior": ("Legend of War", "Combat skill 0.9+"),
    "sage": ("True Wisdom", "Scholarship skill 0.9+"),
    "social_butterfly": ("Well-Connected", "5+ friendships"),
    "blood_feud": ("Vendetta", "Rivalry spans 3+ generations"),
    "mentor_legacy": ("Mentor's Pride", "Mentee outlives mentor 50+ yrs"),
}


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
        self.feuds = set()
        self.feud_intensity = 0
        self.allies = set()
        self.alliance_trust = {}
        self.strategy = "neutral"
        self.resources = 1.0
        self.trade_agreements = set()
        self.dominant_personality = "Stoic"
    def color_a(self, a=255):
        return QColor(self.color.red(), self.color.green(), self.color.blue(), a)


class Memory:
    __slots__ = ['year','event_type','description','emotional_impact','related_ids']
    def __init__(self, year, event_type, description, emotional_impact=0.0, related_ids=None):
        self.year = year; self.event_type = event_type; self.description = description
        self.emotional_impact = emotional_impact; self.related_ids = related_ids or set()


class Relationship:
    __slots__ = ['person_id','other_id','rel_type','strength','year_formed']
    def __init__(self, pid, oid, rel_type, strength=0.5, year=0):
        self.person_id = pid; self.other_id = oid; self.rel_type = rel_type
        self.strength = strength; self.year_formed = year


class Person:
    _ctr = 0
    def __init__(self, a1="i", a2="i", mother=None, father=None, house=None, gen=0):
        Person._ctr += 1
        self.id = Person._ctr
        self.name = random.choice(NAMES)
        self.age = 0.0; self.is_alive = True; self.death_age = None; self.death_cause = None
        self.allele1, self.allele2 = a1, a2
        self.traits = {k: 0.5 for k in ("longevity","fertility","resilience","charisma")}
        self.personality = random.choice(PERSONALITIES)
        self.happiness = random.uniform(-0.1, 0.3)
        self.skills = {s: random.uniform(0.05, 0.2) for s in SKILL_NAMES}
        self.mother, self.father = mother, father
        self.children = []; self.spouse = None
        self.generation = gen; self.house = house
        self.repro_cd = random.uniform(5, 14)
        self.marry_cd = random.uniform(0, 4)
        self.born_year = 0
        self.x = self.y = self.target_x = self.target_y = 0.0
        self.node = None
        self._anc_cache = None; self._anc_cache_id = None
        self.personality_strength = random.uniform(0.3, 1.0)
        self.kills = 0; self.role = None
        self.gender = random.choice(["M", "F"])        
        self.relationships = {}
        self.memories = []
        self.role_experience = 0.0; self.role_age = 0.0
        self.influence = 0.1; 
        self._last_ai_tick = 0.0
        self._mentored_by = None; self._mentees = []
        self.blood_type = self._blood()
        self.max_age = self._max_age()
        self._inherit(mother, father)


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
        for s in SKILL_NAMES:
            vals = []
            if m: vals.append(m.skills.get(s, 0.1) * 0.3)
            if f: vals.append(f.skills.get(s, 0.1) * 0.3)
            base = sum(vals) / max(len(vals), 1)
            self.skills[s] = max(0.02, min(0.3, base + random.gauss(0, 0.05)))
        if m and f and random.random() < 0.6:
            self.personality = random.choice([m.personality, f.personality])
        elif m and random.random() < 0.3: self.personality = m.personality
        elif f and random.random() < 0.3: self.personality = f.personality
        else: self.personality = random.choice(PERSONALITIES)
        if m and random.random() < 0.3:
            notable = [mem for mem in m.memories if abs(mem.emotional_impact) > 0.5]
            if notable:
                mem = random.choice(notable)
                self.memories.append(Memory(0, "inherited", f"Heard stories: {mem.description}",
                                           mem.emotional_impact * 0.3, {m.id}))

    def _max_age(self):
        if self.blood_type == "immortal": return float("inf")
        base = random.uniform(55, 95)
        if self.blood_type == "carrier":
            base *= 1.5 + self.traits["longevity"] * 0.7
        else:
            base *= 0.85 + self.traits["longevity"] * 0.5
        base *= 1.0 + self.skills["survival"] * 0.15
        if self.personality in ("Stoic", "Pious"): base *= 1.05
        if self.personality == "Reckless": base *= 0.9
        if self.happiness > 0.3: base *= 1.03
        elif self.happiness < -0.3: base *= 0.95
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
        anc = self._ancestors(3); oanc = other._ancestors(3)
        if anc & oanc: return False
        if other.id in anc or self.id in oanc: return False
        if self.house and other.house and other.house.name in self.house.feuds: return False
        if other.id in self.relationships and self.relationships[other.id].rel_type == REL_RIVALRY:
            return False
        return True

    def marriage_compatibility(self, other):
        score = 0.5
        age_diff = abs(self.age - other.age)
        score += max(0, (28 - age_diff) / 28) * 0.15
        for k in self.traits:
            score += min(self.traits[k], other.traits[k]) * 0.02
        compat_pairs = {("Ambitious","Charismatic"),("Wise","Pious"),("Creative","Nurturing"),
                       ("Stoic","Wise"),("Cunning","Ambitious"),("Charismatic","Nurturing")}
        if (self.personality, other.personality) in compat_pairs or \
           (other.personality, self.personality) in compat_pairs:
            score += 0.12
        if self.house and other.house and self.house is other.house: score += 0.08
        for s in SKILL_NAMES:
            if abs(self.skills[s] - other.skills[s]) > 0.3: score += 0.02
        if other.id in self.relationships and self.relationships[other.id].rel_type == REL_FRIENDSHIP:
            score += 0.15 * self.relationships[other.id].strength
        if other.id in self.relationships and self.relationships[other.id].rel_type == REL_RIVALRY:
            score -= 0.2
        return max(0.0, min(1.0, score))

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

    def get_friends(self):
        return [rid for rid, r in self.relationships.items() if r.rel_type == REL_FRIENDSHIP]
    def get_rivals(self):
        return [rid for rid, r in self.relationships.items() if r.rel_type == REL_RIVALRY]
    def get_mentors(self):
        return [rid for rid, r in self.relationships.items() if r.rel_type == REL_MENTORSHIP]

    def add_relationship(self, other_id, rel_type, strength=0.5, year=0):
        self.relationships[other_id] = Relationship(self.id, other_id, rel_type, strength, year)
    def remove_relationship(self, other_id):
        self.relationships.pop(other_id, None)

    def add_memory(self, year, event_type, description, emotional_impact=0.0, related_ids=None):
        self.memories.append(Memory(year, event_type, description, emotional_impact, related_ids))
        if emotional_impact > 0: self.happiness = min(1.0, self.happiness + emotional_impact * 0.1)
        elif emotional_impact < 0: self.happiness = max(-1.0, self.happiness + emotional_impact * 0.1)
        if len(self.memories) > 20: self.memories = self.memories[-20:]

    def tick(self, dt):
        self.age += dt
        if self.repro_cd > 0: self.repro_cd -= dt
        if self.marry_cd > 0: self.marry_cd -= dt
        self.role_age += dt
        if self.is_alive and self.age > 5: self._passive_skill_growth(dt)
        if self.blood_type != "immortal" and self.age >= self.max_age:
            self.is_alive = False; self.death_age = self.age
            if not self.death_cause: self.death_cause = "old age"

    def _passive_skill_growth(self, dt):
        growth = dt * 0.001
        affinities = {
            "Ambitious": {"leadership": 3, "diplomacy": 1.5},
            "Wise": {"scholarship": 3, "leadership": 1},
            "Creative": {"craft": 3, "scholarship": 1.5},
            "Ruthless": {"combat": 3, "survival": 1.5},
            "Pious": {"scholarship": 1.5, "diplomacy": 2},
            "Charismatic": {"diplomacy": 3, "leadership": 1.5},
            "Cunning": {"diplomacy": 1.5, "survival": 2},
            "Nurturing": {"craft": 1.5, "scholarship": 1},
            "Reckless": {"combat": 2.5, "survival": 2},
            "Stoic": {"survival": 3, "combat": 1},
        }
        aff = affinities.get(self.personality, {})
        for skill, mult in aff.items():
            self.skills[skill] = min(1.0, self.skills[skill] + growth * mult)
        role_skills = {
            "Leader": {"leadership": 2.5, "diplomacy": 1.5},
            "Elder": {"scholarship": 2, "leadership": 1},
            "Artisan": {"craft": 3, "scholarship": 0.5},
            "Warrior": {"combat": 3, "survival": 1.5},
            "Cleric": {"scholarship": 2, "diplomacy": 1.5},
            "Healer": {"craft": 1.5, "scholarship": 1.5},
            "Diplomat": {"diplomacy": 3, "leadership": 1},
            "Spy": {"survival": 2, "diplomacy": 1.5},
            "Scholar": {"scholarship": 3, "craft": 0.5},
            "Merchant": {"diplomacy": 1.5, "craft": 1.5},
            "Commoner": {"survival": 1, "craft": 0.5},
        }
        rs = role_skills.get(self.role, {})
        for skill, mult in rs.items():
            self.skills[skill] = min(1.0, self.skills[skill] + growth * mult)
        if self.age > 50:
            self.skills["scholarship"] = min(1.0, self.skills["scholarship"] + growth * 0.5)
        for s in self.skills:
            if self.skills[s] > 0.7:
                self.skills[s] = min(1.0, self.skills[s] + (1.0 - self.skills[s]) * growth * 0.1)

    def color(self):
        if not self.is_alive: return QColor(90,90,90,45)
        if self.is_immortal:
            p=0.5+0.5*math.sin(self.age*0.1)
            return QColor(int(200+55*p),int(175+40*p),int(20+30*p),240)
        if self.is_carrier:
            p=0.5+0.5*math.sin(self.age*0.07)
            return QColor(int(130+50*p),int(165+45*p),int(215+40*p),230)
        if self.age < 15: return QColor(100,225,100,225)
        if self.age < 30:
            t=(self.age-15)/15
            return QColor(int(100*(1-t)+60*t),int(225*(1-t)+185*t),int(100*(1-t)+230*t),225)
        if self.age < 55:
            t=(self.age-30)/25
            return QColor(int(60*(1-t)+140*t),int(185*(1-t)+120*t),int(230*(1-t)+210*t),225)
        t=min(1.0,(self.age-55)/40)
        return QColor(int(140*(1-t)+165*t),int(120*(1-t)+135*t),int(210*(1-t)+155*t),max(130,int(225-t*80)))

    def radius(self):
        if not self.is_alive: return 6
        if self.age < 15: return 6+self.age*0.35
        return 15 if self.is_immortal else (14 if self.is_carrier else 13)

    def to_dict(self):
        rel_data = {}
        for rid, r in self.relationships.items():
            rel_data[str(rid)] = [r.rel_type, r.strength, r.year_formed]
        mem_data = [[m.year, m.event_type, m.description, m.emotional_impact, list(m.related_ids)]
                     for m in self.memories[-10:]]
        return dict(
            id=self.id, name=self.name, age=self.age, is_alive=self.is_alive,
            death_age=self.death_age, death_cause=self.death_cause,
            allele1=self.allele1, allele2=self.allele2,
            blood_type=self.blood_type, traits=self.traits,
            mother_id=self.mother.id if self.mother else None,
            father_id=self.father.id if self.father else None,
            children_ids=[c.id for c in self.children],
            spouse_id=self.spouse.id if self.spouse else None,
            generation=self.generation, max_age=self.max_age,
            repro_cd=self.repro_cd, marry_cd=self.marry_cd,
            born_year=self.born_year, x=self.x, y=self.y,
            target_x=self.target_x, target_y=self.target_y,
            house_idx=self.house.name if self.house else None,
            personality=self.personality, personality_strength=self.personality_strength,
            gender=self.gender, kills=self.kills,
            skills=self.skills, relationships=rel_data, memories=mem_data,
            role=self.role, role_experience=self.role_experience, role_age=self.role_age,
            influence=self.influence, happiness=self.happiness,
            mentored_by=self._mentored_by, mentees=list(self._mentees))


class GameEvent:
    PLAGUE="plague"; GOLDEN="golden"; CATASTROPHE="catastrophe"; AWAKEN="awaken"
    BLESS="bless"; MIGRATE="migrate"; FAMINE="famine"; RENAISSANCE="renaissance"
    WAR="war"; BETRAYAL="betrayal"; EPIDEMIC="epidemic"; MIRACLE="miracle"
    ICONS = {PLAGUE:"☠",GOLDEN:"✦",CATASTROPHE:"⚡",AWAKEN:"✨",
             BLESS:"🕊",MIGRATE:"🚶",FAMINE:"🌾",RENAISSANCE:"🎨",
             WAR:"⚔",BETRAYAL:"🗡",EPIDEMIC:"🦠",MIRACLE:"⭐"}
    def __init__(self, etype, year, desc, dur=0, mag=1.0):
        self.etype, self.year, self.desc = etype, year, desc
        self.duration, self.magnitude, self.remaining = dur, mag, dur
    @property
    def icon(self): return self.ICONS.get(self.etype,"?")
    def tick(self, dt):
        if self.remaining > 0: self.remaining -= dt


# ── Graphics Items ───────────────────────────────────────────────────
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


# v5: RelationshipEdge for friendship/rivalry/mentorship
class RelationshipEdge(QGraphicsItem):
    def __init__(self, p1, p2, rel_type):
        super().__init__(); self.p1=p1; self.p2=p2; self.rel_type=rel_type; self.setZValue(0.5)
    def boundingRect(self):
        x1,y1,x2,y2 = self.p1.x,self.p1.y,self.p2.x,self.p2.y; m=15
        return QRectF(min(x1,x2)-m,min(y1,y2)-m,abs(x2-x1)+2*m,abs(y2-y1)+2*m)
    def paint(self, painter, option, widget):
        x1,y1,x2,y2 = self.p1.x,self.p1.y,self.p2.x,self.p2.y
        r1,r2 = self.p1.radius(),self.p2.radius()
        dx,dy = x2-x1,y2-y1; dist=math.hypot(dx,dy)
        if dist<0.1: return
        ux,uy = dx/dist,dy/dist
        sx,sy = x1+ux*(r1+3),y1+uy*(r1+3); ex,ey = x2-ux*(r2+3),y2-uy*(r2+3)
        # get strength from p1's relationships
        rel = self.p1.relationships.get(self.p2.id)
        strength = rel.strength if rel else 0.5
        alpha = int(40 + strength * 80)
        if not self.p1.is_alive or not self.p2.is_alive: alpha = max(15, alpha // 3)
        dimmed = getattr(self.p1, '_dimmed', False) or getattr(self.p2, '_dimmed', False)
        if dimmed: alpha = max(5, alpha // 4)
        if self.rel_type == REL_FRIENDSHIP:
            col = QColor(100,220,100,alpha); style = Qt.DashLine; w = 1.2 + strength
        elif self.rel_type == REL_RIVALRY:
            col = QColor(255,60,60,alpha); style = Qt.DotLine; w = 1.0 + strength * 0.8
        elif self.rel_type == REL_MENTORSHIP:
            col = QColor(180,160,255,alpha); style = Qt.DashDotLine; w = 1.2 + strength * 0.5
        else:
            col = QColor(150,150,150,alpha); style = Qt.SolidLine; w = 1.0
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(col, w, style))
        painter.drawLine(QPointF(sx,sy),QPointF(ex,ey))
    def sync(self): self.prepareGeometryChange(); self.update()


class PersonNode(QGraphicsItem):
    """v5: Draggable node with personality, influence, skills on hover."""
    def __init__(self, person, on_select=None, on_context=None, on_drag=None):
        super().__init__()
        self.person = person
        self.on_select = on_select
        self.on_context = on_context
        self.on_drag_end = on_drag
        self.highlighted = False
        self.dimmed = False
        self._hover = False
        self._dragging = False
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setZValue(10)
        self.setPos(person.x, person.y)

    def hoverEnterEvent(self, e):
        self._hover = True; self.update(); self.setZValue(20)
    def hoverLeaveEvent(self, e):
        if not self._dragging:
            self._hover = False; self.update(); self.setZValue(10)
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._dragging = True
            if self.on_select: self.on_select(self.person)
        super().mousePressEvent(e)
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self._hover = False; self.setZValue(10)
            self.person.target_x = self.person.x = self.pos().x()
            self.person.target_y = self.person.y = self.pos().y()
            if self.on_drag_end: self.on_drag_end(self.person)
        super().mouseReleaseEvent(e)
    def mouseMoveEvent(self, e):
        if self._dragging and e.buttons() & Qt.LeftButton:
            self.setPos(self.mapToParent(e.pos()))
            self.person.x = self.pos().x()
            self.person.y = self.pos().y()
        super().mouseMoveEvent(e)
    def contextMenuEvent(self, e):
        if self.on_context: self.on_context(self.person, e.screenPos())
        super().contextMenuEvent(e)
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.person.x = self.pos().x()
            self.person.y = self.pos().y()
            self.person.target_x = self.pos().x()
            self.person.target_y = self.pos().y()
        return super().itemChange(change, value)

    def boundingRect(self):
        r=self.person.radius(); e=30 if self.person.is_immortal else 18
        return QRectF(-r-e,-r-e,2*(r+e),2*(r+e)+52)

    def paint(self, painter, option, widget):
        p=self.person; r=p.radius(); c=p.color()
        painter.setRenderHint(QPainter.Antialiasing)
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
            painter.setBrush(QBrush(g)); painter.setPen(Qt.NoPen); painter.drawEllipse(QRectF(-r*2,-r-4,2*(r+4),2*(r+4)))
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
        # Gender indicator
        if p.is_alive and r>7 and not dim:
            gsym = "M" if p.gender == "M" else "F"
            gcol = QColor(100,180,255,140) if p.gender == "M" else QColor(255,150,200,140)
            painter.setPen(gcol); painter.setFont(QFont("Segoe UI", max(5, int(r*0.35))))
            painter.drawText(QRectF(-r*0.6, -r*0.2, r*1.2, r*0.7), Qt.AlignCenter, gsym)
        # Age
        if p.is_alive and r>=9 and not dim:
            painter.setPen(QColor(255,255,255,190)); painter.setFont(QFont("Segoe UI",max(6,int(r*0.5)),QFont.Bold))
            painter.drawText(QRectF(-r,r*0.1,2*r,r*0.6),Qt.AlignCenter,str(int(p.age)))
        # v5: Influence dot above node
        if p.is_alive and p.influence > 0.3 and not dim:
            iy = -r - 16
            ir = 2 + p.influence * 3
            icol = QColor(255,215,0, int(80 + p.influence * 150))
            painter.setPen(Qt.NoPen); painter.setBrush(QBrush(icol))
            painter.drawEllipse(QPointF(0, iy), ir, ir)
        # Name + info
        show = self._hover or self.highlighted
        if (show or (p.is_alive and r>9)) and not dim:
            a = 230 if show else 140
            painter.setPen(QColor(220,220,220,a))
            painter.setFont(QFont("Segoe UI",7,QFont.Bold if show else QFont.Normal))
            painter.drawText(QRectF(-48,r+2,96,13),Qt.AlignCenter,p.name)
            painter.setFont(QFont("Segoe UI",6))
            if p.is_immortal: st="INF Immortal"
            elif p.is_carrier: st=f"CAR (x{p.max_age/80:.1f})"
            elif not p.is_alive: st=f"Died {int(p.death_age or p.age)}"
            else: st=f"Gen {p.generation}"
            painter.setPen(QColor(180,180,200,a))
            painter.drawText(QRectF(-48,r+13,96,11),Qt.AlignCenter,st)
            if p.house and show:
                painter.setPen(p.house.color_a(min(255,a+40)))
                painter.drawText(QRectF(-48,r+23,96,11),Qt.AlignCenter,p.house.name)
            # v5: personality + role + happiness on hover
            if show:
                pcol = PERSONALITY_COLORS.get(p.personality, QColor(200,200,200))
                painter.setPen(pcol); painter.setFont(QFont("Segoe UI",5))
                painter.drawText(QRectF(-48,r+33,96,10),Qt.AlignCenter,p.personality)
                role_str = p.role or "None"
                painter.setPen(QColor(180,200,220,a)); painter.setFont(QFont("Segoe UI",5))
                painter.drawText(QRectF(-48,r+42,96,9),Qt.AlignCenter,f"{role_str}")
                # happiness indicator
                hcol = QColor(100,220,100) if p.happiness > 0 else QColor(220,100,100) if p.happiness < 0 else QColor(180,180,180)
                painter.setPen(hcol); painter.setFont(QFont("Segoe UI",5))
                hbar = "+" if p.happiness > 0 else ""
                painter.drawText(QRectF(-48,r+50,96,9),Qt.AlignCenter,f"mood:{hbar}{p.happiness:.2f}")
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
        # v5: Top 3 skills on hover
        if show and p.is_alive and not dim:
            sorted_skills = sorted(p.skills.items(), key=lambda x: x[1], reverse=True)[:3]
            sx,sy = -r-55, -10
            for i,(sk,sv) in enumerate(sorted_skills):
                yy = sy + i*11
                scol = SKILL_COLORS.get(sk, QColor(180,180,180))
                painter.setPen(QColor(180,180,200,200)); painter.setFont(QFont("Segoe UI",4))
                painter.drawText(QRectF(sx,yy,55,9),Qt.AlignLeft,f"{sk[:4]}")
                painter.setPen(Qt.NoPen); painter.setBrush(QColor(40,40,60,180))
                painter.drawRoundedRect(QRectF(sx,yy+8,50,3),1,1)
                painter.setBrush(scol)
                painter.drawRoundedRect(QRectF(sx,yy+8,int(50*sv),3),1,1)
        # Death X
        if not p.is_alive and not dim:
            painter.setPen(QPen(QColor(200,40,40,100),2)); d=r*0.5
            painter.drawLine(QPointF(-d,-d),QPointF(d,d)); painter.drawLine(QPointF(d,-d),QPointF(-d,d))

    def sync(self):
        self.prepareGeometryChange()
        self.setPos(self.person.x, self.person.y)
        self.update()


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


# ── Charts ─────────────────────────────────────────────────────────
class PopChart(QWidget):
    def __init__(self):
        super().__init__(); self.setMinimumHeight(140); self.setMaximumHeight(200); self.data=[]
        self.event_markers = []
    def set_data(self, d): self.data=d; self.update()
    def set_event_markers(self, markers): self.event_markers=markers; self.update()
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
        if self.data:
            min_year = self.data[0][0]; max_year = self.data[-1][0]
            year_span = max(max_year - min_year, 1)
            event_colors = {
                "plague": QColor(200,60,60,120), "catastrophe": QColor(255,100,50,120),
                "awaken": QColor(255,215,0,120), "golden": QColor(255,215,100,100),
                "famine": QColor(180,120,60,100), "bless": QColor(100,200,150,100),
                "renaissance": QColor(150,100,220,100), "migrate": QColor(100,180,220,100),
                "war": QColor(255,50,50,140), "epidemic": QColor(200,80,200,120),
                "miracle": QColor(255,255,100,120), "betrayal": QColor(180,50,80,120),
                "alliance": QColor(100,220,100,120),
            }
            for ey, etype in self.event_markers[-30:]:
                if min_year <= ey <= max_year:
                    ex = m + cw * (ey - min_year) / year_span
                    col = event_colors.get(etype, QColor(150,150,150,80))
                    painter.setPen(QPen(col, 1.5, Qt.DotLine))
                    painter.drawLine(int(ex), m, int(ex), m + ch)
        def dl(idx,col):
            painter.setPen(QPen(col,1.5)); path=QPainterPath()
            for i,d in enumerate(self.data):
                x=m+cw*i/(len(self.data)-1); y=m+ch*(1-d[idx]/mx)
                path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
            painter.drawPath(path)
        dl(1,QColor(80,170,230)); dl(2,QColor(140,180,255)); dl(3,QColor(255,215,0))
        if len(self.data) >= 2:
            painter.setPen(QPen(QColor(255,100,100,120),1.0, Qt.DashLine))
            path = QPainterPath()
            for i, d in enumerate(self.data):
                total = d[1] + d[2] + d[3]; freq = (d[3] + d[2]*0.5) / max(total, 1)
                x = m + cw*i/(len(self.data)-1); y = m + ch*(1-freq)
                path.moveTo(x,y) if i==0 else path.lineTo(x,y)
            painter.drawPath(path)
        painter.setFont(QFont("Segoe UI",7)); lx=m+5
        for lb,co in [("Mortals",QColor(80,170,230)),("Carriers",QColor(140,180,255)),
                       ("Immortals",QColor(255,215,0)),("I-freq",QColor(255,100,100,120))]:
            painter.setPen(Qt.NoPen); painter.setBrush(co); painter.drawEllipse(lx,5,6,6)
            painter.setPen(QColor(180,180,200)); painter.drawText(lx+9,5,60,12,Qt.AlignVCenter|Qt.AlignLeft,lb); lx+=75
        painter.end()


class GeneFreqChart(QWidget):
    def __init__(self):
        super().__init__(); self.setMinimumHeight(100); self.setMaximumHeight(150); self.data=[]
    def set_data(self, d): self.data=d; self.update()
    def paintEvent(self, event):
        painter=QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        w,h = self.width(),self.height(); m=35
        painter.fillRect(self.rect(),QColor(18,18,35))
        if len(self.data)<2:
            painter.setPen(QColor(120,120,150)); painter.setFont(QFont("Segoe UI",9))
            painter.drawText(self.rect(),Qt.AlignCenter,"Collecting data..."); painter.end(); return
        cw,ch = w-2*m, h-2*m
        painter.setPen(QPen(QColor(60,60,80),0.5))
        for i in range(5):
            y=m+ch*i/4; painter.drawLine(m,int(y),w-m,int(y))
            pct = int((1-i/4)*100)
            painter.setPen(QColor(100,100,130)); painter.setFont(QFont("Segoe UI",6))
            painter.drawText(2,int(y)-4,m-4,12,Qt.AlignRight|Qt.AlignVCenter,f"{pct}%")
            painter.setPen(QPen(QColor(60,60,80),0.5))
        lines = [(3, QColor(255,215,0,200), "II"), (2, QColor(140,180,255,200), "Ii"), (1, QColor(80,170,230,200), "ii")]
        for idx, col, label in lines:
            painter.setPen(QPen(col, 1.5)); path = QPainterPath()
            for i, d in enumerate(self.data):
                total = d[1] + d[2] + d[3]; freq = d[idx] / max(total, 1)
                x = m + cw*i/(len(self.data)-1); y = m + ch*(1-freq)
                path.moveTo(x,y) if i==0 else path.lineTo(x,y)
            painter.drawPath(path)
        painter.setFont(QFont("Segoe UI",7)); lx=m+5
        for lb,co in [("ii freq",QColor(80,170,230)),("Ii freq",QColor(140,180,255)),("II freq",QColor(255,215,0))]:
            painter.setPen(Qt.NoPen); painter.setBrush(co); painter.drawEllipse(lx,3,6,6)
            painter.setPen(QColor(180,180,200)); painter.drawText(lx+9,3,55,12,Qt.AlignVCenter|Qt.AlignLeft,lb); lx+=70
        painter.end()


class PopPyramid(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(120); self.setMaximumHeight(180)
        self.male_data = []; self.female_data = []
    def set_data(self, people):
        m_bins = defaultdict(int); f_bins = defaultdict(int)
        bins = ["0-14", "15-29", "30-44", "45-59", "60-74", "75-89", "90+"]
        ranges = [(0,14),(15,29),(30,44),(45,59),(60,74),(75,89),(90,9999)]
        for p in people:
            if not p.is_alive: continue
            for idx, (lo, hi) in enumerate(ranges):
                if lo <= p.age <= hi:
                    if p.gender == "M": m_bins[idx] += 1
                    else: f_bins[idx] += 1
                    break
        self.male_data = [(bins[i], m_bins[i]) for i in range(len(bins))]
        self.female_data = [(bins[i], f_bins[i]) for i in range(len(bins))]
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(self.rect(), QColor(18,18,35))
        if not self.male_data:
            painter.setPen(QColor(120,120,150)); painter.setFont(QFont("Segoe UI",9))
            painter.drawText(self.rect(), Qt.AlignCenter, "Collecting data..."); painter.end(); return
        ml = max(max(d[1] for d in self.male_data), max(d[1] for d in self.female_data), 1)
        lm = 45; rm = 45; gap = 4
        bar_w = (w - lm - rm - gap) / 2
        nb = len(self.male_data)
        bh = max(6, (h - 20) / nb)
        cy = 10
        painter.setFont(QFont("Segoe UI", 6))
        for i, ((mlbl, mc), (flbl, fc)) in enumerate(zip(self.male_data, self.female_data)):
            y = cy + i * bh
            male_color = QColor(80, 170, 230, 200)
            mw = bar_w * mc / ml
            painter.setPen(Qt.NoPen); painter.setBrush(male_color)
            painter.drawRect(QRectF(int(lm + bar_w - mw), y, int(mw), int(bh - 1)))
            fem_color = QColor(255, 150, 200, 200)
            fw = bar_w * fc / ml
            painter.setBrush(fem_color)
            painter.drawRect(QRectF(int(lm + bar_w + gap), y, int(fw), int(bh - 1)))
            painter.setPen(QColor(160,160,180))
            painter.drawText(QRectF(0, y, lm - 3, bh), Qt.AlignRight | Qt.AlignVCenter, mlbl)
            if mc > 0:
                painter.setPen(QColor(180,200,240))
                painter.drawText(QRectF(int(lm + bar_w - mw - 18), y, 18, bh), Qt.AlignRight | Qt.AlignVCenter, str(mc))
            if fc > 0:
                painter.setPen(QColor(240,180,200))
                painter.drawText(QRectF(int(lm + bar_w + gap + fw + 2), y, 18, bh), Qt.AlignLeft | Qt.AlignVCenter, str(fc))
        painter.setPen(QColor(100,100,130)); painter.setFont(QFont("Segoe UI",6))
        mid_x = lm + bar_w + gap/2
        painter.drawText(QRectF(int(mid_x-10), h-14, 20, 12), Qt.AlignCenter, "Age")
        painter.setFont(QFont("Segoe UI",7))
        painter.setPen(Qt.NoPen); painter.setBrush(QColor(80,170,230,200))
        painter.drawEllipse(lm, 2, 6, 6)
        painter.setPen(QColor(180,180,200)); painter.drawText(lm+9, 0, 40, 12, Qt.AlignVCenter|Qt.AlignLeft, "Male")
        painter.setPen(Qt.NoPen); painter.setBrush(QColor(255,150,200,200))
        painter.drawEllipse(lm+55, 2, 6, 6)
        painter.setPen(QColor(180,180,200)); painter.drawText(lm+64, 0, 40, 12, Qt.AlignVCenter|Qt.AlignLeft, "Female")
        painter.end()


class MiniMap(QWidget):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.setMinimumSize(140, 100); self.setMaximumSize(200, 150)
        self.setStyleSheet("border:1px solid #333355; border-radius:4px;")
        self.setMouseTracking(True)
    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(self.rect(), QColor(12, 12, 24, 200))
        scene = self.parent_view.scene()
        if not scene: painter.end(); return
        items = scene.items()
        if not items: painter.end(); return
        br = scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)
        if br.width() <= 0 or br.height() <= 0: painter.end(); return
        sx = w / br.width(); sy = h / br.height()
        scale = min(sx, sy) * 0.9
        ox = (w - br.width() * scale) / 2
        oy = (h - br.height() * scale) / 2
        for item in items:
            if isinstance(item, PersonNode):
                p = item.person
                px = ox + (p.x - br.x()) * scale
                py = oy + (p.y - br.y()) * scale
                if not (0 <= px <= w and 0 <= py <= h): continue
                if p.is_alive:
                    if p.is_immortal: col = QColor(255, 215, 0)
                    elif p.is_carrier: col = QColor(140, 180, 255)
                    else: col = QColor(80, 170, 230)
                    r = 2
                else:
                    col = QColor(80, 80, 80, 80); r = 1
                painter.setPen(Qt.NoPen); painter.setBrush(col)
                painter.drawEllipse(QPointF(px, py), r, r)
        vr = self.parent_view.mapToScene(self.parent_view.viewport().rect()).boundingRect()
        vx = ox + (vr.x() - br.x()) * scale
        vy = oy + (vr.y() - br.y()) * scale
        vw = vr.width() * scale
        vh = vr.height() * scale
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(vx, vy, vw, vh))
        painter.end()
    def mousePressEvent(self, e):
        scene = self.parent_view.scene()
        if not scene: return
        br = scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)
        if br.width() <= 0 or br.height() <= 0: return
        w, h = self.width(), self.height()
        sx = w / br.width(); sy = h / br.height()
        scale = min(sx, sy) * 0.9
        ox = (w - br.width() * scale) / 2
        oy = (h - br.height() * scale) / 2
        scene_x = (e.pos().x() - ox) / scale + br.x()
        scene_y = (e.pos().y() - oy) / scale + br.y()
        self.parent_view.centerOn(scene_x, scene_y)


class ZoomView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene); self._z=0
        self.setRenderHints(QPainter.Antialiasing|QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
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


# ── Simulation Engine v5 ───────────────────────────────────────────
class Engine:
    def __init__(self):
        self.people=[]; self.houses=[]; self.events=[]; self.year=0.0
        self.repro_rate=0.012; self.marry_rate=0.03
        self.total_births=0; self.total_deaths=0; self.total_marriages=0
        self.effects=[]; self.log=[]; self.pop_hist=[]; self._last_snap=-5
        self.event_markers=[]
        self._pdict = {}
        self.achievements = set()
        self.achievement_log = []
        self.timeline = []
        self._last_timeline_snap = -10
        self.wars = []
        self._war_cooldown = 0
        # v5 fields
        self.rel_edges = {}
        self._ai_tick_interval = 3.0
        self._last_ai_tick_year = -5
        self.total_friendships_formed = 0
        self.total_rivalries_formed = 0
        self.total_mentorships = 0
        self.total_alliances_formed = 0

    def _rebuild_dict(self):
        self._pdict = {p.id: p for p in self.people}

    def get_person(self, pid):
        return self._pdict.get(pid)

    def create_house(self, name=None, color=None):
        h=House(name,color); self.houses.append(h); return h

    def add_person(self, a1="i", a2="i", mother=None, father=None, house=None, gen=0):
        if sum(1 for p in self.people if p.is_alive)>=MAX_POP: return None
        p=Person(a1,a2,mother,father,house,gen); p.born_year=self.year
        if mother:
            mother.children.append(p)
            mother.add_memory(self.year, "birth", f"Child {p.name} born", 0.6, {p.id})
        if father:
            father.children.append(p)
            father.add_memory(self.year, "birth", f"Child {p.name} born", 0.6, {p.id})
        self.people.append(p); self._pdict[p.id] = p; self.total_births+=1
        if house and house.extinct: house.extinct=False
        # v5: assign role
        self._assign_role(p)
        # v5: create sibling friendships
        siblings = set()
        if mother:
            for c in mother.children:
                if c is not p and c.is_alive and c.age < 20:
                    siblings.add(c.id)
        if father:
            for c in father.children:
                if c is not p and c.is_alive and c.age < 20:
                    siblings.add(c.id)
        for sid in siblings:
            if random.random() < 0.4:
                sp = self.get_person(sid)
                if sp and p.id not in sp.relationships and sid not in p.relationships:
                    p.add_relationship(sid, REL_FRIENDSHIP, 0.7, int(self.year))
                    sp.add_relationship(p.id, REL_FRIENDSHIP, 0.7, int(self.year))
                    self.total_friendships_formed += 1
        self.layout(); return p

    def _assign_role(self, p):
        """v5: Score ALL possible roles and assign the best fit."""
        if p.age < 15:
            p.role = None; return
        role_scores = {}
        # Personality affinities
        pers_affin = {
            "Ambitious": {"Leader": 0.9, "Diplomat": 0.5, "Merchant": 0.4, "Warrior": 0.3},
            "Wise": {"Elder": 0.9, "Scholar": 0.8, "Cleric": 0.5, "Diplomat": 0.3},
            "Creative": {"Artisan": 0.9, "Scholar": 0.5, "Merchant": 0.4, "Healer": 0.3},
            "Ruthless": {"Warrior": 0.9, "Spy": 0.7, "Leader": 0.4, "Merchant": 0.3},
            "Pious": {"Cleric": 0.9, "Elder": 0.7, "Healer": 0.6, "Scholar": 0.4},
            "Charismatic": {"Diplomat": 0.9, "Leader": 0.7, "Merchant": 0.6, "Cleric": 0.4},
            "Cunning": {"Spy": 0.9, "Diplomat": 0.6, "Merchant": 0.5, "Warrior": 0.3},
            "Nurturing": {"Healer": 0.9, "Artisan": 0.6, "Cleric": 0.5, "Scholar": 0.3},
            "Reckless": {"Warrior": 0.8, "Spy": 0.5, "Merchant": 0.4, "Artisan": 0.3},
            "Stoic": {"Elder": 0.7, "Warrior": 0.6, "Scholar": 0.5, "Healer": 0.3},
        }
        # Skill affinities
        skill_affin = {
            "Leader": {"leadership": 0.5, "diplomacy": 0.3},
            "Elder": {"scholarship": 0.4, "leadership": 0.3},
            "Artisan": {"craft": 0.5, "scholarship": 0.2},
            "Warrior": {"combat": 0.5, "survival": 0.3},
            "Cleric": {"scholarship": 0.3, "diplomacy": 0.3},
            "Healer": {"craft": 0.3, "scholarship": 0.3},
            "Diplomat": {"diplomacy": 0.5, "leadership": 0.2},
            "Spy": {"survival": 0.4, "diplomacy": 0.2},
            "Scholar": {"scholarship": 0.5, "craft": 0.2},
            "Merchant": {"diplomacy": 0.3, "craft": 0.2},
            "Commoner": {},
        }
        all_roles = ["Leader","Elder","Artisan","Warrior","Cleric","Healer","Diplomat","Spy","Scholar","Merchant","Commoner"]
        for role in all_roles:
            score = 0.1  # base score for any role
            # personality bonus
            pa = pers_affin.get(p.personality, {})
            score += pa.get(role, 0) * p.personality_strength
            # skill bonus
            sa = skill_affin.get(role, {})
            for sk, w in sa.items():
                score += p.skills.get(sk, 0) * w
            # age bonus for some roles
            if role == "Elder" and p.age > 50: score += 0.3
            if role == "Warrior" and 20 <= p.age <= 45: score += 0.2
            if role == "Leader" and p.age > 30: score += 0.15
            if role == "Commoner": score += 0.05
            # role experience bonus
            if p.role == role: score += p.role_experience * 0.3
            # trait bonus
            if role == "Leader": score += p.traits["charisma"] * 0.3
            if role == "Warrior": score += p.traits["resilience"] * 0.3
            if role == "Scholar": score += p.traits["longevity"] * 0.2
            role_scores[role] = score
        best_role = max(role_scores, key=role_scores.get)
        # Only change role if new role is significantly better (10% margin) or no current role
        if p.role is None or p.role == "Commoner":
            p.role = best_role; p.role_experience = 0; p.role_age = 0
        elif best_role != p.role and role_scores[best_role] > role_scores.get(p.role, 0) * 1.1:
            old_role = p.role
            p.role = best_role
            p.role_experience = 0; p.role_age = 0
            p.add_memory(self.year, "role_change", f"Role changed: {old_role} -> {best_role}", 0.3)

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
            placed,seen=[],set()
            for p in ppl:
                if p.id in seen: continue
                placed.append(p); seen.add(p.id)
                if (p.spouse and p.spouse.is_alive and p.spouse.generation==gn
                        and p.spouse.id not in seen and p.spouse in ppl):
                    placed.append(p.spouse); seen.add(p.spouse.id)
            n=len(placed); sx=-(n-1)*SPACING_X/2
            for i,p in enumerate(placed):
                if not getattr(p, '_manually_placed', False):
                    p.target_x=sx+i*SPACING_X; p.target_y=gn*GEN_Y+60

    # v5: AI Behavior Methods
    def _ai_tick(self):
        """Master AI tick - runs every 3 years."""
        if self.year - self._last_ai_tick_year < self._ai_tick_interval:
            return
        self._last_ai_tick_year = self.year
        self._ai_relationships()
        self._ai_personality_behaviors()
        self._ai_role_evolution()
        self._ai_mentoring()
        self._ai_influence_propagation()
        self._ai_house_strategy()
        self._ai_happiness_decay()

    def _ai_relationships(self):
        """Form/dissolve friendships and rivalries based on proximity, personality, house."""
        alive = [p for p in self.people if p.is_alive and p.age >= 12]
        for p in alive:
            # Form new relationships
            if len(p.relationships) < 8 and random.random() < 0.15:
                candidates = [q for q in alive
                              if q.id not in p.relationships
                              and q.id != p.id
                              and not (p.spouse and p.spouse.id == q.id)]
                if candidates:
                    q = random.choice(candidates)
                    # Same house bonus
                    score = 0.5
                    if p.house and q.house:
                        if p.house is q.house: score += 0.2
                        elif q.house.name in p.house.feuds:
                            # feud tendency -> rivalry
                            if random.random() < 0.3:
                                p.add_relationship(q.id, REL_RIVALRY, 0.4, int(self.year))
                                q.add_relationship(p.id, REL_RIVALRY, 0.4, int(self.year))
                                self.total_rivalries_formed += 1
                            continue
                    # Personality compatibility
                    compat_pairs = {("Ambitious","Charismatic"),("Wise","Pious"),("Creative","Nurturing"),
                                   ("Stoic","Wise"),("Cunning","Ambitious"),("Charismatic","Nurturing")}
                    if (p.personality, q.personality) in compat_pairs or \
                       (q.personality, p.personality) in compat_pairs:
                        score += 0.25
                    # Same personality mild bonus
                    if p.personality == q.personality:
                        score += 0.1
                    # Ruthless tends to form rivalries
                    if p.personality == "Ruthless" and random.random() < 0.3:
                        p.add_relationship(q.id, REL_RIVALRY, 0.3, int(self.year))
                        q.add_relationship(p.id, REL_RIVALRY, 0.3, int(self.year))
                        self.total_rivalries_formed += 1
                        continue
                    # Form friendship
                    if random.random() < score:
                        strength = random.uniform(0.3, 0.7)
                        p.add_relationship(q.id, REL_FRIENDSHIP, strength, int(self.year))
                        q.add_relationship(p.id, REL_FRIENDSHIP, strength, int(self.year))
                        self.total_friendships_formed += 1
                        p.add_memory(self.year, "friendship", f"Became friends with {q.name}", 0.3, {q.id})
                        q.add_memory(self.year, "friendship", f"Became friends with {p.name}", 0.3, {p.id})
            # Relationship decay/strengthening
            for rid, rel in list(p.relationships.items()):
                other = self.get_person(rid)
                if not other or not other.is_alive:
                    p.remove_relationship(rid)
                    continue
                # Decay
                decay = 0.01
                if rel.rel_type == REL_FRIENDSHIP:
                    # Friends near each other strengthen
                    if abs(p.generation - other.generation) <= 1:
                        rel.strength = min(1.0, rel.strength + 0.02)
                    else:
                        rel.strength -= decay * 2
                elif rel.rel_type == REL_RIVALRY:
                    # Rivals in feuding houses strengthen rivalry
                    if p.house and other.house and other.house.name in p.house.feuds:
                        rel.strength = min(1.0, rel.strength + 0.03)
                    else:
                        rel.strength -= decay
                # Remove weak relationships
                if rel.strength < 0.1:
                    p.remove_relationship(rid)
                    other.remove_relationship(p.id)

    def _ai_personality_behaviors(self):
        """Execute 10 unique personality behavior methods."""
        alive = [p for p in self.people if p.is_alive and p.age >= 16]
        for p in alive:
            ps = p.personality_strength
            if p.personality == "Ambitious":
                self._behavior_ambitious(p, ps)
            elif p.personality == "Wise":
                self._behavior_wise(p, ps)
            elif p.personality == "Creative":
                self._behavior_creative(p, ps)
            elif p.personality == "Ruthless":
                self._behavior_ruthless(p, ps)
            elif p.personality == "Pious":
                self._behavior_pious(p, ps)
            elif p.personality == "Charismatic":
                self._behavior_charismatic(p, ps)
            elif p.personality == "Cunning":
                self._behavior_cunning(p, ps)
            elif p.personality == "Nurturing":
                self._behavior_nurturing(p, ps)
            elif p.personality == "Reckless":
                self._behavior_reckless(p, ps)
            elif p.personality == "Stoic":
                self._behavior_stoic(p, ps)

    def _behavior_ambitious(self, p, strength):
        if random.random() < 0.2 * strength:
            p.skills["leadership"] = min(1.0, p.skills["leadership"] + 0.02)
            p.skills["diplomacy"] = min(1.0, p.skills["diplomacy"] + 0.01)
            p.influence = min(1.0, p.influence + 0.02)
            if p.house:
                p.house.prestige += 0.05 * strength
                p.add_memory(self.year, "ambition", "Pursued leadership goals", 0.2)

    def _behavior_wise(self, p, strength):
        if random.random() < 0.2 * strength and p.age > 30:
            # Mentor younger people
            candidates = [q for q in self.people if q.is_alive and q.age < p.age - 10
                         and q.age >= 12 and p.id not in q.relationships]
            if candidates:
                mentee = random.choice(candidates)
                p.add_relationship(mentee.id, REL_MENTORSHIP, 0.6, int(self.year))
                mentee.add_relationship(p.id, REL_MENTORSHIP, 0.6, int(self.year))
                mentee._mentored_by = p.id
                if mentee.id not in p._mentees: p._mentees.append(mentee.id)
                self.total_mentorships += 1
                p.add_memory(self.year, "mentor", f"Mentored {mentee.name}", 0.3, {mentee.id})
                mentee.add_memory(self.year, "mentored", f"Mentored by {p.name}", 0.3, {p.id})
        p.skills["scholarship"] = min(1.0, p.skills["scholarship"] + 0.01 * strength)

    def _behavior_creative(self, p, strength):
        if random.random() < 0.15 * strength:
            # Boost craft of house members
            if p.house:
                for q in self.people:
                    if q.is_alive and q.house is p.house and q.id != p.id:
                        q.skills["craft"] = min(1.0, q.skills["craft"] + 0.01)
            p.skills["craft"] = min(1.0, p.skills["craft"] + 0.03 * strength)
            p.happiness = min(1.0, p.happiness + 0.05)
            if random.random() < 0.05:
                p.add_memory(self.year, "creation", "Created a masterpiece", 0.5)

    def _behavior_ruthless(self, p, strength):
        if random.random() < 0.1 * strength:
            # Form rivalries
            candidates = [q for q in self.people if q.is_alive and q.id != p.id
                         and q.id not in p.relationships]
            if candidates:
                target = random.choice(candidates)
                p.add_relationship(target.id, REL_RIVALRY, 0.4, int(self.year))
                target.add_relationship(p.id, REL_RIVALRY, 0.3, int(self.year))
                self.total_rivalries_formed += 1
        # May murder (rare)
        if random.random() < 0.02 * strength and p.skills["combat"] > 0.5:
            rivals = p.get_rivals()
            if rivals:
                vid = random.choice(rivals)
                victim = self.get_person(vid)
                if victim and victim.is_alive and victim.age >= 16:
                    # Combat skill check
                    if p.skills["combat"] > victim.skills["combat"] * 0.8:
                        if random.random() < 0.1:
                            victim.is_alive = False; victim.death_age = victim.age
                            victim.death_cause = f"murdered by {p.name}"
                            p.kills += 1; p.skills["combat"] = min(1.0, p.skills["combat"] + 0.05)
                            p.add_memory(self.year, "murder", f"Murdered {victim.name}", -0.3, {victim.id})
                            for fid in p.get_friends():
                                fr = self.get_person(fid)
                                if fr: fr.add_memory(self.year, "shock", f"{p.name} committed murder", -0.4, {p.id})

    def _behavior_pious(self, p, strength):
        if random.random() < 0.2 * strength:
            # Boost resilience of house members
            if p.house:
                for q in self.people:
                    if q.is_alive and q.house is p.house and q.id != p.id:
                        q.traits["resilience"] = min(1.0, q.traits["resilience"] + 0.005)
            p.skills["scholarship"] = min(1.0, p.skills["scholarship"] + 0.01)
            p.happiness = min(1.0, p.happiness + 0.03)

    def _behavior_charismatic(self, p, strength):
        if random.random() < 0.3 * strength:
            # Form strong friendships fast
            candidates = [q for q in self.people if q.is_alive and q.age >= 14
                         and q.id not in p.relationships and q.id != p.id]
            if candidates:
                q = random.choice(candidates)
                p.add_relationship(q.id, REL_FRIENDSHIP, 0.8, int(self.year))
                q.add_relationship(p.id, REL_FRIENDSHIP, 0.8, int(self.year))
                self.total_friendships_formed += 1
        p.skills["diplomacy"] = min(1.0, p.skills["diplomacy"] + 0.02 * strength)
        p.influence = min(1.0, p.influence + 0.015 * strength)

    def _behavior_cunning(self, p, strength):
        if random.random() < 0.15 * strength:
            # Weaken friends' rivalries
            for fid in p.get_friends():
                fr = self.get_person(fid)
                if fr:
                    for rid, rel in list(fr.relationships.items()):
                        if rel.rel_type == REL_RIVALRY:
                            rel.strength = max(0, rel.strength - 0.05)
        p.skills["survival"] = min(1.0, p.skills["survival"] + 0.02 * strength)
        p.influence = min(1.0, p.influence + 0.01)

    def _behavior_nurturing(self, p, strength):
        if random.random() < 0.2 * strength:
            # Boost children's traits
            children_alive = [c for c in p.children if c.is_alive]
            for c in children_alive:
                if c.age < 20:
                    c.traits["resilience"] = min(1.0, c.traits["resilience"] + 0.01)
                    c.traits["charisma"] = min(1.0, c.traits["charisma"] + 0.01)
                    c.happiness = min(1.0, c.happiness + 0.05)
            # Comfort sad people
            for fid in list(p.relationships.keys()):
                fr = self.get_person(fid)
                if fr and fr.happiness < -0.3:
                    fr.happiness = min(1.0, fr.happiness + 0.1)
                    p.happiness = min(1.0, p.happiness + 0.02)
        p.skills["craft"] = min(1.0, p.skills["craft"] + 0.01)

    def _behavior_reckless(self, p, strength):
        if random.random() < 0.1 * strength:
            p.skills["combat"] = min(1.0, p.skills["combat"] + 0.02)
            p.skills["survival"] = min(1.0, p.skills["survival"] + 0.01)
            # Risk accident death
            if random.random() < 0.03 * strength:
                if p.skills["survival"] < 0.3:
                    p.is_alive = False; p.death_age = p.age
                    p.death_cause = "fatal accident"

    def _behavior_stoic(self, p, strength):
        # Resilient to emotional events
        if p.happiness < 0:
            p.happiness = min(1.0, p.happiness + 0.05 * strength)
        # Calm rivals
        for rid in list(p.relationships.keys()):
            rel = p.relationships[rid]
            if rel.rel_type == REL_RIVALRY:
                rel.strength = max(0, rel.strength - 0.03 * strength)
        p.skills["survival"] = min(1.0, p.skills["survival"] + 0.01)
        p.influence = min(1.0, p.influence + 0.005 * strength)

    def _ai_role_evolution(self):
        """Periodically re-evaluate roles."""
        alive = [p for p in self.people if p.is_alive and p.age >= 18]
        for p in alive:
            if p.role_age > 15 and random.random() < 0.1:
                self._assign_role(p)

    def _ai_mentoring(self):
        """Mentors boost mentees' best skill."""
        for p in self.people:
            if not p.is_alive: continue
            for mentee_id in list(p._mentees):
                mentee = self.get_person(mentee_id)
                if not mentee or not mentee.is_alive:
                    p._mentees.remove(mentee_id)
                    continue
                # Boost mentee's best skill
                best_skill = max(mentee.skills, key=mentee.skills.get)
                mentee.skills[best_skill] = min(1.0, mentee.skills[best_skill] + 0.005)
                p.skills["scholarship"] = min(1.0, p.skills["scholarship"] + 0.002)

    def _ai_influence_propagation(self):
        """High-influence people shift nearby traits/personality."""
        alive = [p for p in self.people if p.is_alive and p.influence > 0.5]
        for p in alive:
            # Shift house members' traits slightly
            if p.house:
                for q in self.people:
                    if q.is_alive and q.house is p.house and q.id != p.id:
                        # Influence traits toward p's traits
                        for k in q.traits:
                            diff = p.traits[k] - q.traits[k]
                            q.traits[k] = max(0, min(1.0, q.traits[k] + diff * 0.002 * p.influence))
            # Influence relationship partners
            for rid in list(p.relationships.keys()):
                rel = p.relationships.get(rid)
                if rel and rel.strength > 0.5:
                    other = self.get_person(rid)
                    if other and other.is_alive:
                        # Slight personality influence
                        if random.random() < 0.01 * p.influence:
                            other.personality_strength = max(0.1, other.personality_strength - 0.01)
                            # No personality change, just strength reduction toward influencer

    def _ai_house_strategy(self):
        """Houses form alliances, trade, choose strategies."""
        active_houses = [h for h in self.houses if any(p.is_alive and p.house is h for p in self.people)]
        if len(active_houses) < 2: return
        for h in active_houses:
            members = [p for p in self.people if p.is_alive and p.house is h]
            if not members: continue
            # Determine dominant personality
            pers_count = defaultdict(int)
            for m in members:
                pers_count[m.personality] += 1
            h.dominant_personality = max(pers_count, key=pers_count.get) if pers_count else "Stoic"
            # Set strategy based on dominant personality
            strat_map = {
                "Ambitious": "aggressive", "Ruthless": "aggressive",
                "Wise": "defensive", "Stoic": "neutral",
                "Charismatic": "diplomatic", "Cunning": "diplomatic",
                "Creative": "neutral", "Nurturing": "defensive",
                "Pious": "defensive", "Reckless": "aggressive",
            }
            h.strategy = strat_map.get(h.dominant_personality, "neutral")
            # Update resources
            h.resources = min(10.0, h.resources + len(members) * 0.01)
            # Strategy affects behavior
            if h.strategy == "aggressive":
                h.prestige += 0.05
                # More likely to feud
                for other_h in active_houses:
                    if other_h is not h and other_h.name not in h.feuds:
                        if random.random() < 0.01:
                            h.feuds.add(other_h.name); other_h.feuds.add(h.name)
            elif h.strategy == "diplomatic":
                # Form alliances
                for other_h in active_houses:
                    if other_h is not h and other_h.name not in h.allies and other_h.name not in h.feuds:
                        if random.random() < 0.02 and other_h.strategy in ("diplomatic", "neutral"):
                            h.allies.add(other_h.name)
                            other_h.allies.add(h.name)
                            h.alliance_trust[other_h.name] = 0.5
                            other_h.alliance_trust[h.name] = 0.5
                            self.total_alliances_formed += 1
                            self._log(f"Alliance formed: {h.name} & {other_h.name}!")
                            self.event_markers.append((self.year, "alliance"))
                            self._unlock("first_alliance")
                # Trade agreements
                for other_h in active_houses:
                    if other_h is not h and other_h.name in h.allies:
                        if other_h.name not in h.trade_agreements and random.random() < 0.03:
                            h.trade_agreements.add(other_h.name)
                            other_h.trade_agreements.add(h.name)
                            h.resources = min(10, h.resources + 1)
                            other_h.resources = min(10, other_h.resources + 1)
            elif h.strategy == "defensive":
                # Boost house member resilience
                for m in members:
                    m.traits["resilience"] = min(1.0, m.traits["resilience"] + 0.002)
            # Alliance trust changes
            for ally_name in list(h.alliance_trust.keys()):
                if ally_name in h.allies:
                    h.alliance_trust[ally_name] = min(1.0, h.alliance_trust[ally_name] + 0.02)
                else:
                    h.alliance_trust.pop(ally_name, None)
            # Remove broken alliances
            for ally_name in list(h.allies):
                if ally_name not in h.alliance_trust or h.alliance_trust[ally_name] < 0.2:
                    h.allies.discard(ally_name)
                    other_h = next((x for x in self.houses if x.name == ally_name), None)
                    if other_h:
                        other_h.allies.discard(h.name)
                        other_h.alliance_trust.pop(h.name, None)

    def _ai_happiness_decay(self):
        """Natural happiness decay toward 0, modified by relationships."""
        for p in self.people:
            if not p.is_alive: continue
            # Base decay toward 0
            if abs(p.happiness) > 0.01:
                p.happiness *= 0.98
            # Friends boost happiness
            friend_count = len(p.get_friends())
            p.happiness = min(1.0, p.happiness + friend_count * 0.003)
            # Rivals reduce happiness
            rival_count = len(p.get_rivals())
            p.happiness = max(-1.0, p.happiness - rival_count * 0.004)
            # Marriage boosts happiness
            if p.spouse and p.spouse.is_alive:
                p.happiness = min(1.0, p.happiness + 0.005)
            elif p.is_widowed:
                p.happiness = max(-1.0, p.happiness - 0.01)
            p.happiness = max(-1.0, min(1.0, p.happiness))

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
        # v4: tick wars
        self._tick_wars(dt)
        # tick people
        for p in self.people: p.tick(dt)
        now_alive=sum(1 for p in self.people if p.is_alive)
        self.total_deaths+=prev_alive-now_alive
        # v5: death memories
        newly_dead = [p for p in self.people if not p.is_alive and p.death_age and abs(p.age - p.death_age) < dt + 0.1]
        for dead in newly_dead:
            dead.add_memory(self.year, "death", f"Died of {dead.death_cause or 'unknown'}", -0.8)
            # Mourning for friends, family, spouse, children
            mourners = set()
            if dead.spouse and dead.spouse.is_alive: mourners.add(dead.spouse.id)
            for c in dead.children:
                if c.is_alive: mourners.add(c.id)
            if dead.mother and dead.mother.is_alive: mourners.add(dead.mother.id)
            if dead.father and dead.father.is_alive: mourners.add(dead.father.id)
            for fid in dead.get_friends():
                if fid not in mourners: mourners.add(fid)
            for mid in mourners:
                mourner = self.get_person(mid)
                if mourner:
                    mourner.add_memory(self.year, "mourning", f"Mourned {dead.name}", -0.5, {dead.id})
        # Ancestral resonance (optimized)
        imm_ids={p.id for p in self.people if p.is_immortal and p.is_alive}
        if imm_ids:
            for p in self.people:
                if p.is_alive and not p.is_immortal:
                    cnt=sum(1 for aid in p._ancestors(5) if aid in imm_ids)
                    if cnt > 0:
                        p.traits["longevity"]=min(1.0,p.traits["longevity"]+cnt*0.00015*dt)
                        if p.blood_type!="immortal": p.max_age=p._max_age()
        # Marriage & Reproduction
        self._marriages(dt); self._reproduction(dt)
        # Smooth positions
        for p in self.people:
            p.x+=(p.target_x-p.x)*0.1; p.y+=(p.target_y-p.y)*0.1
        # Events
        self._check_events()
        # v4: check achievements
        self._check_achievements()
        # Snapshot
        if self.year-self._last_snap>=3: self._snapshot(); self._last_snap=self.year
        # v4: timeline snapshot
        if self.year - self._last_timeline_snap >= 10:
            self._save_timeline_snapshot()
            self._last_timeline_snap = self.year
        # v4: war cooldown
        if self._war_cooldown > 0:
            self._war_cooldown -= dt
        # v5: AI tick
        self._ai_tick()
        # v5: update influence based on role
        for p in self.people:
            if p.is_alive and p.age >= 20:
                role_inf = {"Leader": 0.05, "Elder": 0.04, "Diplomat": 0.03, "Scholar": 0.02}
                base = role_inf.get(p.role, 0.005)
                p.influence = min(1.0, p.influence + base * dt * 0.1)
                # Influence decays for commoners
                if p.role == "Commoner":
                    p.influence = max(0.1, p.influence - 0.001)
        # v5: role experience grows
        for p in self.people:
            if p.is_alive and p.role:
                p.role_experience += dt * 0.05

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
            p_rate_mod = 1.0
            if p.personality == "Charismatic": p_rate_mod = 1.3
            elif p.personality == "Reckless": p_rate_mod = 1.2
            elif p.personality == "Stoic": p_rate_mod = 0.7
            if random.random()>rate*dt*(0.5+p.traits["charisma"])*p_rate_mod: continue
            best,bs=None,-1.0
            for q in unmar:
                if q.id in done or q.id==p.id: continue
                if not p.can_marry(q): continue
                # v5: use marriage_compatibility
                score = p.marriage_compatibility(q)
                # Network bonus: friends-of-friends
                for fid in p.get_friends():
                    fr = self.get_person(fid)
                    if fr and q.id in fr.relationships and fr.relationships[q.id].rel_type == REL_FRIENDSHIP:
                        score += 0.05
                # Alliance bonus
                if p.house and q.house and q.house.name in p.house.allies:
                    score += 0.1
                if score > bs: bs=score; best=q
            if best:
                p.spouse=best; best.spouse=p; done.add(p.id); done.add(best.id)
                p.marry_cd=5; best.marry_cd=5; self.total_marriages+=1
                # v5: marriage memory
                p.add_memory(self.year, "marriage", f"Married {best.name}", 0.7, {best.id})
                best.add_memory(self.year, "marriage", f"Married {p.name}", 0.7, {p.id})
                if p.house and best.house and p.house is not best.house:
                    w,l = (p.house,best.house) if p.house.prestige>=best.house.prestige else (best.house,p.house)
                    best.house=w; w.prestige+=1
                    self._log(f"Houses {w.name} & {l.name} united by marriage!")
                    # v5: marriage between houses auto-creates alliance
                    if l.name not in w.allies:
                        w.allies.add(l.name); l.allies.add(w.name)
                        w.alliance_trust[l.name] = 0.6; l.alliance_trust[w.name] = 0.6
                        self.total_alliances_formed += 1

    def _reproduction(self, dt):
        done=set()
        for p in self.people:
            if p.id in done or not p.can_reproduce(): continue
            if p.spouse and p.spouse.is_alive and p.spouse.can_reproduce():
                sp=p.spouse; done.add(p.id); done.add(sp.id)
                rate=self.repro_rate*(0.5+p.traits["fertility"])*(0.5+sp.traits["fertility"])
                rate*=self._eff_mult("fertility_boost")*self._eff_mult("fertility_penalty")
                if p.is_immortal or sp.is_immortal: rate*=0.3
                if p.personality == "Nurturing" or sp.personality == "Nurturing":
                    rate *= 1.2
                if p.personality == "Reckless" or sp.personality == "Reckless":
                    rate *= 1.15
                if p.personality == "Stoic" or sp.personality == "Stoic":
                    rate *= 0.8
                # v5: happiness bonus
                avg_happiness = (p.happiness + sp.happiness) / 2
                if avg_happiness > 0.2: rate *= 1.2
                elif avg_happiness < -0.3: rate *= 0.6
                # v5: house resources bonus
                if p.house: rate *= (1.0 + p.house.resources * 0.02)
                # v5: social support network bonus
                social = len(p.get_friends()) + len(sp.get_friends())
                rate *= (1.0 + social * 0.01)
                if random.random()<rate*dt:
                    ch=self._child(p,sp)
                    if ch: p.repro_cd=random.uniform(6,16); sp.repro_cd=random.uniform(6,16)
            elif not p.spouse or (p.spouse and not p.spouse.is_alive):
                rate=self.repro_rate*0.08*(0.5+p.traits["fertility"])*self._eff_mult("fertility_boost")*self._eff_mult("fertility_penalty")
                # v5: single parents less likely if unhappy
                if p.happiness < -0.3: rate *= 0.3
                if random.random()<rate*dt:
                    ch=self._child(p,None)
                    if ch: p.repro_cd=random.uniform(8,20)

    def _child(self, p1, p2):
        a1=random.choice([p1.allele1,p1.allele2])
        if p2:
            a2=random.choice([p2.allele1,p2.allele2]); gn=max(p1.generation,p2.generation)+1
        else:
            a2=random.choice(["i","i","I"]); gn=p1.generation+1
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
             GameEvent.BLESS,GameEvent.MIGRATE,GameEvent.FAMINE,GameEvent.RENAISSANCE,
             GameEvent.WAR, GameEvent.BETRAYAL, GameEvent.EPIDEMIC, GameEvent.MIRACLE],
            weights=[12,20,8,4,10,12,10,14,8,6,6,4])[0]
        alive=[p for p in self.people if p.is_alive]
        if not alive: return

        if et==GameEvent.PLAGUE:
            k=0
            for p in alive:
                sc=0.4+p.traits["resilience"]*0.5
                # v5: survival skill helps
                sc += p.skills["survival"] * 0.2
                if p.is_carrier: sc+=0.15
                if p.is_immortal: sc=1.0
                if p.personality == "Stoic": sc += 0.05
                if random.random()>sc:
                    p.is_alive=False; p.death_age=p.age; p.death_cause="plague"; k+=1
                    p.add_memory(self.year, "plague", "Caught the plague", -0.7)
            dur=random.uniform(10,25); self.effects.append(["fertility_penalty",-0.3,dur])
            self.events.append(GameEvent(et,self.year,f"Plague! {k} died. Fertility -30% for {int(dur)}y.",dur))
            self._log(f"PLAGUE -- {k} perished! Fertility -30% for {int(dur)}y.")
            self.event_markers.append((self.year, "plague"))
            if k > 0: self._unlock("survive_plague")
            # Survivors get memory
            for p in [pp for pp in alive if pp.is_alive]:
                p.add_memory(self.year, "plague_survive", "Survived the plague", 0.2)

        elif et==GameEvent.GOLDEN:
            dur=random.uniform(15,35); mag=random.uniform(0.3,0.6)
            self.effects.append(["fertility_boost",mag,dur])
            self.events.append(GameEvent(et,self.year,f"Golden Age! Fertility +{int(mag*100)}% for {int(dur)}y.",dur,mag))
            self._log(f"GOLDEN AGE -- Fertility +{int(mag*100)}% for {int(dur)}y!")
            self.event_markers.append((self.year, "golden"))
            self._unlock("golden_age")
            for p in alive: p.add_memory(self.year, "golden_age", "Golden age begins", 0.4)

        elif et==GameEvent.CATASTROPHE:
            k=0
            for p in alive:
                if p.age<40 and not p.is_immortal:
                    # v5: survival skill reduces risk
                    risk = 0.15 - p.skills["survival"] * 0.08
                    if random.random() < max(0.02, risk):
                        p.is_alive=False; p.death_age=p.age; p.death_cause="catastrophe"; k+=1
                        p.add_memory(self.year, "catastrophe", "Caught in catastrophe", -0.8)
            self.events.append(GameEvent(et,self.year,f"Catastrophe! {k} young lost."))
            self._log(f"CATASTROPHE -- {k} young adults died!")
            self.event_markers.append((self.year, "catastrophe"))

        elif et==GameEvent.AWAKEN:
            morts=[p for p in alive if p.blood_type=="mortal"]
            if morts:
                c=random.choice(morts); old=c.allele_str()
                c.allele1="I"; c.allele2="I"; c.blood_type="immortal"; c.max_age=float("inf")
                self.events.append(GameEvent(et,self.year,f"{c.name} awakens Immortal! ({old}->II)"))
                self._log(f"AWAKENING -- {c.name} becomes IMMORTAL!")
                self.event_markers.append((self.year, "awaken"))
                self._unlock("first_awakening")
                c.add_memory(self.year, "awakening", "Awakened as Immortal!", 1.0)

        elif et==GameEvent.BLESS:
            if self.houses:
                h=random.choice(self.houses); dur=random.uniform(20,40)
                self.effects.append(["trait_boost",0.3,dur]); h.prestige+=5
                self.events.append(GameEvent(et,self.year,f"House {h.name} blessed! Traits + for {int(dur)}y.",dur))
                self._log(f"BLESSING -- House {h.name} gains divine favor!")
                self.event_markers.append((self.year, "bless"))
                if h.prestige >= 10: self._unlock("prestige_10")

        elif et==GameEvent.MIGRATE:
            n=random.randint(1,3)
            for _ in range(n):
                h=self.create_house()
                a1,a2=random.choice(["I","i","i","i"]),random.choice(["I","i","i","i"])
                p=self.add_person(a1,a2,house=h,gen=0)
                if p: p.x=p.target_x; p.y=p.target_y; h.founder=p
            self.events.append(GameEvent(et,self.year,f"{n} migrants found new houses!"))
            self._log(f"MIGRATION -- {n} newcomers arrive!")
            self.event_markers.append((self.year, "migrate"))

        elif et==GameEvent.FAMINE:
            dur=random.uniform(10,20); self.effects.append(["fertility_penalty",-0.4,dur])
            self.events.append(GameEvent(et,self.year,f"Famine! Fertility -40% for {int(dur)}y.",dur))
            self._log(f"FAMINE -- Fertility -40% for {int(dur)}y!")
            self.event_markers.append((self.year, "famine"))
            for p in alive: p.happiness = max(-1.0, p.happiness - 0.1)

        elif et==GameEvent.RENAISSANCE:
            dur=random.uniform(15,30)
            self.effects.append(["trait_boost",0.4,dur]); self.effects.append(["fertility_boost",0.2,dur])
            self.events.append(GameEvent(et,self.year,f"Renaissance! Traits & fertility boosted for {int(dur)}y.",dur))
            self._log(f"RENAISSANCE -- All boosted for {int(dur)}y!")
            self.event_markers.append((self.year, "renaissance"))
            # v5: boosts scholarship and craft skills
            for p in alive:
                p.skills["scholarship"] = min(1.0, p.skills["scholarship"] + 0.05)
                p.skills["craft"] = min(1.0, p.skills["craft"] + 0.05)
                p.add_memory(self.year, "renaissance", "Renaissance era begins", 0.4)

        elif et==GameEvent.WAR:
            self._trigger_war()

        elif et==GameEvent.BETRAYAL:
            alive_warriors = [p for p in alive if p.personality == "Ruthless" and p.age >= 20]
            if alive_warriors and len(self.houses) >= 2:
                traitor = random.choice(alive_warriors)
                victim = random.choice([p for p in alive if p is not traitor and p.house and p.house != traitor.house and p.age >= 18])
                if victim:
                    # v5: combat skill check - victim may fight back
                    if victim.skills["combat"] > traitor.skills["combat"] and random.random() < 0.3:
                        # Victim fights back and wins
                        traitor.is_alive = False; traitor.death_age = traitor.age
                        traitor.death_cause = f"killed by {victim.name} (betrayal failed)"
                        victim.kills += 1
                        victim.skills["combat"] = min(1.0, victim.skills["combat"] + 0.05)
                        self.events.append(GameEvent(et, self.year, f"{traitor.name}'s betrayal of {victim.name} failed!"))
                        self._log(f"BETRAYAL FAILED -- {traitor.name} killed by {victim.name}!")
                    else:
                        victim.is_alive = False; victim.death_age = victim.age
                        victim.death_cause = f"betrayed by {traitor.name}"
                        traitor.kills += 1
                        traitor.skills["combat"] = min(1.0, traitor.skills["combat"] + 0.05)
                        self.events.append(GameEvent(et, self.year, f"{traitor.name} betrayed {victim.name}!"))
                        self._log(f"BETRAYAL -- {traitor.name} murdered {victim.name}!")
                        traitor.add_memory(self.year, "betrayal", f"Betrayed {victim.name}", -0.2, {victim.id})
                    self.event_markers.append((self.year, "betrayal"))

        elif et==GameEvent.EPIDEMIC:
            k = 0
            for p in alive:
                if not p.is_immortal:
                    # v5: survival skill reduces death chance
                    risk = 0.08 - p.skills["survival"] * 0.04
                    if random.random() < max(0.01, risk):
                        p.is_alive = False; p.death_age = p.age; p.death_cause = "epidemic"; k += 1
                        p.add_memory(self.year, "epidemic", "Caught the epidemic", -0.6)
            dur = random.uniform(8, 18)
            self.effects.append(["fertility_penalty", -0.2, dur])
            self.events.append(GameEvent(et, self.year, f"Epidemic! {k} died. Fertility -20% for {int(dur)}y.", dur))
            self._log(f"EPIDEMIC -- {k} lost to disease!")
            self.event_markers.append((self.year, "epidemic"))

        elif et==GameEvent.MIRACLE:
            targets = random.sample(alive, min(5, len(alive)))
            for p in targets:
                if not p.is_immortal:
                    p.max_age *= 1.2
                    p.traits["resilience"] = min(1.0, p.traits["resilience"] + 0.1)
                    p.add_memory(self.year, "miracle", "Blessed with longevity", 0.6)
            self.events.append(GameEvent(et, self.year, f"Miracle! {len(targets)} blessed with longevity."))
            self._log(f"MIRACLE -- {len(targets)} people blessed!")
            self.event_markers.append((self.year, "miracle"))

    def _trigger_war(self):
        active_houses = [h for h in self.houses if any(p.is_alive and p.house is h for p in self.people)]
        if len(active_houses) < 2 or self._war_cooldown > 0:
            return
        h1, h2 = random.sample(active_houses, 2)
        # v5: allies can't fight each other
        if h2.name in h1.allies:
            return
        if h2.name in h1.feuds:
            return
        intensity = random.uniform(0.3, 0.8)
        duration = random.uniform(15, 40)
        h1.feuds.add(h2.name); h2.feuds.add(h1.name)
        h1.feud_intensity = intensity; h2.feud_intensity = intensity
        # v5: break alliances between warring houses
        for other_h in self.houses:
            if other_h.name in h1.allies and other_h.name == h2.name:
                h1.allies.discard(h2.name); h2.allies.discard(h1.name)
                h1.alliance_trust.pop(h2.name, None); h2.alliance_trust.pop(h1.name, None)
        self._war_cooldown = 20
        self.wars.append((self.year, h1.name, h2.name, duration, intensity))
        self.events.append(GameEvent(GameEvent.WAR, self.year,
            f"War! House {h1.name} vs {h2.name}! (intensity: {intensity:.0%})", duration, intensity))
        self._log(f"WAR -- House {h1.name} vs {h2.name}!")
        self.event_markers.append((self.year, "war"))
        self._unlock("house_war")
        # v5: War casualties with combat skill
        h1_members = [p for p in self.people if p.is_alive and p.house is h1 and p.age >= 16]
        h2_members = [p for p in self.people if p.is_alive and p.house is h2 and p.age >= 16]
        for members, enemy_members in [(h1_members, h2_members), (h2_members, h1_members)]:
            casualties = random.sample(members, min(int(len(members) * intensity * 0.15), len(members)))
            for p in casualties:
                # v5: Warriors and high-combat people survive better
                if p.role == "Warrior" and random.random() < 0.5: continue
                if p.skills["combat"] > 0.6 and random.random() < p.skills["combat"] * 0.4: continue
                p.is_alive = False; p.death_age = p.age; p.death_cause = "war"
                p.add_memory(self.year, "war_death", "Killed in war", -0.8)
                # v5: killer gets combat XP
                enemies_alive = [e for e in enemy_members if e.is_alive]
                if enemies_alive:
                    killer = random.choice(enemies_alive)
                    killer.kills += 1
                    killer.skills["combat"] = min(1.0, killer.skills["combat"] + 0.05)
                    killer.add_memory(self.year, "war_kill", f"Killed in war vs {p.house.name if p.house else 'unknown'}", -0.2, {p.id})
        # v5: war memories for all participants
        for p in h1_members + h2_members:
            if p.is_alive:
                p.add_memory(self.year, "war", "Participated in a war", -0.3)
                p.happiness = max(-1.0, p.happiness - 0.1)
        # Resolve war prestige
        if h1.prestige > h2.prestige:
            h1.prestige += 3; h2.prestige -= 2
        else:
            h2.prestige += 3; h1.prestige -= 2

    def _tick_wars(self, dt):
        resolved = []
        for i, (start_y, h1n, h2n, dur, intensity) in enumerate(self.wars):
            if self.year - start_y >= dur:
                resolved.append(i)
                for h in self.houses:
                    if h.name == h1n:
                        h.feuds.discard(h2n); h.feud_intensity = 0
                    if h.name == h2n:
                        h.feuds.discard(h1n); h.feud_intensity = 0
                self._log(f"War between {h1n} & {h2n} has ended.")
        for i in reversed(resolved):
            self.wars.pop(i)

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
        if len(self.event_markers)>100: self.event_markers=self.event_markers[-100:]

    def _save_timeline_snapshot(self):
        snap = {
            "year": self.year,
            "people": [(p.id, p.name, p.age, p.is_alive, p.blood_type,
                        p.house.name if p.house else None, p.generation)
                       for p in self.people],
            "pop_hist": list(self.pop_hist[-50:]),
        }
        self.timeline.append(snap)
        if len(self.timeline) > 50:
            self.timeline = self.timeline[-50:]

    def _unlock(self, key):
        if key not in self.achievements and key in ACHIEVEMENTS:
            self.achievements.add(key)
            name, desc = ACHIEVEMENTS[key]
            self.achievement_log.append((int(self.year), key, name, desc))
            self._log(f"ACHIEVEMENT: {name}")

    def _check_achievements(self):
        al = [p for p in self.people if p.is_alive]
        alive_count = len(al)
        if alive_count >= 50: self._unlock("pop_50")
        if alive_count >= 100: self._unlock("pop_100")
        if alive_count >= 200: self._unlock("pop_200")
        mg = max((p.generation for p in self.people), default=0)
        if mg >= 5: self._unlock("gen_5")
        if mg >= 10: self._unlock("gen_10")
        if self.total_births > 7: self._unlock("first_birth")
        im_count = sum(1 for p in al if p.is_immortal)
        if im_count >= 3: self._unlock("immortal_dynasty")
        bloods = set(p.blood_type for p in al)
        if len(bloods) >= 3: self._unlock("diverse_gene")
        if self.total_marriages >= 50: self._unlock("marriage_50")
        for p in al:
            if p.blood_type == "mortal" and p.age >= 100:
                self._unlock("centenarian"); break
        for h in self.houses:
            if h.prestige >= 10: self._unlock("prestige_10")
        extinct = [h for h in self.houses if h.extinct]
        if extinct: self._unlock("house_extinct")
        # v5 achievements
        for p in al:
            if p.skills.get("craft", 0) >= 0.9:
                self._unlock("master_craftsman"); break
        for p in al:
            if p.skills.get("combat", 0) >= 0.9:
                self._unlock("legendary_warrior"); break
        for p in al:
            if p.skills.get("scholarship", 0) >= 0.9:
                self._unlock("sage"); break
        for p in al:
            if len(p.get_friends()) >= 5:
                self._unlock("social_butterfly"); break
        # Blood feud: rivalry spanning 3+ generations
        for p in al:
            for rid, rel in p.relationships.items():
                if rel.rel_type == REL_RIVALRY:
                    other = self.get_person(rid)
                    if other and abs(p.generation - other.generation) >= 3:
                        self._unlock("blood_feud"); break
            else: continue
            break
        # Mentor legacy
        for p in self.people:
            if not p.is_alive and p._mentees:
                for mid in p._mentees:
                    m = self.get_person(mid)
                    if m and m.is_alive and p.death_age and m.age - p.age > 50:
                        self._unlock("mentor_legacy"); break

    def stats(self):
        al=[p for p in self.people if p.is_alive]
        im=[p for p in al if p.is_immortal]; ca=[p for p in al if p.is_carrier]; mo=[p for p in al if p.blood_type=="mortal"]
        mg=max((p.generation for p in self.people),default=0)
        aa=sum(p.age for p in al)/max(1,len(al))
        ah={h for h in self.houses if any(p.is_alive and p.house is h for p in self.people)}
        total_al = max(len(al), 1)
        i_freq = (len(im) + len(ca)*0.5) / total_al
        pers_dist = defaultdict(int)
        for p in al: pers_dist[p.personality] += 1
        males = sum(1 for p in al if p.gender == "M")
        females = sum(1 for p in al if p.gender == "F")
        # v5 stats
        total_rels = sum(len(p.relationships) for p in al)
        total_friends = sum(len(p.get_friends()) for p in al) // 2
        total_rivals = sum(len(p.get_rivals()) for p in al) // 2
        total_mentorships_alive = sum(len(p.get_mentors()) for p in al)
        total_alliances = sum(len(h.allies) for h in self.houses) // 2
        avg_happiness = sum(p.happiness for p in al) / max(1, len(al))
        avg_influence = sum(p.influence for p in al) / max(1, len(al))
        return dict(year=self.year,total=len(self.people),alive=len(al),dead=len(self.people)-len(al),
            immortals=len(im),carriers=len(ca),mortals=len(mo),avg_age=aa,
            oldest=max((p.age for p in self.people),default=0),
            oldest_imm=max((p.age for p in im),default=0),
            oldest_car=max((p.age for p in ca),default=0),
            max_gen=mg,births=self.total_births,deaths=self.total_deaths,
            marriages=self.total_marriages,houses_active=len(ah),
            houses_extinct=len(self.houses)-len(ah),
            gene_freq_I=i_freq, males=males, females=females,
            personality_dist=dict(pers_dist),
            achievements=len(self.achievements),
            avg_happiness=avg_happiness, total_relationships=total_rels,
            total_friendships=total_friends, total_rivalries=total_rivals,
            total_mentorships=total_mentorships_alive, total_alliances=total_alliances,
            avg_influence=avg_influence)

    def house_rankings(self):
        rankings = []
        for h in self.houses:
            members = [p for p in self.people if p.house is h and p.is_alive]
            if members:
                avg_age = sum(p.age for p in members)/len(members)
                rankings.append((h, len(members), avg_age, h.prestige))
        rankings.sort(key=lambda x: x[3], reverse=True)
        return rankings

    def search_people(self, query):
        q = query.lower().strip()
        if not q: return []
        return [p for p in self.people if q in p.name.lower()]

    def search_by_personality(self, personality):
        return [p for p in self.people if p.is_alive and p.personality == personality]

    def search_by_role(self, role):
        return [p for p in self.people if p.is_alive and p.role == role]

    def save_state(self, filepath):
        state = {
            "version": 5,
            "year": self.year,
            "repro_rate": self.repro_rate,
            "marry_rate": self.marry_rate,
            "total_births": self.total_births,
            "total_deaths": self.total_deaths,
            "total_marriages": self.total_marriages,
            "effects": self.effects,
            "log": self.log,
            "pop_hist": self.pop_hist[-100:],
            "event_markers": self.event_markers[-50:],
            "achievements": list(self.achievements),
            "achievement_log": self.achievement_log,
            "houses": [],
            "people": [],
        }
        for i, h in enumerate(self.houses):
            state["houses"].append({
                "name": h.name,
                "color": [h.color.red(), h.color.green(), h.color.blue()],
                "prestige": h.prestige,
                "extinct": h.extinct,
                "founder_id": h.founder.id if h.founder else None,
                "feuds": list(h.feuds),
                "feud_intensity": h.feud_intensity,
                "allies": list(h.allies),
                "alliance_trust": h.alliance_trust,
                "strategy": h.strategy,
                "resources": h.resources,
                "trade_agreements": list(h.trade_agreements),
                "dominant_personality": h.dominant_personality,
            })
        for p in self.people:
            state["people"].append(p.to_dict())
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=1)

    def load_state(self, filepath):
        with open(filepath, 'r') as f:
            state = json.load(f)
        self.reset()
        name_to_house = {}
        for hd in state["houses"]:
            h = self.create_house(hd["name"], QColor(*hd["color"]))
            h.prestige = hd["prestige"]
            h.extinct = hd["extinct"]
            h.feuds = set(hd.get("feuds", []))
            h.feud_intensity = hd.get("feud_intensity", 0)
            h.allies = set(hd.get("allies", []))
            h.alliance_trust = hd.get("alliance_trust", {})
            h.strategy = hd.get("strategy", "neutral")
            h.resources = hd.get("resources", 1.0)
            h.trade_agreements = set(hd.get("trade_agreements", []))
            h.dominant_personality = hd.get("dominant_personality", "Stoic")
            name_to_house[h.name] = h
        max_id = 0
        id_to_person = {}
        for pd in state["people"]:
            p = Person(pd["allele1"], pd["allele2"], gen=pd["generation"])
            p.id = pd["id"]; p.name = pd["name"]; p.age = pd["age"]
            p.is_alive = pd["is_alive"]; p.death_age = pd["death_age"]
            p.death_cause = pd.get("death_cause")
            p.blood_type = pd["blood_type"]; p.traits = pd["traits"]
            p.generation = pd["generation"]; p.max_age = pd["max_age"]
            p.repro_cd = pd["repro_cd"]; p.marry_cd = pd["marry_cd"]
            p.born_year = pd["born_year"]
            p.x = pd["x"]; p.y = pd["y"]
            p.target_x = pd["target_x"]; p.target_y = pd["target_y"]
            if pd["house_name"]: p.house = name_to_house.get(pd["house_name"])
            p.personality = pd.get("personality", "Ambitious")
            p.personality_strength = pd.get("personality_strength", 0.5)
            p.gender = pd.get("gender", "M")
            p.kills = pd.get("kills", 0)
            p.role = pd.get("role", "Commoner")
            # v5 fields
            p.skills = pd.get("skills", {s: 0.1 for s in SKILL_NAMES})
            rel_data = pd.get("relationships", {})
            mem_data = pd.get("memories", [])
            p.relationships = {}
            for rid_str, rdata in rel_data.items():
                rid = int(rid_str)
                p.relationships[rid] = Relationship(p.id, rid, rdata[0], rdata[1], rdata[2])
            p.memories = []
            for md in mem_data:
                p.memories.append(Memory(md[0], md[1], md[2], md[3], set(md[4])))
            p.role_experience = pd.get("role_experience", 0.0)
            p.role_age = pd.get("role_age", 0.0)
            p.influence = pd.get("influence", 0.1)
            p.happiness = pd.get("happiness", 0.0)
            p._mentored_by = pd.get("mentored_by")
            p._mentees = pd.get("mentees", [])
            self.people.append(p); id_to_person[p.id] = p
            if p.id > max_id: max_id = p.id
        for pd in state["people"]:
            p = id_to_person[pd["id"]]
            if pd["mother_id"] and pd["mother_id"] in id_to_person:
                p.mother = id_to_person[pd["mother_id"]]
            if pd["father_id"] and pd["father_id"] in id_to_person:
                p.father = id_to_person[pd["father_id"]]
            for cid in pd["children_ids"]:
                if cid in id_to_person:
                    c = id_to_person[cid]
                    if c not in p.children: p.children.append(c)
            if pd["spouse_id"] and pd["spouse_id"] in id_to_person:
                p.spouse = id_to_person[pd["spouse_id"]]
        Person._ctr = max_id
        self.year = state["year"]
        self.repro_rate = state["repro_rate"]
        self.marry_rate = state["marry_rate"]
        self.total_births = state["total_births"]
        self.total_deaths = state["total_deaths"]
        self.total_marriages = state["total_marriages"]
        self.effects = [list(e) for e in state["effects"]]
        self.log = [tuple(l) for l in state["log"]]
        self.pop_hist = [tuple(p) for p in state["pop_hist"]]
        self.event_markers = [tuple(m) for m in state.get("event_markers", [])]
        self.achievements = set(state.get("achievements", []))
        self.achievement_log = state.get("achievement_log", [])
        for hd in state["houses"]:
            if hd["founder_id"] and hd["founder_id"] in id_to_person:
                name_to_house[hd["name"]].founder = id_to_person[hd["founder_id"]]
        self._rebuild_dict(); self.layout()

    def export_stats_csv(self, filepath):
        import csv
        alive = [p for p in self.people if p.is_alive]
        avg_h = sum(p.happiness for p in alive) / max(1, len(alive))
        total_rels = sum(len(p.relationships) for p in alive)
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Year","Mortals","Carriers","Immortals","Total",
                             "I_Allele_Freq","Pct_Immortals","Pct_Carriers","Males","Females",
                             "Avg_Happiness","Total_Relationships"])
            for row in self.pop_hist:
                year, mo, ca, im = row
                total = mo + ca + im
                i_freq = (im + ca*0.5) / max(total, 1)
                males = int(total * 0.5 + random.uniform(-2, 2))
                females = total - males
                writer.writerow([f"{year:.1f}", mo, ca, im, total,
                                f"{i_freq:.4f}", f"{im/max(total,1)*100:.1f}%",
                                f"{ca/max(total,1)*100:.1f}%", males, females,
                                f"{avg_h:.3f}", total_rels])

    def reset(self):
        self.people.clear(); self.houses.clear(); self.events.clear()
        self.effects.clear(); self.log.clear(); self.pop_hist.clear()
        self.event_markers.clear(); self.achievements.clear()
        self.achievement_log.clear(); self.timeline.clear()
        self.wars.clear(); self._war_cooldown = 0
        # v5: reset new counters
        self.rel_edges.clear()
        self._last_ai_tick_year = -5
        self.total_friendships_formed = 0
        self.total_rivalries_formed = 0
        self.total_mentorships = 0
        self.total_alliances_formed = 0
        self.year=0; self.total_births=0; self.total_deaths=0; self.total_marriages=0
        self._last_snap=-5; self._last_timeline_snap=-10
        Person._ctr=0; House._idx=0
        self._pdict.clear()


# ── Keyboard Shortcuts Help Dialog ──────────────────────────────────
class ShortcutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(360, 400)
        layout = QVBoxLayout(self)
        text = QTextEdit(); text.setReadOnly(True)
        text.setStyleSheet("background:#1a1a2e;color:#d0d0e0;border:1px solid #333355;font-size:12px;")
        text.setHtml("""
        <h3 style='color:#ffd700;'>Keyboard Shortcuts</h3>
        <table style='color:#c0c0d0;font-size:12px;' width='100%'>
        <tr><td><b>Space</b></td><td>Play / Pause</td></tr>
        <tr><td><b>S</b></td><td>Step +2 years</td></tr>
        <tr><td><b>F</b></td><td>Fit all nodes in view</td></tr>
        <tr><td><b>R</b></td><td>Reset simulation</td></tr>
        <tr><td><b>H</b></td><td>Highlight selected person's lineage</td></tr>
        <tr><td><b>T</b></td><td>Toggle mini-map</td></tr>
        <tr><td><b>D</b></td><td>Toggle relationship edges</td></tr>
        <tr><td><b>Ctrl+F</b></td><td>Focus search bar</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Save simulation</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>Load simulation</td></tr>
        <tr><td><b>Ctrl+E</b></td><td>Export statistics CSV</td></tr>
        <tr><td><b>Escape</b></td><td>Clear highlight / close dialog</td></tr>
        <tr><td><b>?</b></td><td>Show this help dialog</td></tr>
        </table>
        <p style='color:#888;margin-top:15px;'>Right-click a person node for context menu.<br>
        Drag nodes to reposition them on the canvas.<br>
        D toggles friendship/rivalry/mentorship edges.</p>
        """)
        layout.addWidget(text)
        btn = QPushButton("Close"); btn.clicked.connect(self.accept)
        layout.addWidget(btn)


# ── Timeline Scrubber ──────────────────────────────────────────────
class TimelineScrubber(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(50); self.setMaximumHeight(65)
        self.year = 0; self.max_year = 10; self.event_positions = []
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { height:4px; background:#2a2a4a; border-radius:2px; }
            QSlider::handle:horizontal { background:#ffd700; width:12px; margin:-4px 0; border-radius:6px; }
            QSlider::sub-page:horizontal { background:#4a4a8a; border-radius:2px; }
        """)
        self.year_label = QLabel("Year: 0")
        self.year_label.setStyleSheet("color:#ffd700;font-size:10px;font-weight:bold;")
        self.year_label.setAlignment(Qt.AlignCenter)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 0, 4, 0); lay.setSpacing(1)
        lay.addWidget(self.year_label)
        lay.addWidget(self.slider)

    def set_year(self, year):
        self.year = year
        if year > self.max_year:
            self.max_year = year + 10
        self.slider.blockSignals(True)
        self.slider.setMaximum(int(self.max_year))
        self.slider.setValue(int(year))
        self.slider.blockSignals(False)
        self.year_label.setText(f"Year: {int(year)}")

    def set_event_positions(self, events):
        self.event_positions = events
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if self.max_year > 0:
            event_colors = {
                "plague": QColor(200,60,60,200), "catastrophe": QColor(255,100,50,200),
                "awaken": QColor(255,215,0,200), "golden": QColor(255,215,100,180),
                "war": QColor(255,50,50,220), "miracle": QColor(255,255,100,200),
                "alliance": QColor(100,220,100,200),
            }
            for ey, etype in self.event_positions[-20:]:
                x = 4 + (w - 8) * ey / max(self.max_year, 1)
                col = event_colors.get(etype, QColor(150,150,150,150))
                painter.setPen(Qt.NoPen); painter.setBrush(col)
                painter.drawEllipse(QPointF(int(x), 38), 3, 3)
        painter.end()


# ── Achievements Panel ─────────────────────────────────────────────
class AchievementsPanel(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2,2,2,2)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["OK", "Achievement", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 25)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background:#1a1a2e; color:#d0d0e0; border:1px solid #333355;
                           gridline-color:#333355; font-size:9px; }
            QTableWidget::item { padding:2px; }
            QTableWidget::item:alternate { background:#222244; }
            QHeaderView::section { background:#2a2a4a; color:#ffd700; border:1px solid #333355;
                                padding:3px; font-size:8px; font-weight:bold; }
        """)
        self.table.setRowCount(len(ACHIEVEMENTS))
        for i, (key, (name, desc)) in enumerate(ACHIEVEMENTS.items()):
            chk = QTableWidgetItem("o")
            chk.setTextAlignment(Qt.AlignCenter)
            chk.setForeground(QBrush(QColor(100,100,120)))
            self.table.setItem(i, 0, chk)
            name_item = QTableWidgetItem(name)
            name_item.setForeground(QBrush(QColor(100,100,120)))
            self.table.setItem(i, 1, name_item)
            desc_item = QTableWidgetItem(desc)
            desc_item.setForeground(QBrush(QColor(80,80,100)))
            self.table.setItem(i, 2, desc_item)
        lay.addWidget(self.table)

    def update_achievements(self, unlocked_keys):
        for i, (key, (name, desc)) in enumerate(ACHIEVEMENTS.items()):
            if key in unlocked_keys:
                chk = self.table.item(i, 0)
                if chk:
                    chk.setText("*")
                    chk.setForeground(QBrush(QColor(255, 215, 0)))
                name_item = self.table.item(i, 1)
                if name_item:
                    name_item.setForeground(QBrush(QColor(255, 215, 0)))
                    name_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                desc_item = self.table.item(i, 2)
                if desc_item:
                    desc_item.setForeground(QBrush(QColor(200, 200, 200)))


# ── v5: Relationships Panel ─────────────────────────────────────────
class RelationshipsPanel(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2,2,2,2)
        self.lbl = QLabel("Select a person to view relationships")
        self.lbl.setStyleSheet("color:#aaa;font-size:10px;")
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Person", "Type", "Strength", "Since"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(3, 40)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background:#1a1a2e; color:#d0d0e0; border:1px solid #333355;
                           gridline-color:#333355; font-size:9px; }
            QTableWidget::item { padding:2px; }
            QTableWidget::item:alternate { background:#222244; }
            QHeaderView::section { background:#2a2a4a; color:#ffd700; border:1px solid #333355;
                                padding:3px; font-size:8px; font-weight:bold; }
        """)
        lay.addWidget(self.table)

    def update_relationships(self, person, engine):
        if not person:
            self.lbl.setText("Select a person to view relationships")
            self.table.setRowCount(0)
            return
        self.lbl.setText(f"Relationships for {person.name} ({len(person.relationships)} total)")
        rels = []
        for rid, rel in person.relationships.items():
            other = engine.get_person(rid)
            if other:
                rels.append((other.name, rel.rel_type, rel.strength, rel.year_formed, rel.rel_type))
        rels.sort(key=lambda x: x[2], reverse=True)
        self.table.setRowCount(len(rels))
        type_colors = {
            REL_FRIENDSHIP: QColor(100,220,100),
            REL_RIVALRY: QColor(255,80,80),
            REL_MENTORSHIP: QColor(180,160,255),
        }
        for i, (name, rtype, strength, year, _) in enumerate(rels):
            name_item = QTableWidgetItem(name)
            self.table.setItem(i, 0, name_item)
            type_item = QTableWidgetItem(rtype.title())
            col = type_colors.get(rtype, QColor(180,180,200))
            type_item.setForeground(QBrush(col))
            self.table.setItem(i, 1, type_item)
            # Strength as visual bar text
            bar_len = int(strength * 10)
            bar = "|" * bar_len + "." * (10 - bar_len)
            str_item = QTableWidgetItem(f"{bar} {strength:.2f}")
            str_item.setForeground(QBrush(col))
            self.table.setItem(i, 2, str_item)
            year_item = QTableWidgetItem(str(year))
            year_item.setForeground(QBrush(QColor(150,150,170)))
            self.table.setItem(i, 3, year_item)


# ── Main Window ────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lineage Simulator v5 -- Advanced AI | Relationships | Skills | Strategy")
        self.setMinimumSize(1300,820); self.resize(1540,920)
        self.eng=Engine(); self.running=False; self.speed=1.0
        self.nodes={}; self.mar_edges={}; self.lin_edges={}; self.gen_lbls={}
        self.auto_fit=True; self.sel_person=None; self._last_log=0; self._notifs=[]
        self.filter_mortals = True; self.filter_carriers = True; self.filter_immortals = True
        self.filter_dead = True
        self.pause_on_event = False
        self.minimap_visible = True
        # v5
        self.show_rel_edges = True
        self.rel_edges = {}
        self._build_ui(); self._apply_theme(); self._seed()
        self.timer=QTimer(self); self.timer.timeout.connect(self._tick); self.timer.setInterval(50)

    def _build_ui(self):
        cw=QWidget(); self.setCentralWidget(cw); root=QHBoxLayout(cw)
        root.setContentsMargins(4,4,4,4); root.setSpacing(4)

        # LEFT
        left=QWidget(); left.setFixedWidth(265); ll=QVBoxLayout(left)
        ll.setContentsMargins(0,0,0,0); ll.setSpacing(3)
        t=QLabel("Aging & Lineage\n     Simulator v5")
        t.setStyleSheet("font-size:15px;font-weight:bold;color:#ffd700;padding:2px;"); ll.addWidget(t)

        # Search bar
        sg_search = QGroupBox("Search"); sl_search = QVBoxLayout(sg_search)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type name to find...")
        self.search_input.setStyleSheet("background:#12122a;color:#e0e0f0;border:1px solid #444466;border-radius:3px;padding:4px;font-size:10px;")
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.returnPressed.connect(self._on_search_select)
        sl_search.addWidget(self.search_input)
        self.search_results_label = QLabel("")
        self.search_results_label.setStyleSheet("color:#888;font-size:8px;")
        self.search_results_label.setWordWrap(True)
        sl_search.addWidget(self.search_results_label)
        search_row = QHBoxLayout()
        self.search_type = QComboBox()
        self.search_type.addItems(["Name", "Personality", "Role"])
        self.search_type.setStyleSheet("background:#12122a;color:#e0e0f0;border:1px solid #444466;border-radius:3px;padding:2px;font-size:9px;")
        self.search_type.currentIndexChanged.connect(lambda: self._on_search(self.search_input.text()))
        search_row.addWidget(QLabel("By:"))
        search_row.addWidget(self.search_type)
        sl_search.addLayout(search_row)
        ll.addWidget(sg_search)

        cg=QGroupBox("Controls"); cl=QVBoxLayout(cg)
        self.btn_play=QPushButton(">> Start"); self.btn_play.setCheckable(True)
        self.btn_play.clicked.connect(self._toggle); cl.addWidget(self.btn_play)
        self.btn_step=QPushButton("Step +2y")
        self.btn_step.clicked.connect(lambda:self._do_step(2.0)); cl.addWidget(self.btn_step)
        rw=QHBoxLayout()
        self.btn_reset=QPushButton("Reset"); self.btn_reset.clicked.connect(self._reset); rw.addWidget(self.btn_reset)
        self.btn_fit=QPushButton("Fit"); self.btn_fit.clicked.connect(self._fit); rw.addWidget(self.btn_fit)
        cl.addLayout(rw)
        cl.addWidget(QLabel("Speed:"))
        self.sl_sp=QSlider(Qt.Horizontal); self.sl_sp.setRange(1,80); self.sl_sp.setValue(10)
        self.sl_sp.valueChanged.connect(self._sp_chg); cl.addWidget(self.sl_sp)
        self.lb_sp=QLabel("1.0x"); cl.addWidget(self.lb_sp)
        cl.addWidget(QLabel("Reproduction:"))
        self.sl_rp=QSlider(Qt.Horizontal); self.sl_rp.setRange(1,60); self.sl_rp.setValue(12)
        self.sl_rp.valueChanged.connect(self._rp_chg); cl.addWidget(self.sl_rp)
        self.lb_rp=QLabel("1.2 %"); cl.addWidget(self.lb_rp)
        self.chk_fit=QCheckBox("Auto-fit"); self.chk_fit.setChecked(True)
        self.chk_fit.toggled.connect(lambda v:setattr(self,'auto_fit',v)); cl.addWidget(self.chk_fit)
        self.chk_pause_event = QCheckBox("Pause on major event")
        self.chk_pause_event.toggled.connect(lambda v:setattr(self,'pause_on_event',v))
        cl.addWidget(self.chk_pause_event)
        ll.addWidget(cg)

        # Filters
        fg=QGroupBox("Filters"); fl=QVBoxLayout(fg)
        self.chk_mortals=QCheckBox("Show Mortals (ii)"); self.chk_mortals.setChecked(True)
        self.chk_mortals.toggled.connect(self._apply_filters); fl.addWidget(self.chk_mortals)
        self.chk_carriers=QCheckBox("Show Carriers (Ii)"); self.chk_carriers.setChecked(True)
        self.chk_carriers.toggled.connect(self._apply_filters); fl.addWidget(self.chk_carriers)
        self.chk_immortals=QCheckBox("Show Immortals (II)"); self.chk_immortals.setChecked(True)
        self.chk_immortals.toggled.connect(self._apply_filters); fl.addWidget(self.chk_immortals)
        self.chk_dead=QCheckBox("Show Dead"); self.chk_dead.setChecked(True)
        self.chk_dead.toggled.connect(self._apply_filters); fl.addWidget(self.chk_dead)
        # v5: Show Relationships toggle
        self.chk_rels = QCheckBox("Show Relationships (D)")
        self.chk_rels.setChecked(True)
        self.chk_rels.toggled.connect(self._toggle_rel_edges)
        fl.addWidget(self.chk_rels)
        ll.addWidget(fg)

        ag=QGroupBox("Add Founders"); al_layout=QVBoxLayout(ag)
        for lb,al_pair in [("Mortal (ii)",("i","i")),("Carrier (Ii)",("I","i")),("Immortal (II)",("I","I"))]:
            b=QPushButton(lb); b.clicked.connect(lambda c,a=al_pair:self._add_founder(a[0],a[1])); al_layout.addWidget(b)
        b3=QPushButton("Seed Population"); b3.clicked.connect(self._seed); al_layout.addWidget(b3)
        ll.addWidget(ag)

        # File buttons
        iog=QGroupBox("File"); iol=QHBoxLayout(iog)
        btn_save=QPushButton("Save"); btn_save.clicked.connect(self._save); iol.addWidget(btn_save)
        btn_load=QPushButton("Load"); btn_load.clicked.connect(self._load); iol.addWidget(btn_load)
        btn_export=QPushButton("Export CSV"); btn_export.clicked.connect(self._export_csv); iol.addWidget(btn_export)
        ll.addWidget(iog)

        sg=QGroupBox("Statistics"); sl=QGridLayout(sg); self._st={}
        for i,(k,lb) in enumerate([
            ("year","Year"),("total","Total Born"),("alive","Alive"),("dead","Dead"),
            ("immortals","Immortals (II)"),("carriers","Carriers (Ii)"),("mortals","Mortals (ii)"),
            ("males","Males"),("females","Females"),
            ("avg_age","Avg Age"),("oldest","Oldest Ever"),("oldest_imm","Oldest Immortal"),
            ("oldest_car","Oldest Carrier"),("max_gen","Max Generation"),("births","Births"),
            ("deaths","Deaths"),("marriages","Marriages"),("houses_active","Active Houses"),
            ("houses_extinct","Extinct Houses"),("gene_freq_I","I Gene Freq"),
            ("achievements","Achievements"),
            ("avg_happiness","Avg Happiness"),("total_relationships","Relationships"),
            ("total_friendships","Friendships"),("total_rivalries","Rivalries"),
            ("total_mentorships","Mentorships"),("total_alliances","Alliances"),
            ("avg_influence","Avg Influence")]):
            sl.addWidget(QLabel(lb+":"),i,0); v=QLabel("0")
            v.setStyleSheet("color:#ffd700;font-weight:bold;font-size:10px;"); sl.addWidget(v,i,1); self._st[k]=v
        ll.addWidget(sg)

        lg=QGroupBox("Legend"); lgl=QVBoxLayout(lg)
        for tx,co in [("Young mortal (0-15)","#64e064"),("Adult mortal (15-55)","#3cb8e6"),
            ("Elder mortal (55+)","#7868c8"),("Carrier (Ii) shimmer","#8cb4ff"),
            ("Immortal (II) golden glow","#ffd700"),("Dead grey faded","#5a5a5a"),
            ("M / F gender","#8cb4ff"),
            ("-- Lineage parent->child","#7899d2"),("-- Marriage bond","#ff8cb4"),
            ("House dynasty ring","#aaaaaa"),("Allele badge (Ii)","#ffd700"),
            ("-- I-allele frequency","#ff6464"),
            ("-- Friendship edge","#64dc64"),(".. Rivalry edge","#ff3c3c"),
            ("-.- Mentorship edge","#b4a0ff"),("* Influence indicator","#ffd700")]:
            l=QLabel(tx); l.setStyleSheet(f"color:{co};font-size:9px;"); lgl.addWidget(l)
        ll.addWidget(lg); ll.addStretch(); root.addWidget(left)

        # CENTER (with minimap overlay)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0,0,0,0); center_layout.setSpacing(0)
        self.scene=QGraphicsScene(); self.scene.setBackgroundBrush(QBrush(QColor(12,12,24)))
        self.view=ZoomView(self.scene)
        center_layout.addWidget(self.view, 1)
        self.timeline_scrubber = TimelineScrubber()
        center_layout.addWidget(self.timeline_scrubber)
        root.addWidget(center_widget, 1)

        # v4: Mini-map overlay
        self.minimap = MiniMap(self.view)
        self.minimap.setParent(self.view.viewport())
        self.minimap.move(self.view.viewport().width() - self.minimap.width() - 10,
                          self.view.viewport().height() - self.minimap.height() - 10)
        self.minimap.show()

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
        bl=QPushButton("Highlight Lineage"); bl.clicked.connect(self._hl_lineage); il.addWidget(bl)
        bc=QPushButton("Clear Highlight"); bc.clicked.connect(self._clr_hl); il.addWidget(bc)
        bf=QPushButton("Center on Person"); bf.clicked.connect(self._center_on_sel); il.addWidget(bf)
        tabs.addTab(iw,"Inspector")

        # Event log
        lw=QWidget(); lol=QVBoxLayout(lw)
        self.ev_disp=QTextEdit(); self.ev_disp.setReadOnly(True)
        self.ev_disp.setStyleSheet("background:#1a1a2e;color:#d0d0e0;border:1px solid #333355;font-size:10px;")
        lol.addWidget(self.ev_disp); tabs.addTab(lw,"Events")

        # Chart tab
        chw=QWidget(); cvl=QVBoxLayout(chw)
        self.pop_chart=PopChart(); cvl.addWidget(self.pop_chart)
        self.gene_chart=GeneFreqChart(); cvl.addWidget(self.gene_chart)
        self.pop_pyramid = PopPyramid(); cvl.addWidget(self.pop_pyramid)
        self.eff_lbl=QLabel("No active effects"); self.eff_lbl.setStyleSheet("color:#ff9966;font-size:10px;")
        self.eff_lbl.setWordWrap(True); cvl.addWidget(self.eff_lbl)
        tabs.addTab(chw,"Charts")

        # House Rankings tab
        htw=QWidget(); htl=QVBoxLayout(htw)
        self.house_table = QTableWidget()
        self.house_table.setColumnCount(7)
        self.house_table.setHorizontalHeaderLabels(["House", "Members", "Avg Age", "Prestige", "Feuds", "Allies", "Strategy"])
        self.house_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.house_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.house_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.house_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.house_table.setColumnWidth(4, 40)
        self.house_table.setColumnWidth(5, 40)
        self.house_table.setColumnWidth(6, 60)
        self.house_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.house_table.setAlternatingRowColors(True)
        self.house_table.setStyleSheet("""
            QTableWidget { background:#1a1a2e; color:#d0d0e0; border:1px solid #333355;
                           gridline-color:#333355; font-size:10px; }
            QTableWidget::item { padding:3px; }
            QTableWidget::item:alternate { background:#222244; }
            QHeaderView::section { background:#2a2a4a; color:#ffd700; border:1px solid #333355;
                                padding:4px; font-size:9px; font-weight:bold; }
        """)
        htl.addWidget(self.house_table)
        tabs.addTab(htw,"Houses")

        # Achievements tab
        self.achievements_panel = AchievementsPanel()
        tabs.addTab(self.achievements_panel, "Achievements")

        # v5: Relationships tab
        self.rel_panel = RelationshipsPanel()
        tabs.addTab(self.rel_panel, "Relations")

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
            QLineEdit{font-size:10px;}
            QComboBox{font-size:10px;}
        """)

    def _on_search(self, text):
        mode = self.search_type.currentText()
        if mode == "Name": results = self.eng.search_people(text) if text else []
        elif mode == "Personality": results = self.eng.search_by_personality(text) if text else []
        elif mode == "Role": results = self.eng.search_by_role(text) if text else []
        else: results = []
        if results:
            alive_count = sum(1 for p in results if p.is_alive)
            self.search_results_label.setText(
                f"Found {len(results)} ({alive_count} alive) -- Enter to select first match")
        else:
            self.search_results_label.setText("No matches")

    def _on_search_select(self):
        text = self.search_input.text().strip()
        if not text: return
        mode = self.search_type.currentText()
        if mode == "Name": results = self.eng.search_people(text)
        elif mode == "Personality": results = self.eng.search_by_personality(text)
        elif mode == "Role": results = self.eng.search_by_role(text)
        else: results = []
        if results:
            alive = [p for p in results if p.is_alive]
            target = alive[0] if alive else results[0]
            self.sel_person = target; self._upd_insp(); self._center_on_sel()
            if target.id in self.nodes:
                self.nodes[target.id].highlighted = True
                self.nodes[target.id].sync()
                QTimer.singleShot(1500, lambda: self._clr_hl())

    def _apply_filters(self):
        self.filter_mortals = self.chk_mortals.isChecked()
        self.filter_carriers = self.chk_carriers.isChecked()
        self.filter_immortals = self.chk_immortals.isChecked()
        self.filter_dead = self.chk_dead.isChecked()
        for pid, node in self.nodes.items():
            p = self.eng.get_person(pid)
            if p:
                visible = True
                if not p.is_alive and not self.filter_dead: visible = False
                elif p.is_alive:
                    if p.blood_type == "mortal" and not self.filter_mortals: visible = False
                    elif p.is_carrier and not self.filter_carriers: visible = False
                    elif p.is_immortal and not self.filter_immortals: visible = False
                node.setVisible(visible); node.update()

    def _toggle_rel_edges(self, checked):
        self.show_rel_edges = checked
        for e in self.rel_edges.values():
            e.setVisible(checked)
            e.update()

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Simulation", "", "JSON Files (*.json);;All Files (*)")
        if path:
            try: self.eng.save_state(path); self._notif(f"Saved to {os.path.basename(path)}")
            except Exception as e: QMessageBox.warning(self, "Save Error", str(e))

    def _load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Simulation", "", "JSON Files (*.json);;All Files (*)")
        if path:
            try: self.eng.load_state(path); self._full_rebuild(); self._notif(f"Loaded from {os.path.basename(path)}")
            except Exception as e: QMessageBox.warning(self, "Load Error", str(e))

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Statistics", "", "CSV Files (*.csv);;All Files (*)")
        if path:
            try: self.eng.export_stats_csv(path); self._notif(f"Exported to {os.path.basename(path)}")
            except Exception as e: QMessageBox.warning(self, "Export Error", str(e))

    def _full_rebuild(self):
        self.scene.clear(); self.nodes.clear(); self.mar_edges.clear()
        self.lin_edges.clear(); self.gen_lbls.clear(); self._notifs.clear()
        self.rel_edges.clear()
        self.year_item=self.scene.addText("Year: 0",QFont("Segoe UI",15,QFont.Bold))
        self.year_item.setDefaultTextColor(QColor(255,215,0,170)); self.year_item.setZValue(100)
        for p in self.eng.people:
            self._mk_node(p)
        self._upd_gen(); self._fit()
        self._rebuild_rel_edges()

    def _on_node_context(self, person, screen_pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background:#2a2a4a; color:#e0e0f0; border:1px solid #444466;
                    padding:4px; font-size:10px; }
            QMenu::item { padding:5px 25px; }
            QMenu::item:selected { background:#4a4a8a; }
            QMenu::separator { height:1px; background:#444466; margin:2px 10px; }
        """)
        act_select = menu.addAction(f"Select {person.name}")
        act_select.triggered.connect(lambda: self._sel(person))
        act_center = menu.addAction(f"Center on {person.name}")
        act_center.triggered.connect(lambda: self._center_on_person(person))
        act_hl = menu.addAction(f"Highlight Lineage")
        act_hl.triggered.connect(lambda: (self._sel(person), self._hl_lineage()))
        menu.addSeparator()
        bt_str = person.blood_type.upper()
        menu.addAction(f"{bt_str} ({person.allele_str()})").setEnabled(False)
        menu.addAction(f"{person.house.name if person.house else 'No House'}").setEnabled(False)
        menu.addAction(f"{person.personality} ({person.role or 'None'})").setEnabled(False)
        menu.addAction(f"{person.gender}").setEnabled(False)
        if person.kills > 0:
            menu.addAction(f"Kills: {person.kills}").setEnabled(False)
        # v5: show relationship count, happiness, influence
        menu.addSeparator()
        menu.addAction(f"Relationships: {len(person.relationships)}").setEnabled(False)
        menu.addAction(f"Happiness: {person.happiness:.2f}").setEnabled(False)
        menu.addAction(f"Influence: {person.influence:.2f}").setEnabled(False)
        menu.addSeparator()
        act_pin = menu.addAction(f"Pin to Center")
        act_pin.triggered.connect(lambda: self._pin_person(person))
        locked = getattr(person, '_manually_placed', False)
        act_lock = menu.addAction(f"{'Unlock' if locked else 'Lock'} Position")
        act_lock.triggered.connect(lambda: self._toggle_lock_pos(person))
        menu.exec(screen_pos)

    def _toggle_lock_pos(self, person):
        person._manually_placed = not getattr(person, '_manually_placed', False)
        status = "locked" if person._manually_placed else "unlocked"
        self._notif(f"{person.name}'s position {status}")

    def _center_on_person(self, person):
        self.view.centerOn(person.x, person.y)

    def _center_on_sel(self):
        if self.sel_person and self.sel_person.id in self.nodes:
            self.view.centerOn(self.sel_person.x, self.sel_person.y)

    def _pin_person(self, person):
        self.sel_person = person; self._upd_insp()
        self.view.centerOn(person.x, person.y)

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
        n=PersonNode(person,on_select=self._sel, on_context=self._on_node_context)
        self.scene.addItem(n); self.nodes[person.id]=n
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
        st="IMMORTAL" if p.is_immortal else ("Carrier" if p.is_carrier else ("Deceased" if not p.is_alive else "Mortal"))
        gsym = "M" if p.gender == "M" else "F"
        self.insp_title.setText(f"{p.name} {gsym} -- {st}")
        hn=p.house.name if p.house else "None"
        ma="inf" if p.is_immortal else f"{p.max_age:.1f}"
        par=[]
        if p.mother: par.append(f"  Parent 1: {p.mother.name} ({p.mother.allele_str()})")
        if p.father: par.append(f"  Parent 2: {p.father.name} ({p.father.allele_str()})")
        sp=f"{p.spouse.name} ({p.spouse.allele_str()})" if p.spouse and p.spouse.is_alive else ("Widowed" if p.is_widowed else "Single")
        ch=", ".join(f"{c.name}({c.allele_str()})" for c in p.children[:8])
        if len(p.children)>8: ch+=f" +{len(p.children)-8}"
        sib = []
        if p.mother or p.father:
            seen_sib = set()
            for pr in [p.mother, p.father]:
                if pr:
                    for c in pr.children:
                        if c is not p and c.id not in seen_sib:
                            sib.append(c); seen_sib.add(c.id)
        stxt=", ".join(s.name for s in sib[:6]) or "None"
        anc=len(p.all_ancestors()); des=len(p.all_descendants())
        imm_ids={pp.id for pp in self.eng.people if pp.is_immortal and pp.is_alive}
        ia=sum(1 for a in p.all_ancestors() if a in imm_ids)
        tb=""
        for k,v in p.traits.items():
            f=int(v*10); tb+=f"  {k:10s} {'#'*f}{'.'*(10-f)} {v:.2f}\n"
        # v5: skills bars
        sb=""
        for sk,sv in sorted(p.skills.items(), key=lambda x:x[1], reverse=True):
            f=int(sv*10); sb+=f"  {sk:12s} {'#'*f}{'.'*(10-f)} {sv:.2f}\n"
        # v5: relationship summary
        n_friends = len(p.get_friends()); n_rivals = len(p.get_rivals()); n_mentors = len(p.get_mentors())
        rel_txt = f"  Friends: {n_friends}  Rivals: {n_rivals}  Mentors: {n_mentors}\n"
        # v5: recent memories
        mem_txt = ""
        recent = sorted(p.memories, key=lambda m: m.year, reverse=True)[:5]
        for mem in recent:
            mem_txt += f"  [Y{int(mem.year)}] {mem.description}\n"
        death_info = ""
        if p.death_age:
            cause = p.death_cause or "old age"
            death_info = f"""
== Death ==
  Died at age: {p.death_age:.1f}
  Cause:       {cause}
  Death year:  {int(p.born_year+p.death_age)}"""
        text=f"""== Identity ==
  Age:       {p.age:.1f} / {ma}
  Born:      Year {int(p.born_year)}
  Generation: {p.generation}
  Alleles:   {p.allele1}|{p.allele2}  ({p.allele_str()})
  Blood:     {p.blood_type.upper()}
  Gender:    {gsym}
  ID:        {p.id}

== House ==
  Name:      {hn}
  Prestige:  {p.house.prestige:.1f}
  Strategy:  {p.house.strategy if p.house else 'N/A'}
  Allies:    {len(p.house.allies) if p.house else 0}

== Personality & Role ==
  Type:      {p.personality}
  Strength:  {p.personality_strength:.2f}
  Role:      {p.role or 'None'}
  Role Exp:  {p.role_experience:.1f}
  Kills:     {p.kills}

== v5: Skills ==
{sb}
== Traits ==
{tb}
== v5: Relationships ==
{rel_txt}
== v5: Mood & Influence ==
  Happiness: {p.happiness:.2f}
  Influence: {p.influence:.2f}

== Family ==
  Spouse:    {sp}
  Children:  {len(p.children)}  {ch}
  Siblings:  {len(sib)}  {stxt}
  Ancestors: {anc} total
  Descendants: {des} total
  Living Immortal Ancestors: {ia}
{death_info}
== v5: Recent Memories ==
{mem_txt if mem_txt else "  (none)"}"""
        self.insp_det.setPlainText(text)

    def _hl_lineage(self):
        p=self.sel_person
        if not p: return
        ids={p.id}|p.all_ancestors()|p.all_descendants()
        for pid in list(ids):
            pp=self.eng.get_person(pid)
            if pp and pp.spouse: ids.add(pp.spouse.id)
        # v5: also highlight friends
        for fid in p.get_friends():
            ids.add(fid)
        for nid,n in self.nodes.items():
            if nid in ids: n.highlighted=True; n.dimmed=False; n.setZValue(15)
            else: n.highlighted=False; n.dimmed=True; n.setZValue(5)
            n.sync()

    def _clr_hl(self):
        for n in self.nodes.values():
            n.highlighted=False; n.dimmed=False; n.setZValue(10); n.sync()

    def _toggle(self, checked):
        self.running=checked
        if checked: self.btn_play.setText("|| Pause"); self.timer.start()
        else: self.btn_play.setText(">> Start"); self.timer.stop()

    def _sp_chg(self, v): self.speed=v/10.0; self.lb_sp.setText(f"{self.speed:.1f}x")
    def _rp_chg(self, v): self.eng.repro_rate=v/1000.0; self.lb_rp.setText(f"{self.eng.repro_rate*100:.1f} %")
    def _fit(self): self.view.fit_all()

    def _rebuild_rel_edges(self):
        """v5: Create/update RelationshipEdge graphics for all alive people."""
        # Remove old edges
        for key, edge in list(self.rel_edges.items()):
            if edge.scene(): self.scene.removeItem(edge)
        self.rel_edges.clear()
        if not self.show_rel_edges: return
        seen = set()
        for p in self.eng.people:
            if not p.is_alive: continue
            for rid, rel in p.relationships.items():
                key = (min(p.id, rid), max(p.id, rid))
                if key in seen: continue
                other = self.eng.get_person(rid)
                if other and other.is_alive and other.id in self.nodes and p.id in self.nodes:
                    seen.add(key)
                    edge = RelationshipEdge(p, other, rel.rel_type)
                    edge.setVisible(self.show_rel_edges)
                    self.scene.addItem(edge)
                    self.rel_edges[key] = edge

    def _reset(self):
        self.running=False; self.btn_play.setChecked(False); self.btn_play.setText(">> Start"); self.timer.stop()
        self.scene.clear(); self.nodes.clear(); self.mar_edges.clear()
        self.lin_edges.clear(); self.gen_lbls.clear(); self._notifs.clear()
        self.rel_edges.clear()
        self.sel_person=None; self.eng.reset(); self._last_log=0
        self.year_item=self.scene.addText("Year: 0",QFont("Segoe UI",15,QFont.Bold))
        self.year_item.setDefaultTextColor(QColor(255,215,0,170)); self.year_item.setZValue(100)
        self.insp_title.setText("Click a person to inspect"); self.insp_det.clear()
        self.ev_disp.clear(); self.pop_chart.set_data([]); self.gene_chart.set_data([])
        self.pop_pyramid.set_data([])
        self.achievements_panel.update_achievements(set())
        self.rel_panel.update_relationships(None, self.eng)
        self._seed()

    def _do_step(self, dt):
        prev_log_count = len(self.eng.log)
        self.eng.step(dt*self.speed)
        if self.pause_on_event and len(self.eng.log) > prev_log_count:
            for _, t in self.eng.log[prev_log_count:]:
                if any(marker in t for marker in ["PLAGUE","CATASTROPHE","AWAKENING","WAR","BETRAYAL","EPIDEMIC"]):
                    self.running = False
                    self.btn_play.setChecked(False)
                    self.btn_play.setText(">> Start")
                    self.timer.stop()
                    self._notif("Paused: Major Event!")
                    break
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
                for k in [k for k in self.rel_edges if k[0]==pid or k[1]==pid]:
                    self.scene.removeItem(self.rel_edges[k]); del self.rel_edges[k]
                self.scene.removeItem(self.nodes[pid]); del self.nodes[pid]

    def _sync(self):
        for p in self.eng.people:
            if p.id in self.nodes: self.nodes[p.id].sync()
        for e in self.lin_edges.values(): e.sync()
        for e in self.mar_edges.values(): e.sync()
        for e in self.rel_edges.values(): e.sync()
        s=self.eng.stats()
        self.year_item.setPlainText(f"Year: {int(s['year'])}")
        self.year_item.setPos(self.view.mapToScene(15,10))
        for k,l in self._st.items():
            v=s.get(k,0)
            if k == "gene_freq_I": l.setText(f"{v:.1%}")
            elif isinstance(v,float): l.setText(f"{v:.2f}")
            else: l.setText(str(v))
        if self.sel_person: self._upd_insp()
        if self.eng.log:
            lt="\n".join(f"[Y{y}] {t}" for y,t in self.eng.log[-50:])
            self.ev_disp.setPlainText(lt)
            sb=self.ev_disp.verticalScrollBar(); sb.setValue(sb.maximum())
        self.pop_chart.set_data(self.eng.pop_hist)
        self.pop_chart.set_event_markers(self.eng.event_markers)
        self.gene_chart.set_data(self.eng.pop_hist)
        alive = [p for p in self.eng.people if p.is_alive]
        self.pop_pyramid.set_data(alive)
        if self.eng.effects:
            pts=[]
            for e in self.eng.effects:
                n=e[0].replace("_"," ").title()
                pts.append(f"* {n}: {e[1]:+.0%} ({e[2]:.0f}y)")
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
                h.extinct=True; self.eng._log(f"House {h.name} has gone EXTINCT!")
        self._update_house_table()
        self._apply_filters()
        self.timeline_scrubber.set_year(self.eng.year)
        self.timeline_scrubber.set_event_positions(self.eng.event_markers)
        self.achievements_panel.update_achievements(self.eng.achievements)
        # v5: update relationships panel
        self.rel_panel.update_relationships(self.sel_person, self.eng)
        # v5: periodically rebuild rel_edges
        if int(self.eng.year) % 6 == 0:
            self._rebuild_rel_edges()
        # Minimap
        if self.minimap_visible:
            self.minimap.move(self.view.viewport().width() - self.minimap.width() - 10,
                              self.view.viewport().height() - self.minimap.height() - 10)
            self.minimap.update()
        if self.auto_fit and random.random()<0.02: self.view.fit_all()

    def _update_house_table(self):
        rankings = self.eng.house_rankings()
        self.house_table.setRowCount(len(rankings))
        for i, (house, members, avg_age, prestige) in enumerate(rankings):
            name_item = QTableWidgetItem(f"  {house.name}")
            name_item.setForeground(QBrush(house.color))
            name_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.house_table.setItem(i, 0, name_item)
            self.house_table.setItem(i, 1, QTableWidgetItem(str(members)))
            self.house_table.setItem(i, 2, QTableWidgetItem(f"{avg_age:.1f}"))
            pres_item = QTableWidgetItem(f"{prestige:.1f}")
            pres_item.setForeground(QBrush(QColor(255, 215, 0) if prestige > 3 else QColor(180, 180, 200)))
            self.house_table.setItem(i, 3, pres_item)
            feud_count = len(house.feuds)
            feud_item = QTableWidgetItem(str(feud_count) if feud_count else "--")
            feud_item.setForeground(QBrush(QColor(255, 80, 80) if feud_count > 0 else QColor(100, 100, 120)))
            self.house_table.setItem(i, 4, feud_item)
            ally_count = len(house.allies)
            ally_item = QTableWidgetItem(str(ally_count) if ally_count else "--")
            ally_item.setForeground(QBrush(QColor(100, 220, 100) if ally_count > 0 else QColor(100, 100, 120)))
            self.house_table.setItem(i, 5, ally_item)
            strat_colors = {"aggressive": QColor(255,80,80), "defensive": QColor(80,170,230),
                           "diplomatic": QColor(100,220,100), "neutral": QColor(180,180,200)}
            strat_item = QTableWidgetItem(house.strategy.title())
            strat_item.setForeground(QBrush(strat_colors.get(house.strategy, QColor(180,180,200))))
            self.house_table.setItem(i, 6, strat_item)

    def _notif(self, text):
        it=self.scene.addText(text,QFont("Segoe UI",11,QFont.Bold))
        it.setDefaultTextColor(QColor(255,200,100,200)); it.setZValue(200)
        yo=len(self._notifs)*30; it.setPos(self.view.mapToScene(15,40+yo))
        self._notifs.append(it); QTimer.singleShot(4000,lambda i=it:self._rm_notif(i))

    def _rm_notif(self, it):
        if it in self._notifs: self._notifs.remove(it)
        if it.scene()==self.scene: self.scene.removeItem(it)

    def keyPressEvent(self, e):
        if e.key()==Qt.Key_Space:
            self.btn_play.toggle(); self._toggle(self.btn_play.isChecked())
        elif e.key()==Qt.Key_F and not (e.modifiers() & Qt.ControlModifier):
            self._fit()
        elif e.key()==Qt.Key_R:
            self._reset()
        elif e.key()==Qt.Key_H:
            self._hl_lineage()
        elif e.key()==Qt.Key_Escape:
            self._clr_hl()
        elif e.key()==Qt.Key_S and not (e.modifiers() & Qt.ControlModifier):
            self._do_step(2.0)
        elif e.key()==Qt.Key_Question:
            ShortcutsDialog(self).exec()
        # v5: D key for relationship toggle
        elif e.key()==Qt.Key_D:
            self.show_rel_edges = not self.show_rel_edges
            self.chk_rels.setChecked(self.show_rel_edges)
            self._toggle_rel_edges(self.show_rel_edges)
            self._notif(f"Relationships {'ON' if self.show_rel_edges else 'OFF'}")
        elif e.key()==Qt.Key_T:
            self.minimap_visible = not self.minimap_visible
            self.minimap.setVisible(self.minimap_visible)
            self._notif(f"Mini-map {'ON' if self.minimap_visible else 'OFF'}")
        elif e.modifiers() & Qt.ControlModifier:
            if e.key()==Qt.Key_F:
                self.search_input.setFocus(); e.accept()
            elif e.key()==Qt.Key_S:
                self._save(); e.accept()
            elif e.key()==Qt.Key_O:
                self._load(); e.accept()
            elif e.key()==Qt.Key_E:
                self._export_csv(); e.accept()
        else:
            super().keyPressEvent(e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.minimap_visible:
            self.minimap.move(self.view.viewport().width() - self.minimap.width() - 10,
                              self.view.viewport().height() - self.minimap.height() - 10)


if __name__=="__main__":
    app=QApplication(sys.argv); app.setStyle("Fusion")
    win=MainWindow(); win.show()
    QTimer.singleShot(100,win._fit)
    sys.exit(app.exec())
