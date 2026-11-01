import { app } from '../../scripts/app.js';
import { api } from '../../scripts/api.js';
import { applyLayout } from './picker_state.mjs';

const TYPE='MossPanelDatasetFlexible';
const FAVORITES='moss.panelDataset.favorites.v1';
let catalogPromise;
const el=(tag,text,className)=>{const n=document.createElement(tag);if(text)n.textContent=text;if(className)n.className=className;return n;};
const favorites=()=>{try{return new Set(JSON.parse(localStorage.getItem(FAVORITES)||'[]'));}catch{return new Set();}};
function saveFavorites(values){try{localStorage.setItem(FAVORITES,JSON.stringify([...values]));}catch{}}
async function catalog(force=false){
    if(force||!catalogPromise)catalogPromise=api.fetchApi('/moss_panel_dataset/catalog').then(r=>{if(!r.ok)throw Error('コマ割り一覧を読み込めません。');return r.json();}).then(data=>data.layouts).catch(e=>{catalogPromise=null;throw e;});
    return catalogPromise;
}
const factory=type=>{
    const engine=globalThis.LiteGraph??globalThis.comfyAPI?.litegraph?.LiteGraph;
    if(!engine?.createNode)throw Error('ComfyUIのノード作成機能が見つかりません。');
    return engine.createNode(type);
};

function style(){
    if(document.getElementById('moss-panel-picker-style'))return;
    const s=el('style');s.id='moss-panel-picker-style';
    s.textContent=`.mpp-dialog{width:min(1300px,94vw);max-height:90vh;padding:0;border:1px solid #64748b;border-radius:12px;background:#f4f6f9;color:#172033;font:15px/1.6 system-ui;box-shadow:0 18px 60px #0008}.mpp-dialog::backdrop{background:#0009}.mpp-top{position:sticky;top:0;background:#f4f6f9;z-index:2;padding:14px 18px;border-bottom:1px solid #cbd5e1}.mpp-title{display:flex;justify-content:space-between;align-items:center;gap:16px}.mpp-title h2{font-size:21px;margin:0}.mpp-filters{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:12px}.mpp-dialog button,.mpp-dialog select,.mpp-dialog input{font:inherit}.mpp-dialog button,.mpp-dialog select{padding:6px 12px;border:1px solid #aeb9c8;border-radius:6px;background:white;color:#172033;cursor:pointer}.mpp-dialog button:hover{border-color:#2463ce;background:#eef4ff}.mpp-search{padding:7px;min-width:160px;border:1px solid #aeb9c8;border-radius:6px}.mpp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:14px;padding:18px;overflow:auto}.mpp-card{background:white;border:1px solid #d4dbe5;border-radius:8px;overflow:hidden;min-width:0}.mpp-dialog .mpp-pick{display:block;border:0;border-radius:0;padding:9px;width:100%;text-align:left}.mpp-pick img{display:block;width:100%;aspect-ratio:2/3;object-fit:contain;background:white}.mpp-name{display:block;font-size:13px;margin-top:7px;min-height:42px;overflow-wrap:anywhere}.mpp-foot{display:flex;justify-content:space-between;align-items:center;padding:4px 8px 8px;font-size:12px;color:#526074}.mpp-dialog .mpp-star{font-size:20px;padding:0 7px}.mpp-note{font-size:12px;color:#526074;margin:8px 0 0}.mpp-preview{width:100%;display:flex;flex-direction:column;align-items:center;padding:5px;box-sizing:border-box;color:var(--input-text,#ddd);font:12px/1.5 system-ui}.mpp-preview img{display:block;width:100%;height:180px;object-fit:contain}.mpp-preview p{margin:4px;overflow-wrap:anywhere;text-align:center}`;
    document.head.append(s);
}

async function preview(node,entry){
    const box=node._mossPreview;if(!box)return;
    box.replaceChildren();
    if(!entry){box.append(el('p','画像からコマ割りを選んでください。'));return;}
    if(entry.preview){const img=el('img');img.alt=entry.name;img.src=api.apiURL(entry.preview);box.append(img);}
    box.append(el('p',`${entry.name}／${entry.count}コマ`));
    const retired=Object.keys(node.properties?.mossRetiredPanels??{}).length;
    if(retired)box.append(el('p',`${retired}コマ分の入力を退避中。コマ数を戻すと復元します。`));
    node.setDirtyCanvas?.(true,true);
}

async function select(node,entry){
    applyLayout(node,entry,factory);
    await preview(node,entry);
    app.canvas?.setDirty(true,true);
}

