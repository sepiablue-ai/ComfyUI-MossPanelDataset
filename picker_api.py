"""同梱JSONを読み取り、見本のWebPをComfyUIへ配信する。"""
import json
import re
from pathlib import Path
from . import dataset as core

ROOT = Path(__file__).resolve().parent
CATEGORY_EN = {'通常': 'Standard', '直線': 'Straight', '斜め': 'Diagonal', '特殊': 'Special'}


def position_en(text, index):
    m = re.fullmatch(r'(\d+)(コマ目|番目の領域)', text)
    if not m:
        return f'Panel {index}'
    return f'Panel {m[1]}' if m[2] == 'コマ目' else f'Region {m[1]}'


def catalog_items():
    items = []
    for record in core.load_catalog():
        ident,name,layout=record['id'],record['name'],record['specification']
        category = {'斜め線': '斜め', '特殊配置': '特殊'}.get(layout.get('category'), layout.get('category', '直線'))
        items.append({
            'id': ident, 'name': name, 'name_en': record.get('name_en', name), 'count': len(layout['panels']), 'category': category,
            'category_en': CATEGORY_EN.get(category, category),
            'positions': [p.get('display_position', f'{i}コマ目') for i, p in enumerate(layout['panels'], 1)],
            'positions_en': [position_en(p.get('display_position', f'{i}コマ目'), i) for i, p in enumerate(layout['panels'], 1)],
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


def client_table():
    """画面側で選択肢とノード名を表示言語へそろえるための日本語・英語の組。"""
    from . import composition
    from . import i18n
    ja = json.loads((ROOT / 'locales' / 'ja' / 'nodeDefs.json').read_text(encoding='utf-8'))
    en = i18n.LABELS
    speakers = {f'話者{i}': i18n.SPEAKERS for i in (1, 2, 3)}
    combos = {
        'MossPanelDatasetFlexible': {'コマ割り': [[r['name'], r.get('name_en', r['name'])] for r in core.load_catalog()],
                                     '生成内容': i18n.OUTPUTS},
        'MossMangaCharacters': {'人物1_名前': i18n.DEFAULT_NAMES, '人物2_名前': i18n.DEFAULT_NAMES},
        'MossMangaPanel': {'登場人物': i18n.ACTORS, **speakers},
        'MossPromptEditor': {'使うプロンプト': i18n.EDITOR_MODES},
        'MossCompositionTemplate': {'構図テンプレート': [[c['name'], c['name_en']] for c in composition.catalog()]},
        'MossCharacterAppearance': {'指定方法': i18n.APPEARANCE_MODES},
    }
    legacy = {'MossPanelDatasetFlexible': ['画像からコマ割りを選ぶ（2〜6コマ）']}
    return {'nodes': {name: {'display': [ja[name]['display_name'], en[name]['display_name']],
                             'legacy_titles': legacy.get(name, []),
                             'combos': {k: [list(p) for p in v] for k, v in combos[name].items()}}
                      for name in en}}


def register_routes(routes):
    from aiohttp import web

    @routes.get('/moss_panel_dataset/i18n')
    async def translations(request):
        return web.json_response(client_table())

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
