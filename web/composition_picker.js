import { app } from '../../scripts/app.js';
import { api } from '../../scripts/api.js';
import { useApp, tr } from './i18n.mjs';

useApp(app);
const TYPE='MossCompositionTemplate', KEY='moss.composition.favorites.v1';
const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
const stars=()=>{try{return new Set(JSON.parse(localStorage.getItem(KEY)||'[]'));}catch{return new Set();}};
async function catalog(){const r=await api.fetchApi('/moss_panel_dataset/composition/catalog');if(!r.ok)throw Error(tr('構図一覧を取得できません。','Could not load the composition list.'));return r.json();}
// 同梱データの日本語名・英語名のどちらでも同じ構図として扱う。
const label=item=>tr(item.name,item.name_en??item.name);
const findItem=(data,value)=>data.compositions.find(e=>e.name===value||e.name_en===value);
function display(node,item){
    const box=node._compositionPreview;box.replaceChildren();
    if(!item){box.append(el('p',tr('見本から構図を選んでください。','Choose a composition from the previews.')));return;}
    const img=el('img');img.src=api.apiURL(item.preview);img.alt=label(item);img.style.cssText='width:100%;height:190px;object-fit:contain';
    box.append(img,el('p',label(item)));node.setDirtyCanvas?.(true,true);
}
async function open(node){
    let data;try{data=await catalog();}catch(e){alert(e.message);return;}
    const heading=tr('構図見本を選ぶ','Choose a composition');
    const d=el('dialog');d.setAttribute('aria-label',heading);d.style.cssText='width:min(1200px,94vw);max-height:90vh;background:#f4f6f9;color:#172033;border-radius:12px;padding:20px';
    const close=el('button',tr('閉じる','Close'));close.onclick=()=>d.close();
    d.append(close,el('h2',heading));
    const filters=el('div');filters.style.cssText='display:flex;gap:12px;flex-wrap:wrap';
    const category=el('select');category.setAttribute('aria-label',tr('構図カテゴリ','Composition category'));
    const names=data.categories_en??data.categories;
    for(const [value,text] of [['',tr('すべて','All categories')],...data.categories.map((c,i)=>[c,tr(c,names[i]??c)])]){const o=el('option',text);o.value=value;category.append(o);}
    const count=el('select');count.setAttribute('aria-label',tr('構図の人数','Number of characters'));
    for(const [value,text] of [['',tr('人数すべて','Any number of characters')],['1',tr('1人','1 person')],['2',tr('2人','2 people')],['3',tr('3人','3 people')]]){const o=el('option',text);o.value=value;count.append(o);}
    const search=el('input');search.placeholder=tr('名前・英語プロンプトで検索','Search by name or English prompt');search.setAttribute('aria-label',tr('構図を検索','Search compositions'));search.style.width='280px';
    const favLabel=el('label'),fav=el('input');fav.type='checkbox';favLabel.append(fav,document.createTextNode(' '+tr('お気に入りのみ','Favorites only')));
    const total=el('span');total.setAttribute('aria-live','polite');filters.append(count,category,search,favLabel,total);d.append(filters);
    d.append(el('p',tr('選択ノードの「コマに接続する構図」を、各コマの「構図」へ接続します。見本と登場人物の人数を合わせ、選んだ人物を番号順に構図へ割り当てます。3人目は共通の人物設定へ名前と外見を入力してください。縦横比や特殊形状での完全再現は保証しません。',
        'Connect "Composition for panel" of this node to "Composition" of each panel. Match the number of characters in the preview and in the panel; the selected characters are assigned to the composition in numerical order. For a third character, enter a name and appearance in Shared characters. An exact match for other aspect ratios or special panel shapes is not guaranteed.')));
    const grid=el('div');grid.style.cssText='display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px';d.append(grid);
    const favorites=stars();
    function render(){
        grid.replaceChildren();const q=search.value.toLowerCase();
        const entries=data.compositions.filter(e=>(!count.value||e.boxes.length===Number(count.value))&&(!category.value||e.category===category.value)&&(!fav.checked||favorites.has(e.id))&&`${e.name} ${e.name_en??''} ${e.prompt}`.toLowerCase().includes(q));
        total.textContent=tr(`${entries.length}件`,`${entries.length} found`);
        if(!entries.length)grid.append(el('p',tr('条件に合う生成済みの見本がありません。','No compositions match the filters.')));
        for(const item of entries){
            const name=label(item);
            const card=el('article');card.style.cssText='background:white;padding:8px;border:1px solid #cad2dd;border-radius:8px';
            const pick=el('button');pick.style.cssText='width:100%;background:white;color:#172033;border:0;cursor:pointer';pick.setAttribute('aria-label',tr(`${name}を選ぶ`,`Choose ${name}`));
            const img=el('img');img.src=api.apiURL(item.preview);img.alt=name;img.loading='lazy';img.style.cssText='width:100%;aspect-ratio:1;object-fit:contain';pick.append(img,el('p',name));
            pick.onclick=()=>{const w=node.widgets.find(w=>w.name==='構図テンプレート');w.value=name;w.callback?.(name);display(node,item);app.graph?.change();d.close();};
            const star=el('button',favorites.has(item.id)?'★':'☆');star.setAttribute('aria-label',tr(`${name}のお気に入り`,`Favorite ${name}`));star.setAttribute('aria-pressed',String(favorites.has(item.id)));
            star.onclick=()=>{favorites.has(item.id)?favorites.delete(item.id):favorites.add(item.id);try{localStorage.setItem(KEY,JSON.stringify([...favorites]));}catch{}render();};
            const n=item.boxes.length;
            card.append(pick,el('span',tr(`${n}人・${item.category} `,`${n} ${n===1?'person':'people'} · ${item.category_en??item.category} `)),star);
            grid.append(card);
        }
    }
    for(const control of [count,category,search,fav])control.oninput=render;
    d.addEventListener('close',()=>d.remove(),{once:true});document.body.append(d);render();d.showModal();
}
function install(node){
    if(node._compositionPreview)return;
    node.addWidget('button',tr('画像から構図を選ぶ','Choose a composition from images'),null,()=>open(node),{serialize:false});
    const box=el('div');box.style.cssText='width:100%;text-align:center';node._compositionPreview=box;
    for(const event of ['pointerdown','mousedown','dblclick','keydown','click'])box.addEventListener(event,e=>e.stopPropagation());
    node.addDOMWidget(tr('構図の見本','Composition preview'),'custom',box,{serialize:false,hideOnZoom:false,getMinHeight:()=>235,getMaxHeight:()=>260});
    node.setSize([Math.max(360,node.size[0]),Math.max(340,node.size[1])]);
    const w=node.widgets.find(w=>w.name==='構図テンプレート'),old=w?.callback;
    if(w)w.callback=function(value,...args){old?.call(this,value,...args);catalog().then(d=>display(node,findItem(d,value))).catch(()=>display(node,null));};
    catalog().then(d=>display(node,findItem(d,w?.value))).catch(()=>display(node,null));
}
app.registerExtension({name:'MossPanelDataset.CompositionPicker',beforeRegisterNodeDef(type,data){if(data.name!==TYPE)return;const old=type.prototype.onNodeCreated;type.prototype.onNodeCreated=function(...args){const result=old?.apply(this,args);install(this);return result;};},loadedGraphNode(node){if(node.type===TYPE)install(node);}});
