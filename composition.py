"""構図JSONと任意のコマ比率に共通の構図指定。画像補正は行わない。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / 'data' / 'compositions.json'
CATEGORIES = ['1人の会話', '2人の会話', '3人の会話', '肩越し', '顔アップ', '全身', '俯瞰', 'あおり']

def records():
    if not CATALOG.exists():
        return []
    document=json.loads(CATALOG.read_text(encoding='utf-8'))
    if document.get('schema_version')!=1:
        raise ValueError('対応していない構図データ形式です。')
    return sorted(document['compositions'],key=lambda item:item['id'])

def catalog():
    return [dict(id=r['id'],name=r['name'],category=r['category'],prompt=r['prompt'],boxes=r['boxes'],review=r['review'],preview=f"/moss_panel_dataset/composition/preview/{r['id']}") for r in records()]

def load(identifier):
    for item in catalog():
        if identifier in (item['id'], item['name']):
            return item
    raise ValueError('生成済みの構図を選んでください。')

def preview_path(ident):
    if not re.fullmatch(r'[a-z0-9_]{1,80}', ident):
        raise ValueError('構図IDが不正です。')
    record=next((item for item in records() if item['id']==ident),None)
    if not record or not record['image_path']:
        raise FileNotFoundError('構図見本がありません。')
    path = (ROOT / record['image_path']).resolve()
    if not path.is_relative_to((ROOT / 'images' / 'compositions').resolve()) or path.suffix != '.webp' or not path.is_file():
        raise FileNotFoundError('構図見本がありません。')
    return path

def register_routes(routes):
    from aiohttp import web
    @routes.get('/moss_panel_dataset/composition/catalog')
    async def listing(request):
        return web.json_response({'compositions':catalog(), 'categories':CATEGORIES})
    @routes.get('/moss_panel_dataset/composition/preview/{ident}')
    async def preview(request):
        try:
            path = preview_path(request.match_info['ident'])
        except (ValueError, FileNotFoundError):
            raise web.HTTPNotFound()
        return web.FileResponse(path, headers={'Cache-Control':'no-cache', 'Content-Type':'image/webp'})
