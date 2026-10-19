const n = new URLSearchParams(location.search).get("n");
const name = `worker_ws_${n}`;
const opener = {
  [name]() {
    new WebSocket(`ws://${location.host}/stacktrace_ws_worker_${n}`);
  },
};
opener[name]();