async function openPicker(node){
    style();
    let entries;
    try{entries=await catalog(true);}catch(error){alert(error.message);return;}
    const dialog=el('dialog',null,'mpp-dialog');dialog.setAttribute('aria-label','漫画のコマ割りを選ぶ');
    const top=el('div',null,'mpp-top'),title=el('div',null,'mpp-title');
    title.append(el('h2','漫画のコマ割りを選ぶ'));
    const close=el('button','閉じる');close.onclick=()=>dialog.close();title.append(close);top.append(title);
    const filters=el('div',null,'mpp-filters');
    const makeSelect=(label,values)=>{const l=el('label',label+' '),s=el('select');s.setAttribute('aria-label',label);for(const [value,text] of values){const o=el('option',text);o.value=value;s.append(o);}l.append(s);filters.append(l);return s;};
    const count=makeSelect('コマ数',[['','すべて'],...[2,3,4,5,6].map(n=>[String(n),`${n}コマ`])]);
    const type=makeSelect('種類',[['normal','通常'],['diagonal','斜め'],['special','特殊'],['','すべて']]);
    type.value='normal';
    const selected=entries.find(e=>e.name===node.widgets.find(w=>w.name==='コマ割り')?.value);
    count.value=selected?String(selected.count):'';
    const favLabel=el('label'),fav=el('input');fav.type='checkbox';fav.setAttribute('aria-label','お気に入りのみ');favLabel.append(fav,document.createTextNode(' お気に入りのみ'));filters.append(favLabel);
    const search=el('input',null,'mpp-search');search.placeholder='名前で検索';search.setAttribute('aria-label','コマ割り名で検索');filters.append(search);
    const total=el('span');total.setAttribute('aria-live','polite');filters.append(total);top.append(filters);
    top.append(el('p','画像を選ぶと今のワークフローへ反映します。人物・セリフは保持し、減るコマは退避します。画像はMOSSの出力をWebPへ圧縮したものです。','mpp-note'));
    const grid=el('div',null,'mpp-grid');dialog.append(top,grid);document.body.append(dialog);
    let stars=favorites();
    function render(){
        grid.replaceChildren();
        const list=entries.filter(e=>e.preview&&(!count.value||e.count===Number(count.value))&&(!type.value||(type.value==='normal'?['通常','直線'].includes(e.category):type.value==='diagonal'?e.category==='斜め':e.category==='特殊'))&&(!fav.checked||stars.has(e.id))&&(!search.value||e.name.toLowerCase().includes(search.value.toLowerCase())));
        total.textContent=`${list.length}件`;
        if(!list.length){grid.append(el('p','条件に合う生成済みのコマ割りがありません。'));return;}
        for(const entry of list){
            const card=el('article',null,'mpp-card'),pick=el('button',null,'mpp-pick');pick.type='button';pick.setAttribute('aria-label',`${entry.name}を選ぶ`);
            const img=el('img');img.src=api.apiURL(entry.preview);img.alt=entry.name;img.loading='lazy';pick.append(img,el('span',entry.name,'mpp-name'));
            pick.onclick=async()=>{try{await select(node,entry);dialog.close();}catch(error){alert(error.message);}};
            const foot=el('div',null,'mpp-foot');foot.append(el('span',`${entry.count}コマ・${entry.category}${entry.quality==='near_duplicate'?'・重複候補':entry.quality==='needs_review'||entry.status==='needs_review'?'・要確認':''}`));
            const star=el('button',stars.has(entry.id)?'★':'☆','mpp-star');star.type='button';star.setAttribute('aria-label',`${entry.name}のお気に入りを切り替え`);star.setAttribute('aria-pressed',String(stars.has(entry.id)));
            star.onclick=()=>{stars.has(entry.id)?stars.delete(entry.id):stars.add(entry.id);saveFavorites(stars);render();};foot.append(star);card.append(pick,foot);grid.append(card);
        }
    }
    for(const control of [count,type,fav,search])control.addEventListener('input',render);
    dialog.addEventListener('close',()=>dialog.remove(),{once:true});render();dialog.showModal();
}

function install(node){
    if(node._mossPickerInstalled)return;node._mossPickerInstalled=true;style();
    node.addWidget('button','画像からコマ割りを選ぶ',null,()=>openPicker(node),{serialize:false});
    const box=el('div',null,'mpp-preview');node._mossPreview=box;
    for(const event of ['pointerdown','mousedown','dblclick','keydown','click'])box.addEventListener(event,e=>e.stopPropagation());
    node.addDOMWidget('コマ割りの見本','custom',box,{serialize:false,hideOnZoom:false,getMinHeight:()=>225,getMaxHeight:()=>260});
    node.setSize([Math.max(node.size[0],390),Math.max(node.size[1],400)]);
    const widget=node.widgets.find(w=>w.name==='コマ割り');
    if(widget){
        const previous=widget.callback;
        widget.callback=function(value,...args){
            previous?.call(this,value,...args);
            catalog().then(entries=>{const entry=entries.find(e=>e.name===value);if(entry)return select(node,entry);}).catch(error=>console.warn('コマ割りの反映に失敗しました。',error));
        };
        catalog().then(entries=>preview(node,entries.find(e=>e.name===widget.value))).catch(()=>preview(node,null));
    }
}

app.registerExtension({name:'MossPanelDataset.ImagePicker',beforeRegisterNodeDef(nodeType,nodeData){
    if(nodeData.name!==TYPE)return;
    const old=nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated=function(...args){const result=old?.apply(this,args);install(this);return result;};
},loadedGraphNode(node){if(node.type===TYPE)install(node);}});
