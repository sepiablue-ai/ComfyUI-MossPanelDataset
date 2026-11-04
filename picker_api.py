"""同梱JSONを読み取り、見本のWebPをComfyUIへ配信する。"""
import re
from pathlib import Path
from . import dataset as core

ROOT = Path(__file__).resolve().parent
def catalog_items():
    items = []
    for record in core.load_catalog():
        ident,name,layout=record['id'],record['name'],record['specification']
        category = {'斜め線': '斜め', '特殊配置': '特殊'}.get(layout.get('category'), layout.get('category', '直線'))
        items.append({
            'id': ident, 'name': name, 'count': len(layout['panels']), 'category': category,
            'positions': [p.get('display_position', f'{i}コマ目') for i, p in enumerate(layout['panels'], 1)],
            'preview': f'/moss_panel_dataset/preview/{ident}', 'status': 'complete',
            'quality': 'distinct_candidate',
            'priority': {'通常': 0, '直線': 1, '斜め': 2, '特殊': 3}.get(category, 4),
        })
    return sorted(items, key=lambda item: (item['priority'], item['count'], item['name']))


def preview_path(ident):
    if not re.fullmatch(r'[A-Za-z0-9_]{1,100}', ident):
        raise ValueError('配置IDが不正です。')
    record=next((item for item in core.load_catalog() if item['id']==ident),None)
    if not record:
        raise FileNotFoundError('見本画像がありません。')
    path = (ROOT / record['preview']['image_path']).resolve()
    if not path.is_relative_to((ROOT / 'images').resolve()) or path.suffix.lower() != '.webp':
        raise ValueError('見本画像フォルダの外は参照できません。')
    if not path.is_file():
        raise FileNotFoundError('見本画像が見つかりません。')
    return path


def register_routes(routes):
    from aiohttp import web

    @routes.get('/moss_panel_dataset/catalog')
    async def catalog(request):
        return web.json_response({'layouts': catalog_items()})

    @routes.get('/moss_panel_dataset/preview/{ident}')
    async def preview(request):
        try:
            path = preview_path(request.match_info['ident'])
        except (ValueError, FileNotFoundError):
            raise web.HTTPNotFound()
        return web.FileResponse(path, headers={'Cache-Control': 'no-cache', 'Content-Type': 'image/webp'})
