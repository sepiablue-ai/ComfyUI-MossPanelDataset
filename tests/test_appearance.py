import unittest
import torch
from test_composition import nodes
from importlib import import_module

appearance=import_module(nodes.__package__+'.appearance')

class FakeClip:
    def __init__(self,text='Long black hair, a white blouse, a ribbon headband.'):
        self.text=text;self.calls=[]
    def tokenize(self,text,**kw):self.calls.append(('tokenize',text,kw));return 'tokens'
    def generate(self,tokens,**kw):self.calls.append(('generate',tokens,kw));return 'ids'
    def decode(self,ids):return self.text

class Appearance(unittest.TestCase):
    def test_manual_does_not_use_connected_models(self):
        result=nodes.MossCharacterAppearance().build('文章のみ','  Short hair.\nBlue coat.  ',Qwen=object(),参考画像=object())
        self.assertEqual(result['result'],('  Short hair.\nBlue coat.  ',))
        self.assertEqual(nodes.MossCharacterAppearance().check_lazy_status('文章のみ',Qwen=None,参考画像=None),[])
    def test_lazy_requests_only_connected_pending_inputs(self):
        n=nodes.MossCharacterAppearance()
        self.assertEqual(n.check_lazy_status('画像から抽出'),[])
        self.assertEqual(n.check_lazy_status('画像から抽出',Qwen=None,参考画像=object()),['Qwen'])
    def test_image_and_hybrid_pass_the_actual_model_answer(self):
        clip=FakeClip();image=torch.zeros(1,40,60,3)
        n=nodes.MossCharacterAppearance()
        out=n.build('画像から抽出',外見プロンプト='ignored',Qwen=clip,参考画像=image)
        self.assertEqual(out['result'],(clip.text,))
        self.assertIs(clip.calls[0][2]['image'],image)
        self.assertFalse(clip.calls[0][2]['thinking']);self.assertFalse(clip.calls[1][2]['do_sample'])
        hybrid=n.build('画像から抽出＋文章で補足','Red glasses.',Qwen=clip,参考画像=image)
        self.assertEqual(hybrid['result'][0],clip.text+'\nAdditional appearance details: Red glasses.')
    def test_age_group_is_asked_separately_and_prefixed(self):
        class AgeClip(FakeClip):
            def decode(self,ids):
                asked=[c[1] for c in self.calls if c[0]=='tokenize'][-1]
                return 'Middle-aged.' if asked==appearance.AGE_ASK else self.text
        clip=AgeClip();image=torch.zeros(1,40,60,3)
        out=nodes.MossCharacterAppearance().build('画像から抽出',Qwen=clip,参考画像=image)
        self.assertEqual(out['result'],('Apparent age group: middle-aged. '+clip.text,))
        asked=[c for c in clip.calls if c[0]=='tokenize']
        self.assertEqual([c[1] for c in asked],[appearance.ASK,appearance.AGE_ASK])
        self.assertTrue(all(c[2]['image'] is image for c in asked))
        self.assertEqual(appearance.age_group('An adult in their thirties.'),'adult in their thirties')
        self.assertEqual(appearance.age_group('Young adult'),'young adult')
        self.assertIsNone(appearance.age_group('Unknown.'))
    def test_resize_keeps_ratio_and_rejects_batches(self):
        image=torch.zeros(1,1200,600,3)
        self.assertEqual(tuple(appearance.prepare_image(image).shape),(1,768,384,3))
        with self.assertRaises(ValueError):appearance.prepare_image(torch.zeros(2,50,50,3))
    def test_missing_inputs_and_incomplete_reasoning_are_errors(self):
        n=nodes.MossCharacterAppearance()
        for call in (lambda:n.build('文章のみ',''),lambda:n.build('画像から抽出'),lambda:n.build('画像から抽出',参考画像=torch.zeros(1,20,20,3))):
            with self.assertRaises(ValueError):call()
        self.assertEqual(appearance.answer_only('<think>reason</think>Hair and clothes.'),'Hair and clothes.')
        for raw in ('','<think>unfinished'):
            with self.assertRaises(ValueError):appearance.answer_only(raw)

if __name__=='__main__':unittest.main()
