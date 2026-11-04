import { app } from '../../scripts/app.js';
import { api } from '../../scripts/api.js';

const TYPE='MossCompositionTemplate', KEY='moss.composition.favorites.v1';
const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
const stars=()=>{try{return new Set(JSON.parse(localStorage.getItem(KEY)||'[]'));}catch{return new Set();}};
async function catalog(){const r=await api.fetchApi('/moss_panel_dataset/composition/catalog');if(!r.ok)throw Error('構図一覧を取得できません。');return r.json();}
function display(node,item){
    const box=node._compositionPreview;box.replaceChildren();
    if(!item){box.append(el('p','見本から構図を選んでください。'));return;}
    const img=el('img');img.src=api.apiURL(item.preview);img.alt=item.name;img.style.cssText='width:100%;height:190px;object-fit:contain';
    box.append(img,el('p',item.name));node.setDirtyCanvas?.(true,true);
}
async function open(node){
    let data;try{data=await catalog();}catch(e){alert(e.message);return;}
    const d=el('dialog');d.setAttribute('aria-label','構図見本を選ぶ');d.style.cssText='width:min(1200px,94vw);max-height:90vh;background:#f4f6f9;color:#172033;border-radius:12px;padding:20px';
    const close=el('button','閉じる');close.onclick=()=>d.close();
    const heading=el('h2','構図見本を選ぶ');d.append(close,heading);
    const filters=el('div');filters.style.cssText='display:flex;gap:12px;flex-wrap:wrap';
    const category=el('select');category.setAttribute('aria-label','構図カテゴリ');
    for(const name of ['すべて',...data.categories]){const o=el('option',name);o.value=name;category.append(o);}
    const count=el('select');count.setAttribute('aria-label','構図の人数');
    for(const [value,label] of [['','人数すべて'],['1','1人'],['2','2人'],['3','3人']]){const o=el('option',label);o.value=value;count.append(o);}
    const search=el('input');search.placeholder='名前・英語プロンプトで検索';search.setAttribute('aria-label','構図を検索');search.style.width='280px';
    const label=el('label'),fav=el('input');fav.type='checkbox';label.append(fav,document.createTextNode(' お気に入りのみ'));
    const total=el('span');total.setAttribute('aria-live','polite');filters.append(count,category,search,label,total);d.append(filters);
    d.append(el('p','選択ノードの「コマに接続する構図」を、各コマの「構図」へ接続します。見本と登場人物の人数を合わせ、選んだ人物を番号順に構図へ割り当てます。3人目は共通の人物設定へ名前と外見を入力してください。縦横比や特殊形状での完全再現は保証しません。'));
    const grid=el('div');grid.style.cssText='display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px';d.append(grid);
    const favorites=stars();
    function render(){
        grid.replaceChildren();const q=search.value.toLowerCase();
        const entries=data.compositions.filter(e=>(!count.value||e.boxes.length===Number(count.value))&&(category.value==='すべて'||e.category===category.value)&&(!fav.checked||favorites.has(e.id))&&`${e.name} ${e.prompt}`.toLowerCase().includes(q));total.textContent=`${entries.length}件`;
        if(!entries.length)grid.append(el('p','条件に合う生成済みの見本がありません。'));
        for(const item of entries){
            const card=el('article');card.style.cssText='background:white;padding:8px;border:1px solid #cad2dd;border-radius:8px';
            const pick=el('button');pick.style.cssText='width:100%;background:white;color:#172033;border:0;cursor:pointer';pick.setAttribute('aria-label',`${item.name}を選ぶ`);
            const img=el('img');img.src=api.apiURL(item.preview);img.alt=item.name;img.loading='lazy';img.style.cssText='width:100%;aspect-ratio:1;object-fit:contain';pick.append(img,el('p',item.name));
            pick.onclick=()=>{const w=node.widgets.find(w=>w.name==='構図テンプレート');w.value=item.name;w.callback?.(item.name);display(node,item);app.graph?.change();d.close();};
            const star=el('button',favorites.has(item.id)?'★':'☆');star.setAttribute('aria-label',`${item.name}のお気に入り`);star.setAttribute('aria-pressed',String(favorites.has(item.id)));
            star.onclick=()=>{favorites.has(item.id)?favorites.delete(item.id):favorites.add(item.id);try{localStorage.setItem(KEY,JSON.stringify([...favorites]));}catch{}render();};
            card.append(pick,el('span',`${item.boxes.length}人・${item.category} `),star);
            grid.append(card);
        }
    }
    for(const control of [count,category,search,fav])control.oninput=render;
    d.addEventListener('close',()=>d.remove(),{once:true});document.body.append(d);render();d.showModal();
}
function install(node){
    if(node._compositionPreview)return;
    node.addWidget('button','画像から構図を選ぶ',null,()=>open(node),{serialize:false});
    const box=el('div');box.style.cssText='width:100%;text-align:center';node._compositionPreview=box;
    for(const event of ['pointerdown','mousedown','dblclick','keydown','click'])box.addEventListener(event,e=>e.stopPropagation());
    node.addDOMWidget('構図の見本','custom',box,{serialize:false,hideOnZoom:false,getMinHeight:()=>235,getMaxHeight:()=>260});
    node.setSize([Math.max(360,node.size[0]),Math.max(340,node.size[1])]);
    const w=node.widgets.find(w=>w.name==='構図テンプレート'),old=w?.callback;
    if(w)w.callback=function(value,...args){old?.call(this,value,...args);catalog().then(d=>display(node,d.compositions.find(e=>e.name===value))).catch(()=>display(node,null));};
    catalog().then(d=>display(node,d.compositions.find(e=>e.name===w?.value))).catch(()=>display(node,null));
}
app.registerExtension({name:'MossPanelDataset.CompositionPicker',beforeRegisterNodeDef(type,data){if(data.name!==TYPE)return;const old=type.prototype.onNodeCreated;type.prototype.onNodeCreated=function(...args){const result=old?.apply(this,args);install(this);return result;};},loadedGraphNode(node){if(node.type===TYPE)install(node);}});
