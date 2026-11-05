"""コマ割りの保存とMOSSネイティブJSONの組み立て。画像の加工は行わない。"""
import json
import math
import re
import copy
from pathlib import Path

from .i18n import both

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / 'data' / 'layouts.json'
DEFAULT_CAST = {
    '漫画家': 'An adult woman aged 22, long straight black hair, white blouse, dark pleated skirt.',
    '編集者': 'An adult man aged 35, short light hair, rectangular glasses, black business suit and tie.'}
DEFAULT_PANELS = [
    {'scene': '漫画家 sits at a desk drawing manga with a pen. Medium shot, peaceful studio.', 'dialogue': '漫画家「あと少し！」'},
    {'scene': '編集者 stands at the open studio door holding a folder. Medium shot.', 'dialogue': '編集者「原稿は？」'},
    {'scene': '漫画家 looks away nervously, holding a pen above a blank manuscript. Close-up.', 'dialogue': ''},
    {'scene': '編集者 and 漫画家 face each other across the desk with blank manuscript sheets. Medium two-shot.', 'dialogue': '編集者「まだ白紙だね」'}]


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2)


def list_layouts(language='ja'):
    key='name_en' if language=='en' else 'name'
    return [(item['id'],item[key]) for item in load_catalog()]


def load_catalog():
    document=json.loads(CATALOG.read_text(encoding='utf-8'))
    if document.get('schema_version')!=1:
        raise ValueError(both('対応していないコマ割りデータ形式です。','Unsupported layout data format.'))
    return sorted(document['layouts'],key=lambda item:item['id'])


def load_layout(identifier):
    for item in load_catalog():
        if identifier in (item['id'],item['name'],item.get('name_en')):
            return copy.deepcopy(item['specification'])
    raise ValueError(both(f'コマ割り「{identifier}」は同梱データにありません。「画像からコマ割りを選ぶ」で選び直してください。',f'The layout "{identifier}" is not in the bundled data. Pick it again with "Choose a layout from images".'))


def validate_layout(layout):
    if len(layout['panels']) not in (2,3,4,5,6):
        raise ValueError(both('対応するコマ数は2〜6です。','Layouts must have 2 to 6 panels.'))
    for i, panel in enumerate(layout['panels']):
        if panel.get('id')!=i+1:
            raise ValueError(both('コマ番号は読む順に1から連番で指定してください。','Number panels consecutively from 1 in reading order.'))
        b = panel['bbox']
        if len(b) != 4 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in b) or not (0 <= b[0] < b[2] <= 1 and 0 <= b[1] < b[3] <= 1):
            raise ValueError(both('コマ座標が不正です。','Invalid panel coordinates.'))
        polygon=panel_polygon(panel)
        if len(polygon)<3 or any(len(p)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in p) or not(b[0]<=p[0]<=b[2] and b[1]<=p[1]<=b[3]) for p in polygon):
            raise ValueError(both('コマ形状の頂点が不正です。','Invalid panel shape vertices.'))
        turns=[cross(polygon[j-1],polygon[j],polygon[(j+1)%len(polygon)]) for j in range(len(polygon))]
        if not (all(t>=-1e-9 for t in turns) or all(t<=1e-9 for t in turns)) or all(abs(t)<1e-9 for t in turns):
            raise ValueError(both('対応する多角形は面積のある凸多角形です。','Panel shapes must be convex polygons with an area.'))
        content=panel.get('content_bbox',b)
        if len(content)!=4 or not (content[0]<content[2] and content[1]<content[3]) or not all(point_inside(p,polygon) for p in rect_polygon(content)):
            raise ValueError(both('人物・セリフ用の内側領域がコマ形状からはみ出しています。','The inner area for characters and dialogue extends outside the panel shape.'))
        for other in layout['panels'][:i]:
            child,parent=(panel,other) if panel.get('parent')==other['id'] else (other,panel)
            if child.get('parent')==parent['id'] and parent.get('allow_insets'):
                if not all(point_inside(p,panel_polygon(parent)) for p in panel_polygon(child)):
                    raise ValueError(both('重ねる小コマが親コマからはみ出しています。','An inset panel extends outside its parent panel.'))
                continue
            if polygons_overlap(polygon,panel_polygon(other)):
                raise ValueError(both('コマ同士が重なっています。','Panels overlap each other.'))


