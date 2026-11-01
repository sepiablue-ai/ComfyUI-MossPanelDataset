"""同梱DBを読み取り専用で使い、見本のWebPをComfyUIへ配信する。"""
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data' / 'layouts.sqlite3'


def connect():
    return sqlite3.connect(f'{DB.as_uri()}?mode=ro', uri=True)


def catalog_items():
    with closing(connect()) as conn:
        rows = conn.execute('SELECT l.id,l.name,l.specification FROM layouts l JOIN previews p ON p.layout_id=l.id').fetchall()
    items = []
    for ident, name, spec in rows:
        layout = json.loads(spec)
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
    with closing(connect()) as conn:
        row = conn.execute('SELECT image_path FROM previews WHERE layout_id=?', (ident,)).fetchone()
    if not row:
        raise FileNotFoundError('見本画像がありません。')
    path = (ROOT / row[0]).resolve()
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
