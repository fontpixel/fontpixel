/** Plain-language summaries of the licences the collection actually uses.
 *
 * Every font page shows the summary for its own licence, so the reader does not
 * have to parse a legal text to answer "may I ship this in my game". The seven
 * flags are deliberately the questions people actually ask; the prose carries
 * the caveats that a flag cannot. Every flag is phrased as a freedom, so a tick
 * always reads as permissive and a cross always as a restriction — no row means
 * the opposite of its neighbours.
 *
 * The wording is ours, not the licensors'. Nothing here overrides the licence
 * text bundled with a font, which is why the disclaimer sits right underneath.
 */

/** ✓ yes · ⚠ conditional · × no, or not required */
export type Flag = 'yes' | 'cond' | 'no';

export interface LicenseSummary {
  /** Which of the three broad families this licence belongs to */
  tier: 'permissive-max' | 'permissive' | 'copyleft';
  flags: {
    /** Commercial use */
    commercial: Flag;
    /** Modifying the font */
    modify: Flag;
    /** Embedding in a document — yes means the document's own licence is unaffected */
    documents: Flag;
    /** Embedding in an application — yes means the app's own licence is unaffected */
    apps: Flag;
    /** No notice requirement — yes means the notices need not travel with it */
    notice: Flag;
    /** No copyleft — yes means derivatives need not stay under the same licence */
    sameLicense: Flag;
    /** No renaming requirement — yes means a modified version may keep the name */
    rename: Flag;
  };
  /** One or two short paragraphs; the first should answer the common case */
  body: string[];
}

/** Order of the flag columns, shared by the table and the legend. */
export const FLAG_KEYS = [
  'commercial', 'modify', 'documents', 'apps', 'notice', 'sameLicense', 'rename',
] as const;
export type FlagKey = (typeof FLAG_KEYS)[number];

const F = (
  commercial: Flag, modify: Flag, documents: Flag, apps: Flag,
  notice: Flag, sameLicense: Flag, rename: Flag,
) => ({ commercial, modify, documents, apps, notice, sameLicense, rename });

