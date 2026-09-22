---
title: "Class: Glyph"
description: "TypeScript API for the bdfparser Glyph class: constructors, properties, and methods to inspect character metrics and draw individual pixel glyphs as bitmaps."
label: "API · Glyph"
order: 12
---

`Glyph` object

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/glyph](https://font.tomchen.org/bdfparser_js/glyph)

## Hierarchy

* **Glyph**

## Constructors

### constructor

\+ **new Glyph**(`meta_obj`: [*GlyphMeta*](../../types/glyphmeta/), `font`: [*Font*](../font/)): [*Glyph*](../glyph/)

`Glyph` object constructor

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/glyph](https://font.tomchen.org/bdfparser_js/glyph)

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`meta_obj` | [*GlyphMeta*](../../types/glyphmeta/) | Meta information   |
`font` | [*Font*](../font/) | The font the glyph belongs to    |

**Returns:** [*Glyph*](../glyph/)

Defined in: [bdfparser.ts:970](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L970)

## Properties

### font

• **font**: [*Font*](../font/)

Defined in: [bdfparser.ts:970](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L970)

___

### meta

• **meta**: [*GlyphMeta*](../../types/glyphmeta/)

Defined in: [bdfparser.ts:969](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L969)

## Methods

### \_\_draw\_bb

▸ `Private`**__draw_bb**(): [*Bitmap*](../bitmap/)

**Returns:** [*Bitmap*](../bitmap/)

Defined in: [bdfparser.ts:1097](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1097)

___

### \_\_draw\_fbb

▸ `Private`**__draw_fbb**(): [*Bitmap*](../bitmap/)

**Returns:** [*Bitmap*](../bitmap/)

Defined in: [bdfparser.ts:1114](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1114)

___

### \_\_draw\_original

▸ `Private`**__draw_original**(): [*Bitmap*](../bitmap/)

**Returns:** [*Bitmap*](../bitmap/)

Defined in: [bdfparser.ts:1085](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1085)

___

### \_\_draw\_user\_specified

▸ `Private`**__draw_user_specified**(`fbb`: [*number*, *number*, *number*, *number*]): [*Bitmap*](../bitmap/)

#### Parameters:

Name | Type |
------ | ------ |
`fbb` | [*number*, *number*, *number*, *number*] |

**Returns:** [*Bitmap*](../bitmap/)

Defined in: [bdfparser.ts:1077](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1077)

___

### chr

▸ **chr**(): *string*

Get the character of the glyph.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/glyph#chr](https://font.tomchen.org/bdfparser_js/glyph#chr)

**Returns:** *string*

Character (one character string) of the glyph

Defined in: [bdfparser.ts:1033](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1033)

___

### cp

▸ **cp**(): *number*

Get the codepoint of the glyph.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/glyph#cp](https://font.tomchen.org/bdfparser_js/glyph#cp)

**Returns:** *number*

Codepoint of the glyph

Defined in: [bdfparser.ts:1022](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1022)

___

### draw

▸ **draw**(`mode?`: *null* \| *0* \| *1* \| *-1* \| *2*, `bb?`: *null* \| [*number*, *number*, *number*, *number*]): [*Bitmap*](../bitmap/)

Draw the glyph to a `Bitmap` object.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/glyph#draw](https://font.tomchen.org/bdfparser_js/glyph#draw)

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`mode?` | *null* \| *0* \| *1* \| *-1* \| *2* | Mode   |
`bb?` | *null* \| [*number*, *number*, *number*, *number*] | Bounding box    |

**Returns:** [*Bitmap*](../bitmap/)

`Bitmap` object

Defined in: [bdfparser.ts:1047](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1047)

___

### origin

▸ **origin**(`options?`: { `fromorigin?`: *undefined* \| *null* \| *boolean* ; `mode?`: *undefined* \| *null* \| *0* \| *1* \| *-1* \| *2* ; `xoff?`: *undefined* \| *null* \| *number* ; `yoff?`: *undefined* \| *null* \| *number*  }): [*number*, *number*]

Get the relative position (displacement) of the origin from the left bottom corner of the bitmap drawn by the method `.draw()`, or vice versa.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/glyph#origin](https://font.tomchen.org/bdfparser_js/glyph#origin)

#### Parameters:

Name | Type | Default value |
------ | ------ | ------ |
`options` | { `fromorigin?`: *undefined* \| *null* \| *boolean* ; `mode?`: *undefined* \| *null* \| *0* \| *1* \| *-1* \| *2* ; `xoff?`: *undefined* \| *null* \| *number* ; `yoff?`: *undefined* \| *null* \| *number*  } | ... |

**Returns:** [*number*, *number*]

The relative position (displacement) represented by `[x, y]` array / tuple (where right and top directions are positive)

Defined in: [bdfparser.ts:1139](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1139)

___

### repr

▸ **repr**(): *string*

Gets a programmer-readable `string` representation of the `Glyph` object.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/glyph#repr](https://font.tomchen.org/bdfparser_js/glyph#repr)

**Returns:** *string*

String representation

Defined in: [bdfparser.ts:1003](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1003)

___

### toString

▸ **toString**(): *string*

Gets a human-readable (multi-line) `string` representation of the `Glyph` object.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/glyph#tostring](https://font.tomchen.org/bdfparser_js/glyph#tostring)

**Returns:** *string*

String representation

Defined in: [bdfparser.ts:992](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L992)
