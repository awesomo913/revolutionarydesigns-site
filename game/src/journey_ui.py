"""Shared Journey menus, field guide, HUD and end screens."""
import math
import pygame
from config import LEVEL_NAMES, PLAYER_MAX_HP
from journey_art import CREAM, GOLD, SAGE, DARK, CACHE, world, panda, creature, relic, GUIDE_KEYS, LEVEL_WORLDS

def font(size,bold=False):
    key=('font',size,bold)
    if key not in CACHE:
        f=pygame.font.Font(None,size);f.set_bold(bold);CACHE[key]=f
    return CACHE[key]

def text(screen,value,pos,size=22,color=CREAM,center=False):
    art=font(size).render(str(value),True,color)
    screen.blit(art,art.get_rect(center=pos) if center else pos)

def wrap(screen,value,pos,width,size=22,color=SAGE,leading=26):
    y=pos[1]
    for paragraph in value.split('\n'):
        line=''
        for word in paragraph.split():
            candidate=(line+' '+word).strip()
            if font(size).size(candidate)[0]>width and line:
                text(screen,line,(pos[0],y),size,color);y+=leading;line=word
            else: line=candidate
        if line: text(screen,line,(pos[0],y),size,color);y+=leading
        elif not paragraph: y+=leading//2
    return y

def panel(screen,rect,alpha=235):
    rect=pygame.Rect(rect);surf=pygame.Surface(rect.size,pygame.SRCALPHA)
    pygame.draw.rect(surf,(*DARK,alpha),surf.get_rect(),border_radius=14)
    pygame.draw.rect(surf,(112,129,87,200),surf.get_rect(),1,border_radius=14)
    screen.blit(surf,rect)

def shade(screen,alpha=180):
    surf=pygame.Surface(screen.get_size(),pygame.SRCALPHA);surf.fill((*DARK,alpha));screen.blit(surf,(0,0))

ABILITIES=[('Move','A / D or arrows','Follow the trail to the glowing gate.',0),
 ('Double jump','Space / W / Up','Release, then jump again in the air.',0),
 ('Bamboo staff','E / X or click','Collect a staff to strike. Watch its timer.',2),
 ('Throw bamboo','Q / Ctrl','Requires a staff. One throw every 0.5s.',3),
 ('Dash','Shift','Collect boots, then burst through a gap.',4),
 ('Leaf glide','Hold Space in air','Leaf charge runs only while gliding.',5),
 ('Ground slam','S / Down in air','Drop quickly onto a stompable enemy.',0),
 ('Ice magic','R','Beat a boss. Cast when mana is full.',6)]

