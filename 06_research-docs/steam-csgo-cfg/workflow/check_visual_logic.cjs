// Exercise the HTML's actual inline script with a minimal DOM; no layout claims.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const file=process.argv[2]||'out/repair10/LEETED_Ablauf_und_Test.html';
const html=fs.readFileSync(file,'utf8'),elements=[];
function el(){const e={textContent:'',value:'',dataset:{},children:[],attrs:{},append(...x){this.children.push(...x)},replaceChildren(...x){this.children=x},setAttribute(k,v){this.attrs[k]=String(v)}};elements.push(e);return e}
const nodes={};for(const m of html.matchAll(/id="([^"]+)"/g))nodes[m[1]]=el();
nodes['cfg-data'].textContent=html.match(/<script id="cfg-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const document={getElementById:id=>nodes[id],createElement:el,createElementNS:el,createTextNode:s=>s,querySelectorAll:selector=>elements.filter(e=>selector==='[data-key]'?e.dataset.key:selector==='[data-slot]'?e.dataset.slot:false)};
const ctx=vm.createContext({document,console});const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];assert.equal(scripts.length,1);vm.runInContext(scripts[0][1],ctx);
const run=s=>vm.runInContext(s,ctx);let tests=0;
function check(s){assert.equal(run(s),true,s);tests++}
run("key('space');key('capslock');key('space');key('capslock')");check("m.weapon===1 && m.hand==='rechts' && !m.inspect && m.sprint && m.drop.length===0 && !m.binds.mwheeldown");
run("reset();command('inspect_on');key('z');key('space');key('alt');key('space');key('alt')");check("m.weapon===1 && m.hand==='rechts' && !m.inspect");
run("reset();command('c_nweed');key('mouse1');key('enter');key('mouse1')");check("m.values.cl_crosshair_recoil==='1' && m.aliases.refresh_crosshair==='crosshair_fire'");
run("key('enter')");check("m.values.cl_crosshair_recoil==='0' && m.values.cl_crosshaircolor_g==='255' && m.values.cl_crosshaircolor_r==='155'");
run("command('shot_t');key('mouse1')");check("m.values.cl_crosshairstyle==='4' && m.values.cl_crosshaircolor_r==='255' && m.values.cl_crosshaircolor_g==='0'");
run("command('shot_off')");check("m.values.cl_crosshair_recoil==='0' && m.values.cl_crosshaircolor_r==='155'");
run("reset();command('inspect_on');key('q')");check('m.inspect');run("command('inspect_off')");check('!m.inspect');run("key('q')");check("m.hand==='rechts' && m.weapon===1");
run("reset();command('c_npink');command('color_lock_off');command('movecross')");check("m.values.cl_crosshaircolor_g==='255'");run("command('color_lock_on')");check("m.values.cl_crosshaircolor_g==='0' && m.values.cl_crosshaircolor_b==='255'");
console.log(tests+' HTML-script state assertions passed; minimal DOM only, no browser/layout validation.');
