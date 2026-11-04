"""専用欄の入力をMOSSプロンプトへ渡すComfyUIノード。"""
import json

from . import dataset as core
from . import composition

SLOTS=['人物1','人物2','人物3']
ACTORS={'人物1のみ':['人物1'],'人物2のみ':['人物2'],'人物1と人物2':['人物1','人物2'],'人物なし':[],
    '人物3のみ':['人物3'],'人物1と人物3':['人物1','人物3'],'人物2と人物3':['人物2','人物3'],'人物1と人物2と人物3':SLOTS.copy()}
SCENES=['Drawing a manga manuscript with a pen at a desk. Medium shot of the studio.','Standing at the open studio door holding a folder.','Looking away nervously, holding a pen above a blank manuscript. Close-up.','Facing each other across a desk with blank manuscript sheets. Medium two-shot.']

class MossMangaCharacters:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{
            '人物1_名前':('STRING',{'default':'漫画家'}),
            '人物1_外見':('STRING',{'multiline':True,'default':core.DEFAULT_CAST['漫画家'],'tooltip':'外見を英語で入力します。翻訳せず、そのまま描写指定へ渡します。'}),
            '人物2_名前':('STRING',{'default':'編集者'}),
            '人物2_外見':('STRING',{'multiline':True,'default':core.DEFAULT_CAST['編集者'],'tooltip':'外見を英語で入力します。翻訳せず、そのまま描写指定へ渡します。'})},
            'optional':{'人物3_名前':('STRING',{'default':'','tooltip':'3人目を使うときだけ名前と外見を両方入力します。'}),
            '人物3_外見':('STRING',{'multiline':True,'default':'','tooltip':'3人目の外見を英語で入力します。空欄なら従来の2人設定です。'})}}
    RETURN_TYPES=('MOSS_MANGA_CAST',)
    RETURN_NAMES=('共通の人物設定',)
    FUNCTION='build'
    CATEGORY='漫画／コマ割りデータセット'
    def build(self,**kw):
        cast={s:{'name':kw[s+'_名前'].strip(),'appearance':kw[s+'_外見'].strip()} for s in SLOTS[:2]}
        third={'name':kw.get('人物3_名前','').strip(),'appearance':kw.get('人物3_外見','').strip()}
        if third['name'] or third['appearance']:
            cast['人物3']=third
        if any(not p['name'] or not p['appearance'] for p in cast.values()):
            raise ValueError('人物の名前と外見を入力してください。')
        if len({person['name'] for person in cast.values()})!=len(cast):
            raise ValueError('人物の名前は別々にしてください。')
        return (cast,)

class MossMangaPanel:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{
            '場面':('STRING',{'multiline':True,'default':SCENES[0],'tooltip':'場面を英語で入力します。翻訳せず、そのまま描写指定へ渡します。'}),
            '登場人物':(list(ACTORS),),
            '話者1':(['セリフなし']+SLOTS,),
            'セリフ1':('STRING',{'multiline':True,'default':'','tooltip':'描きたい言語で本文だけ入力。日本語・英語とも翻訳せず、原文のまま渡します。'}),
            '話者2':(['セリフなし']+SLOTS,),
            'セリフ2':('STRING',{'multiline':True,'default':'','tooltip':'描きたい言語で本文だけ入力。翻訳は行いません。'})},
            'optional':{'構図':('MOSS_COMPOSITION',),
                '話者3':(['セリフなし']+SLOTS,{'default':'セリフなし'}),
                'セリフ3':('STRING',{'multiline':True,'default':'','tooltip':'3つ目の発言。原文のままMOSSへ渡します。'})}}
    RETURN_TYPES=('MOSS_MANGA_PANEL',)
    RETURN_NAMES=('このコマの内容',)
    FUNCTION='build'
    CATEGORY='漫画／コマ割りデータセット'
    def build(self,**kw):
        scene=kw['場面'].strip()
        if not scene:
            raise ValueError('場面を入力してください。')
        actors=ACTORS[kw['登場人物']]
        lines=[]
        for i in (1,2,3):
            speaker,text=kw.get(f'話者{i}','セリフなし'),kw.get(f'セリフ{i}','')
            if speaker=='セリフなし':
                if text.strip():
                    raise ValueError(f'セリフ{i}の話者を選んでください。入力した本文は黙って捨てません。')
                continue
            if speaker not in actors:
                raise ValueError(f'話者{i}を登場人物にも含めてください。')
            if not text.strip():
                raise ValueError(f'セリフ{i}の本文を入力するか「セリフなし」を選んでください。')
            lines.append({'slot':speaker,'text':text})
        panel={'scene':scene,'actors':list(actors),'dialogue':lines}
        if kw.get('構図') is not None:
            template=kw['構図']
            boxes=template.get('boxes')
            if not isinstance(template.get('prompt'),str) or not template['prompt'].strip() or not isinstance(boxes,list):
                raise ValueError('構図データが不正です。構図選択ノードを接続してください。')
            if len(actors)!=len(boxes):
                raise ValueError('構図見本と登場人物の人数を合わせてください。')
            panel['scene']=scene+' Composition: '+template['prompt']
            panel['composition_boxes']=template['boxes']
        return (panel,)

