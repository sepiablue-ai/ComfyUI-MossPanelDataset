// 画面の表示言語。ComfyUIの言語設定（Comfy.Locale）が日本語なら日本語、それ以外は英語にする。
let appRef=null;
export function useApp(app){appRef=app??appRef;}

export function locale(){
    try{
        const app=appRef??globalThis.comfyAPI?.app?.app;
        const value=app?.extensionManager?.setting?.get?.('Comfy.Locale')??app?.ui?.settings?.getSettingValue?.('Comfy.Locale');
        if(value)return String(value);
    }catch{}
    return globalThis.navigator?.language??'en';
}
export const isJa=()=>/^ja(\b|[-_])/i.test(locale());
export const tr=(ja,en)=>isJa()?ja:en;

let tablePromise=null;
export function translations(fetchApi){
    tablePromise??=fetchApi('/moss_panel_dataset/i18n').then(r=>{if(!r.ok)throw Error(tr('翻訳データを読み込めません。','Could not load translations.'));return r.json();}).catch(e=>{tablePromise=null;throw e;});
    return tablePromise;
}

// [日本語, 英語] の組から、今の表示言語の値を返す。どちらにも当たらない値はそのまま。
export function localizeValue(pairs,value){
    const pair=pairs.find(p=>p[0]===value||p[1]===value);
    return pair?pair[isJa()?0:1]:value;
}

// 選択肢を表示言語の値だけにし、保存済みの値も同じ意味の表示言語の値へ置き換える。
export function localizeCombo(widget,pairs,{text=false}={}){
    if(!widget||!pairs?.length)return false;
    if(!text&&Array.isArray(widget.options?.values))widget.options.values=pairs.map(p=>p[isJa()?0:1]);
    const next=localizeValue(pairs,widget.value);
    if(next===widget.value)return false;
    widget.value=next;
    return true;
}
