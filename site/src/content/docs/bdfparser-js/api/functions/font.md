---
title: "Function: $Font"
description: "TypeScript reference for the $Font factory function: parameters and return type for creating bdfparser Font objects."
label: "API · $Font"
order: 14
---

▸ `Const`**$Font**(`filelines`: *AsyncIterableIterator*<*string*\>): *Promise*<[*Font*](../../classes/font/)\>

Shortcut for `new Font().load_filelines(filelines)` so you don't need to write `new` and `.load_filelines`

#### Parameters:

Name | Type | Description |
------ | ------ | ------ |
`filelines` | *AsyncIterableIterator*<*string*\> | Asynchronous iterator containing each line in string text from the font file    |

**Returns:** *Promise*<[*Font*](../../classes/font/)\>

The newly instantiated `Font` object that's loaded the font file

Defined in: [bdfparser.ts:1838](https://github.com/tomchen/bdfparser-js/blob/898ed20/src/bdfparser.ts#L1838)
