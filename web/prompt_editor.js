import { app } from '../../scripts/app.js';

const TYPE='MossPromptEditor';

function show(node,text){
    if(!node._mossReceived)return;
    node._mossReceived.value=text??'';
    node._mossReceived.placeholder='実行すると、受け取ったプロンプトをここに表示します。';
}

function copyToEditor(node){
    const editor=node.widgets.find(w=>w.name==='編集用プロンプト');
    const text=node.properties?.mossReceivedPrompt;
    if(!editor||!text){alert('まだプロンプトを受け取っていません。一度実行してください。');return;}
    if(editor.value.trim()&&editor.value!==text&&!confirm('編集欄の内容を、受け取ったプロンプトで置き換えますか？'))return;
    editor.value=text;editor.callback?.(text);
    app.canvas?.setDirty(true,true);
}

function install(node){
    if(node._mossEditorInstalled)return;node._mossEditorInstalled=true;
    node.properties??={};
    const box=document.createElement('textarea');
    box.readOnly=true;box.setAttribute('aria-label','受け取ったプロンプト');
    box.style.cssText='width:100%;height:100%;box-sizing:border-box;resize:none;font:12px/1.4 monospace;background:var(--comfy-input-bg,#222);color:var(--input-text,#ddd);border:1px solid var(--border-color,#555);border-radius:4px;padding:4px;';
    for(const event of ['pointerdown','mousedown','wheel','keydown'])box.addEventListener(event,e=>e.stopPropagation());
    node._mossReceived=box;
    node.addDOMWidget('受け取ったプロンプト','custom',box,{serialize:false,hideOnZoom:false,getMinHeight:()=>160});
    node.addWidget('button','受け取ったプロンプトを編集欄へコピー',null,()=>copyToEditor(node),{serialize:false});
    show(node,node.properties.mossReceivedPrompt);
    node.setSize([Math.max(node.size[0],460),Math.max(node.size[1],520)]);
}

app.registerExtension({name:'MossPanelDataset.PromptEditor',beforeRegisterNodeDef(nodeType,nodeData){
    if(nodeData.name!==TYPE)return;
    const created=nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated=function(...args){const result=created?.apply(this,args);install(this);return result;};
    const executed=nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted=function(message){
        executed?.apply(this,arguments);
        const text=message?.text?.[0];
        if(typeof text!=='string')return;
        this.properties.mossReceivedPrompt=text;
        show(this,text);
        // 編集欄が空のときだけ自動で入れ、手で直した内容は上書きしない。
        const editor=this.widgets.find(w=>w.name==='編集用プロンプト');
        if(editor&&!editor.value.trim()){editor.value=text;editor.callback?.(text);}
        app.canvas?.setDirty(true,true);
    };
},loadedGraphNode(node){if(node.type!==TYPE)return;install(node);show(node,node.properties?.mossReceivedPrompt);}});
