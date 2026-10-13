const inner = new Worker("stealth_worker_inner.js");
inner.onmessage = ({ data }) => postMessage(data);
