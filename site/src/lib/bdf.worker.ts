import { decodeBdf } from './bdf';

self.onmessage = async ({ data }: MessageEvent<{ id: number; buffer: ArrayBuffer }>) => {
  try {
    const font = await decodeBdf(data.buffer);
    const first = font.glyphs.values().next().value;
    self.postMessage({ id: data.id, font }, { transfer: first ? [first.rows.buffer] : [] });
  } catch (error) {
    self.postMessage({ id: data.id, error: String(error) });
  }
};
