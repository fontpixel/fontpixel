/** Visual styles, separate from measured sizes and supported writing systems. */
const labels: Record<string, [string, string, string, string, string]> = {
  'retro-computer': ['Retro computer', '复古电脑', 'レトロコンピュータ', '레트로 컴퓨터', 'Ordinateur rétro'],
  'game-ui': ['Game UI', '游戏界面', 'ゲーム UI', '게임 UI', 'Interface de jeu'],
  arcade: ['Arcade', '街机', 'アーケード', '아케이드', 'Arcade'],
  console: ['Console', '游戏主机', 'ゲーム機', '게임 콘솔', 'Console'],
  handheld: ['Handheld', '掌机', '携帯ゲーム機', '휴대용 게임기', 'Console portable'],
  'nintendo-ds': ['Nintendo DS', 'Nintendo DS', 'ニンテンドー DS', '닌텐도 DS', 'Nintendo DS'],
  jrpg: ['JRPG', '日式角色扮演', 'JRPG', 'JRPG', 'JRPG'],
  'western-rpg': ['Western RPG', '西式角色扮演', '西洋 RPG', '서양 RPG', 'RPG occidental'],
  dos: ['DOS', 'DOS', 'DOS', 'DOS', 'DOS'],
  bios: ['BIOS', 'BIOS', 'BIOS', 'BIOS', 'BIOS'],
  cga: ['CGA', 'CGA', 'CGA', 'CGA', 'CGA'],
  ega: ['EGA', 'EGA', 'EGA', 'EGA', 'EGA'],
  vga: ['VGA', 'VGA', 'VGA', 'VGA', 'VGA'],
  microcomputer: ['Microcomputer', '早期微型电脑', 'マイコン', '마이크로컴퓨터', 'Micro-ordinateur'],
  demoscene: ['Demoscene', '演示场景文化', 'デモシーン', '데모씬', 'Demoscene'],
  terminal: ['Terminal', '终端', '端末', '터미널', 'Terminal'],
  unix: ['Unix / X11', 'Unix / X11', 'Unix / X11', 'Unix / X11', 'Unix / X11'],
  programming: ['Programming', '编程', 'プログラミング', '프로그래밍', 'Programmation'],
  technical: ['Technical', '技术界面', '技術的', '기술 인터페이스', 'Technique'],
  industrial: ['Industrial', '工业', '工業的', '산업', 'Industriel'],
  'sci-fi': ['Science fiction', '科幻', 'SF', '공상 과학', 'Science-fiction'],
  'retro-futuristic': ['Retro-futuristic', '复古未来', 'レトロフューチャー', '레트로 퓨처', 'Rétrofuturiste'],
  vhs: ['VHS / VCR', 'VHS / 录像机', 'VHS / ビデオ', 'VHS / 비디오', 'VHS / magnétoscope'],
  'crt-osd': ['CRT on-screen display', 'CRT 屏幕显示', 'CRT 画面表示', 'CRT 화면 표시', 'Affichage à tube cathodique'],
  'dot-matrix': ['Dot matrix', '点阵显示', 'ドットマトリクス', '도트 매트릭스', 'Matrice de points'],
  blackletter: ['Blackletter', '哥特黑体', 'ブラックレター', '블랙레터', 'Écriture gothique'],
  textura: ['Textura', 'Textura 织体', 'テクストゥーラ', '텍스투라', 'Textura'],
  bastarda: ['Bastarda', 'Bastarda 混合体', 'バスタルダ', '바스타르다', 'Bâtarde'],
  uncial: ['Uncial', '安色尔体', 'アンシャル', '언셜', 'Onciale'],
  manuscript: ['Manuscript', '手稿', '写本', '필사본', 'Manuscrit'],
  vyaz: ['Vyaz', '斯拉夫编织书体', 'ヴャジ', '뱌지', 'Vyaz'],
  'web-pixel': ['Early web pixel', '早期网页像素', '初期ウェブ', '초기 웹 픽셀', 'Pixel du Web ancien'],
  serif: ['Serif', '衬线', 'セリフ', '세리프', 'Avec empattements'],
  'slab-serif': ['Slab serif', '板状衬线', 'スラブセリフ', '슬랩 세리프', 'Empattements rectangulaires'],
  book: ['Book typography', '书籍排印', '書籍組版', '책 조판', 'Typographie de livre'],
  typewriter: ['Typewriter', '打字机', 'タイプライター', '타자기', 'Machine à écrire'],
  elegant: ['Elegant', '优雅', '優雅', '우아함', 'Élégant'],
  'art-nouveau': ['Art Nouveau', '新艺术', 'アール・ヌーヴォー', '아르누보', 'Art nouveau'],
  constructivist: ['Constructivist', '构成主义', '構成主義', '구성주의', 'Constructivisme'],
  grunge: ['Grunge', '粗粝破损', 'グランジ', '그런지', 'Grunge'],
  handwriting: ['Handwriting', '手写', '手書き', '손글씨', 'Manuscrit à main levée'],
  cursive: ['Cursive', '连笔', '筆記体', '흘림체', 'Cursive'],
  crooked: ['Crooked', '歪斜', 'ゆがみ', '비뚤어진 글자', 'Irrégulier'],
  rounded: ['Rounded', '圆润', '丸み', '둥근 글자', 'Arrondi'],
  block: ['Block', '块状', 'ブロック', '블록', 'Massif'],
  outline: ['Outline', '轮廓', 'アウトライン', '윤곽선', 'Contour'],
  shadow: ['Shadow', '阴影', '影', '그림자', 'Ombre'],
  '3d': ['Three-dimensional', '立体', '立体', '입체', 'Relief'],
  textile: ['Textile / embroidery', '织物与刺绣', '織物・刺繍', '직물 / 자수', 'Textile / broderie'],
  symbols: ['Icons / ornaments', '图标与纹饰', 'アイコン・装飾', '아이콘 / 장식', 'Icônes / ornements'],
  sports: ['Sports lettering', '运动字样', 'スポーツ', '스포츠', 'Lettrage sportif'],
  micro: ['Micro', '微型', '極小', '초소형', 'Miniature'],
  experimental: ['Experimental', '实验', '実験的', '실험적', 'Expérimental'],
  cute: ['Cute', '可爱', 'かわいい', '귀여움', 'Mignon'],
  fallback: ['Unicode fallback', 'Unicode 后备', 'Unicode フォールバック', '유니코드 대체', 'Police de secours Unicode'],
  // Retain labels for older links and uncurated third-party catalogues.
  classic: ['Classic', '经典', 'クラシック', '클래식', 'Classique'],
  decorative: ['Decorative', '装饰', '装飾', '장식', 'Décoratif'],
  'retro-game': ['Retro game', '复古游戏', 'レトロゲーム', '레트로 게임', 'Jeu rétro'],
  'terminal-hardcore': ['Terminal / hardcore', '硬核终端', '端末', '터미널', 'Terminal'],
};

