/** gzip 解压:浏览器用 DecompressionStream,Node(测试)用 zlib。 */

export async function gunzip(buf: ArrayBuffer): Promise<ArrayBuffer> {
  if (typeof DecompressionStream !== 'undefined') {
    const ds = new DecompressionStream('gzip');
    const stream = new Response(new Blob([buf]).stream().pipeThrough(ds));
    return await stream.arrayBuffer();
  }
  const { gunzipSync } = await import('node:zlib');
  const out = gunzipSync(new Uint8Array(buf));
  return out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength) as ArrayBuffer;
}
