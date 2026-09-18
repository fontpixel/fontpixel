import { expect, test } from 'vitest';
import { CODE_INK, CODE_PAPER } from './codehl';
import { FRAMES, FRAME_LABEL_KEY, GAME_INK, GAME_PAPER, framePalette } from './frames';
import { LANGS, t } from '../i18n';

const THEME = { ink: [1, 2, 3, 255], paper: [4, 5, 6, 255] } as const;

test('none and invert follow the theme; invert is a CSS filter, not a palette swap', () => {
  expect(framePalette('none', THEME)).toEqual(THEME);
  expect(framePalette('invert', THEME)).toEqual(THEME);
});

test('code and game override the theme with their own fixed palette', () => {
  expect(framePalette('code', THEME)).toEqual({ ink: CODE_INK, paper: CODE_PAPER });
  expect(framePalette('game', THEME)).toEqual({ ink: GAME_INK, paper: GAME_PAPER });
});

// The Invert radio once lost its label because the catalogue's own Invert
// control was deleted and took the shared string with it; nothing failed.
test('every frame has a non-empty label in every language', () => {
  for (const lang of LANGS)
    for (const f of FRAMES) expect(t(lang).catalogue[FRAME_LABEL_KEY[f]]).toBeTruthy();
});
