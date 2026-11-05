import json
import unittest
from test_composition import nodes

class ThreeCharacters(unittest.TestCase):
    def cast(self,third=True):
        fields={'人物1_名前':'花子','人物1_外見':'Black hair, white blouse.','人物2_名前':'太郎','人物2_外見':'Short light hair, glasses, dark suit.'}
        if third:fields.update({'人物3_名前':'葵','人物3_外見':'Short wavy hair, cardigan, light trousers.'})
        return nodes.MossMangaCharacters().build(**fields)[0]
    def panel(self):
        return nodes.MossMangaPanel().build(**{'場面':'Three adults have a conversation.','登場人物':'人物1と人物2と人物3','話者1':'人物1','セリフ1':'おはよう。','話者2':'人物2','セリフ2':'こんにちは。','話者3':'人物3','セリフ3':'こんばんは。'})[0]
    def test_old_cast_stays_two_people(self):
        self.assertEqual(list(self.cast(False)),['人物1','人物2'])
    def test_three_people_and_three_original_dialogues(self):
        cast=self.cast();panel=self.panel()
        data=json.loads(nodes.MossPanelDatasetFlexible().build(**{'コマ割り':'normal_2_01','生成内容':'漫画','人物設定':cast,'コマ1':panel,'コマ2':panel})[0])
        self.assertEqual(len([x for x in data['items'] if x['label']=='character']),6)
        self.assertEqual([x['text'] for x in data['items'] if x['label']=='text'],['おはよう。','こんにちは。','こんばんは。']*2)
        for group in ([x for x in data['items'] if x['label']=='character'][:3],[x for x in data['items'] if x['label']=='text'][:3]):
            self.assertGreater(group[0]['bbox'][1],group[1]['bbox'][1]);self.assertGreater(group[1]['bbox'][1],group[2]['bbox'][1])
    def test_missing_third_and_duplicate_names_are_errors(self):
        panel=self.panel()
        with self.assertRaisesRegex(ValueError,'人物3'):
            nodes.MossPanelDatasetFlexible().build(**{'コマ割り':'normal_2_01','生成内容':'漫画','人物設定':self.cast(False),'コマ1':panel,'コマ2':panel})
        fields={'人物1_名前':'花子','人物1_外見':'Woman.','人物2_名前':'太郎','人物2_外見':'Man.','人物3_名前':'花子','人物3_外見':'Woman.'}
        with self.assertRaises(ValueError):nodes.MossMangaCharacters().build(**fields)
        fields['人物3_名前']='葵';fields['人物3_外見']=''
        with self.assertRaises(ValueError):nodes.MossMangaCharacters().build(**fields)
    def test_three_person_template_preserves_cast_order(self):
        boxes=[[.67,.15,.98,.95],[.35,.20,.65,.95],[.02,.15,.33,.95]]
        fields={'場面':'Three adults talking.','登場人物':'人物1と人物2と人物3','話者1':'人物3','セリフ1':'三番目から。','話者2':'セリフなし','セリフ2':'','構図':{'prompt':'Person 1 right, person 2 center, person 3 left.','boxes':boxes}}
        p=nodes.MossMangaPanel().build(**fields)[0]
        data=json.loads(nodes.MossPanelDatasetFlexible().build(**{'コマ割り':'normal_2_02','生成内容':'漫画','人物設定':self.cast(),'コマ1':p,'コマ2':p})[0])
        people=[x for x in data['items'] if x['label']=='character']
        self.assertIn('Black hair',people[0]['caption']);self.assertIn('glasses',people[1]['caption']);self.assertIn('cardigan',people[2]['caption'])
    def test_every_nonempty_subset_of_three_is_available(self):
        self.assertEqual({frozenset(v) for v in nodes.ACTOR_SLOTS.values()},{frozenset(s for j,s in enumerate(nodes.SLOTS) if mask&(1<<j)) for mask in range(8)})

if __name__=='__main__':unittest.main()