def rect_polygon(b):
    x0,y0,x1,y1=b
    return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]


def panel_polygon(panel):
    return panel.get('polygon',rect_polygon(panel['bbox']))


def cross(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def point_inside(p,poly):
    turns=[cross(poly[i],poly[(i+1)%len(poly)],p) for i in range(len(poly))]
    return all(t>=-1e-9 for t in turns) or all(t<=1e-9 for t in turns)


def polygons_overlap(a,b):
    for poly in (a,b):
        for i,p in enumerate(poly):
            q=poly[(i+1)%len(poly)]; axis=(-(q[1]-p[1]),q[0]-p[0])
            pa=[v[0]*axis[0]+v[1]*axis[1] for v in a]; pb=[v[0]*axis[0]+v[1]*axis[1] for v in b]
            if min(max(pa),max(pb))-max(min(pa),min(pb))<=1e-9:
                return False
    return True


def compile_prompt(layout, mode='漫画', cast=None, panels=None):
    validate_layout(layout)
    if mode not in ('空のコマ枠', '漫画'):
        raise ValueError(both('生成内容が不正です。','Invalid output mode.'))
    w,h = layout['width'],layout['height']
    def native(b):
        x0,y0,x1,y1=b
        return [round(y0*h)-h//2,round(x0*w)-w//2,round(y1*h)-h//2,round(x1*w)-w//2]
    def within(pb, child):
        x0,y0,x1,y1=pb
        a,b,c,d=child
        return [x0+a*(x1-x0),y0+b*(y1-y0),x0+c*(x1-x0),y0+d*(y1-y0)]
    items=[]
    description=layout.get('blank_description',layout['description']) if mode=='空のコマ枠' else layout['description']
    summary=description+' Portrait white page, black and white Japanese manga. Read right to left. '
    if mode == '空のコマ枠':
        count=len(layout['panels'])
        summary += f'An empty manga page template consisting ONLY of {count} thin solid black panel frames of the specified shapes on pure white paper. All {count} interiors are entirely blank white. No people, faces, characters, scenes, backgrounds, objects, speech balloons, lettering, numbers, labels, shading, or decorations.'
        for p in layout['panels']:
            shape=p.get('shape_description','rectangular')
            items.append({'label':'object','caption':'One empty '+shape+' panel in the '+p['position']+'. Thin solid black border enclosing a completely blank pure white interior. Only the frame is visible.', 'bbox':native(p['bbox'])})
    else:
        cast = DEFAULT_CAST if cast is None else cast
        panels = DEFAULT_PANELS if panels is None else panels
        if not isinstance(cast,dict) or not cast or any(not isinstance(k,str) or not k.strip() or not isinstance(v,str) or not v.strip() for k,v in cast.items()):
            raise ValueError(both('人物設定は名前と外見説明のJSONオブジェクトで指定してください。','Characters must be a JSON object of names and appearance descriptions.'))
        if len(panels) != len(layout['panels']):
            raise ValueError(both(f"場面は{len(layout['panels'])}コマ分指定してください。",f"Provide scenes for {len(layout['panels'])} panels."))
        summary += 'Professional inked manga with screentones. Draw each character with the apparent age and natural body proportions given in their own description. Keep each recurring character identical. One frozen moment per panel. Only the explicitly supplied dialogue may appear; preserve its original language. Do not print character names, directions or panel numbers.'
        for p,s in zip(layout['panels'],panels):
            if not isinstance(s.get('scene'),str) or not s['scene'].strip():
                raise ValueError(both(f"{p['id']}コマ目の場面が空です。",f"The scene of panel {p['id']} is empty."))
            dialogue=[]
            supplied=s.get('dialogue','')
            for line in supplied if isinstance(supplied,list) else supplied.splitlines():
                if isinstance(line,dict):
                    if line.get('speaker') not in cast or not isinstance(line.get('text'),str) or not line['text'].strip():
                        raise ValueError(both(f"{p['id']}コマ目の話者またはセリフが不正です。",f"Invalid speaker or line in panel {p['id']}."))
                    dialogue.append((line['speaker'],line['text']))
                    continue
                if not line.strip():
                    continue
                m=re.fullmatch(r'\s*([^「」\n]+?)\s*「([^「」\n]+)」\s*',line)
                if not m or m[1] not in cast:
                    raise ValueError(both(f"{p['id']}コマ目のセリフは登録名「本文」の形式で指定してください。",f"Write the dialogue of panel {p['id']} as Name「text」."))
                dialogue.append((m[1],m[2]))
            if len(dialogue)>3:
                raise ValueError(both('セリフは1コマにつき3つまでです。','Up to three lines per panel.'))
            actors=s.get('actors',[name for name in cast if name in s['scene'] or any(a==name for a,_ in dialogue)])
            if not isinstance(actors,list) or not 0<=len(actors)<=3 or len(set(actors))!=len(actors) or any(a not in cast for a in actors):
                raise ValueError(both(f"{p['id']}コマ目の登場人物が不正です。",f"Invalid characters in panel {p['id']}."))
            if any(a not in actors for a,_ in dialogue):
                raise ValueError(both(f"{p['id']}コマ目の話者が登場人物に含まれていません。",f"A speaker in panel {p['id']} is not one of its characters."))
            scene=s['scene']
            pb=p.get('content_bbox',p['bbox'])
            shape=p.get('shape_description','rectangular')
            items.append({'label':'object','caption':'One black-bordered '+shape+' manga panel in the '+p['position']+'. '+scene+f' Exactly {len(actors)} people, each drawn once.'+(' Silent panel, no balloons or text.' if not dialogue else ''),'bbox':native(p['bbox'])})
            actor_boxes={}
            # First speaking person is placed at the reading-order start (right).
            boxes=s.get('composition_boxes')
            if boxes is not None and (len(boxes)!=len(actors) or any(not isinstance(b,list) or len(b)!=4 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in b) or not (0<=b[0]<b[2]<=1 and 0<=b[1]<b[3]<=1) for b in boxes)):
                raise ValueError(both('構図の人物領域が不正です。','Invalid character regions in the composition.'))
            ordered=actors if boxes is not None else list(dict.fromkeys([a for a,_ in dialogue]+actors))
            for j,name in enumerate(ordered):
                box=[.12,.32,.88,.96] if len(ordered)==1 else ([.54,.32,.96,.96] if j==0 else [.04,.32,.46,.96])
                if len(ordered)==3:
                    box=[[.69,.32,.98,.96],[.35,.32,.65,.96],[.02,.32,.31,.96]][j]
                if boxes is not None:
                    box=boxes[j]
                actor_boxes[name]=box
                items.append({'label':'character','caption':cast[name]+' One person, drawn once in this panel.','bbox':native(within(pb,box))})
            for j,(name,text) in enumerate(dialogue):
                box=[.20,.04,.94,.29] if len(dialogue)==1 else ([.53,.04,.96,.29] if j==0 else [.04,.04,.47,.29])
                if len(dialogue)==3:
                    box=[[.68,.04,.98,.29],[.35,.04,.65,.29],[.02,.04,.32,.29]][j]
                ab=actor_boxes[name]
                mouth_y=ab[1]+.23*(ab[3]-ab[1]) if boxes is not None else .47
                mouth=within(pb,[(ab[0]+ab[2])/2,mouth_y,(ab[0]+ab[2])/2,mouth_y])
                target=f'x={round(mouth[0]*w-w/2)}, y={round(mouth[1]*h-h/2)}'
                items.append({'label':'text','caption':f'White speech balloon with legible black manga lettering. The speaker is the character whose mouth is near {target}; point the balloon tail to that mouth. Render only the supplied text exactly once, in its original language.','text':text,'bbox':native(within(pb,box))})
    result={'summary':{'caption':summary},'items':items,'bbox_coord_space':'abs_centralized','bbox_format':'yxyx'}
    return dumps(result)
