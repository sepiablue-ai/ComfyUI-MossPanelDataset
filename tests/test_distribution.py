"""別フォルダへの導入、同梱画像、入力契約、実HTTPをCPUだけで検査する。"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import types
import unittest
from contextlib import closing
from unittest.mock import patch

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

SOURCE = Path(__file__).resolve().parents[1]


def import_package(root, name):
    spec = importlib.util.spec_from_file_location(name, root / '__init__.py', submodule_search_locations=[str(root)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Distribution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_parent = Path(os.environ.get('MOSS_TEST_TMPDIR', tempfile.gettempdir())).resolve()
        cls.temp = tempfile.TemporaryDirectory(prefix='moss_panel_', dir=cls.temp_parent)
        cls.root = Path(cls.temp.name) / '独立した導入先 with spaces' / 'ComfyUI-MossPanelDataset'
        cls.root.mkdir(parents=True)
        for name in ('__init__.py', 'nodes.py', 'dataset.py', 'picker_api.py'):
            shutil.copyfile(SOURCE / name, cls.root / name)
        for name in ('data', 'images', 'web', 'example_workflows'):
            shutil.copytree(SOURCE / name, cls.root / name)
        cls.package = import_package(cls.root, '_moss_panel_distribution_test')
        cls.core = cls.package.nodes.core
        cls.api = importlib.import_module('_moss_panel_distribution_test.picker_api')

    @classmethod
    def tearDownClass(cls):
        for name in list(sys.modules):
            if name.startswith('_moss_panel_distribution_test'):
                del sys.modules[name]
        assert Path(cls.temp.name).resolve().parent == cls.temp_parent
        cls.temp.cleanup()

    def test_independent_import_and_clean_database(self):
        self.assertEqual(self.core.ROOT, self.root)
        self.assertEqual(self.api.ROOT, self.root)
        with closing(self.api.connect()) as conn:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertEqual(tables, {'layouts', 'previews'})
            self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM previews').fetchone()[0], 196)
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute('DELETE FROM layouts')

    def test_all_layouts_and_webp_hashes(self):
        counts = {n: 0 for n in range(2, 7)}
        normal_counts = counts.copy()
        before = hashlib.sha256(self.core.DB.read_bytes()).hexdigest()
        with closing(self.api.connect()) as conn:
            rows = conn.execute('SELECT l.id,l.name,l.specification,p.image_path,p.sha256 FROM layouts l JOIN previews p ON p.layout_id=l.id').fetchall()
        self.assertEqual(len(rows), 196)
        for ident, name, spec, path, sha in rows:
            with self.subTest(layout=ident):
                self.assertFalse(re.search(r'(?i)[a-z]:[\\/]|/Users/|/home/', spec + path))
                layout = self.core.load_layout(name)
                self.core.validate_layout(layout)
                n = len(layout['panels'])
                counts[n] += 1
                if ident.startswith('normal_'):
                    normal_counts[n] += 1
                raw = self.api.preview_path(ident).read_bytes()
                self.assertTrue(raw[:4] == b'RIFF' and raw[8:12] == b'WEBP')
                self.assertEqual(hashlib.sha256(raw).hexdigest(), sha)
                self.assertEqual(path, f'images/{ident}.webp')
                prompt = json.loads(self.core.compile_prompt(layout, '空のコマ枠'))
                self.assertEqual(len(prompt['items']), n)
                self.assertTrue(all(p['label'] == 'object' and 'text' not in p for p in prompt['items']))
        self.assertEqual(counts, {2: 38, 3: 39, 4: 40, 5: 40, 6: 39})
        self.assertEqual(normal_counts, {n: 20 for n in range(2, 7)})
        self.assertEqual(hashlib.sha256(self.core.DB.read_bytes()).hexdigest(), before)

    def test_every_layout_preserves_dialogue_through_nodes(self):
        nodes = self.package.nodes
        cast = nodes.MossMangaCharacters().build(**{
            '人物1_名前': '花子', '人物1_外見': 'An adult woman, black hair, white blouse.',
            '人物2_名前': '編集者', '人物2_外見': 'An adult man, glasses, black suit.',
        })[0]
        text = '  あと少し！\nAlmost done!「そのまま」  '
        panel = nodes.MossMangaPanel().build(**{
            '場面': 'Drawing a manuscript at a desk.', '登場人物': '人物1のみ',
            '話者1': '人物1', 'セリフ1': text, '話者2': 'セリフなし', 'セリフ2': '',
        })[0]
        for ident, name in self.core.list_layouts():
            with self.subTest(layout=ident):
                layout = self.core.load_layout(ident)
                count = len(layout['panels'])
                args = {'コマ割り': name, '生成内容': '漫画', '人物設定': cast}
                args.update({f'コマ{i}': panel for i in range(1, count + 1)})
                prompt, width, height = nodes.MossPanelDatasetFlexible().build(**args)
                result = json.loads(prompt)
                summary = result['summary']['caption']
                for forbidden in ('empty rectangular manga panels', 'closed empty frames', 'blank white interiors', 'people or text', 'never draw text or numbers'):
                    self.assertNotIn(forbidden, summary)
                self.assertEqual([p['text'] for p in result['items'] if p['label'] == 'text'], [text] * count)
                self.assertEqual((width, height), (1024, 1536))
                args[f'コマ{count}'] = None
                with self.assertRaises(ValueError):
                    nodes.MossPanelDatasetFlexible().build(**args)

    def test_paths_reject_unknown_ids_and_escape(self):
        for ident in ('../README', 'a.b', 'normal_2_01/extra', 'x' * 101):
            with self.assertRaises(ValueError):
                self.api.preview_path(ident)
        with self.assertRaises(FileNotFoundError):
            self.api.preview_path('not_registered')
        db = Path(self.temp.name) / 'path_test.sqlite3'
        shutil.copyfile(self.core.DB, db)
        with closing(sqlite3.connect(db)) as conn, conn:
            conn.execute('UPDATE previews SET image_path=? WHERE layout_id=?', ('../outside.webp', 'normal_2_01'))
        with patch.object(self.api, 'DB', db):
            with self.assertRaises(ValueError):
                self.api.preview_path('normal_2_01')

    def test_example_custom_nodes_and_connections(self):
        workflow = json.loads((self.root / 'example_workflows' / 'make_manga.json').read_text('utf-8'))
        nodes = {n['id']: n for n in workflow['nodes']}
        links = {link[0]: link for link in workflow['links']}
        for node in nodes.values():
            for slot, entry in enumerate(node['inputs']):
                if entry.get('link') is not None:
                    link = links[entry['link']]
                    self.assertEqual((link[3], link[4]), (node['id'], slot))
                    self.assertIn(link[1], nodes)
                    self.assertIn(link[0], nodes[link[1]]['outputs'][link[2]]['links'])
        output = {}
        for ident in (11, 12, 13, 14, 15, 1):
            node = nodes[ident]
            cls = self.package.NODE_CLASS_MAPPINGS[node['type']]
            fields = cls.INPUT_TYPES()
            args = {}
            widgets = iter(node['widgets_values'])
            inputs = {p['name']: p for p in node['inputs']}
            for name, definition in {**fields.get('required', {}), **fields.get('optional', {})}.items():
                if isinstance(definition[0], list) or definition[0] in ('STRING', 'INT', 'FLOAT', 'BOOLEAN'):
                    args[name] = next(widgets)
                elif inputs.get(name, {}).get('link') is not None:
                    link = links[inputs[name]['link']]
                    args[name] = output[link[1]][link[2]]
            output[ident] = cls().build(**args)
        self.assertEqual(output[1][1:], (1024, 1536))
        prompt = json.loads(output[1][0])
        self.assertEqual([p['text'] for p in prompt['items'] if p['label'] == 'text'], ['あと少し！', '原稿は？', 'できました！', 'お疲れさま！'])
        self.assertEqual(nodes[7]['widgets_values'][:2], [1024, 1536])
        self.assertEqual(nodes[2]['widgets_values'][1], 'moss_image')

    def test_comfy_entry_point_routes_and_duplicate_install(self):
        server = types.ModuleType('server')
        server.PromptServer = types.SimpleNamespace(instance=types.SimpleNamespace(routes=web.RouteTableDef()))
        with patch.dict(sys.modules, {'server': server}):
            module = import_package(self.root, '_moss_panel_distribution_test_entry')
            self.assertEqual(module.WEB_DIRECTORY, './web')
            self.assertEqual(len(server.PromptServer.instance.routes), 2)
            self.assertEqual(set(module.NODE_CLASS_MAPPINGS), {'MossPanelDatasetFlexible', 'MossMangaCharacters', 'MossMangaPanel'})
            with self.assertRaisesRegex(RuntimeError, '重複'):
                import_package(self.root, '_moss_panel_distribution_test_duplicate')


class Routes(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.package = import_package(SOURCE, '_moss_panel_distribution_test_http')
        self.api = importlib.import_module('_moss_panel_distribution_test_http.picker_api')
        routes = web.RouteTableDef()
        self.api.register_routes(routes)
        app = web.Application()
        app.add_routes(routes)
        self.client = TestClient(TestServer(app, host='127.0.0.1'))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        for name in list(sys.modules):
            if name.startswith('_moss_panel_distribution_test_http'):
                del sys.modules[name]

    async def test_catalog_image_and_not_found(self):
        response = await self.client.get('/moss_panel_dataset/catalog')
        self.assertEqual(response.status, 200)
        items = (await response.json())['layouts']
        self.assertEqual(len(items), 196)
        self.assertEqual(sum(p['category'] == '通常' for p in items), 100)
        item = items[0]
        response = await self.client.get(item['preview'])
        self.assertEqual(response.status, 200)
        self.assertEqual(response.content_type, 'image/webp')
        self.assertEqual(await response.read(), self.api.preview_path(item['id']).read_bytes())
        for ident in ('not_registered', 'bad.id'):
            response = await self.client.get(f'/moss_panel_dataset/preview/{ident}')
            self.assertEqual(response.status, 404)


if __name__ == '__main__':
    unittest.main()