export const SUMMARIES_EN: Record<string, LicenseSummary> = {
  "CC0-1.0": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      'Use, modify, embed, and redistribute commercially without permission or attribution. Copyright is waived as far as legally possible, but patent and trademark rights are not included.',
    ],
  },
  "LicenseRef-PublicDomain": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      'Generally unrestricted, but public domain is a legal status rather than a standard license. Its validity may vary by source and jurisdiction, and trademark or moral rights may remain.',
    ],
  },
  "LicenseRef-Mplus": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      'Commercial use, modification, embedding, and redistribution are allowed without attribution, copyleft, or renaming requirements. Current M+ FONTS releases use OFL-1.1, so check the included license.',
    ],
  },
  "LicenseRef-Tamsyn": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      'Commercial use, modification, embedding, and redistribution are allowed without attribution, copyleft, or renaming requirements. The font is provided without warranty.',
    ],
  },
  "WTFPL": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      'Almost unrestricted, including commercial use, modification, redistribution, and relicensing. It has no explicit warranty disclaimer or patent grant.',
    ],
  },
  "MIT": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      'Commercial use, modification, embedding, sublicensing, and redistribution are allowed. Copies or substantial portions must retain the copyright and permission notices.',
    ],
  },
  "BSD-2-Clause": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      'Commercial use, modification, embedding, and redistribution are allowed. Keep the copyright notice, license terms, and disclaimer; binary distributions may place them in accompanying materials.',
    ],
  },
  "MirOS": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      'Commercial use, modification, embedding, sale, sublicensing, and redistribution are allowed. Keep the copyright notices, license terms, and disclaimer.',
    ],
  },
  "HPND": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      'Generally free to use, modify, embed, and redistribute if the required notices are preserved. Some variants also require notices in supporting documentation or restrict promotional use of the copyright holder\'s name.',
    ],
  },
  "LicenseRef-ISAS-1988": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      'Commercial use and resale are allowed. "Without fee" means the permission is granted without a license fee, not that copies must be free. Keep the notices, and do not use the institute\'s name to promote distribution without written permission.',
    ],
  },
  "LicenseRef-Baekmuk": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      'Commercial use, modification, embedding, and redistribution are allowed if the notices are preserved. Supporting documentation must acknowledge the registered Baekmuk font trademarks.',
    ],
  },
  "LicenseRef-UW-ttyp0": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'cond'),
    body: [
      'Commercial use, modification, embedding, sale, and redistribution are allowed if the notices are preserved. Changing or adding glyphs requires a new name; metadata-only changes and repackaging do not. The new name cannot contain "UW", and "ttyp0" must follow a different foundry name.',
    ],
  },
  "OFL-1.1": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'no', 'cond'),
    body: [
      'Fonts may be used, embedded, modified, bundled, and commercially distributed, but cannot be sold by themselves. Redistributed fonts and derivatives remain under OFL.',
      'If Reserved Font Names are declared, modified versions must use different names. Format conversion and rebuilds that change the font also count as modifications. Documents and applications using the font are not subject to OFL.',
    ],
  },
  "OFL-1.1 OR GPL-2.0-with-font-exception": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'cond', 'no', 'no', 'yes'),
    body: [
      'Choose either license. Under OFL, modified fonts remain under OFL and cannot be sold by themselves; the current official Unifont release declares no Reserved Font Name, so no renaming is required.',
      'Under GPL, modified fonts remain under the selected GPL version and their corresponding source must be available, but standalone sale is allowed. Direct application embedding may require a distributed application to use GPL; choosing OFL allows the application to remain proprietary.',
    ],
  },
  "GPL-2.0-with-font-exception": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'cond', 'no', 'no', 'yes'),
    body: [
      'The Font Exception allows document embedding without making the document subject to GPL. Modified fonts still require GPL 2 and corresponding source when distributed.',
      'Modifiers may remove the exception, and it does not clearly cover direct application embedding. Check the license of modified versions.',
    ],
  },
  "GPL-2.0-only": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      'Commercial use and private modification are allowed. Distributed copies and derivatives remain under GPL 2 and require notices, change information, and corresponding source or a permitted written source offer.',
      'The source must be the preferred editable form, such as BDF, SFD, UFO, or HEX files, with necessary build scripts. Generated TTF or PCF files alone may not be enough. Separate bundling does not affect unrelated software, but embedding may create GPL obligations when distributed.',
    ],
  },
  "GPL-2.0-or-later": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      'Commercial use and private modification are allowed. Distributed copies and derivatives must follow GPL 2 or a later GPL version and include the required notices and corresponding source.',
      'Separate bundling does not affect unrelated software, but distributing a document or application that embeds the font may create GPL obligations.',
    ],
  },
  "CC-BY-SA-4.0": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      'Commercial use, modification, embedding, and redistribution are allowed. When sharing, provide credit, a license link, and an indication of changes; adaptations must use the same or a compatible license.',
      'There is no font-specific embedding exception, so the effect on a document or application\'s license may depend on applicable law. Patent and trademark rights are not included.',
    ],
  },
};

