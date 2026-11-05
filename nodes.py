"""専用欄の入力をMOSSプロンプトへ渡すComfyUIノード。"""
import json

from . import dataset as core
from . import composition
from .appearance import MossCharacterAppearance
from .i18n import (ACTORS, SPEAKERS, OUTPUTS, EDITOR_MODES, CATEGORY, LABELS, SLOT_EN, both, canonical,
    labeled, options, outputs, slot_label, actors_label)

SLOTS=['人物1','人物2','人物3']
ACTOR_SLOTS={'人物1のみ':['人物1'],'人物2のみ':['人物2'],'人物1と人物2':['人物1','人物2'],'人物なし':[],
    '人物3のみ':['人物3'],'人物1と人物3':['人物1','人物3'],'人物2と人物3':['人物2','人物3'],'人物1と人物2と人物3':SLOTS.copy()}
SCENES=['Drawing a manga manuscript with a pen at a desk. Medium shot of the studio.','Standing at the open studio door holding a folder.','Looking away nervously, holding a pen above a blank manuscript. Close-up.','Facing each other across a desk with blank manuscript sheets. Medium two-shot.']


class MossMangaCharacters:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':labeled('MossMangaCharacters',{
            '人物1_名前':('STRING',{'default':'漫画家'}),
            '人物1_外見':('STRING',{'multiline':True,'default':core.DEFAULT_CAST['漫画家']}),
            '人物2_名前':('STRING',{'default':'編集者'}),
            '人物2_外見':('STRING',{'multiline':True,'default':core.DEFAULT_CAST['編集者']})}),
            'optional':labeled('MossMangaCharacters',{'人物3_名前':('STRING',{'default':''}),
            '人物3_外見':('STRING',{'multiline':True,'default':''})})}
    RETURN_TYPES=('MOSS_MANGA_CAST',)
    RETURN_NAMES=outputs('MossMangaCharacters',1)
    DESCRIPTION=LABELS['MossMangaCharacters']['description']
    FUNCTION='build'
    CATEGORY=CATEGORY
    def build(self,**kw):
        cast={s:{'name':kw[s+'_名前'].strip(),'appearance':kw[s+'_外見'].strip()} for s in SLOTS[:2]}
        third={'name':kw.get('人物3_名前','').strip(),'appearance':kw.get('人物3_外見','').strip()}
        if third['name'] or third['appearance']:
            if not third['name'] or not third['appearance']:
                missing,missing_en=('人物3_名前','Character 3 name') if not third['name'] else ('人物3_外見','Character 3 appearance')
                raise ValueError(both(f'人物3を使うには「人物3_名前」と「人物3_外見」を両方入力してください。今は「{missing}」が空です。使わない場合は両方空欄にしてください。',
                    f'To use character 3, fill in both "Character 3 name" and "Character 3 appearance". "{missing_en}" is empty. Leave both empty if you do not use character 3.'))
            cast['人物3']=third
        for slot,person in cast.items():
            n=slot[-1]
            if not person['name']:
                raise ValueError(both(f'「人物{n}_名前」が空です。名前を入力してください（日本語でも構いません）。',f'"Character {n} name" is empty. Enter a name (any language).'))
            if not person['appearance']:
                raise ValueError(both(f'「人物{n}_外見」が空です。外見を英語で入力するか、「人物の外見（画像／文章）」の出力を接続してください。',
                    f'"Character {n} appearance" is empty. Describe the appearance in English, or connect the output of "Character appearance (image / text)".'))
        names=[person['name'] for person in cast.values()]
        duplicated=sorted({name for name in names if names.count(name)>1})
        if duplicated:
            raise ValueError(both(f'人物の名前「{"」「".join(duplicated)}」が重複しています。人物ごとに別の名前にしてください。',
                f'The character name "{", ".join(duplicated)}" is used more than once. Give each character a different name.'))
        return (cast,)

