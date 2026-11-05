"""MOSSのQwenを共有して参照画像から外見文を抽出する。画像の生成・補修はしない。"""
from .i18n import APPEARANCE_MODES, CATEGORY, LABELS, both, canonical, labeled, options, outputs

MODES=[ja for ja,_ in APPEARANCE_MODES]
ASK=(
    'Describe only the visible fixed visual appearance of the main character in this image so the '
    'same character can be redrawn in other manga panels. Start with the apparent sex. '
    'Then describe face shape, build, distinctive facial '
    'features such as moles or freckles, eye shape and size, hair length, color or grayscale shade, '
    'hairstyle, bangs, braids, animal ears if present, headwear, accessories, and clothing including '
    'collar, sleeves and decorations. '
    'Do not describe pose, expression, gaze, camera angle, framing, lighting, background or art style. '
    'Do not state an age or age group. Do not invent hidden details, names, personality or backstory. '
    'If multiple characters are visible, describe only the largest foreground character. '
    'Return only one concise English paragraph of visual appearance, without an introduction, '
    'analysis, headings, bullet points or JSON.'
)

AGE_GROUPS=('child','young teenager','older teenager','young adult','adult in their thirties','middle-aged','elderly')
AGE_ASK=(
    'How old does the main character in this image look? Manga often draws every age with smooth skin and '
    'large eyes, so judge from face fullness, cheek and smile lines, lines at the eye corners, head-to-body '
    'proportion, build, hairstyle, clothing and occupation cues. Answer with exactly one of: '+', '.join(AGE_GROUPS)+'.'
)

def age_group(raw):
    text=answer_only(raw).lower()
    found=[g for g in AGE_GROUPS if g in text]
    # 「young adult」と「adult in their thirties」のように重なる語は、長い方を優先する。
    return max(found,key=len) if found else None

def prepare_image(image):
    if getattr(image,'ndim',None)!=4 or image.shape[0]!=1 or image.shape[-1]!=3:
        raise ValueError(both('「参考画像」には1枚のRGB画像を接続してください。画像バッチや透過画像には対応していません。','Connect a single RGB image to "Reference image". Image batches and images with alpha are not supported.'))
    height,width=image.shape[1:3]
    if min(height,width)<1:
        raise ValueError(both('参考画像の寸法が不正です。','The reference image has an invalid size.'))
    if max(height,width)<=768:
        return image
    import torch.nn.functional as F
    ratio=768/max(height,width)
    size=(max(1,round(height*ratio)),max(1,round(width*ratio)))
    return F.interpolate(image.movedim(-1,1),size=size,mode='area').movedim(1,-1)

def answer_only(raw):
    if not isinstance(raw,str):
        raise ValueError(both('Qwenの出力を文章として読めません。','The Qwen output could not be read as text.'))
    if '</think>' in raw:
        raw=raw.partition('</think>')[2]
    elif raw.lstrip().startswith('<think>'):
        raise ValueError(both('外見の抽出が推論途中で終わりました。「最大トークン数」を増やしてください。','Appearance extraction stopped while still reasoning. Increase "Max tokens".'))
    result=raw.strip()
    if not result:
        raise ValueError(both('外見の抽出結果が空です。画像とQwenの接続を確認してください。','The extracted appearance is empty. Check the image and Qwen connections.'))
    return result

class MossCharacterAppearance:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':labeled('MossCharacterAppearance',{
            '指定方法':(options(APPEARANCE_MODES),{'default':'文章のみ'}),
            '外見プロンプト':('STRING',{'multiline':True,'default':''}),
            '最大トークン数':('INT',{'default':256,'min':64,'max':1024,'step':32})}),
            'optional':labeled('MossCharacterAppearance',{'Qwen':('CLIP',{'lazy':True}),
                '参考画像':('IMAGE',{'lazy':True})})}
    RETURN_TYPES=('STRING',)
    RETURN_NAMES=outputs('MossCharacterAppearance',1)
    DESCRIPTION=LABELS['MossCharacterAppearance']['description']
    FUNCTION='build'
    CATEGORY=CATEGORY

    def check_lazy_status(self,指定方法,**kwargs):
        if 指定方法 in ('文章のみ','Text only'):
            return []
        return [name for name in ('Qwen','参考画像') if name in kwargs and kwargs[name] is None]

    def build(self,指定方法,外見プロンプト='',最大トークン数=256,Qwen=None,参考画像=None):
        指定方法=canonical(APPEARANCE_MODES,指定方法,'指定方法','Method')
        if 指定方法=='文章のみ':
            if not 外見プロンプト.strip():
                raise ValueError(both('「指定方法」が「文章のみ」なのに「外見プロンプト」が空です。外見を英語で入力するか、画像から抽出する方法を選んでください。',
                    '"Method" is "Text only" but "Appearance prompt" is empty. Describe the appearance in English, or choose a method that extracts it from an image.'))
            result=外見プロンプト
        else:
            if 参考画像 is None:
                raise ValueError(both('「指定方法」が画像から抽出する方法なのに「参考画像」が接続されていません。「画像を読み込む」ノードを接続してください。','"Method" extracts from an image, but "Reference image" is not connected. Connect a "Load Image" node.'))
            if Qwen is None or any(not callable(getattr(Qwen,name,None)) for name in ('tokenize','generate','decode')):
                raise ValueError(both('画像から抽出するには「Qwen」へMOSS用のCLIPLoaderを接続してください。CLIPLoaderの種類（type）はmoss_imageです。','To extract from an image, connect the MOSS CLIPLoader to "Qwen". Set the CLIPLoader type to moss_image.'))
            image=prepare_image(参考画像)
            tokens=Qwen.tokenize(ASK,image=image,thinking=False,min_length=1)
            ids=Qwen.generate(tokens,do_sample=False,max_length=最大トークン数,mtp=False)
            extracted=answer_only(Qwen.decode(ids))
            tokens=Qwen.tokenize(AGE_ASK,image=image,thinking=False,min_length=1)
            group=age_group(Qwen.decode(Qwen.generate(tokens,do_sample=False,max_length=24,mtp=False)))
            result=(f'Apparent age group: {group}. ' if group else '')+extracted
            if 指定方法=='画像から抽出＋文章で補足' and 外見プロンプト.strip():
                result+='\nAdditional appearance details: '+外見プロンプト.strip()
        return {'ui':{'text':[result]},'result':(result,)}
