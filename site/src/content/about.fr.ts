/** Texte français de la page À propos, traduit depuis about.zh.ts. */

import type { AboutSection } from './about.zh';

export const aboutIntro =
  '« Polices bitmap (pixel) libres et open source » rassemble des polices bitmap open source dispersées en un même cabinet de spécimens : chaque glyphe est analysé, mesuré selon une norme commune et recensé dans les différents jeux de caractères, avec des aperçus où vous pouvez saisir votre propre texte. Les polices appartiennent à leurs auteurs respectifs ; ce site ne fait que les cataloguer et les présenter.';

export const aboutSections: AboutSection[] = [
  {
    id: 'criteria',
    heading: 'Critères d’inclusion',
    paragraphs: [
      'Seules les polices sous licence libre sont retenues, selon des critères stricts : la licence doit autoriser explicitement chacun à utiliser, copier, modifier et redistribuer la police, usage commercial compris, et couvrir de façon vérifiable le fichier précis catalogué ici. « Gratuit », « gratuit pour usage commercial », « freeware », la seule copie autorisée ou la promesse de « passer plus tard en open source » ne suffisent pas. Toutes les polices du site peuvent donc être utilisées commercialement en toute confiance.',
      'Les polices assorties de conditions rédigées sur mesure (« déclaration de l’auteur ») sont rarement retenues. Ce qui compte n’est pas le nom de ces conditions mais leur conformité aux définitions admises du logiciel libre et des polices libres : chacun peut utiliser, étudier, modifier et redistribuer à toute fin ; aucune restriction ne tient à l’usage ni à l’utilisateur ; l’autorisation est irrévocable et se transmet aux dérivés. Qu’il en manque une seule et la police est consignée dans le rapport d’import, pas au catalogue.',
      'La collection ne se limite à aucune écriture : fontes CJK et latines y ont toute leur place. Les formats bitmap se convertissent entre eux sans perte — BDF, PCF, OTB, kbitx — et sont donc traités sur un pied d’égalité. Ce qui compte, c’est de savoir si la fonte est bien un bitmap : lorsqu’un auteur ne publie qu’une police de contours pixelisés vectoriels (TTF/OTF), elle est rastérisée sur sa grille de pixels d’origine, signalée comme « Convertie » sur la page et accompagnée d’une explication de la conversion.',
      'La page détaillée de chaque police indique sa provenance. Si vous repérez une inclusion erronée ou souhaitez faire retirer une police, ouvrez une issue dans le dépôt.',
    ],
  },
  {
    id: 'metrics',
    heading: 'Méthode de mesure',
    paragraphs: [
      'La taille nominale vient de la déclaration de la police (PIXEL_SIZE, SIZE ou FONTBOUNDINGBOX) et correspond à la hauteur de sa grille de conception en pixels.',
      'L’emprise des sinogrammes est mesurée à partir des pixels réellement allumés. La compilation prend les caractères de niveau 1 de la Table des caractères chinois d’usage général que la police couvre, ou tous les idéogrammes unifiés s’ils sont moins de 100. Elle calcule la boîte englobante des pixels allumés de chaque glyphe, puis indique la largeur et la hauteur médianes. Une police « 16px » dessine généralement ses sinogrammes sur 15×15 ou 14×15 ; cette mesure rend mieux compte de la taille visuelle de la fonte que sa taille nominale. Pour une police sans glyphe Han, la hauteur des capitales et la hauteur d’x sont indiquées à la place.',
      'L’emprise maximale est la plus grande zone allumée relevée parmi tous les glyphes. Les signes combinatoires et les glyphes très larges des zones à usage privé peuvent dépasser le cadre nominal ; c’est normal.',
    ],
  },
  {
    id: 'coverage',
    heading: 'Calcul de la couverture',
    paragraphs: [
      'La couverture est calculée par point de code : chaque point de code de la table d’encodage de la police compte une fois. Les dénominateurs proviennent de fichiers de jeux de caractères versionnés dans le dépôt. La source et la version figurent dans l’en-tête de chaque fichier et s’affichent au survol du nom du jeu.',
      'Pour les blocs Unicode, les dénominateurs utilisent les points de code assignés dans Unicode 17.0, en excluant les substituts et en incluant les zones à usage privé. Les chiffres peuvent donc différer légèrement de ceux des outils fondés sur une ancienne version d’Unicode.',
      'Les idéogrammes de compatibilité sont comptés à part ; douze de ces points de code sont en réalité, selon les annotations d’Unicode, des idéogrammes unifiés, ce que l’aperçu signale en note.',
      'Les trois niveaux de mise en œuvre de GB 18030-2022 sont construits à partir des définitions des sinogrammes et des radicaux du chapitre 9 de la norme, soit 27,584 / 27,780 / 88,115 caractères. Le raisonnement et les extraits cités se trouvent dans docs/research/ dans le dépôt.',
    ],
  },
  {
    id: 'rendering',
    heading: 'Rendu des aperçus',
    paragraphs: [
      'Chaque aperçu est dessiné pixel par pixel sur un canvas du navigateur. Chaque point reste un carré net et rien ne passe par le moteur de rastérisation des polices du système d’exploitation. Le résultat est donc identique sur toutes les plateformes et montre la police telle qu’elle est réellement.',
      'La mise en page aligne simplement les glyphes de gauche à droite, sans façonnage, crénage ni écriture verticale. Les caractères absents sont signalés par des cadres pointillés sur fond rougeâtre.',
    ],
  },
  {
    id: 'contribute',
    heading: 'Ajouter une police',
    paragraphs: [
      'Placez les fichiers BDF ou PCF (éventuellement compressés en .gz) dans un nouveau répertoire sous fonts/, puis lancez la compilation. Un fichier family.toml dans ce répertoire permet d’ajouter les informations saisies à la main. Il reste facultatif : sans lui, la famille est tout de même compilée et porte la mention « Non vérifiée » sur le site.',
    ],
    code: `fonts/my-font/
  my-font-16.bdf
  OFL.txt
  family.toml    # facultatif, par exemple :

name = "My Font"
name_zh = "我的字体"
authors = ["Nom de l’auteur"]
homepage = "https://example.com"
description = "Description en une ligne"
form = "gothic"          # catégorie : gothic|mingcho|rounded|kai|fangsong|…
vibes = ["retro-game"]   # tags d’ambiance, saisie libre
aliases = ["Ancien nom"] # optionnel : anciens noms / alias, pour la recherche seule`,
  },
  {
    id: 'disclaimer',
    heading: 'Avertissement',
    paragraphs: [
      'Les informations de licence sont détectées automatiquement par l’outil de compilation ou saisies à la main et sont fournies à titre indicatif. Seul le texte de licence publié en amont par l’auteur régit réellement la police. Vérifiez-le vous-même avant tout usage commercial.',
      'L’inclusion ne se juge ici qu’au regard de la licence de droit d’auteur. Certains noms de fontes contiennent des marques déposées de tiers (IBM VGA, Adobe Helvetica…) : c’est un emploi nominatif, qui indique d’où viennent les glyphes. Elles sont cataloguées sous leur vrai nom, sans approbation ni affiliation des titulaires de marques.',
      'Les sources tierces et les licences des données de jeux de caractères figurent dans le fichier THIRD_PARTY_NOTICES.md du dépôt.',
    ],
  },
];

export const aboutDataSourcesHeading = 'Sources des jeux de caractères';
export const aboutDataSourcesIntro =
  'Les jeux de caractères ci-dessous servent au calcul de la couverture et leur source est indiquée. Les références complètes et les licences se trouvent dans le dépôt.';