class MossMangaPanel:
    @classmethod
    def INPUT_TYPES(cls):
        speakers=options(SPEAKERS)
        return {'required':labeled('MossMangaPanel',{
            '場面':('STRING',{'multiline':True,'default':SCENES[0]}),
            '登場人物':(options(ACTORS),),
            '話者1':(speakers,),
            'セリフ1':('STRING',{'multiline':True,'default':''}),
            '話者2':(speakers,),
            'セリフ2':('STRING',{'multiline':True,'default':''})}),
            'optional':labeled('MossMangaPanel',{'構図':('MOSS_COMPOSITION',),
                '話者3':(speakers,{'default':'セリフなし'}),
                'セリフ3':('STRING',{'multiline':True,'default':''})})}
    RETURN_TYPES=('MOSS_MANGA_PANEL',)
    RETURN_NAMES=outputs('MossMangaPanel',1)
    DESCRIPTION=LABELS['MossMangaPanel']['description']
    FUNCTION='build'
    CATEGORY=CATEGORY
    def build(self,**kw):
        scene=kw['場面'].strip()
        if not scene:
            raise ValueError(both('「場面」が空です。このコマの場面を英語で入力してください。','"Scene" is empty. Describe the scene of this panel in English.'))
        chosen=canonical(ACTORS,kw['登場人物'],'登場人物','Characters')
        actors=ACTOR_SLOTS[chosen]
        lines=[]
        for i in (1,2,3):
            speaker=canonical(SPEAKERS,kw.get(f'話者{i}','セリフなし'),f'話者{i}',f'Speaker {i}')
            text=kw.get(f'セリフ{i}','')
            if speaker=='セリフなし':
                if text.strip():
                    raise ValueError(both(f'「セリフ{i}」に本文がありますが、「話者{i}」が「セリフなし」です。話者{i}で話す人物を選ぶか、セリフ{i}を空欄にしてください。',
                        f'"Line {i}" has text, but "Speaker {i}" is "No dialogue". Choose who says line {i}, or clear line {i}.'))
                continue
            if not actors:
                raise ValueError(both(f'登場人物が「人物なし」のコマには、セリフを付けられません。「話者{i}」が{slot_label(speaker)}になっています。登場人物を選ぶか、話者{i}を「セリフなし」にしてください。',
                    f'A panel with "No characters" cannot have dialogue, but "Speaker {i}" is {SLOT_EN[speaker]}. Choose characters for the panel, or set speaker {i} to "No dialogue".'))
            if speaker not in actors:
                raise ValueError(both(f'「話者{i}」に{slot_label(speaker)}を選んでいますが、このコマの登場人物は{actors_label(chosen)}です。{speaker}はこのコマに登場しないため、セリフを話せません。登場人物に{speaker}を含めるか、話者{i}を変えてください。',
                    f'"Speaker {i}" is {SLOT_EN[speaker]}, but this panel\'s characters are "{dict(ACTORS)[chosen]}". {SLOT_EN[speaker]} is not in this panel and cannot speak. Add {SLOT_EN[speaker]} to the characters, or change speaker {i}.'))
            if not text.strip():
                raise ValueError(both(f'「話者{i}」に{slot_label(speaker)}を選んでいますが、「セリフ{i}」が空です。本文を入力するか、話者{i}を「セリフなし」にしてください。',
                    f'"Speaker {i}" is {SLOT_EN[speaker]}, but "Line {i}" is empty. Enter the line, or set speaker {i} to "No dialogue".'))
            lines.append({'slot':speaker,'text':text})
        panel={'scene':scene,'actors':list(actors),'dialogue':lines}
        if kw.get('構図') is not None:
            template=kw['構図']
            boxes=template.get('boxes')
            if not isinstance(template.get('prompt'),str) or not template['prompt'].strip() or not isinstance(boxes,list):
                raise ValueError(both('構図データが不正です。「構図」には「構図を選ぶ（見本画像）」ノードの出力を接続してください。',
                    'Invalid composition data. Connect the output of "Choose a composition (preview images)" to "Composition".'))
            if len(actors)!=len(boxes):
                raise ValueError(both(f'接続した構図「{template.get("name","")}」は{len(boxes)}人用ですが、このコマの登場人物は{len(actors)}人（{actors_label(chosen)}）です。人数の合う構図を選ぶか、登場人物を変えてください。',
                    f'The connected composition "{template.get("name_en") or template.get("name","")}" is for {len(boxes)} character(s), but this panel has {len(actors)} ("{dict(ACTORS)[chosen]}"). Choose a composition with the same number of characters, or change the characters.'))
            panel['scene']=scene+' Composition: '+template['prompt']
            panel['composition_boxes']=template['boxes']
        return (panel,)

