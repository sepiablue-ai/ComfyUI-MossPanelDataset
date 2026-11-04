import assert from 'node:assert/strict';
import { applyLayout } from '../web/picker_state.mjs';
let id=1,linkId=1;
class Graph{
    constructor(){this.nodes=new Map();this.links={};}
    add(n){n.id=id++;n.graph=this;this.nodes.set(n.id,n);}
    getNodeById(n){return this.nodes.get(n);}
    remove(n){for(let i=0;i<n.inputs.length;i++)n.disconnectInput(i);this.nodes.delete(n.id);}
}
function make(type){return {type,id:0,pos:[0,0],size:[400,400],flags:{},properties:{},outputs:[{links:[]}],inputs:type==='MossMangaPanel'?[{name:'構図'}]:[],widgets:type==='MossMangaPanel'?[{name:'場面',value:'Original scene'},{name:'セリフ1',value:'元のセリフ'}]:[],connect(out,target,slot){
    const lid=linkId++;this.graph.links[lid]={origin_id:this.id,origin_slot:out,target_id:target.id,target_slot:slot};this.outputs[out].links.push(lid);target.inputs[slot].link=lid;
},getInputLink(slot){return this.graph.links[this.inputs[slot]?.link];},disconnectInput(slot){const l=this.getInputLink(slot);if(!l)return;const source=this.graph.getNodeById(l.origin_id);source.outputs[l.origin_slot].links=source.outputs[l.origin_slot].links.filter(x=>x!==this.inputs[slot].link);delete this.graph.links[this.inputs[slot].link];this.inputs[slot].link=null;}};}
const graph=new Graph(),selector=make('MossPanelDatasetFlexible');selector.inputs=[{name:'人物設定'},...[1,2,3,4,5,6].map(i=>({name:`コマ${i}`}))];selector.widgets=[{name:'コマ割り',value:'旧配置'}];graph.add(selector);
const sampler=make('KSampler');sampler.widgets=[{name:'seed',value:999}];graph.add(sampler);
const layout=n=>({id:`layout${n}`,name:`${n}コマ配置`,count:n,positions:Array.from({length:n},(_,i)=>`${i+1}番目`)});
applyLayout(selector,layout(4),make);
const third=graph.getNodeById(selector.getInputLink(3).origin_id);third.widgets[1].value='保持するセリフ';
const composition=make('MossCompositionTemplate');graph.add(composition);composition.connect(0,third,0);
applyLayout(selector,layout(2),make);
assert.equal([...graph.nodes.values()].filter(n=>n.type==='MossMangaPanel').length,2);
assert.equal(selector.properties.mossRetiredPanels[3].widgets['セリフ1'],'保持するセリフ');
applyLayout(selector,layout(6),make);
assert.equal([...graph.nodes.values()].filter(n=>n.type==='MossMangaPanel').length,6);
assert.equal(graph.getNodeById(selector.getInputLink(3).origin_id).widgets[1].value,'保持するセリフ');
assert.equal(graph.getNodeById(selector.getInputLink(3).origin_id).getInputLink(0).origin_id,composition.id);
assert.equal(sampler.widgets[0].value,999);
assert.equal(selector.widgets[0].value,'6コマ配置');
assert.equal([...graph.nodes.values()].filter(n=>n.type==='MossMangaCharacters').length,1);
// 他のノードでも使うコマは、コマ数を減らしても削除しない。
const shared=graph.getNodeById(selector.getInputLink(6).origin_id),other=make('Consumer');other.inputs=[{name:'入力'}];graph.add(other);shared.connect(0,other,0);
applyLayout(selector,layout(2),make);assert.equal(graph.getNodeById(shared.id),shared);
applyLayout(selector,layout(6),make);assert.equal(selector.getInputLink(6).origin_id,shared.id);
console.log('コマ数変更、入力退避・復元、共有ノード保護、生成設定維持の検査が通りました。');
