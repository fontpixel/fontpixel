---
title: "Class: Bitmap"
label: "API · Bitmap"
order: 10
---

`Bitmap` object

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap](https://font.tomchen.org/bdfparser_js/bitmap)

## Hierarchy

* **Bitmap**

## Constructors

### constructor

\+ **new Bitmap**(`bin_bitmap_list`: *string*[]): [*Bitmap*](../bitmap/)

Initialize a `Bitmap` object. Load binary bitmap data (`array` of `string`s).

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap](https://font.tomchen.org/bdfparser_js/bitmap)

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`bin_bitmap_list` | *string*[] | Binary bitmap data    |

**Returns:** [*Bitmap*](../bitmap/)

Defined in: [bdfparser.ts:1188](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1188)

## Properties

### bindata

• **bindata**: *string*[]

Defined in: [bdfparser.ts:1188](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1188)

## Methods

### bytepad

▸ **bytepad**(`bits?`: *null* \| *number*): [*Bitmap*](../bitmap/)

Pad each line (row) to multiple of 8 (or other numbers) bits/pixels, with `'0'`s.

Do this before using the bitmap for a glyph in a BDF font.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#bytepad](https://font.tomchen.org/bdfparser_js/bitmap#bytepad)

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`bits?` | *null* \| *number* | Each line should be padded to multiple of how many bits/pixels    |

**Returns:** [*Bitmap*](../bitmap/)

The `Bitmap` object itself, which now has the altered bitmap as its `.bindata`

Defined in: [bdfparser.ts:1734](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1734)

___

### clone

▸ **clone**(): [*Bitmap*](../bitmap/)

Get a deep copy / clone of the `Bitmap` object.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#clone](https://font.tomchen.org/bdfparser_js/bitmap#clone)

**Returns:** [*Bitmap*](../bitmap/)

A deep copy of the original `Bitmap` object

Defined in: [bdfparser.ts:1256](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1256)

___

### concat

▸ **concat**(`bitmap`: [*Bitmap*](../bitmap/), `options?`: { `align?`: *undefined* \| *null* \| *0* \| *1* ; `direction?`: *undefined* \| *null* \| *0* \| *1* \| *-1* \| *2* ; `offset?`: *undefined* \| *null* \| *number*  }): [*Bitmap*](../bitmap/)

Concatenate another `Bitmap` objects to the current one.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#concat](https://font.tomchen.org/bdfparser_js/bitmap#concat)

#### Parameters:

Name | Type | Default value | Description |
------ | ------ | ------ | ------ |
`bitmap` | [*Bitmap*](../bitmap/) | - | Bitmap to concatenate   |
`options` | { `align?`: *undefined* \| *null* \| *0* \| *1* ; `direction?`: *undefined* \| *null* \| *0* \| *1* \| *-1* \| *2* ; `offset?`: *undefined* \| *null* \| *number*  } | ... | - |

**Returns:** [*Bitmap*](../bitmap/)

The `Bitmap` object itself, which now has the combined bitmap as its `.bindata`

Defined in: [bdfparser.ts:1538](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1538)

___

### crop

▸ **crop**(`w`: *number*, `h`: *number*, `xoff?`: *null* \| *number*, `yoff?`: *null* \| *number*): [*Bitmap*](../bitmap/)

Crop and/or extend the bitmap.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#crop](https://font.tomchen.org/bdfparser_js/bitmap#crop)

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`w` | *number* | Width   |
`h` | *number* | Height   |
`xoff?` | *null* \| *number* | X offset   |
`yoff?` | *null* \| *number* | Y offset    |

**Returns:** [*Bitmap*](../bitmap/)

The `Bitmap` object itself, which now has only the specified area as its `.bindata`

Defined in: [bdfparser.ts:1380](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1380)

___

### draw2canvas

▸ **draw2canvas**(`context`: CanvasContext, `pixelcolors?`: *null* \| *Record*<*0* \| *1* \| *2*, *null* \| *string*\>): [*Bitmap*](../bitmap/)

Draw the bitmap to HTML canvas

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#draw2canvas](https://font.tomchen.org/bdfparser_js/bitmap#draw2canvas)

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`context` | CanvasContext | Canvas 2D context (`canvas.getContext("2d")`)   |
`pixelcolors?` | *null* \| *Record*<*0* \| *1* \| *2*, *null* \| *string*\> | Object mapping `'0'`/`'1'`/`'2'` in the bitmap data to color    |

**Returns:** [*Bitmap*](../bitmap/)

The `Bitmap` object itself

Defined in: [bdfparser.ts:1806](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1806)

___

### enlarge

▸ **enlarge**(`x?`: *number*, `y?`: *number*): [*Bitmap*](../bitmap/)

Enlarge a `Bitmap` object, by multiplying every pixel in x (right) direction and in y (top) direction.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#enlarge](https://font.tomchen.org/bdfparser_js/bitmap#enlarge)

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`x?` | *number* | Multiplier in x (right) direction   |
`y?` | *number* | Multiplier in y (top) direction    |

**Returns:** [*Bitmap*](../bitmap/)

The `Bitmap` object itself, which now has the enlarged bitmap as its `.bindata`

Defined in: [bdfparser.ts:1593](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1593)

___

### glow

▸ **glow**(`mode?`: *null* \| *0* \| *1*): [*Bitmap*](../bitmap/)

Add glow effect to the shape in the bitmap.

The glowing area is one pixel up, right, bottom and left to the original pixels (corners will not be filled in default mode 0 but will in mode 1), and will be filled by `'2'`s.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#glow](https://font.tomchen.org/bdfparser_js/bitmap#glow)

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`mode?` | *null* \| *0* \| *1* | Mode    |

**Returns:** [*Bitmap*](../bitmap/)

The `Bitmap` object itself, which now has a bitmap of the original shape with glow effect as the `Bitmap` object's `.bindata`

Defined in: [bdfparser.ts:1690](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1690)

___

### height

▸ **height**(): *number*

Get the height of the bitmap.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#height](https://font.tomchen.org/bdfparser_js/bitmap#height)

**Returns:** *number*

Height of the bitmap

Defined in: [bdfparser.ts:1245](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1245)

___

### overlay

▸ **overlay**(`bitmap`: [*Bitmap*](../bitmap/)): [*Bitmap*](../bitmap/)

Overlay another bitmap over the current one.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#overlay](https://font.tomchen.org/bdfparser_js/bitmap#overlay)

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`bitmap` | [*Bitmap*](../bitmap/) | The incoming bitmap to overlay over the current one    |

**Returns:** [*Bitmap*](../bitmap/)

The `Bitmap` object itself, which now has the combined bitmap as its `.bindata`

Defined in: [bdfparser.ts:1396](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1396)

___

### replace

▸ **replace**(`substr`: *string* \| *number*, `newsubstr`: *string* \| *number*): [*Bitmap*](../bitmap/)

Replace a string by another in the bitmap.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#replace](https://font.tomchen.org/bdfparser_js/bitmap#replace)

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`substr` | *string* \| *number* | Substring to be replaced   |
`newsubstr` | *string* \| *number* | New substring as the replacement    |

**Returns:** [*Bitmap*](../bitmap/)

The `Bitmap` object itself, which now has the altered bitmap as its `.bindata`

Defined in: [bdfparser.ts:1608](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1608)

___

### repr

▸ **repr**(): *string*

Gets a programmer-readable (multi-line) `string` representation of the `Bitmap` object.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#repr](https://font.tomchen.org/bdfparser_js/bitmap#repr)

**Returns:** *string*

String representation

Defined in: [bdfparser.ts:1223](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1223)

___

### shadow

▸ **shadow**(`xoff?`: *null* \| *number*, `yoff?`: *null* \| *number*): [*Bitmap*](../bitmap/)

Add shadow to the shape in the bitmap.

The shadow will be filled by `'2'`s.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#shadow](https://font.tomchen.org/bdfparser_js/bitmap#shadow)

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`xoff?` | *null* \| *number* | Shadow's offset in x (right) direction   |
`yoff?` | *null* \| *number* | Shadow's offset in y (top) direction    |

**Returns:** [*Bitmap*](../bitmap/)

The `Bitmap` object itself, which now has a bitmap of the original shape with its shadow as the `Bitmap` object's `.bindata`

Defined in: [bdfparser.ts:1646](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1646)

___

### toString

▸ **toString**(): *string*

Gets a human-readable (multi-line) `string` representation of the `Bitmap` object.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#tostring](https://font.tomchen.org/bdfparser_js/bitmap#tostring)

**Returns:** *string*

String representation

Defined in: [bdfparser.ts:1208](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1208)

___

### todata

▸ **todata**&lt;T&gt;(`datatype?`: T): [*TodataFuncRetType*](../../types/todatafuncrettype/)&lt;T&gt;

Get the bitmap's data in the specified type and format.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#todata](https://font.tomchen.org/bdfparser_js/bitmap#todata)

#### Type parameters:

Name | Type |
------ | ------ |
`T` | *null* \| *0* \| *1* \| *2* \| *4* \| *3* \| *5* |

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`datatype?` | T | Output data type    |

**Returns:** [*TodataFuncRetType*](../../types/todatafuncrettype/)&lt;T&gt;

Bitmap data in the specified type (list or string) and format

Defined in: [bdfparser.ts:1754](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1754)

___

### width

▸ **width**(): *number*

Get the width of the bitmap.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#width](https://font.tomchen.org/bdfparser_js/bitmap#width)

**Returns:** *number*

Width of the bitmap

Defined in: [bdfparser.ts:1234](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1234)

___

### \_\_crop\_bitmap

▸ `Private` `Static`**__crop_bitmap**(`bitmap`: *string*[], `w`: *number*, `h`: *number*, `xoff`: *number*, `yoff`: *number*): *string*[]

#### Parameters:

Name | Type |
------ | ------ |
`bitmap` | *string*[] |
`w` | *number* |
`h` | *number* |
`xoff` | *number* |
`yoff` | *number* |

**Returns:** *string*[]

Defined in: [bdfparser.ts:1347](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1347)

___

### \_\_crop\_string

▸ `Private` `Static`**__crop_string**(`s`: *string*, `start`: *number*, `length`: *number*): *string*

#### Parameters:

Name | Type |
------ | ------ |
`s` | *string* |
`start` | *number* |
`length` | *number* |

**Returns:** *string*

Defined in: [bdfparser.ts:1260](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1260)

___

### \_\_enlarge\_bindata

▸ `Private` `Static`**__enlarge_bindata**(`bindata`: *string*[], `x?`: *null* \| *number*, `y?`: *null* \| *number*): *string*[]

#### Parameters:

Name | Type |
------ | ------ |
`bindata` | *string*[] |
`x?` | *null* \| *number* |
`y?` | *null* \| *number* |

**Returns:** *string*[]

Defined in: [bdfparser.ts:1556](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1556)

___

### \_\_listofstr\_offset\_concat

▸ `Private` `Static`**__listofstr_offset_concat**(`list1`: *string*[], `list2`: *string*[], `offset?`: *null* \| *number*): *string*[]

#### Parameters:

Name | Type |
------ | ------ |
`list1` | *string*[] |
`list2` | *string*[] |
`offset?` | *null* \| *number* |

**Returns:** *string*[]

Defined in: [bdfparser.ts:1306](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1306)

___

### \_\_string\_offset\_concat

▸ `Private` `Static`**__string_offset_concat**(`s1`: *string*, `s2`: *string*, `offset?`: *null* \| *number*): *string*

#### Parameters:

Name | Type |
------ | ------ |
`s1` | *string* |
`s2` | *string* |
`offset?` | *null* \| *number* |

**Returns:** *string*

Defined in: [bdfparser.ts:1279](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1279)

___

### concatall

▸ `Static`**concatall**(`bitmaplist`: [*Bitmap*](../bitmap/)[], `options?`: { `align?`: *undefined* \| *null* \| *0* \| *1* ; `direction?`: *undefined* \| *null* \| *0* \| *1* \| *-1* \| *2* ; `offsetlist?`: *undefined* \| *null* \| *number*[]  }): [*Bitmap*](../bitmap/)

Concatenate all `Bitmap` objects in an `array`.

**`see`** online docs: [https://font.tomchen.org/bdfparser_js/bitmap#bitmapconcatall](https://font.tomchen.org/bdfparser_js/bitmap#bitmapconcatall)

#### Parameters:

Name | Type | Default value | Description |
------ | ------ | ------ | ------ |
`bitmaplist` | [*Bitmap*](../bitmap/)[] | - | List of bitmaps to concatenate   |
`options` | { `align?`: *undefined* \| *null* \| *0* \| *1* ; `direction?`: *undefined* \| *null* \| *0* \| *1* \| *-1* \| *2* ; `offsetlist?`: *undefined* \| *null* \| *number*[]  } | ... | - |

**Returns:** [*Bitmap*](../bitmap/)

`Bitmap` object

Defined in: [bdfparser.ts:1428](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1428)
