const TARGET = 'ws://127.0.0.1:9222/devtools/page/510291CC21A42B2154BDF96120E81430';
const ws = new WebSocket(TARGET);
ws.onopen = () => {
  ws.send(JSON.stringify({
    id: 1,
    method: 'Runtime.evaluate',
    params: {
      expression: `JSON.stringify({
        ice: typeof __ICE_APP_CONTEXT__,
        xtalk: typeof window.xtalk,
        mtop: typeof mtop,
        perfUrls: performance.getEntriesByType("resource")
          .map(r=>r.name)
          .filter(u=>u.includes("mtop")||u.includes("xtalk")||u.includes("/im"))
          .slice(0,20)
      })`,
      awaitPromise: false
    }
  }));
};
ws.onmessage = (e) => { console.log(e.data); process.exit(0); };
setTimeout(() => process.exit(1), 10000);
