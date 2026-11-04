import { app } from '../../scripts/app.js';

const TYPE='MossCharacterAppearance';
function install(node){
    if(node._mossAppearanceView){node._mossAppearanceView.textContent=node.properties?.mossAppearanceText??'';return;}
    node.properties??={};
    const box=document.createElement('div');box.setAttribute('role','textbox');box.setAttribute('aria-readonly','true');box.setAttribute('aria-label','人物の外見の結果');
    box.title='実行すると、人物設定へ渡す外見の文章がここに表示されます。';
    box.style.cssText='width:100%;height:100%;box-sizing:border-box;overflow:auto;white-space:pre-wrap;user-select:text;background:var(--comfy-input-bg,#222);color:var(--input-text,#ddd);font:13px/1.5 system-ui;padding:8px;';
    box.textContent=node.properties.mossAppearanceText??'';node._mossAppearanceView=box;
    for(const event of ['pointerdown','mousedown','wheel','keydown'])box.addEventListener(event,e=>e.stopPropagation());
    node.addDOMWidget('外見の結果','custom',box,{serialize:false,hideOnZoom:false,getMinHeight:()=>150,getValue:()=>node.properties.mossAppearanceText??'',setValue:()=>{box.textContent=node.properties.mossAppearanceText??'';}});
    node.addWidget('button','結果を文章欄へコピー（文章のみに切替）',null,()=>{
        const text=node.properties.mossAppearanceText;
        if(!text){alert('一度実行して、外見の結果を取得してください。');return;}
        const field=node.widgets.find(w=>w.name==='外見プロンプト'),mode=node.widgets.find(w=>w.name==='指定方法');
        if(field&&mode){field.value=text;mode.value='文章のみ';field.callback?.(text);mode.callback?.(mode.value);app.graph?.change();node.setDirtyCanvas?.(true,true);}
    },{serialize:false});
    node.setSize([Math.max(450,node.size[0]),Math.max(510,node.size[1])]);
}
app.registerExtension({name:'MossPanelDataset.CharacterAppearance',beforeRegisterNodeDef(type,data){
    if(data.name!==TYPE)return;
    const created=type.prototype.onNodeCreated,executed=type.prototype.onExecuted,configured=type.prototype.onConfigure;
    type.prototype.onNodeCreated=function(...args){const result=created?.apply(this,args);install(this);return result;};
    type.prototype.onConfigure=function(...args){const result=configured?.apply(this,args);install(this);queueMicrotask(()=>install(this));return result;};
    type.prototype.onExecuted=function(message){executed?.apply(this,arguments);const text=message?.text?.[0];if(typeof text==='string'){this.properties??={};this.properties.mossAppearanceText=text;if(this._mossAppearanceView)this._mossAppearanceView.textContent=text;}};
},loadedGraphNode(node){if(node.type===TYPE)install(node);}});

