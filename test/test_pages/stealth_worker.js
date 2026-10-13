// Dedicated worker probe for the stealth worker instrument (TestStealthWorkers).
const FTS = Function.prototype.toString;
const ctxProto = OffscreenCanvasRenderingContext2D.prototype;
const hcGetter = Object.getOwnPropertyDescriptor(
  WorkerNavigator.prototype,
  "hardwareConcurrency",
).get;
const report = {
  // Read before anything else: an instrument that ran later misses it.
  hardwareConcurrency: navigator.hardwareConcurrency,
  userAgent: navigator.userAgent,
  languages: navigator.languages.join(","),
  platform: navigator.platform,
  tells: {
    fillTextToString: FTS.call(ctxProto.fillText),
    convertToBlobToString: FTS.call(OffscreenCanvas.prototype.convertToBlob),
    getterToString: FTS.call(hcGetter),
    fillTextInstanceofFunction: ctxProto.fillText instanceof Function,
    fillTextShape: [
      ctxProto.fillText.name,
      ctxProto.fillText.length,
      Reflect.ownKeys(ctxProto.fillText).join(","),
      "prototype" in ctxProto.fillText,
    ].join("|"),
    getterShape: [
      hcGetter.name,
      hcGetter.length,
      Reflect.ownKeys(hcGetter).join(","),
    ].join("|"),
  },
};

function fnv(bytes) {
  let h = 0x811c9dc5;
  for (const b of bytes) {
    h = Math.imul(h ^ b, 0x01000193) >>> 0;
  }
  return h.toString(16);
}

function draw(ctx) {
  ctx.fillStyle = "#f60";
  ctx.fillRect(10, 5, 100, 20);
  ctx.fillStyle = "#069";
  ctx.font = "14px sans-serif";
  ctx.fillText("OpenWPM worker \u{1F600}", 2, 18);
}

let unhandled = 0;
self.addEventListener("unhandledrejection", () => unhandled++);

async function main() {
  const canvas = new OffscreenCanvas(220, 40);
  const ctx = canvas.getContext("2d");
  draw(ctx);
  report.pixels = fnv(ctx.getImageData(0, 0, 220, 40).data);
  try {
    ctx.getImageData(0, 0, 0, 0);
  } catch (e) {
    report.tells.errorStack = String(e.stack);
  }
  const promise = canvas.convertToBlob();
  report.promise = [
    promise instanceof Promise,
    Object.getPrototypeOf(promise) === Promise.prototype,
    Object.getOwnPropertyNames(promise).length,
  ].join("|");
  const blob = await promise;
  report.blob = fnv(new Uint8Array(await blob.arrayBuffer())) + ":" + blob.size;
  // Rejects; nobody handles it, so the page must see unhandledrejection.
  new OffscreenCanvas(0, 0).convertToBlob();
  await new Promise((resolve) => setTimeout(resolve, 500));
  report.unhandledRejections = unhandled;
  postMessage(report);
}

main().catch((e) => postMessage({ error: String(e), stack: e.stack }));
