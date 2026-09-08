"""Validated high scores, persisted across browser reloads when storage allows."""
import json
import sys
from pathlib import Path
from config import SAVE_FILE
MAX_SCORES=3
STORAGE_KEY='bamboo-forest.high-scores.v1'

def initials(value):
    letters=''.join(c for c in str(value).upper() if 'A'<=c<='Z')[:3]
    return letters.ljust(3,'A')

def _storage():
    if sys.platform=='emscripten':
        import platform
        return platform.window.localStorage
    return None

def load_high_scores():
    try:
        storage=_storage()
        raw=storage.getItem(STORAGE_KEY) if storage is not None else Path(SAVE_FILE).read_text()
        data=json.loads(str(raw)) if raw else {}
        candidates=data.get('high_scores',[]) if isinstance(data,dict) else []
        scores=[{'score':s['score'],'level':s['level'],'initials':initials(s.get('initials','AAA'))} for s in candidates if isinstance(s,dict) and type(s.get('score')) is int and type(s.get('level')) is int and 0<=s['score']<=1000000 and 1<=s['level']<=18]
        return sorted(scores,key=lambda s:s['score'],reverse=True)[:MAX_SCORES]
    except Exception:
        # Private browsing, malformed data or disabled storage must never stop play.
        return []

def qualifies(score):
    scores=load_high_scores()
    return score>0 and (len(scores)<MAX_SCORES or score>scores[-1]['score'])

def save_high_score(score,level_reached,name='AAA'):
    if type(score) is not int or type(level_reached) is not int or not 0<=score<=1000000 or not 1<=level_reached<=18: return False
    scores=load_high_scores();entry={'score':score,'level':level_reached,'initials':initials(name)}
    scores.append(entry);scores.sort(key=lambda s:s['score'],reverse=True);scores=scores[:MAX_SCORES]
    try:
        raw=json.dumps({'high_scores':scores})
        storage=_storage()
        if storage is not None: storage.setItem(STORAGE_KEY,raw)
        else: Path(SAVE_FILE).write_text(raw)
    except Exception: return False
    return entry in scores

def get_best_score():
    scores=load_high_scores();return scores[0]['score'] if scores else 0