export const VIBE_GROUPS = [
  { id: 'computers', names: ['Computers & games', '电脑与游戏', 'コンピュータ・ゲーム', '컴퓨터와 게임', 'Ordinateurs et jeux'], tags: ['retro-computer', 'dos', 'bios', 'cga', 'ega', 'vga', 'microcomputer', 'demoscene', 'web-pixel', 'game-ui', 'arcade', 'console', 'handheld', 'nintendo-ds', 'jrpg', 'western-rpg', 'retro-game'] },
  { id: 'technical', names: ['Terminals & displays', '终端与显示设备', '端末・表示装置', '터미널과 디스플레이', 'Terminaux et affichages'], tags: ['terminal', 'unix', 'programming', 'technical', 'industrial', 'sci-fi', 'retro-futuristic', 'vhs', 'crt-osd', 'dot-matrix', 'terminal-hardcore', 'fallback'] },
  { id: 'print', names: ['Print & manuscripts', '印刷与手稿', '印刷・写本', '인쇄와 필사본', 'Imprimés et manuscrits'], tags: ['blackletter', 'textura', 'bastarda', 'uncial', 'manuscript', 'vyaz', 'serif', 'slab-serif', 'book', 'typewriter', 'elegant', 'classic'] },
  { id: 'expressive', names: ['Art & handwriting', '艺术与手写', '芸術・手書き', '예술과 손글씨', 'Art et écriture'], tags: ['art-nouveau', 'constructivist', 'grunge', 'handwriting', 'cursive', 'crooked', 'textile', 'sports', 'experimental'] },
  { id: 'shapes', names: ['Shapes & ornaments', '造型与纹饰', '形・装飾', '모양과 장식', 'Formes et ornements'], tags: ['rounded', 'block', 'outline', 'shadow', '3d', 'symbols', 'micro', 'cute', 'decorative'] },
];

const languageIndex = (lang: string) => ({ en: 0, zh: 1, 'zh-Hant': 1, ja: 2, ko: 3, fr: 4 }[lang] ?? 0);
export const vibeNames = (lang: string): Record<string, string> =>
  Object.fromEntries(Object.entries(labels).map(([key, values]) => [key, values[languageIndex(lang)]]));
export const vibeGroupName = (group: typeof VIBE_GROUPS[number], lang: string): string => {
  if (lang === 'zh-Hant') return { computers: '電腦與遊戲', technical: '終端與顯示設備', print: '印刷與手稿', expressive: '藝術與手寫', shapes: '造型與紋飾' }[group.id] ?? group.names[1];
  return group.names[languageIndex(lang)];
};
