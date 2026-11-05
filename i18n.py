"""日本語・英語の選択肢とエラーメッセージ。

内部では従来の日本語の値を正とし、英語の値は同じ意味の別名として受け付ける。
保存済みワークフローやAPI形式の入力は、どちらの言語の値でもそのまま動く。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# 英語の表示名・説明は locales/en/nodeDefs.json を正とする。日本語は locales/ja/nodeDefs.json でComfyUIが切り替える。
LABELS = json.loads((ROOT / 'locales' / 'en' / 'nodeDefs.json').read_text(encoding='utf-8'))
CATEGORY = 'Manga panel dataset'


def labeled(node, fields):
    """入力へ英語の表示名と説明を付ける。内部名（日本語）は保存済みワークフローとの互換のため変えない。"""
    inputs = LABELS[node].get('inputs', {})
    result = {}
    for name, spec in fields.items():
        extra = dict(spec[1]) if len(spec) > 1 else {}
        label = inputs.get(name, {})
        if 'name' in label:
            extra['display_name'] = label['name']
        if 'tooltip' in label:
            extra['tooltip'] = label['tooltip']
        result[name] = (spec[0], extra) if extra else (spec[0],)
    return result


def outputs(node, count):
    return tuple(LABELS[node]['outputs'][str(i)]['name'] for i in range(count))


# (日本語, 英語) の組。並び順が画面の選択肢の順になる。
ACTORS = [
    ('人物1のみ', 'Character 1 only'), ('人物2のみ', 'Character 2 only'),
    ('人物1と人物2', 'Characters 1 and 2'), ('人物なし', 'No characters'),
    ('人物3のみ', 'Character 3 only'), ('人物1と人物3', 'Characters 1 and 3'),
    ('人物2と人物3', 'Characters 2 and 3'), ('人物1と人物2と人物3', 'Characters 1, 2, and 3'),
]
SPEAKERS = [('セリフなし', 'No dialogue'), ('人物1', 'Character 1'), ('人物2', 'Character 2'), ('人物3', 'Character 3')]
OUTPUTS = [('漫画', 'Manga'), ('空のコマ枠', 'Empty panel frames')]
EDITOR_MODES = [('受け取ったまま', 'As received'), ('編集した文', 'Edited text')]
APPEARANCE_MODES = [
    ('文章のみ', 'Text only'), ('画像から抽出', 'Extract from image'),
    ('画像から抽出＋文章で補足', 'Extract from image + text'),
]
DEFAULT_NAMES = [('漫画家', 'Manga artist'), ('編集者', 'Editor')]
SLOT_EN = dict(SPEAKERS)


def options(pairs):
    """日本語の値の後に英語の値を並べた、ComfyUIの検証に通る選択肢。"""
    return [ja for ja, _ in pairs] + [en for _, en in pairs if en not in {ja for ja, _ in pairs}]


def canonical(pairs, value, label_ja, label_en):
    """英語の値を日本語の値へそろえる。どちらでもなければ分かるように止める。"""
    for ja, en in pairs:
        if value in (ja, en):
            return ja
    choices = ' / '.join(f'{ja}（{en}）' for ja, en in pairs)
    raise ValueError(both(f'「{label_ja}」の値「{value}」は選べません。次から選んでください: {choices}',
                          f'"{value}" is not a valid value for "{label_en}". Choose one of: {choices}'))


def both(ja, en):
    """利用者の表示言語はPython側で分からないため、日本語と英語を併記する。"""
    return f'{ja}\n{en}'


def slot_label(slot):
    return f'{slot}（{SLOT_EN.get(slot, slot)}）'


def actors_label(value):
    return f'{value}（{dict(ACTORS).get(value, value)}）'