class JourneyMenu:
    def __init__(self,paused=False):
        self.paused=paused;self.page='home';self.page_number=0;self.selected_char=None
        self.gallery_open=False;self.prompt_timer=0.;self.action=None;self.buttons=[];self.focus=0
        self._gallery_button_rect=pygame.Rect(0,0,0,0);self._card_rects=[]
    def update(self,dt): self.prompt_timer+=dt
    def button(self,screen,label,rect,action,primary=False):
        rect=pygame.Rect(rect);index=len(self.buttons)
        hover=rect.collidepoint(pygame.mouse.get_pos()) or index==self.focus
        color=(183,199,128) if primary else (35,59,44) if hover else (15,34,28)
        pygame.draw.rect(screen,color,rect,border_radius=9)
        pygame.draw.rect(screen,GOLD if hover else (106,123,79),rect,2 if hover else 1,border_radius=9)
        text(screen,label,rect.center,23,DARK if primary else CREAM,True)
        self.buttons.append((rect,action));return rect
    def activate(self,action):
        if action in ('field','chapters','controls','home'):
            self.page=action;self.page_number=0;self.selected_char=None;self.focus=0;self.gallery_open=action=='field'
        elif action=='back':
            if self.selected_char is not None: self.selected_char=None
            else: self.page='home';self.gallery_open=False
            self.focus=0
        elif action in ('next','prev'):
            count=3 if self.page=='chapters' else math.ceil(len(self.characters())/8)
            self.page_number=(self.page_number+(1 if action=='next' else -1))%count;self.focus=0
        elif action.startswith('char:'):
            self.selected_char=self.characters()[int(action.split(':')[1])];self.focus=0
        else: self.action=action
    def handle_click(self,pos):
        for i,(rect,action) in enumerate(self.buttons):
            if rect.collidepoint(pos): self.focus=i;self.activate(action);return True
        return False
    def handle_key(self,key):
        if key in (pygame.K_ESCAPE,pygame.K_BACKSPACE):
            if self.page!='home' or self.selected_char: self.activate('back')
            elif self.paused: self.action='resume'
            return True
        if key in (pygame.K_LEFT,pygame.K_UP,pygame.K_RIGHT,pygame.K_DOWN,pygame.K_TAB):
            self.focus=(self.focus+(-1 if key in (pygame.K_LEFT,pygame.K_UP) else 1))%max(1,len(self.buttons));return True
        if key in (pygame.K_RETURN,pygame.K_SPACE):
            if self.buttons: self.activate(self.buttons[min(self.focus,len(self.buttons)-1)][1])
            return True
        if self.paused and key==pygame.K_q: self.action='quit'
        return True
    @staticmethod
    def characters():
        from ui import _CHARACTERS
        return _CHARACTERS+[dict(name='Grove Keeper',role='GUIDE',desc='A friend along the path',key='npc',story='The keepers remember every path through the forest. Approach a keeper to read their advice. They are friendly: you can safely walk past them.\n\nTIP: Look for the gold question mark and listen before entering a new region.')]
    def draw(self,screen):
        self.buttons=[];self._card_rects=[]
        screen.blit(world('forest'),(0,0));shade(screen,80 if self.page=='home' else 205)
        if self.page=='home':
            panel(screen,(38,36,430,468),238)
            text(screen,'THE LEGEND OF PAIN-DA',(68,64),19,GOLD)
            text(screen,'Bamboo',(64,100),76);text(screen,'Forest',(64,164),76)
            wrap(screen,'A small guardian. An extraordinary journey.',(68,247),335,24,CREAM,28)
            text(screen,'18 chapters  /  One enchanted world',(68,312),21,SAGE)
            self.button(screen,'Continue journey' if self.paused else 'Begin journey',(68,350,370,48),'resume' if self.paused else 'start',True)
            self._gallery_button_rect=self.button(screen,'Field guide',(68,413,177,40),'field')
            self.button(screen,'Abilities',(261,413,177,40),'controls')
            self.button(screen,'Return to title' if self.paused else 'Explore chapters',(68,466,370,26),'quit' if self.paused else 'chapters')
            from journey_art import tile
            screen.blit(tile(272,38),(576,461))
            hero=panda(0,(185,195));screen.blit(hero,hero.get_rect(midbottom=(712,461)))
            text(screen,'JOURNEY PAUSED' if self.paused else 'WOODLAND EDITION',(718,52),19,GOLD,True)
            from save import load_high_scores
            panel(screen,(511,79,403,171),220)
            text(screen,'TOP THREE / THIS DEVICE',(713,101),19,GOLD,True)
            scores=load_high_scores()
            for i in range(3):
                row=scores[i] if i<len(scores) else None
                text(screen,f'{i+1:02}',(536,133+i*34),23,SAGE)
                text(screen,row['initials'] if row else '---',(583,133+i*34),25,CREAM)
                text(screen,f"{row['score']:06}  / CH {row['level']:02}" if row else 'Your journey awaits',(670,135+i*34),20,GOLD)
            text(screen,'Enter to choose / M music / N effects',(713,510),19,CREAM,True);return
        text(screen,{'field':'The field guide','chapters':'Choose your chapter','controls':'Your abilities'}[self.page],(38,31),44)
        self.button(screen,'Back',(806,27,118,40),'back')
        if self.page=='controls':
            text(screen,'Collect relics, read their timers, and learn when to use each move.',(40,83),21,SAGE)
            for i,(name,keys,desc,idx) in enumerate(ABILITIES):
                x=38+(i%2)*449;y=125+(i//2)*94;panel(screen,(x,y,435,82))
                icon=panda(4 if name=='Double jump' else 10 if name=='Ground slam' else 2,(43,50)) if idx==0 else relic(idx,(43,50))
                screen.blit(icon,icon.get_rect(center=(x+37,y+38)))
                text(screen,name,(x+72,y+10),24);text(screen,keys,(x+72,y+35),19,GOLD)
                wrap(screen,desc,(x+72,y+56),345,17,SAGE,19)
            return
        if self.page=='chapters':
            text(screen,'PRACTICE MODE  /  Unlimited retries. Equipped abilities. No high scores.',(40,84),21,SAGE)
            for j in range(6):
                i=self.page_number*6+j;x=38+j%3*299;y=123+j//3*162
                screen.blit(world(LEVEL_WORLDS[i],(284,106)),(x,y))
                self.button(screen,f'{i+1:02}  {LEVEL_NAMES[i]}',(x,y+105,284,42),f'practice:{i}')
        elif self.selected_char is not None:
            char=self.selected_char;panel(screen,(38,113,884,377))
            art=panda(0,(208,258)) if char['key']=='panda' else creature(GUIDE_KEYS.get(char['key'],23),(230,258))
            screen.blit(art,art.get_rect(center=(183,302)))
            text(screen,char['role'],(340,138),18,GOLD);text(screen,char['name'],(338,166),42)
            wrap(screen,char['story'],(340,222),547,22,CREAM,26);return
        else:
            text(screen,'Know the creatures. Learn their tells. Find your opening.',(40,84),21,SAGE)
            for j,char in enumerate(self.characters()[self.page_number*8:self.page_number*8+8]):
                x=38+(j%4)*224;y=122+(j//4)*165
                rect=self.button(screen,'',(x,y,211,150),f'char:{self.page_number*8+j}')
                art=panda(0,(95,85)) if char['key']=='panda' else creature(GUIDE_KEYS.get(char['key'],23),(115,85))
                screen.blit(art,art.get_rect(center=(x+105,y+51)))
                text(screen,char['name'],(x+105,y+106),23,CREAM,True);text(screen,char['role'],(x+105,y+130),16,GOLD,True)
                self._card_rects.append((rect,char))
        self.button(screen,'Previous',(38,477,144,38),'prev')
        count=3 if self.page=='chapters' else math.ceil(len(self.characters())/8)
        text(screen,f'{self.page_number+1} / {count}',(480,496),23,SAGE,True)
        self.button(screen,'Next',(778,477,144,38),'next')

def hud_draw(self,screen,player,level_num,camera):
    panel(screen,(16,14,263,78));icon=panda(0,(43,51));screen.blit(icon,(26,25))
    text(screen,'VITALITY',(82,25),16,SAGE)
    pygame.draw.rect(screen,(61,66,45),(82,46,177,9),border_radius=4)
    ratio=max(0,min(1,self.displayed_hp/PLAYER_MAX_HP))
    pygame.draw.rect(screen,(179,202,126),(82,46,int(177*ratio),9),border_radius=4)
    text(screen,f'{int(player.health)} / {PLAYER_MAX_HP}',(82,65),17,CREAM)
    text(screen,'PRACTICE' if getattr(self,'practice',False) else f'{self.lives} LIVES',(183,65),17,GOLD)
    panel(screen,(690,14,254,78));text(screen,f'{level_num:02}  {LEVEL_NAMES[level_num-1]}',(705,26),22)
    text(screen,f'{player.score:05}  /  {self.collected_bamboos}/{self.total_bamboos} bamboo',(705,62),18,GOLD)
    panel(screen,(292,14,386,58),200)
    progress=max(0,min(1,player.rect.centerx/max(1,camera.world_width-150)))
    pygame.draw.line(screen,(74,88,60),(301,29),(664,29),2)
    pygame.draw.line(screen,GOLD,(301,29),(301+int(363*progress),29),2)
    pygame.draw.circle(screen,CREAM,(301+int(363*progress),29),4)
    text(screen,'FOLLOW THE BAMBOO',(482,48),15,SAGE,True)
    powers=[('E',2,player.weapon_time_remaining),('SHIFT',4,player.dash_time_remaining),('SPACE',5,player.glide_time_remaining)]
    if player.has_ice_magic: powers.append(('R',6,player.mana))
    for i,(key,idx,amount) in enumerate(powers):
        x=16+i*65;panel(screen,(x,106,58,73),208)
        art=relic(idx,(30,30));screen.blit(art,art.get_rect(center=(x+29,130)))
        text(screen,key,(x+29,153),14,CREAM,True)
        label=('READY' if amount>=player.mana_max else f'{int(amount)}%') if idx==6 else f'{math.ceil(amount)}s' if amount>0 else '--'
        text(screen,label,(x+29,169),14,GOLD if amount>0 else SAGE,True)
    if player.combo_count>1: text(screen,f'{player.combo_count}x COMBO',(480,80),26,GOLD,True)
    for floating in self.floating_texts: floating.draw(screen,camera)

class EndScreen:
    def __init__(self,victory=False):
        self.timer=0.;self.fade_alpha=0.;self.victory=victory
        self.pending=False;self.initials=['A','A','A'];self.cursor=0;self.saved=False;self.save_failed=False;self.score=0;self.level=1
    def offer(self,score,level,practice=False):
        from save import qualifies
        self.score=score;self.level=level;self.pending=not practice and qualifies(score)
    def submit(self):
        from save import save_high_score
        self.saved=save_high_score(self.score,self.level,''.join(self.initials));self.save_failed=not self.saved;self.pending=False
    def handle_key(self,key):
        if not self.pending: return False
        if pygame.K_a<=key<=pygame.K_z:
            self.initials[self.cursor]=chr(key).upper();self.cursor=min(2,self.cursor+1)
        elif key in (pygame.K_LEFT,pygame.K_BACKSPACE): self.cursor=max(0,self.cursor-1)
        elif key==pygame.K_RIGHT: self.cursor=min(2,self.cursor+1)
        elif key in (pygame.K_UP,pygame.K_DOWN):
            self.initials[self.cursor]=chr(65+(ord(self.initials[self.cursor])-65+(1 if key==pygame.K_UP else -1))%26)
        elif key==pygame.K_RETURN: self.submit()
        return True
    def handle_click(self,pos):
        if not self.pending: return False
        if pygame.Rect(310,403,340,49).collidepoint(pos): self.submit()
        for i in range(3):
            if pygame.Rect(392+i*60,330,52,58).collidepoint(pos):
                self.cursor=i;self.initials[i]=chr(65+(ord(self.initials[i])-64)%26)
        return True
    def update(self,dt): self.timer+=dt;self.fade_alpha=min(220,self.fade_alpha+dt*300)
    def draw(self,screen,score,is_high_score=False):
        screen.blit(world('forest' if self.victory else 'corrupted'),(0,0));shade(screen,125);panel(screen,(256,42,448,456))
        text(screen,'THE GROVE REMEMBERS',(480,74),18,GOLD,True)
        art=panda(11 if self.victory else 9,(130,145));screen.blit(art,art.get_rect(midbottom=(480,248)))
        text(screen,'Forest restored' if self.victory else 'A moment to rest',(480,282),45,CREAM,True)
        text(screen,f'{score:05}  JOURNEY SCORE',(480,327),25,GOLD,True)
        if self.pending:
            for i,letter in enumerate(self.initials):
                pygame.draw.rect(screen,(64,83,51) if i==self.cursor else DARK,(392+i*60,341,52,44),border_radius=5)
                text(screen,letter,(418+i*60,363),32,GOLD,True)
        else: text(screen,'Score saved to the top three' if self.saved else ('Storage unavailable: score not saved' if self.save_failed else 'Every path teaches you something.'),(480,365),22,SAGE,True)
        pygame.draw.rect(screen,(180,198,130),(310,403,340,49),border_radius=9)
        text(screen,'Save initials' if self.pending else 'Return to title',(480,427),25,DARK,True)
        text(screen,'Type 3 letters / tap a letter to change it' if self.pending else 'Enter or click to continue',(480,475),18,SAGE,True)

class VictoryScreen(EndScreen):
    def __init__(self): super().__init__(True)

class LevelTransition:
    def __init__(self,level_number): self.level_number=level_number;self.timer=0.;self.duration=2.4
    def update(self,dt): self.timer+=dt;return self.timer>=self.duration
    def draw(self,screen):
        i=max(0,min(17,self.level_number-1));screen.blit(world(LEVEL_WORLDS[i]),(0,0));shade(screen,145);panel(screen,(202,181,556,179),200)
        text(screen,f'CHAPTER {self.level_number:02}',(480,218),21,GOLD,True)
        text(screen,LEVEL_NAMES[i],(480,270),47,CREAM,True);text(screen,'A new path through the forest',(480,320),23,SAGE,True)
