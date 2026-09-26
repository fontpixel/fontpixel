---
title: "Function: $Glyph"
description: "TypeScript reference for the $Glyph factory function: parameters and return type for creating bdfparser Glyph objects."
label: "API · $Glyph"
order: 15
---

▸ `Const`**$Glyph**(`meta_obj`: [*GlyphMeta*](../../types/glyphmeta/), `font`: [*Font*](../../classes/font/)): [*Glyph*](../../classes/glyph/)

Shortcut for `new Glyph(meta_obj, font)` so you don't need to write `new`

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`meta_obj` | [*GlyphMeta*](../../types/glyphmeta/) | Meta information   |
`font` | [*Font*](../../classes/font/) | The font the glyph belongs to    |

**Returns:** [*Glyph*](../../classes/glyph/)

The newly instantiated `Glyph` object

Defined in: [bdfparser.ts:1852](https://github.com/fontpixel/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1852)