export const SUMMARIES_ZH: Record<string, LicenseSummary> = {
  "CC0-1.0": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '无需许可或署名，即可将字体用于商业用途、修改、嵌入和再分发。权利人已在法律允许的最大范围内放弃著作权，但不包括专利权和商标权。',
    ],
  },
  "LicenseRef-PublicDomain": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '通常不受限制，但公有领域是一种法律状态，而非标准许可证。其有效性可能因来源和司法管辖区而异，商标权或著作人身权也可能仍然存在。',
    ],
  },
  "LicenseRef-Mplus": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '允许商业使用、修改、嵌入和再分发，无须署名，也没有著佐权或重命名要求。当前发布的 M+ FONTS 采用 OFL-1.1，因此请检查字体随附的许可证。',
    ],
  },
  "LicenseRef-Tamsyn": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '允许商业使用、修改、嵌入和再分发，无须署名，也没有著佐权或重命名要求。字体不附带任何担保。',
    ],
  },
  "WTFPL": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '几乎不受限制，包括商业使用、修改、再分发和改用其他许可证。该许可证没有明确的担保免责声明或专利许可。',
    ],
  },
  "MIT": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '允许商业使用、修改、嵌入、再许可和再分发。字体副本或字体的实质性部分必须保留著作权声明和许可声明。',
    ],
  },
  "BSD-2-Clause": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '允许商业使用、修改、嵌入和再分发。须保留著作权声明、许可条款和免责声明；二进制发行版可将这些内容放在随附材料中。',
    ],
  },
  "MirOS": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '允许商业使用、修改、嵌入、销售、再许可和再分发。须保留著作权声明、许可条款和免责声明。',
    ],
  },
  "HPND": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '只要保留所要求的声明，通常可以自由使用、修改、嵌入和再分发。某些许可证变体还要求在配套文档中保留声明，或限制将著作权人的姓名用于宣传。',
    ],
  },
  "LicenseRef-ISAS-1988": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '允许商业使用和转售。“Without fee”表示授予许可本身不收取许可费，并非要求副本必须免费。须保留相关声明；未经书面许可，不得使用该机构的名称宣传分发活动。',
    ],
  },
  "LicenseRef-Baekmuk": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '只要保留相关声明，即可进行商业使用、修改、嵌入和再分发。配套文档必须注明 Baekmuk 字体商标已经注册。',
    ],
  },
  "LicenseRef-UW-ttyp0": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'cond'),
    body: [
      '只要保留相关声明，即可进行商业使用、修改、嵌入、销售和再分发。更改或添加字形时，字体必须改用新名称；仅修改元数据或重新打包则无须改名。新名称不得包含“UW”，且必须在“ttyp0”前冠以其他字库厂商的名称。',
    ],
  },
  "OFL-1.1": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'no', 'cond'),
    body: [
      '允许使用、嵌入、修改、捆绑和商业分发字体，但不得单独销售字体。再分发的字体及其衍生版本仍须采用 OFL。',
      '如果声明了保留字体名称，修改后的版本必须使用不同的名称。格式转换或重新构建如果改变了字体，也算作修改。使用该字体的文档和应用不受 OFL 约束。',
    ],
  },
  "OFL-1.1 OR GPL-2.0-with-font-exception": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'cond', 'no', 'no', 'yes'),
    body: [
      '可任选其中一种许可证。采用 OFL 时，修改后的字体仍须采用 OFL，且不得单独销售；当前的 Unifont 官方版本没有声明保留字体名称，因此无须重命名。',
      '采用 GPL 时，修改后的字体仍须使用所选的 GPL 版本，并且必须提供相应源代码，但允许单独销售。直接嵌入应用可能会要求分发的应用采用 GPL；选择 OFL 则可使应用继续采用专有许可证。',
    ],
  },
  "GPL-2.0-with-font-exception": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'cond', 'no', 'no', 'yes'),
    body: [
      '字体例外条款允许将字体嵌入文档，而不会使该文档受 GPL 约束。修改后的字体在分发时仍须采用 GPL 2，并提供相应源代码。',
      '修改者可以移除该例外条款，而且该条款是否涵盖直接嵌入应用并不明确。请检查修改版本的许可证。',
    ],
  },
  "GPL-2.0-only": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      '允许商业使用和非公开修改。分发的副本和衍生版本仍须采用 GPL 2，并附上相关声明、变更信息和相应源代码，或提供许可证允许的书面源代码提供要约。',
      '源代码必须是首选的可编辑形式，例如 BDF、SFD、UFO 或 HEX 文件，并包含必要的构建脚本。仅提供生成的 TTF 或 PCF 文件可能不够。作为独立组件捆绑分发不会影响无关软件，但嵌入字体后分发可能会产生 GPL 义务。',
    ],
  },
  "GPL-2.0-or-later": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      '允许商业使用和非公开修改。分发的副本和衍生版本必须遵循 GPL 2 或更高版本，并附上所要求的声明和相应源代码。',
      '作为独立组件捆绑分发不会影响无关软件，但分发嵌入该字体的文档或应用可能会产生 GPL 义务。',
    ],
  },
  "CC-BY-SA-4.0": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      '允许商业使用、修改、嵌入和再分发。分享时须提供署名信息和许可证链接，并说明所做的更改；改编版本必须采用相同或兼容的许可证。',
      '该许可证没有针对字体嵌入的专门例外条款，因此其对文档或应用许可证的影响可能取决于适用法律。该许可证不包括专利权和商标权。',
    ],
  },
};

