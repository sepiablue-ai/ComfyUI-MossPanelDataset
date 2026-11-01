"""専用欄の入力をMOSSプロンプトへ渡すComfyUIノード。"""
from . import dataset as core

SLOTS=['人物1','人物2']
ACTORS={'人物1のみ':['人物1'],'人物2のみ':['人物2'],'人物1と人物2':['人物1','人物2'],'人物なし':[]}
SCENES=['Drawing a manga manuscript with a pen at a desk. Medium shot of the studio.','Standing at the open studio door holding a folder.','Looking away nervously, holding a pen above a blank manuscript. Close-up.','Facing each other across a desk with blank manuscript sheets. Medium two-shot.']

class MossMangaCharacters:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{
            '人物1_名前':('STRING',{'default':'漫画家'}),
            '人物1_外見':('STRING',{'multiline':True,'default':core.DEFAULT_CAST['漫画家'],'tooltip':'外見を英語で入力します。翻訳せず、そのまま描写指定へ渡します。'}),
            '人物2_名前':('STRING',{'default':'編集者'}),
            '人物2_外見':('STRING',{'multiline':True,'default':core.DEFAULT_CAST['編集者'],'tooltip':'外見を英語で入力します。翻訳せず、そのまま描写指定へ渡します。'})}}
    RETURN_TYPES=('MOSS_MANGA_CAST',)
    RETURN_NAMES=('共通の人物設定',)
    FUNCTION='build'
    CATEGORY='漫画／コマ割りデータセット'
    def build(self,**kw):
        cast={s:{'name':kw[s+'_名前'].strip(),'appearance':kw[s+'_外見'].strip()} for s in SLOTS}
        if any(not p['name'] or not p['appearance'] for p in cast.values()):
            raise ValueError('人物の名前と外見を入力してください。')
        if cast['人物1']['name']==cast['人物2']['name']:
            raise ValueError('二人の名前は別々にしてください。')
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
            'セリフ2':('STRING',{'multiline':True,'default':'','tooltip':'描きたい言語で本文だけ入力。翻訳は行いません。'})}}
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
        for i in (1,2):
            speaker,text=kw[f'話者{i}'],kw[f'セリフ{i}']
            if speaker=='セリフなし':
                if text.strip():
                    raise ValueError(f'セリフ{i}の話者を選んでください。入力した本文は黙って捨てません。')
                continue
            if speaker not in actors:
                raise ValueError(f'話者{i}を登場人物にも含めてください。')
            if not text.strip():
                raise ValueError(f'セリフ{i}の本文を入力するか「セリフなし」を選んでください。')
            lines.append({'slot':speaker,'text':text})
        return ({'scene':scene,'actors':list(actors),'dialogue':lines},)

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
        return core.DB.stat().st_mtime_ns

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
                panels.append({'scene':p['scene'],'actors':[cast[s]['name'] for s in p['actors']],
                    'dialogue':[{'speaker':cast[line['slot']]['name'],'text':line['text']} for line in p['dialogue']]})
            prompt=core.compile_prompt(layout,'漫画',{p['name']:p['appearance'] for p in cast.values()},panels)
        return prompt,layout['width'],layout['height']

NODE_CLASS_MAPPINGS={'MossPanelDatasetFlexible':MossPanelDatasetFlexible,'MossMangaCharacters':MossMangaCharacters,'MossMangaPanel':MossMangaPanel}
NODE_DISPLAY_NAME_MAPPINGS={'MossPanelDatasetFlexible':'コマ割りを選ぶ（2〜6コマ）','MossMangaCharacters':'共通の人物設定（普通の文章で入力）','MossMangaPanel':'コマの内容（場面・登場人物・セリフ）'}
