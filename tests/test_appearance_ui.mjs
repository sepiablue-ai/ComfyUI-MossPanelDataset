import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';

test('外見の結果を復元・表示し文章欄へコピーする',async()=>{
    let extension;
    const app={registerExtension:e=>extension=e,graph:{change(){}}};
    const source=readFileSync(new URL('../web/appearance.js',import.meta.url),'utf8').replace(/^import .*;\r?\n/,'');
    vm.runInNewContext(source,{app,document:{createElement:()=>({setAttribute(){},addEventListener(){},style:{}})},queueMicrotask});
    class Node {
        constructor(){this.properties={};this.size=[200,200];this.widgets=[{name:'外見プロンプト',value:''},{name:'指定方法',value:'画像から抽出'}];}
        addDOMWidget(){} addWidget(type,name,value,callback){this.copy=callback;} setSize(){}
    }
    extension.beforeRegisterNodeDef(Node,{name:'MossCharacterAppearance'});
    const node=new Node();node.onNodeCreated();
    node.properties.mossAppearanceText='Long hair, a ribbon.';node.onConfigure();await Promise.resolve();
    assert.equal(node._mossAppearanceView.textContent,'Long hair, a ribbon.');
    node.onExecuted({text:['Short hair, glasses.']});node.copy();
    assert.equal(node._mossAppearanceView.textContent,'Short hair, glasses.');
    assert.equal(node.widgets[0].value,'Short hair, glasses.');
    assert.equal(node.widgets[1].value,'文章のみ');
});