export const SUMMARIES_JA: Record<string, LicenseSummary> = {
  "CC0-1.0": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '商用利用、改変、埋め込み、再頒布が、許可や帰属表示なしに認められています。著作権は法的に可能な限り放棄されていますが、特許権および商標権は対象に含まれません。',
    ],
  },
  "LicenseRef-PublicDomain": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '一般に制約はありませんが、パブリックドメインは標準ライセンスではなく、法的な地位です。パブリックドメインとしての有効性は出所や法域によって異なる場合があり、商標権や著作者人格権が残ることもあります。',
    ],
  },
  "LicenseRef-Mplus": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '帰属表示、コピーレフト、改名の要件なしに、商用利用、改変、埋め込み、再頒布が認められています。現在の M+ FONTS リリースでは OFL-1.1 が使われているため、同梱のライセンスを確認してください。',
    ],
  },
  "LicenseRef-Tamsyn": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '帰属表示、コピーレフト、改名の要件なしに、商用利用、改変、埋め込み、再頒布が認められています。このフォントは無保証で提供されます。',
    ],
  },
  "WTFPL": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '商用利用、改変、再頒布、再ライセンスを含め、ほぼ制約がありません。無保証条項も特許権の許諾も明記されていません。',
    ],
  },
  "MIT": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '商用利用、改変、埋め込み、サブライセンス、再頒布が認められています。複製物またはその重要な部分には、著作権表示および許諾表示を保持しなければなりません。',
    ],
  },
  "BSD-2-Clause": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '商用利用、改変、埋め込み、再頒布が認められています。著作権表示、ライセンス条項、免責条項を保持してください。バイナリ形式で頒布する場合は、それらを付属資料に記載できます。',
    ],
  },
  "MirOS": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '商用利用、改変、埋め込み、販売、サブライセンス、再頒布が認められています。著作権表示、ライセンス条項、免責条項を保持してください。',
    ],
  },
  "HPND": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '一般に、必要な表示を保持すれば、自由に使用、改変、埋め込み、再頒布できます。一部のバリエーションでは、付属文書への表示が必要な場合や、著作権者名の宣伝目的での使用が制限される場合があります。',
    ],
  },
  "LicenseRef-ISAS-1988": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '商用利用および再販売が認められています。「無償」とは、使用許諾がライセンス料なしで付与されるという意味であり、複製物を無料にしなければならないという意味ではありません。表示を保持し、書面による許可なしに研究所の名称を頒布の宣伝に使用しないでください。',
    ],
  },
  "LicenseRef-Baekmuk": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '表示を保持すれば、商用利用、改変、埋め込み、再頒布が認められています。付属文書には、Baekmuk フォントの登録商標を明記しなければなりません。',
    ],
  },
  "LicenseRef-UW-ttyp0": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'cond'),
    body: [
      '表示を保持すれば、商用利用、改変、埋め込み、販売、再頒布が認められています。グリフの変更または追加には新しい名前が必要ですが、メタデータのみの変更や再パッケージ化には必要ありません。新しい名前に「UW」を含めることはできず、「ttyp0」の前には別のファウンドリ名を付けなければなりません。',
    ],
  },
  "OFL-1.1": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'no', 'cond'),
    body: [
      'フォントの使用、埋め込み、改変、同梱、商用頒布は認められていますが、フォント単体では販売できません。再頒布されるフォントおよび派生物には、引き続き OFL が適用されます。',
      '予約されたフォント名（Reserved Font Names）が指定されている場合、改変版には異なる名前を使用しなければなりません。フォントに変更を加える形式変換や再ビルドも改変に該当します。フォントを使用する文書やアプリケーションは OFL の適用対象にはなりません。',
    ],
  },
  "OFL-1.1 OR GPL-2.0-with-font-exception": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'cond', 'no', 'no', 'yes'),
    body: [
      'いずれか一方のライセンスを選択します。OFL では、改変したフォントには引き続き OFL が適用され、フォント単体で販売することはできません。現在の公式 Unifont リリースでは予約されたフォント名（Reserved Font Name）が指定されていないため、改名は不要です。',
      'GPL では、改変したフォントには選択した GPL バージョンが引き続き適用され、対応するソースコードを入手可能にしなければなりませんが、単体での販売は認められています。アプリケーションに直接埋め込むと、頒布するアプリケーションにも GPL の適用が必要になる場合があります。OFL を選択すれば、アプリケーションをプロプライエタリのままにできます。',
    ],
  },
  "GPL-2.0-with-font-exception": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'cond', 'no', 'no', 'yes'),
    body: [
      'フォント例外（Font Exception）により、文書を GPL の適用対象にせずにフォントを埋め込めます。改変したフォントを頒布する場合には、引き続き GPL 2 の適用と対応するソースコードが必要です。',
      '改変者はこの例外条項を削除できます。また、この例外条項がアプリケーションへの直接の埋め込みを対象とするかは明確ではありません。改変版のライセンスを確認してください。',
    ],
  },
  "GPL-2.0-only": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      '商用利用および私的な改変が認められています。頒布される複製物および派生物には引き続き GPL 2 を適用し、表示、変更に関する情報、および対応するソースコードまたはライセンスで認められた書面によるソースコード提供の申し出を含めなければなりません。',
      'ソースコードは、BDF、SFD、UFO、HEX ファイルなど、改変を加える上で好ましい編集可能な形式であり、必要なビルドスクリプトも含めなければなりません。生成された TTF または PCF ファイルだけでは不十分な場合があります。フォントを他のソフトウェアとは別個に同梱するだけなら無関係のソフトウェアには影響しませんが、埋め込んで頒布すると GPL 上の義務が生じる場合があります。',
    ],
  },
  "GPL-2.0-or-later": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      '商用利用および私的な改変が認められています。頒布される複製物および派生物は GPL 2 またはそれ以降の GPL バージョンに従い、必要な表示と対応するソースコードを含めなければなりません。',
      'フォントを他のソフトウェアとは別個に同梱するだけなら無関係のソフトウェアには影響しませんが、フォントを埋め込んだ文書やアプリケーションを頒布すると GPL 上の義務が生じる場合があります。',
    ],
  },
  "CC-BY-SA-4.0": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      '商用利用、改変、埋め込み、再頒布が認められています。共有時には、クレジットとライセンスへのリンクを示し、変更を加えた旨を明記しなければなりません。翻案物には同一または互換性のあるライセンスを適用しなければなりません。',
      'フォントに特化した埋め込み例外はないため、文書やアプリケーションのライセンスに及ぼす影響は、適用される法律によって異なる場合があります。特許権および商標権は対象に含まれません。',
    ],
  },
};

