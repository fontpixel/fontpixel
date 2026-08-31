/** gzip decompression: DecompressionStream in the browser, zlib on Node (tests). */

export async function gunzip(buf: ArrayBuffer): Promise<ArrayBuffer> {
  // If the server sets Content-Encoding: gzip (e.g. astro preview), the
  // browser already decompressed it at the transport layer; sniff the gzip
  // magic bytes and return as-is if it's not gzip.
  const head = new Uint8Array(buf);
  if (head.length < 2 || head[0] !== 0x1f || head[1] !== 0x8b) {
    return buf;
  }
  if (typeof DecompressionStream !== 'undefined') {
    const ds = new DecompressionStream('gzip');
    const stream = new Response(new Blob([buf]).stream().pipeThrough(ds));
    return await stream.arrayBuffer();
  }
  const { gunzipSync } = await import('node:zlib');
  const out = gunzipSync(new Uint8Array(buf));
  return out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength) as ArrayBuffer;
}
