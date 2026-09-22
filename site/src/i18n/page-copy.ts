import type { Lang } from './types';

/** Small page-specific strings, safe to use in browser islands without OpenCC. */
export const pageCopy: Record<Lang, { about: string; compare: string; footer: string; top: string; bottom: string }> = {
  en: {
    about: 'How FontPixel selects freely licensed pixel fonts, measures glyphs, reports character coverage, and documents licenses and sources.',
    compare: 'Compare open-source pixel fonts side by side. Type your own text and adjust font variants, zoom, and preview styles.',
    footer: 'Footer navigation', top: 'Top', bottom: 'Bottom',
  },
  zh: {
    about: '了解 FontPixel 开源像素字体馆的收录标准、字体许可证、字形度量、字符覆盖率计算方法与数据来源。',
    compare: '并排比较自由开源像素字体，输入自定义文字，切换字体变体、缩放比例和预览样式。',
    footer: '页脚导航', top: '顶部', bottom: '底部',
  },
  'zh-Hant': {
    about: '了解 FontPixel 開源像素字型館的收錄標準、字型授權、字形度量、字元覆蓋率計算方法與資料來源。',
    compare: '並排比較自由開源像素字型，輸入自訂文字，切換字型變體、縮放比例和預覽樣式。',
    footer: '頁尾導覽', top: '頂部', bottom: '底部',
  },
  ja: {
    about: 'FontPixel の自由なライセンスのピクセルフォントの収録基準、字形の計測方法、文字カバレッジ、ライセンスと出典を紹介します。',
    compare: 'オープンソースのピクセルフォントを並べて比較。好きな文字を入力し、バリアント、拡大率、プレビューの表示を調整できます。',
    footer: 'フッターナビゲーション', top: '上部', bottom: '下部',
  },
  ko: {
    about: 'FontPixel의 자유 라이선스 픽셀 글꼴 수록 기준, 글리프 측정 방법, 문자 지원 범위, 라이선스와 출처를 알아보세요.',
    compare: '오픈 소스 픽셀 글꼴을 나란히 비교하세요. 원하는 문자를 입력하고 글꼴 변형, 확대 비율, 미리보기 스타일을 조절할 수 있습니다.',
    footer: '바닥글 탐색', top: '상단', bottom: '하단',
  },
  fr: {
    about: 'Découvrez les critères de sélection de FontPixel, les mesures des glyphes, la couverture des caractères, les licences et les sources des polices pixel.',
    compare: 'Comparez des polices pixel libres côte à côte. Saisissez votre texte et ajustez les variantes, le zoom et le style des aperçus.',
    footer: 'Navigation de pied de page', top: 'Haut', bottom: 'Bas',
  },
};