export const SUMMARIES_KO: Record<string, LicenseSummary> = {
  "CC0-1.0": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '허가나 저작자 표시 없이 상업적으로 사용, 수정, 임베딩 및 재배포할 수 있습니다. 법적으로 가능한 범위에서 저작권을 포기하지만, 특허권과 상표권은 포함되지 않습니다.',
    ],
  },
  "LicenseRef-PublicDomain": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '일반적으로 제한 없이 사용할 수 있지만, 퍼블릭 도메인은 표준 라이선스가 아니라 법적 상태입니다. 그 유효성은 출처와 관할권에 따라 달라질 수 있으며, 상표권이나 저작인격권은 여전히 존속할 수 있습니다.',
    ],
  },
  "LicenseRef-Mplus": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '저작자 표시, 카피레프트 또는 이름 변경 요구 없이 상업적으로 사용, 수정, 임베딩 및 재배포할 수 있습니다. 현재 M+ FONTS 릴리스에는 OFL-1.1이 적용되므로 포함된 라이선스를 확인하십시오.',
    ],
  },
  "LicenseRef-Tamsyn": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '저작자 표시, 카피레프트 또는 이름 변경 요구 없이 상업적으로 사용, 수정, 임베딩 및 재배포할 수 있습니다. 이 글꼴에는 어떠한 보증도 제공되지 않습니다.',
    ],
  },
  "WTFPL": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      '상업적 이용, 수정, 재배포, 재라이선스를 포함해 거의 제한이 없습니다. 명시적인 보증 부인 조항이나 특허권 허여 조항은 없습니다.',
    ],
  },
  "MIT": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '상업적 이용, 수정, 임베딩, 서브라이선스 허여 및 재배포가 허용됩니다. 복제물이나 글꼴의 상당 부분에는 저작권 고지와 허가 고지가 유지되어야 합니다.',
    ],
  },
  "BSD-2-Clause": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '상업적 이용, 수정, 임베딩 및 재배포가 허용됩니다. 저작권 고지, 라이선스 조건 및 면책 조항을 유지해야 하며, 바이너리 배포물의 경우 동봉 자료에 이를 기재할 수 있습니다.',
    ],
  },
  "MirOS": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '상업적 이용, 수정, 임베딩, 판매, 서브라이선스 허여 및 재배포가 허용됩니다. 저작권 고지, 라이선스 조건 및 면책 조항을 유지해야 합니다.',
    ],
  },
  "HPND": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '일반적으로 필수 고지를 유지하면 자유롭게 사용, 수정, 임베딩 및 재배포할 수 있습니다. 일부 변형 라이선스는 지원 문서에도 고지를 포함하도록 요구하거나, 저작권자 이름을 홍보 목적으로 사용하는 것을 제한합니다.',
    ],
  },
  "LicenseRef-ISAS-1988": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '상업적 이용과 재판매가 허용됩니다. "무상으로"라는 표현은 라이선스 사용료 없이 허가한다는 뜻이지, 복제물을 무료로 제공해야 한다는 뜻은 아닙니다. 고지를 유지해야 하며, 서면 허가 없이 해당 기관의 이름을 배포 홍보에 사용해서는 안 됩니다.',
    ],
  },
  "LicenseRef-Baekmuk": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      '고지를 유지하면 상업적 이용, 수정, 임베딩 및 재배포가 허용됩니다. 지원 문서에는 Baekmuk 글꼴 상표가 등록 상표임을 명시해야 합니다.',
    ],
  },
  "LicenseRef-UW-ttyp0": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'cond'),
    body: [
      '고지를 유지하면 상업적 이용, 수정, 임베딩, 판매 및 재배포가 허용됩니다. 글리프를 변경하거나 추가하면 새 이름을 사용해야 하지만, 메타데이터만 변경하거나 재패키징하는 경우에는 새 이름이 필요하지 않습니다. 새 이름에는 "UW"를 포함할 수 없으며, "ttyp0" 앞에는 다른 폰드리 이름을 붙여야 합니다.',
    ],
  },
  "OFL-1.1": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'no', 'cond'),
    body: [
      '글꼴을 사용, 임베드, 수정하거나 다른 항목과 묶어 상업적으로 배포할 수 있습니다. 다만 글꼴만 따로 판매할 수는 없습니다. 재배포되는 글꼴과 파생 글꼴에는 OFL을 계속 적용해야 합니다.',
      '예약 글꼴 이름(Reserved Font Names)이 지정된 경우, 수정된 버전은 다른 이름을 사용해야 합니다. 글꼴을 변경하는 형식 변환과 재빌드도 수정으로 간주됩니다. 이 글꼴을 사용하는 문서와 애플리케이션에는 OFL이 적용되지 않습니다.',
    ],
  },
  "OFL-1.1 OR GPL-2.0-with-font-exception": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'cond', 'no', 'no', 'yes'),
    body: [
      '두 라이선스 중 하나를 선택하십시오. OFL을 선택하면 수정된 글꼴에는 OFL을 계속 적용해야 하며, 글꼴만 따로 판매할 수 없습니다. 현재 공식 Unifont 릴리스에는 예약 글꼴 이름(Reserved Font Name)이 지정되어 있지 않으므로 이름을 변경할 필요가 없습니다.',
      'GPL을 선택하면 수정된 글꼴에는 선택한 GPL 버전을 계속 적용하고 상응하는 소스 코드를 제공해야 하지만, 글꼴만 따로 판매할 수 있습니다. 애플리케이션에 직접 임베드하면 배포 시 그 애플리케이션에도 GPL을 적용해야 할 수 있습니다. OFL을 선택하면 애플리케이션을 사유 라이선스로 유지할 수 있습니다.',
    ],
  },
  "GPL-2.0-with-font-exception": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'cond', 'no', 'no', 'yes'),
    body: [
      'Font Exception(글꼴 예외 조항)에 따라 문서에 글꼴을 임베드해도 해당 문서에 GPL을 적용할 필요가 없습니다. 수정된 글꼴을 배포할 때는 여전히 GPL 2를 적용하고 상응하는 소스 코드를 제공해야 합니다.',
      '글꼴 수정자는 Font Exception을 삭제할 수 있으며, 이 조항이 애플리케이션에 직접 임베드하는 경우까지 적용되는지는 명확하지 않습니다. 수정본의 라이선스를 확인하십시오.',
    ],
  },
  "GPL-2.0-only": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      '상업적 이용과 비공개 수정이 허용됩니다. 배포되는 복제물과 파생물에는 GPL 2를 계속 적용해야 하며, 고지와 변경 사항을 포함하고 상응하는 소스 코드를 제공하거나 라이선스가 허용하는 서면 소스 코드 제공 제안을 해야 합니다.',
      '상응하는 소스 코드는 BDF, SFD, UFO 또는 HEX 파일처럼 수정할 때 주로 사용하는 형식이어야 하며, 필요한 빌드 스크립트도 포함해야 합니다. 생성된 TTF 또는 PCF 파일만으로는 충분하지 않을 수 있습니다. 별도로 묶어 배포하는 것은 관련 없는 소프트웨어에 영향을 주지 않지만, 임베드하면 배포 시 GPL 의무가 발생할 수 있습니다.',
    ],
  },
  "GPL-2.0-or-later": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      '상업적 이용과 비공개 수정이 허용됩니다. 배포되는 복제물과 파생물은 GPL 2 또는 그 이후 버전을 따라야 하며, 필수 고지와 상응하는 소스 코드를 포함해야 합니다.',
      '별도로 묶어 배포하는 것은 관련 없는 소프트웨어에 영향을 주지 않지만, 글꼴이 임베드된 문서나 애플리케이션을 배포하면 GPL 의무가 발생할 수 있습니다.',
    ],
  },
  "CC-BY-SA-4.0": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      '상업적 이용, 수정, 임베딩 및 재배포가 허용됩니다. 공유할 때는 저작자 표시와 라이선스 링크를 제공하고 변경 사항을 표시해야 하며, 변형물에는 동일하거나 호환되는 라이선스를 적용해야 합니다.',
      '글꼴 임베딩을 위한 별도 예외 조항이 없으므로 문서나 애플리케이션의 라이선스에 미치는 영향은 적용되는 법률에 따라 달라질 수 있습니다. 이 라이선스에는 특허권과 상표권이 포함되지 않습니다.',
    ],
  },
};