class MossPanelDatasetFlexible:
    @classmethod
    def INPUT_TYPES(cls):
        names=[name for _,name in core.list_layouts()]+[name for _,name in core.list_layouts('en')]
        required={'コマ割り':(names,),'生成内容':(options(OUTPUTS),),'人物設定':('MOSS_MANGA_CAST',)}
        required.update({f'コマ{i}':('MOSS_MANGA_PANEL',) for i in (1,2)})
        return {'required':labeled('MossPanelDatasetFlexible',required),'optional':labeled('MossPanelDatasetFlexible',{f'コマ{i}':('MOSS_MANGA_PANEL',) for i in (3,4,5,6)})}
    RETURN_TYPES=('STRING','INT','INT')
    RETURN_NAMES=outputs('MossPanelDatasetFlexible',3)
    DESCRIPTION=LABELS['MossPanelDatasetFlexible']['description']
    FUNCTION='build'
    CATEGORY=CATEGORY
    @classmethod
    def IS_CHANGED(cls,**kw):
        return core.CATALOG.stat().st_mtime_ns

    def build(self,**kw):
        layout=core.load_layout(kw['コマ割り'])
        mode=canonical(OUTPUTS,kw['生成内容'],'生成内容','Output')
        if mode=='空のコマ枠':
            prompt=core.compile_prompt(layout,'空のコマ枠')
        else:
            count=len(layout['panels'])
            expected={i for i in range(1,count+1)}
            supplied={i for i in range(1,7) if kw.get(f'コマ{i}') is not None}
            if supplied!=expected:
                missing=sorted(expected-supplied); extra=sorted(supplied-expected)
                detail_ja='・'.join(([f'未接続: {"、".join(f"コマ{i}" for i in missing)}'] if missing else [])+([f'余分: {"、".join(f"コマ{i}" for i in extra)}'] if extra else []))
                detail_en='; '.join(([f'not connected: {", ".join(f"panel {i}" for i in missing)}'] if missing else [])+([f'extra: {", ".join(f"panel {i}" for i in extra)}'] if extra else []))
                raise ValueError(both(f'選んだコマ割りは{count}コマです。コマ1〜コマ{count}に「コマの内容」を1つずつ接続し、それ以外の接続は外してください（{detail_ja}）。',
                    f'The selected layout has {count} panels. Connect one "Panel content" node to each of panel 1 to panel {count}, and disconnect the others ({detail_en}).'))
            cast=kw['人物設定']
            panels=[]
            for i in range(1,count+1):
                p=kw[f'コマ{i}']
                missing=[slot for slot in p['actors'] if slot not in cast]
                if missing:
                    slot=missing[0]
                    raise ValueError(both(f'{i}コマ目の登場人物に{slot_label(slot)}がいますが、「共通の人物設定」に{slot}が登録されていません。「{slot}_名前」と「{slot}_外見」を両方入力するか、{i}コマ目の登場人物を変えてください。',
                        f'Panel {i} uses {SLOT_EN[slot]}, but {SLOT_EN[slot]} is not set in "Shared characters". Fill in both "{SLOT_EN[slot]} name" and "{SLOT_EN[slot]} appearance", or change the characters of panel {i}.'))
                panels.append({'scene':p['scene'],'actors':[cast[s]['name'] for s in p['actors']],
                    'dialogue':[{'speaker':cast[line['slot']]['name'],'text':line['text']} for line in p['dialogue']]})
                if 'composition_boxes' in p:
                    panels[-1]['composition_boxes']=p['composition_boxes']
            prompt=core.compile_prompt(layout,'漫画',{p['name']:p['appearance'] for p in cast.values()},panels)
        return prompt,layout['width'],layout['height']

class MossPromptEditor:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':labeled('MossPromptEditor',{
            'プロンプト':('STRING',{'forceInput':True}),
            '使うプロンプト':(options(EDITOR_MODES),),
            '編集用プロンプト':('STRING',{'multiline':True,'default':''})})}
    RETURN_TYPES=('STRING',)
    RETURN_NAMES=outputs('MossPromptEditor',1)
    DESCRIPTION=LABELS['MossPromptEditor']['description']
    FUNCTION='build'
    CATEGORY=CATEGORY
    def build(self,**kw):
        received=kw['プロンプト']
        if canonical(EDITOR_MODES,kw['使うプロンプト'],'使うプロンプト','Prompt to use')=='受け取ったまま':
            prompt=received
        else:
            edited=kw['編集用プロンプト']
            if not edited.strip():
                raise ValueError(both('「編集用プロンプト」が空です。一度「受け取ったまま」で実行すると、受け取った内容が入ります。',
                    '"Edited prompt" is empty. Run once with "As received" to fill it with the received prompt.'))
            try:
                prompt=core.dumps(json.loads(edited))
            except json.JSONDecodeError as error:
                raise ValueError(both(f'「編集用プロンプト」をJSONとして読めません（{error.lineno}行目{error.colno}文字目）。括弧・カンマ・引用符を確認してください。',
                    f'"Edited prompt" is not valid JSON (line {error.lineno}, column {error.colno}). Check brackets, commas, and quotes.')) from error
        return {'ui':{'text':[received]},'result':(prompt,)}

class MossCompositionTemplate:
    @classmethod
    def INPUT_TYPES(cls):
        items=composition.catalog()
        names=[item['name'] for item in items]+[item['name_en'] for item in items]
        return {'required':labeled('MossCompositionTemplate',{'構図テンプレート':(names or ['生成済みの構図がありません / No compositions'],)})}
    RETURN_TYPES=('MOSS_COMPOSITION','STRING')
    RETURN_NAMES=outputs('MossCompositionTemplate',2)
    DESCRIPTION=LABELS['MossCompositionTemplate']['description']
    FUNCTION='build'
    CATEGORY=CATEGORY
    @classmethod
    def IS_CHANGED(cls,**kw):
        return composition.CATALOG.stat().st_mtime_ns if composition.CATALOG.exists() else 0
    def build(self,**kw):
        item=composition.load(kw['構図テンプレート'])
        return item,item['prompt']

NODE_CLASS_MAPPINGS={'MossCompositionTemplate':MossCompositionTemplate,'MossPanelDatasetFlexible':MossPanelDatasetFlexible,'MossMangaCharacters':MossMangaCharacters,'MossMangaPanel':MossMangaPanel,'MossPromptEditor':MossPromptEditor,'MossCharacterAppearance':MossCharacterAppearance}
NODE_DISPLAY_NAME_MAPPINGS={name:LABELS[name]['display_name'] for name in NODE_CLASS_MAPPINGS}
