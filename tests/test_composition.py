import importlib.util
import json
from pathlib import Path
import sys
import unittest
import hashlib
from PIL import Image
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('_composition_test',ROOT/'__init__.py',submodule_search_locations=[str(ROOT)])
pkg=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pkg;spec.loader.exec_module(pkg)
nodes=pkg.nodes

class Composition(unittest.TestCase):
    def test_dataset_is_complete_and_unmodified(self):
        records=nodes.composition.records()
        self.assertEqual(len(records),120)
        self.assertEqual({n:sum(len(item['boxes'])==n for item in records) for n in (1,2,3)},{1:40,2:40,3:40})
        # 見本はMOSS出力PNG（source_png_sha256）を品質90のWebPへ変換したもの。生成条件はJSON側に収録する。
        self.assertEqual(len({item['source_png_sha256'] for item in records}),120)
        for item in records:
            with self.subTest(template=item['id']):
                file=ROOT/item['image_path']
                self.assertEqual(item['image_path'],f"images/compositions/{item['id']}.webp")
                self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),item['sha256'])
                with Image.open(file) as im:
                    self.assertEqual((im.format,im.size),('WEBP',(1024,1024)))
                self.assertIn(item['prompt'],item['generation_prompt'])
                self.assertIsInstance(item['conditions']['seed'],int)
                self.assertEqual(nodes.composition.preview_path(item['id']),file.resolve())
    def panel(self,template=None,reverse=False):
        kw={'場面':'A quiet conversation.','登場人物':'人物1と人物2','話者1':'人物2' if reverse else '人物1','セリフ1':'そのまま！','話者2':'人物1' if reverse else '人物2','セリフ2':'はい。'}
        if template is not None:kw['構図']=template
        return nodes.MossMangaPanel().build(**kw)[0]
    def test_optional_preserves_old_panel(self):
        p=self.panel()
        self.assertEqual(set(p),{'scene','actors','dialogue'})
        self.assertEqual(p['scene'],'A quiet conversation.')
    def test_template_boxes_are_not_swapped_by_speaking_order(self):
        t={'prompt':'Over the shoulder.','boxes':[[.60,.10,1.,1.],[.08,.20,.53,.90]]}
        a=self.panel(t);b=self.panel(t,True)
        self.assertEqual(a['composition_boxes'],b['composition_boxes'])
        self.assertIn(t['prompt'],b['scene'])
        cast=nodes.MossMangaCharacters().build(**{'人物1_名前':'花子','人物1_外見':'Black hair.','人物2_名前':'太郎','人物2_外見':'Glasses.'})[0]
        for layout_id in ('normal_2_01','normal_2_02','normal_2_03'):
            values={'コマ割り':layout_id,'生成内容':'漫画','人物設定':cast,'コマ1':a,'コマ2':b}
            data=json.loads(nodes.MossPanelDatasetFlexible().build(**values)[0])
            chars=[i for i in data['items'] if i['label']=='character']
            self.assertIn('Black hair.',chars[0]['caption']);self.assertIn('Glasses.',chars[1]['caption'])
            self.assertGreater(chars[0]['bbox'][1],chars[1]['bbox'][1])
            self.assertEqual([i['text'] for i in data['items'] if i['label']=='text'],['そのまま！','はい。']*2)
    def test_actor_mismatch_and_invalid_boxes(self):
        with self.assertRaises(ValueError):self.panel({'prompt':'Solo.','boxes':[[0,0,1,1]]})
        core=nodes.core;layout=core.load_layout('normal_2_01')
        p={'scene':'Conversation.','actors':list(core.DEFAULT_CAST),'dialogue':[],'composition_boxes':[[0,0,float('nan'),1],[0,0,1,1]]}
        with self.assertRaises(ValueError):core.compile_prompt(layout,'漫画',core.DEFAULT_CAST,[p,p])

class CompositionHTTP(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        routes=web.RouteTableDef();nodes.composition.register_routes(routes)
        app=web.Application();app.add_routes(routes);self.client=TestClient(TestServer(app));await self.client.start_server()
    async def asyncTearDown(self):await self.client.close()
    async def test_catalog_and_paths(self):
        r=await self.client.get('/moss_panel_dataset/composition/catalog');self.assertEqual(r.status,200)
        data=await r.json();self.assertIn('1人の会話',data['categories'])
        for item in data['compositions']:
            im=await self.client.get(item['preview']);self.assertEqual(im.status,200);body=await im.read();self.assertEqual(im.content_type,'image/webp');self.assertTrue(body[:4]==b'RIFF' and body[8:12]==b'WEBP')
        for ident in ('bad.id','missing','..%2f..%2fsecret'):
            self.assertEqual((await self.client.get('/moss_panel_dataset/composition/preview/'+ident)).status,404)

if __name__=='__main__':unittest.main()
