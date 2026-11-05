import { app } from '../../scripts/app.js';
import { api } from '../../scripts/api.js';
import { useApp, isJa, translations, localizeCombo } from './i18n.mjs';

// 各ノードの選択肢・既定の名前・ノード名を、ComfyUIの表示言語へそろえる。
useApp(app);
const TYPES=new Set(['MossPanelDatasetFlexible','MossMangaCharacters','MossMangaPanel','MossPromptEditor','MossCompositionTemplate','MossCharacterAppearance']);
const TEXT_FIELDS=new Set(['人物1_名前','人物2_名前']);

async function localize(node){
    let data;
    try{data=await translations(path=>api.fetchApi(path));}catch(error){console.warn('[MossPanelDataset]',error);return;}
    const info=data.nodes?.[node.type];
    if(!info)return;
    let changed=false;
    for(const [name,pairs] of Object.entries(info.combos??{})){
        changed=localizeCombo(node.widgets?.find(w=>w.name===name),pairs,{text:TEXT_FIELDS.has(name)})||changed;
    }
    const known=[...info.display,...(info.legacy_titles??[])];
    if(known.includes(node.title)){
        const title=info.display[isJa()?0:1];
        if(node.title!==title){node.title=title;changed=true;}
    }
    if(changed)node.setDirtyCanvas?.(true,true);
}

app.registerExtension({
    name:'MossPanelDataset.Locale',
    nodeCreated(node){if(TYPES.has(node.type??node.comfyClass))localize(node);},
    loadedGraphNode(node){if(TYPES.has(node.type))localize(node);},
});
