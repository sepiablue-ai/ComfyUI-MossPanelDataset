const clone=v=>JSON.parse(JSON.stringify(v));
const linkAt=(node,slot)=>node.getInputLink?.(slot)??node.graph?.links?.[node.inputs[slot]?.link];
const slotAt=(node,i)=>node.inputs.findIndex(s=>s.name===`コマ${i}`);

function snapshot(node){
    const incoming=(node.inputs??[]).flatMap((input,slot)=>{const link=linkAt(node,slot);return link?[{name:input.name,origin:link.origin_id,slot:link.origin_slot}]:[];});
    return {nodeId:node.id,title:node.title,pos:Array.from(node.pos),size:Array.from(node.size),flags:clone(node.flags??{}),properties:clone(node.properties??{}),incoming,widgets:Object.fromEntries((node.widgets??[]).filter(w=>w.name&&w.value!==undefined).map(w=>[w.name,clone(w.value)]))};
}

function restore(node,saved){
    if(!saved)return;
    for(const w of node.widgets??[])if(Object.hasOwn(saved.widgets,w.name))w.value=clone(saved.widgets[w.name]);
    node.title=saved.title;node.pos=[...saved.pos];node.size=[...saved.size];node.flags=clone(saved.flags);node.properties={...node.properties,...clone(saved.properties)};
    for(const input of saved.incoming??[]){
        const slot=(node.inputs??[]).findIndex(s=>s.name===input.name),source=node.graph?.getNodeById(input.origin);
        if(slot>=0&&source&&!linkAt(node,slot))source.connect(input.slot,node,slot);
    }
}

export function applyLayout(node,layout,createNode){
    const graph=node.graph;
    if(!graph)throw Error('ワークフローがありません。');
    const count=Number(layout.count);
    if(!Number.isInteger(count)||count<2||count>6)throw Error('対応するコマ数は2〜6です。');
    const widget=node.widgets.find(w=>w.name==='コマ割り');
    if(!widget)throw Error('コマ割りの選択欄がありません。');
    node.properties??={};
    const stash=node.properties.mossRetiredPanels??={};
    graph.beforeChange?.();
    try{
        for(let i=count+1;i<=6;i++){
            const slot=slotAt(node,i);if(slot<0)continue;
            const link=linkAt(node,slot);if(!link)continue;
            const panel=graph.getNodeById(link.origin_id);
            if(panel?.type==='MossMangaPanel'){
                panel.properties.mossDatasetOwner??=node.id;
                stash[i]=snapshot(panel);
            }
            node.disconnectInput(slot);
            if(panel?.type==='MossMangaPanel'&&panel.properties.mossDatasetOwner===node.id&&(panel.outputs??[]).every(o=>!o.links?.length))graph.remove(panel);
        }
        for(let i=1;i<=count;i++){
            const slot=slotAt(node,i);if(slot<0)throw Error(`コマ${i}の入力がありません。ComfyUIを再起動してください。`);
            const existing=linkAt(node,slot);
            let panel=existing&&graph.getNodeById(existing.origin_id);
            if(!panel){
                const saved=stash[i];
                panel=saved&&graph.getNodeById(saved.nodeId);
                if(panel?.type!=='MossMangaPanel'){
                    panel=createNode('MossMangaPanel');if(!panel)throw Error('コマ入力ノードを作れません。');
                    graph.add(panel);restore(panel,saved);
                    if(!saved){panel.pos=[node.pos[0]-520,node.pos[1]+(i-1)*520];panel.setSize?.([450,460]);}
                }
                panel.connect(0,node,slot);
                delete stash[i];
            }
            if(panel.type==='MossMangaPanel'){
                panel.properties.mossDatasetOwner=node.id;
                panel.title=`${i}コマ目（${layout.positions?.[i-1]??`${i}番目`}）`;
            }
        }
        const castSlot=node.inputs.findIndex(s=>s.name==='人物設定');
        if(castSlot>=0&&!linkAt(node,castSlot)){
            const cast=createNode('MossMangaCharacters');if(!cast)throw Error('人物設定ノードを作れません。');
            graph.add(cast);cast.pos=[node.pos[0]-1000,node.pos[1]];cast.connect(0,node,castSlot);
        }
        widget.value=layout.name;
        node.properties.mossSelectedLayout=layout.id;
        node.properties.mossPanelCount=count;
        node.setDirtyCanvas?.(true,true);graph.setDirtyCanvas?.(true,true);
        return count;
    }finally{graph.afterChange?.();}
}