class MossPanelDatasetFlexible:
    @classmethod
    def INPUT_TYPES(cls):
        required={'コマ割り':([name for _,name in core.list_layouts()],),'生成内容':(['漫画','空のコマ枠'],),'人物設定':('MOSS_MANGA_CAST',)}
        required.update({f'コマ{i}':('MOSS_MANGA_PANEL',) for i in (1,2)})
        return {'required':required,'optional':{f'コマ{i}':('MOSS_MANGA_PANEL',) for i in (3,4,5,6)}}
    RETURN_TYPES=('STRING','INT','INT')
    RETURN_NAMES=('MOSS用プロンプト','幅','高さ')
    FUNCTION='build'
    CATEGORY='漫画／コマ割りデータセット'
    @classmethod
    def IS_CHANGED(cls,**kw):
        return core.CATALOG.stat().st_mtime_ns

    def build(self,**kw):
        layout=core.load_layout(kw['コマ割り'])
        if kw['生成内容']=='空のコマ枠':
            prompt=core.compile_prompt(layout,'空のコマ枠')
        else:
            count=len(layout['panels'])
            expected={f'コマ{i}' for i in range(1,count+1)}
            supplied={f'コマ{i}' for i in range(1,7) if kw.get(f'コマ{i}') is not None}
            if supplied!=expected:
                raise ValueError(f'選んだ配置には{count}コマ分の内容を接続してください。余った接続も外してください。')
            cast=kw['人物設定']
            panels=[]
            for i in range(1,count+1):
                p=kw[f'コマ{i}']
                if any(slot not in cast for slot in p['actors']):
                    raise ValueError(f'{i}コマ目で使う人物を共通の人物設定に登録してください。人物3は名前と外見を両方入力します。')
                panels.append({'scene':p['scene'],'actors':[cast[s]['name'] for s in p['actors']],
                    'dialogue':[{'speaker':cast[line['slot']]['name'],'text':line['text']} for line in p['dialogue']]})
                if 'composition_boxes' in p:
                    panels[-1]['composition_boxes']=p['composition_boxes']
            prompt=core.compile_prompt(layout,'漫画',{p['name']:p['appearance'] for p in cast.values()},panels)
        return prompt,layout['width'],layout['height']

class MossPromptEditor:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{
            'プロンプト':('STRING',{'forceInput':True}),
            '使うプロンプト':(['受け取ったまま','編集した文'],{'tooltip':'「編集した文」にすると、下の編集欄の内容をMOSSへ渡します。'}),
            '編集用プロンプト':('STRING',{'multiline':True,'default':'','tooltip':'空欄なら実行後に受け取ったプロンプトが入ります。JSONとして読める形で編集してください。'})}}
    RETURN_TYPES=('STRING',)
    RETURN_NAMES=('MOSS用プロンプト',)
    FUNCTION='build'
    CATEGORY='漫画／コマ割りデータセット'
    def build(self,**kw):
        received=kw['プロンプト']
        if kw['使うプロンプト']=='受け取ったまま':
            prompt=received
        else:
            edited=kw['編集用プロンプト']
            if not edited.strip():
                raise ValueError('編集用プロンプトが空です。一度「受け取ったまま」で実行すると受け取った内容が入ります。')
            try:
                prompt=core.dumps(json.loads(edited))
            except json.JSONDecodeError as error:
                raise ValueError(f'編集用プロンプトをJSONとして読めません（{error.lineno}行目{error.colno}文字目）。括弧・カンマ・引用符を確認してください。') from error
        return {'ui':{'text':[received]},'result':(prompt,)}

class MossCompositionTemplate:
    @classmethod
    def INPUT_TYPES(cls):
        names=[item['name'] for item in composition.catalog()]
        return {'required':{'構図テンプレート':(names or ['生成済みの構図がありません'],)}}
    RETURN_TYPES=('MOSS_COMPOSITION','STRING')
    RETURN_NAMES=('コマに接続する構図','構図の英語プロンプト')
    FUNCTION='build'
    CATEGORY='漫画／コマ割りデータセット'
    @classmethod
    def IS_CHANGED(cls,**kw):
        return composition.CATALOG.stat().st_mtime_ns if composition.CATALOG.exists() else 0
    def build(self,**kw):
        item=composition.load(kw['構図テンプレート'])
        return item,item['prompt']

NODE_CLASS_MAPPINGS={'MossCompositionTemplate':MossCompositionTemplate,'MossPanelDatasetFlexible':MossPanelDatasetFlexible,'MossMangaCharacters':MossMangaCharacters,'MossMangaPanel':MossMangaPanel,'MossPromptEditor':MossPromptEditor}
NODE_DISPLAY_NAME_MAPPINGS={'MossPanelDatasetFlexible':'コマ割りを選ぶ（2〜6コマ）','MossMangaCharacters':'共通の人物設定（普通の文章で入力）','MossMangaPanel':'コマの内容（場面・登場人物・セリフ）','MossPromptEditor':'MOSSプロンプトを確認・編集'}
NODE_DISPLAY_NAME_MAPPINGS['MossCompositionTemplate']='構図を選ぶ（見本画像）'