export const SUMMARIES_FR: Record<string, LicenseSummary> = {
  "CC0-1.0": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      'La police peut être utilisée, modifiée, incorporée et redistribuée à des fins commerciales, sans autorisation ni attribution. Le titulaire renonce au droit d’auteur dans toute la mesure permise par la loi, mais les droits de brevet et de marque ne sont pas inclus.',
    ],
  },
  "LicenseRef-PublicDomain": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      'En règle générale, aucune restriction ne s’applique, mais le domaine public est un statut juridique et non une licence standard. La validité de ce statut peut varier selon la source et le droit applicable ; des droits de marque ou des droits moraux peuvent subsister.',
    ],
  },
  "LicenseRef-Mplus": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      'L’utilisation commerciale, la modification, l’incorporation et la redistribution sont autorisées sans exigence d’attribution, de copyleft ni de changement de nom. Les versions actuelles de M+ FONTS sont publiées sous OFL-1.1 ; vérifiez donc la licence fournie.',
    ],
  },
  "LicenseRef-Tamsyn": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      'L’utilisation commerciale, la modification, l’incorporation et la redistribution sont autorisées sans exigence d’attribution, de copyleft ni de changement de nom. La police est fournie sans garantie.',
    ],
  },
  "WTFPL": {
    tier: 'permissive-max',
    flags: F('yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'),
    body: [
      'Cette licence n’impose presque aucune restriction à l’utilisation commerciale, à la modification, à la redistribution ou au placement sous une autre licence. Elle ne comporte ni clause explicite d’exclusion de garantie ni octroi de droits de brevet.',
    ],
  },
  "MIT": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      'L’utilisation commerciale, la modification, l’incorporation, la concession de sous-licences et la redistribution sont autorisées. Les copies ou parties substantielles doivent conserver les mentions de droit d’auteur et d’autorisation.',
    ],
  },
  "BSD-2-Clause": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      'L’utilisation commerciale, la modification, l’incorporation et la redistribution sont autorisées. Conservez la mention de droit d’auteur, les conditions de la licence et la clause de non-responsabilité ; pour les distributions sous forme binaire, ces éléments peuvent figurer dans la documentation d’accompagnement.',
    ],
  },
  "MirOS": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      'L’utilisation commerciale, la modification, l’incorporation, la vente, la concession de sous-licences et la redistribution sont autorisées. Conservez les mentions de droit d’auteur, les conditions de la licence et la clause de non-responsabilité.',
    ],
  },
  "HPND": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      'L’utilisation, la modification, l’incorporation et la redistribution sont généralement libres à condition de conserver les mentions requises. Certaines variantes exigent également de faire figurer ces mentions dans la documentation d’accompagnement ou restreignent l’utilisation du nom du titulaire du droit d’auteur à des fins promotionnelles.',
    ],
  },
  "LicenseRef-ISAS-1988": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      'L’utilisation commerciale et la revente sont autorisées. La mention « sans frais » signifie que l’autorisation est accordée sans redevance de licence, et non que les copies doivent être gratuites. Conservez les mentions et n’utilisez pas le nom de l’institut pour promouvoir la distribution sans autorisation écrite.',
    ],
  },
  "LicenseRef-Baekmuk": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'yes'),
    body: [
      'L’utilisation commerciale, la modification, l’incorporation et la redistribution sont autorisées à condition de conserver les mentions. La documentation d’accompagnement doit faire état des marques déposées des polices Baekmuk.',
    ],
  },
  "LicenseRef-UW-ttyp0": {
    tier: 'permissive',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'yes', 'cond'),
    body: [
      'L’utilisation commerciale, la modification, l’incorporation, la vente et la redistribution sont autorisées à condition de conserver les mentions. Toute modification ou tout ajout de glyphes impose un nouveau nom. Les modifications limitées aux métadonnées et le reconditionnement n’en imposent pas. Le nouveau nom ne peut pas contenir « UW », et « ttyp0 » doit être précédé du nom d’une autre fonderie.',
    ],
  },
  "OFL-1.1": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'yes', 'no', 'no', 'cond'),
    body: [
      'Les polices peuvent être utilisées, incorporées, modifiées, regroupées et distribuées commercialement, mais elles ne peuvent pas être vendues seules. Les polices redistribuées et les polices dérivées restent sous l’OFL.',
      'Si des noms de police réservés (« Reserved Font Names ») sont déclarés, les versions modifiées doivent porter des noms différents. Les conversions de format et les reconstructions qui modifient la police sont également considérées comme des modifications. Les documents et applications utilisant la police ne sont pas soumis à l’OFL.',
    ],
  },
  "OFL-1.1 OR GPL-2.0-with-font-exception": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'cond', 'no', 'no', 'yes'),
    body: [
      'Vous pouvez choisir l’une ou l’autre licence. Sous l’OFL, les polices modifiées restent sous l’OFL et ne peuvent pas être vendues seules. La version officielle actuelle d’Unifont ne déclare aucun nom de police réservé ; aucun changement de nom n’est donc requis.',
      'Sous la GPL, les polices modifiées restent soumises à la version de la GPL choisie et leur source correspondante doit être mise à disposition, mais la vente séparée est autorisée. L’intégration directe dans une application peut obliger à distribuer celle-ci sous la GPL ; choisir l’OFL permet de la maintenir sous licence propriétaire.',
    ],
  },
  "GPL-2.0-with-font-exception": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'yes', 'cond', 'no', 'no', 'yes'),
    body: [
      'La Font Exception (exception relative aux polices) permet l’intégration dans un document sans que celui-ci soit soumis à la GPL. Lorsqu’elles sont distribuées, les polices modifiées restent soumises à la GPL 2 et leur source correspondante doit être mise à disposition.',
      'Les personnes qui modifient la police peuvent supprimer l’exception, qui ne couvre pas clairement l’intégration directe dans une application. Vérifiez la licence des versions modifiées.',
    ],
  },
  "GPL-2.0-only": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      'L’utilisation commerciale et la modification à titre privé sont autorisées. Les copies et les dérivés distribués restent sous la GPL 2 et doivent inclure les mentions requises et les informations sur les modifications, ainsi que le code source correspondant ou, lorsque la licence le permet, une offre écrite de le fournir.',
      'La source doit être la forme privilégiée pour apporter des modifications, par exemple des fichiers BDF, SFD, UFO ou HEX, accompagnés des scripts de compilation nécessaires. Des fichiers TTF ou PCF générés peuvent ne pas suffire à eux seuls. Le simple regroupement dans une même distribution n’a pas d’incidence sur les logiciels sans lien avec la police, mais l’intégration peut entraîner des obligations au titre de la GPL lors de la distribution.',
    ],
  },
  "GPL-2.0-or-later": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      'L’utilisation commerciale et la modification à titre privé sont autorisées. Les copies et les dérivés distribués doivent respecter les dispositions de la GPL 2 ou d’une version ultérieure de la GPL et inclure les mentions requises ainsi que le code source correspondant.',
      'Le simple regroupement dans une même distribution n’a pas d’incidence sur les logiciels sans lien avec la police, mais la distribution d’un document ou d’une application intégrant la police peut entraîner des obligations au titre de la GPL.',
    ],
  },
  "CC-BY-SA-4.0": {
    tier: 'copyleft',
    flags: F('yes', 'yes', 'cond', 'cond', 'no', 'no', 'yes'),
    body: [
      'L’utilisation commerciale, la modification, l’incorporation et la redistribution sont autorisées. En cas de partage, créditez l’œuvre, fournissez un lien vers la licence et signalez les modifications ; les adaptations doivent être placées sous la même licence ou une licence compatible.',
      'Il n’existe aucune exception propre à l’intégration de polices ; son effet sur la licence d’un document ou d’une application peut donc dépendre du droit applicable. Les droits de brevet et de marque ne sont pas inclus.',
    ],
  },
};
