document.addEventListener("DOMContentLoaded",()=>{

const splash=document.getElementById("bootSplash");

if(!splash) return;

const MIN_TIME=2200;

const start=performance.now();

window.addEventListener("load",()=>{

const elapsed=performance.now()-start;

const wait=Math.max(0,MIN_TIME-elapsed);

setTimeout(()=>{

splash.classList.add("hide");

setTimeout(()=>{

splash.remove();

},800);

},wait);

});

});
