"""MOSSのQwenを共有して参照画像から外見文を抽出する。画像の生成・補修はしない。"""

MODES=['文章のみ','画像から抽出','画像から抽出＋文章で補足']
ASK=(
    'Describe only the visible fixed visual appearance of the main character in this image so the '
    'same character can be redrawn in other manga panels. Describe hair length, color or grayscale '
    'shade, hairstyle, bangs, braids, visible eye features, animal ears if present, headwear, '
    'accessories, and clothing including collar, sleeves and decorations. '
    'Do not describe pose, expression, gaze, camera angle, framing, lighting, background or art style. '
    'Do not invent hidden details, names, exact ages, personality or backstory. '
    'If multiple characters are visible, describe only the largest foreground character. '
    'Return only one concise English paragraph of visual appearance, without an introduction, '
    'analysis, headings, bullet points or JSON.'
)

def prepare_image(image):
    if getattr(image,'ndim',None)!=4 or image.shape[0]!=1 or image.shape[-1]!=3:
        raise ValueError('参考画像は1枚のRGB画像を接続してください。画像バッチには対応していません。')
    height,width=image.shape[1:3]
    if min(height,width)<1:
        raise ValueError('参考画像の寸法が不正です。')
    if max(height,width)<=768:
        return image
    import torch.nn.functional as F
    ratio=768/max(height,width)
    size=(max(1,round(height*ratio)),max(1,round(width*ratio)))
    return F.interpolate(image.movedim(-1,1),size=size,mode='area').movedim(1,-1)

def answer_only(raw):
    if not isinstance(raw,str):
        raise ValueError('Qwenの出力を文章として読めません。')
    if '</think>' in raw:
        raw=raw.partition('</think>')[2]
    elif raw.lstrip().startswith('<think>'):
        raise ValueError('外見の抽出が推論途中で終わりました。最大トークン数を増やしてください。')
    result=raw.strip()
    if not result:
        raise ValueError('外見の抽出結果が空です。画像とQwenの接続を確認してください。')
    return result

class MossCharacterAppearance:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{
            '指定方法':(MODES,{'default':'文章のみ'}),
            '外見プロンプト':('STRING',{'multiline':True,'default':'','tooltip':'文章のみでは外見を英語で入力します。画像＋文章では髪色・服装などの補足を入力できます。ポーズや背景はコマの場面欄へ入力してください。'}),
            '最大トークン数':('INT',{'default':256,'min':64,'max':1024,'step':32})},
            'optional':{'Qwen':('CLIP',{'lazy':True,'tooltip':'MOSS生成でも使うCLIPLoader（type=moss_image）の出力を共有できます。文章のみでは評価しません。'}),
                '参考画像':('IMAGE',{'lazy':True,'tooltip':'画像を読み込むノードから人物が分かる画像1枚を接続。必要な場合だけ、長辺768pxまで比率を保って縮小して解析します。'})}}
    RETURN_TYPES=('STRING',)
    RETURN_NAMES=('人物設定に渡す外見',)
    FUNCTION='build'
    CATEGORY='漫画／コマ割りデータセット'

    def check_lazy_status(self,指定方法,**kwargs):
        if 指定方法=='文章のみ':
            return []
        return [name for name in ('Qwen','参考画像') if name in kwargs and kwargs[name] is None]

    def build(self,指定方法,外見プロンプト='',最大トークン数=256,Qwen=None,参考画像=None):
        if 指定方法 not in MODES:
            raise ValueError('外見の指定方法が不正です。')
        if 指定方法=='文章のみ':
            if not 外見プロンプト.strip():
                raise ValueError('外見プロンプトを入力するか、画像から抽出する方法を選んでください。')
            result=外見プロンプト
        else:
            if 参考画像 is None:
                raise ValueError('参考画像を接続してください。')
            if Qwen is None or any(not callable(getattr(Qwen,name,None)) for name in ('tokenize','generate','decode')):
                raise ValueError('MOSS用のQwenを接続してください。CLIPLoaderの種類はmoss_imageです。')
            image=prepare_image(参考画像)
            tokens=Qwen.tokenize(ASK,image=image,thinking=False,min_length=1)
            ids=Qwen.generate(tokens,do_sample=False,max_length=最大トークン数,mtp=False)
            extracted=answer_only(Qwen.decode(ids))
            result=extracted
            if 指定方法=='画像から抽出＋文章で補足' and 外見プロンプト.strip():
                result+='\nAdditional appearance details: '+外見プロンプト.strip()
        return {'ui':{'text':[result]},'result':(result,)}
