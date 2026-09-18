/** The four canvas frames, shared by the type-test box and the comparison grid.
 *
 * Both places have to dress the canvas identically — a comparison whose columns
 * were framed differently from the detail page would be showing two variables at
 * once — so the palette and the label keys live here, the chrome in
 * FrameShell.svelte and the radios in FrameControls.svelte.
 */

import type { Rgba } from './render';
import { CODE_INK, CODE_PAPER } from './codehl';
import type { UIStrings } from '../i18n/types';

/** Declaration order is the order the radios are shown in. */
export const FRAMES = ['none', 'invert', 'game', 'code'] as const;
export type Frame = (typeof FRAMES)[number];

/** Retro-game dialog box: dark navy paper, near-white ink, fixed against the site theme. */
export const GAME_PAPER: Rgba = [19, 19, 83, 255];
export const GAME_INK: Rgba = [240, 240, 252, 255];

/**
 * Which UI string labels each frame. Typed against UIStrings so deleting a key
 * is a compile error rather than a radio button that silently loses its label.
 */
export const FRAME_LABEL_KEY = {
  none: 'frameNone',
  invert: 'frameInvert',
  game: 'frameGame',
  code: 'frameCode',
} as const satisfies Record<Frame, keyof UIStrings['catalogue']>;

/**
 * Ink and paper for a frame. `none` and `invert` both follow the theme: invert
 * is a CSS filter over the whole canvas container (paper texture included), so
 * the rasterizer still draws it the normal way round.
 */
export function framePalette(
  frame: Frame,
  theme: { ink: Rgba; paper: Rgba },
): { ink: Rgba; paper: Rgba } {
  if (frame === 'code') return { ink: CODE_INK, paper: CODE_PAPER };
  if (frame === 'game') return { ink: GAME_INK, paper: GAME_PAPER };
  return theme;
}
