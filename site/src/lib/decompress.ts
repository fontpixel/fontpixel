/** gzip 解压:浏览器用 DecompressionStream,Node(测试)用 zlib。 */

export async function gunzip(buf: ArrayBuffer): Promise<ArrayBuffer> {
  // 服务器若设置 Content-Encoding: gzip(如 astro preview),浏览器已在传输层
  // 解压;嗅探 gzip 魔数,非 gzip 直接原样返回。
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
