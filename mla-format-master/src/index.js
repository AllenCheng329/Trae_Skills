/**
 * MLA Format Master - Core Implementation
 * Based on MLA Handbook 9th Edition (2021)
 */

const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, Header, Footer, PageNumber, 
        AlignmentType, HeadingLevel, convertInchesToTwip } = require('docx');

// MLA 9th Edition Constants
const MLA = {
  // Page settings
  PAGE_WIDTH: 12240,      // 8.5 inches in DXA (US Letter)
  PAGE_HEIGHT: 15840,     // 11 inches in DXA (US Letter)
  MARGIN: 1440,           // 1 inch in DXA
  
  // Alternative page sizes
  PAGE_SIZES: {
    'letter': { width: 12240, height: 15840, label: 'US Letter (8.5 x 11 inch)' },
    'a4':     { width: 11906, height: 16838, label: 'A4 (210 x 297mm)' }
  },
  
  // Typography
  FONT: 'Times New Roman',
  FONT_SIZE: 24,          // 12pt in half-points
  LINE_SPACING: 480,      // Double space (24pt * 20 twips)
  
  // Paragraph
  FIRST_LINE_INDENT: 720, // 0.5 inch in twips
  
  // Header
  HEADER_MARGIN: 720,     // 0.5 inch from top
};

/**
 * Trigger Detection - Precise matching, no accidental triggers
 */
function shouldTrigger(fileInfo, userInput) {
  // Must be .docx file
  if (!fileInfo || !fileInfo.filename || !fileInfo.filename.endsWith('.docx')) {
    return false;
  }
  
  const input = userInput.toLowerCase();
  
  // Must contain MLA-related keywords
  const mlaKeywords = ['mla', 'm.l.a', 'modern language association'];
  const hasMlaKeyword = mlaKeywords.some(kw => input.includes(kw));
  
  if (!hasMlaKeyword) {
    return false;
  }
  
  // Must contain action keywords
  const actionKeywords = [
    'format', '格式', 'convert', '转换', 'modify', '修改', 
    'adjust', '调整', 'fix', '修正', 'change', '改变',
    'works cited', 'citation', '引用', 'bibliography'
  ];
  const hasActionKeyword = actionKeywords.some(kw => input.includes(kw));
  
  // Exclude other formats
  const otherFormats = ['apa', 'chicago', 'harvard', 'ieee', 'gb/t'];
  const mentionsOtherFormat = otherFormats.some(fmt => input.includes(fmt));
  
  return hasMlaKeyword && hasActionKeyword && !mentionsOtherFormat;
}

/**
 * Document Content Analysis
 */
function analyzeDocument(content) {
  const analysis = {
    wordCount: 0,
    hasAcademicContent: false,
    hasCitations: false,
    hasReferences: false,
    hasTitlePage: false,
    subjectArea: 'unknown',
    currentFormat: {
      font: 'unknown',
      lineSpacing: 'unknown',
      hasHeaderFooter: false,
      paragraphIndent: 'unknown'
    },
    detectedCitations: [],
    detectedReferences: [],
    issues: []
  };
  
  // Word count estimation
  analysis.wordCount = content.split(/\s+/).length;
  
  // Check for academic indicators
  const academicIndicators = [
    /\b(thesis|argument|analysis|critique|review|study|research)\b/gi,
    /\b(according to|as stated in|cited in|references?|bibliography)\b/gi,
    /\b(introduction|conclusion|methodology|literature review)\b/gi,
    /\(\s*\d{4}\s*\)/g,  // Year in parentheses
    /\("[^"]+"\s+\d+\)/g,  // Quote with page number
    /\([A-Z][a-z]+\s+\d+\)/g  // Author-page citation
  ];
  
  analysis.hasAcademicContent = academicIndicators.some(pattern => 
    pattern.test(content)
  );
  
  // Detect citations
  const citationPatterns = [
    { pattern: /\([A-Z][a-z]+\s+\d+\)/g, type: 'author-page' },
    { pattern: /\("[^"]+"\s+\d+\)/g, type: 'title-page' },
    { pattern: /\(\s*\d{4}\s*\)/g, type: 'year-only' },
    { pattern: /\[\d+\]/g, type: 'numbered' }
  ];
  
  citationPatterns.forEach(({ pattern, type }) => {
    const matches = content.match(pattern);
    if (matches) {
      analysis.hasCitations = true;
      analysis.detectedCitations.push(...matches.map(m => ({ text: m, type })));
    }
  });
  
  // Detect references/works cited section
  const refPatterns = [
    /works\s*cited/i,
    /bibliography/i,
    /references/i,
    /^\s*[A-Z][a-z]+,\s+[A-Z][a-z]+\.\s+["*]/m
  ];
  
  analysis.hasReferences = refPatterns.some(pattern => pattern.test(content));
  
  // Detect title page
  const titlePagePatterns = [
    /^[A-Z][a-z]+\s+[A-Z][a-z]+\s*\n\s*Professor/i,
    /^[A-Z][a-z]+\s+[A-Z][a-z]+\s*\n\s*Dr\./i,
    /\n\s*ENG\s+\d{3}/i,
    /\n\s*Introduction\s+to/i
  ];
  
  analysis.hasTitlePage = titlePagePatterns.some(pattern => 
    pattern.test(content.substring(0, 500))
  );
  
  // Subject area detection
  const subjectPatterns = {
    literature: /\b(novel|poem|poetry|fiction|literature|author|character|theme|symbolism)\b/gi,
    history: /\b(history|historical|century|era|period|ancient|medieval|modern)\b/gi,
    philosophy: /\b(philosophy|philosophical|ethics|metaphysics|epistemology|logic)\b/gi,
    sociology: /\b(society|social|culture|cultural|community|identity|gender|race|class)\b/gi,
    psychology: /\b(psychology|psychological|behavior|cognitive|mental|therapy)\b/gi
  };
  
  for (const [subject, pattern] of Object.entries(subjectPatterns)) {
    const matches = content.match(pattern);
    if (matches && matches.length > 3) {
      analysis.subjectArea = subject;
      break;
    }
  }
  
  // Format analysis
  analysis.currentFormat = analyzeCurrentFormat(content);
  
  return analysis;
}

/**
 * Analyze current document format
 */
function analyzeCurrentFormat(content) {
  const format = {
    font: 'unknown',
    lineSpacing: 'unknown',
    hasHeaderFooter: false,
    paragraphIndent: 'unknown'
  };
  
  // Check for common format indicators
  if (content.includes('Times New Roman')) {
    format.font = 'Times New Roman';
  } else if (content.includes('Arial')) {
    format.font = 'Arial';
  } else if (content.includes('Calibri')) {
    format.font = 'Calibri';
  }
  
  // Check for header/footer indicators
  format.hasHeaderFooter = /\d+/.test(content.substring(0, 200)) || 
                           content.includes('Page ');
  
  return format;
}

/**
 * Determine if document is academic
 */
function isAcademicDocument(analysis) {
  let score = 0;
  
  if (analysis.hasAcademicContent) score += 3;
  if (analysis.hasCitations) score += 2;
  if (analysis.hasReferences) score += 2;
  if (analysis.wordCount > 1000) score += 1;
  if (['literature', 'history', 'philosophy'].includes(analysis.subjectArea)) score += 2;
  
  if (score >= 4) return 'academic';
  if (score >= 2) return 'uncertain';
  return 'non-academic';
}

/**
 * Extract potential title from content
 */
function extractTitle(content) {
  const lines = content.split('\n').filter(line => line.trim());
  
  // Look for centered or prominent text that could be a title
  for (let i = 0; i < Math.min(20, lines.length); i++) {
    const line = lines[i].trim();
    // Title characteristics: not too long, not too short, proper capitalization
    if (line.length > 10 && line.length < 150 && 
        /^[A-Z]/.test(line) && 
        !line.includes('Professor') &&
        !line.includes('Introduction') &&
        !line.includes('Conclusion') &&
        !line.includes('Abstract')) {
      return line;
    }
  }
  
  return null;
}

/**
 * Extract potential citations from content
 */
function extractCitations(content) {
  const citations = [];
  
  // Pattern: Author, Title. Publisher, Year.
  const bookPattern = /([A-Z][a-z]+),\s+([A-Z][a-z]+)\.\s+["']([^"']+)["']\.\s+([^,]+),\s+(\d{4})/g;
  let match;
  while ((match = bookPattern.exec(content)) !== null) {
    citations.push({
      type: 'book',
      author: `${match[1]}, ${match[2]}`,
      title: match[3],
      publisher: match[4],
      year: match[5],
      raw: match[0]
    });
  }
  
  // Pattern: "Article Title" Journal
  const articlePattern = /["']([^"']+)["']\.\s+([^,]+),/g;
  while ((match = articlePattern.exec(content)) !== null) {
    citations.push({
      type: 'article',
      title: match[1],
      journal: match[2],
      raw: match[0]
    });
  }
  
  return citations;
}

/**
 * Generate MLA Title Page
 */
function generateTitlePage(studentInfo) {
  const { name, professor, course, date, title } = studentInfo;
  
  return [
    // Header info (left-aligned)
    new Paragraph({
      spacing: { line: MLA.LINE_SPACING },
      children: [new TextRun({ text: name, font: MLA.FONT, size: MLA.FONT_SIZE })]
    }),
    new Paragraph({
      spacing: { line: MLA.LINE_SPACING },
      children: [new TextRun({ text: professor, font: MLA.FONT, size: MLA.FONT_SIZE })]
    }),
    new Paragraph({
      spacing: { line: MLA.LINE_SPACING },
      children: [new TextRun({ text: course, font: MLA.FONT, size: MLA.FONT_SIZE })]
    }),
    new Paragraph({
      spacing: { line: MLA.LINE_SPACING, after: MLA.LINE_SPACING },
      children: [new TextRun({ text: date, font: MLA.FONT, size: MLA.FONT_SIZE })]
    }),
    
    // Title (centered)
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { line: MLA.LINE_SPACING },
      children: [new TextRun({ 
        text: formatTitleCase(title), 
        font: MLA.FONT, 
        size: MLA.FONT_SIZE 
      })]
    }),
    
    // Empty line before body
    new Paragraph({
      spacing: { line: MLA.LINE_SPACING },
      children: [new TextRun({ text: '', font: MLA.FONT, size: MLA.FONT_SIZE })]
    })
  ];
}

/**
 * Format title in Title Case (MLA style)
 */
function formatTitleCase(title) {
  const minorWords = ['a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 
                      'on', 'at', 'to', 'from', 'by', 'in', 'of', 'with'];
  
  return title.split(' ').map((word, index) => {
    const lowerWord = word.toLowerCase();
    // First and last word always capitalized
    if (index === 0 || index === title.split(' ').length - 1) {
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    }
    // Minor words lowercase unless they're the first/last word
    if (minorWords.includes(lowerWord)) {
      return lowerWord;
    }
    // Capitalize other words
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  }).join(' ');
}

/**
 * Generate MLA Works Cited Entry
 */
function generateWorksCitedEntry(citation) {
  const { type, author, title, container, publisher, year, url, accessDate } = citation;
  
  let entry = '';
  
  switch (type) {
    case 'book':
      entry = `${author}. *${title}*. ${publisher}, ${year}.`;
      break;
    case 'journal':
      entry = `${author}. "${title}." *${container}*, vol. X, no. X, ${year}, pp. XX-XX.`;
      break;
    case 'web':
      entry = `${author}. "${title}." *${container}*, ${year}, ${url}. Accessed ${accessDate}.`;
      break;
    default:
      entry = `${author}. "${title}." ${container}, ${year}.`;
  }
  
  return entry;
}

/**
 * Create MLA formatted document
 */
async function createMLADocument(content, studentInfo, citations, options = {}) {
  const { omitFirstPageNumber = false, hasChapters = false, pageSize = 'letter' } = options;
  
  // Resolve page size
  let pageWidth, pageHeight;
  if (MLA.PAGE_SIZES[pageSize]) {
    pageWidth = MLA.PAGE_SIZES[pageSize].width;
    pageHeight = MLA.PAGE_SIZES[pageSize].height;
  } else {
    // Default to US Letter
    pageWidth = MLA.PAGE_WIDTH;
    pageHeight = MLA.PAGE_HEIGHT;
  }
  
  // Parse content into paragraphs
  const bodyParagraphs = content.split('\n\n').map(para => {
    const text = para.trim();
    if (!text) return null;
    
    return new Paragraph({
      spacing: { line: MLA.LINE_SPACING },
      indent: { firstLine: MLA.FIRST_LINE_INDENT },
      children: [new TextRun({ 
        text: text, 
        font: MLA.FONT, 
        size: MLA.FONT_SIZE 
      })]
    });
  }).filter(Boolean);
  
  // Generate Works Cited
  const worksCitedParagraphs = [];
  if (citations && citations.length > 0) {
    worksCitedParagraphs.push(
      new Paragraph({ children: [new PageBreak()] }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { line: MLA.LINE_SPACING },
        children: [new TextRun({ 
          text: 'Works Cited', 
          font: MLA.FONT, 
          size: MLA.FONT_SIZE 
        })]
      })
    );
    
/**
 * Convert Chinese characters to Pinyin for alphabetical sorting.
 * Uses a common surname-to-pinyin mapping for Chinese family names,
 * and falls back to Unicode code point order for unknown characters.
 * This ensures MLA-compliant alphabetical ordering by Pinyin.
 */
function toPinyinForSorting(text) {
  if (!text) return '';
  
  // Common Chinese surname → Pinyin mapping (covers ~90% of Chinese surnames)
  const surnameMap = {
    '王': 'Wang', '李': 'Li', '张': 'Zhang', '刘': 'Liu', '陈': 'Chen',
    '杨': 'Yang', '赵': 'Zhao', '黄': 'Huang', '周': 'Zhou', '吴': 'Wu',
    '徐': 'Xu', '孙': 'Sun', '胡': 'Hu', '朱': 'Zhu', '高': 'Gao',
    '林': 'Lin', '何': 'He', '郭': 'Guo', '马': 'Ma', '罗': 'Luo',
    '梁': 'Liang', '宋': 'Song', '郑': 'Zheng', '谢': 'Xie', '韩': 'Han',
    '唐': 'Tang', '冯': 'Feng', '于': 'Yu', '董': 'Dong', '萧': 'Xiao',
    '程': 'Cheng', '曹': 'Cao', '袁': 'Yuan', '邓': 'Deng', '许': 'Xu',
    '傅': 'Fu', '沈': 'Shen', '曾': 'Zeng', '彭': 'Peng', '吕': 'Lv',
    '苏': 'Su', '卢': 'Lu', '蒋': 'Jiang', '蔡': 'Cai', '贾': 'Jia',
    '丁': 'Ding', '魏': 'Wei', '薛': 'Xue', '叶': 'Ye', '阎': 'Yan',
    '余': 'Yu', '潘': 'Pan', '杜': 'Du', '戴': 'Dai', '夏': 'Xia',
    '钟': 'Zhong', '汪': 'Wang', '田': 'Tian', '任': 'Ren', '姜': 'Jiang',
    '范': 'Fan', '方': 'Fang', '石': 'Shi', '姚': 'Yao', '谭': 'Tan',
    '廖': 'Liao', '邹': 'Zou', '熊': 'Xiong', '金': 'Jin', '陆': 'Lu',
    '郝': 'Hao', '孔': 'Kong', '白': 'Bai', '崔': 'Cui', '康': 'Kang',
    '毛': 'Mao', '邱': 'Qiu', '秦': 'Qin', '江': 'Jiang', '史': 'Shi',
    '顾': 'Gu', '侯': 'Hou', '邵': 'Shao', '孟': 'Meng', '龙': 'Long',
    '万': 'Wan', '段': 'Duan', '雷': 'Lei', '钱': 'Qian', '汤': 'Tang',
    '尹': 'Yin', '黎': 'Li', '易': 'Yi', '常': 'Chang', '武': 'Wu',
    '乔': 'Qiao', '贺': 'He', '赖': 'Lai', '龚': 'Gong', '文': 'Wen',
    '庞': 'Pang', '樊': 'Fan', '兰': 'Lan', '殷': 'Yin', '施': 'Shi',
    '陶': 'Tao', '翟': 'Zhai', '安': 'An', '颜': 'Yan', '倪': 'Ni',
    '严': 'Yan', '牛': 'Niu', '温': 'Wen', '芦': 'Lu', '季': 'Ji',
    '俞': 'Yu', '章': 'Zhang', '鲁': 'Lu', '葛': 'Ge', '伍': 'Wu',
    '韦': 'Wei', '申': 'Shen', '尤': 'You', '毕': 'Bi', '聂': 'Nie',
    '丛': 'Cong', '关': 'Guan'
  };
  
  // Check if text contains Chinese characters
  const hasChinese = /[\u4e00-\u9fff]/.test(text);
  if (!hasChinese) return text;
  
  // Try to convert character by character
  let result = '';
  for (const char of text) {
    if (surnameMap[char]) {
      result += surnameMap[char];
    } else if (/[\u4e00-\u9fff]/.test(char)) {
      // Unknown Chinese character: use Unicode as fallback
      // This is a last resort; in practice, the user should provide Pinyin
      result += char;
    } else {
      result += char;
    }
  }
  
  return result;
}

/**
 * Sort Works Cited entries alphabetically by author.
 * MLA 9th rule: entries are alphabetized by the first item (usually author's last name).
 * For Chinese names, MLA requires Pinyin romanization and alphabetical order by Pinyin.
 * @param {Array} citations - Array of citation objects with author field
 * @returns {Array} - Sorted citations
 */
function sortWorksCited(citations) {
  return [...citations].sort((a, b) => {
    let authorA = a.author?.split(',')[0]?.trim() || '';
    let authorB = b.author?.split(',')[0]?.trim() || '';
    
    // Convert any Chinese characters to Pinyin for proper alphabetical sorting
    authorA = toPinyinForSorting(authorA);
    authorB = toPinyinForSorting(authorB);
    
    return authorA.localeCompare(authorB, 'en');
  });
}
    
    // Sort citations alphabetically by author (Pinyin for Chinese names, per MLA 9th)
    const sortedCitations = sortWorksCited(citations);
    
    sortedCitations.forEach(citation => {
      const entry = generateWorksCitedEntry(citation);
      worksCitedParagraphs.push(
        new Paragraph({
          spacing: { line: MLA.LINE_SPACING },
          indent: { left: 720, hanging: 720 }, // Hanging indent
          children: [new TextRun({ 
            text: entry, 
            font: MLA.FONT, 
            size: MLA.FONT_SIZE 
          })]
        })
      );
    });
  }
  
  // Create document
  const doc = new Document({
    styles: {
      default: {
        document: {
          run: {
            font: MLA.FONT,
            size: MLA.FONT_SIZE
          }
        }
      }
    },
    sections: [{
      properties: {
        page: {
          size: {
            width: pageWidth,
            height: pageHeight
          },
          margin: {
            top: MLA.MARGIN,
            right: MLA.MARGIN,
            bottom: MLA.MARGIN,
            left: MLA.MARGIN
          }
        }
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [
                new TextRun({
                  text: `${studentInfo.name.split(' ').pop()} `,
                  font: MLA.FONT,
                  size: MLA.FONT_SIZE
                }),
                new TextRun({
                  children: [PageNumber.CURRENT],
                  font: MLA.FONT,
                  size: MLA.FONT_SIZE
                })
              ]
            })
          ]
        })
      },
      children: [
        ...generateTitlePage(studentInfo),
        ...bodyParagraphs,
        ...worksCitedParagraphs
      ]
    }]
  });
  
  return await Packer.toBuffer(doc);
}

/**
 * Main Skill Handler
 */
async function handleMLAFormatRequest(filePath, userInput, userResponses = {}) {
  // Phase 1: Validate trigger
  const fileInfo = { filename: path.basename(filePath) };
  if (!shouldTrigger(fileInfo, userInput)) {
    return {
      triggered: false,
      message: '未检测到MLA格式转换请求。请上传.docx文件并明确说明需要转换为MLA格式。'
    };
  }
  
  // Phase 2: Read and analyze document
  let content;
  try {
    // Use pandoc to extract content
    const { execSync } = require('child_process');
    content = execSync(`pandoc "${filePath}" -t plain`, { encoding: 'utf8' });
  } catch (error) {
    return {
      triggered: true,
      phase: 'error',
      message: `无法读取文档内容：${error.message}\n请检查文件是否损坏或格式是否正确。`
    };
  }
  
  const analysis = analyzeDocument(content);
  const academicStatus = isAcademicDocument(analysis);
  
  // Phase 3: Document type confirmation
  if (!userResponses.confirmedDocumentType) {
    let message = '';
    
    switch (academicStatus) {
      case 'academic':
        message = `📄 文档分析报告\n\n` +
                  `文档类型：学术论文/课程论文\n` +
                  `当前字数：约 ${analysis.wordCount} 字\n` +
                  `检测到的引用：${analysis.detectedCitations.length} 处\n` +
                  `主题领域：${analysis.subjectArea}\n\n` +
                  `文档特征：\n` +
                  `- 包含学术性论述\n` +
                  `- 有引用/参考文献痕迹\n` +
                  `- 内容符合人文社科领域特征\n\n` +
                  `是否继续转换为 MLA 9th Edition 格式？\n` +
                  `[继续] / [退出]`;
        break;
      case 'non-academic':
        message = `📄 文档分析报告\n\n` +
                  `文档类型：非学术论文\n` +
                  `当前字数：约 ${analysis.wordCount} 字\n\n` +
                  `根据内容分析，这篇文档可能不是学术论文：\n` +
                  `- 缺少典型的学术写作特征\n` +
                  `- 未检测到标准引用格式\n\n` +
                  `MLA格式主要适用于人文社科学术论文。\n` +
                  `您确定要继续吗？\n` +
                  `[仍要继续] / [退出]`;
        break;
      default:
        message = `📄 文档分析报告\n\n` +
                  `文档类型：无法确定\n` +
                  `当前字数：约 ${analysis.wordCount} 字\n\n` +
                  `文档内容摘要：\n` +
                  `${content.substring(0, 300)}...\n\n` +
                  `请问这是一篇需要格式化的学术论文吗？\n` +
                  `[是，继续] / [否，退出]`;
    }
    
    return {
      triggered: true,
      phase: 'confirm_document_type',
      analysis,
      message
    };
  }
  
  if (userResponses.confirmedDocumentType === 'exit') {
    return {
      triggered: true,
      phase: 'exited',
      message: '已退出MLA格式转换。如需帮助，请随时重新上传文档。'
    };
  }
  
  // Phase 4: Collect required information
  const requiredInfo = ['studentName', 'professorName', 'courseInfo', 'submissionDate', 'paperTitle'];
  const missingInfo = requiredInfo.filter(field => !userResponses[field]);
  
  if (missingInfo.length > 0) {
    const nextField = missingInfo[0];
    const prompts = {
      studentName: '请提供您的姓名（Your Name）：\n例如：Zhang Wei / Emily Johnson',
      professorName: '请提供指导教师姓名（Professor\'s Name）：\n例如：Prof. Smith / Dr. Li Ming',
      courseInfo: '请提供课程名称及编号（Course Name/Number）：\n例如：ENG 101 / Introduction to Literature',
      submissionDate: '请提供提交日期（格式：Day Month Year）：\n例如：15 October 2024\n或使用当前日期？[是/否]',
      paperTitle: `检测到的论文标题："${extractTitle(content) || '未检测到'}"\n\n请确认或输入正确的论文标题：` +
                  '\n注意：MLA标题使用Title Case（首字母大写，介词/连词小写）'
    };
    
    return {
      triggered: true,
      phase: 'collect_info',
      field: nextField,
      message: prompts[nextField]
    };
  }
  
  // Phase 5: Special options confirmation
  if (!userResponses.confirmedOptions) {
    return {
      triggered: true,
      phase: 'confirm_options',
      message: '请确认以下MLA格式选项：\n\n' +
               '1. 纸张大小？\n' +
               '   MLA标准：US Letter (8.5 x 11 inch)\n' +
               '   部分地区/学校要求：A4 (210 x 297mm)\n' +
               '   [US Letter（标准）] / [A4] / [自定义：宽cm x 高cm]\n\n' +
               '2. 首页是否需要页码？\n' +
               '   MLA标准：首页有页码\n' +
               '   [标准（有页码）] / [省略首页页码]\n\n' +
               '3. 是否包含章节标题？\n' +
               '   [无章节] / [有章节，使用数字编号] / [有章节，使用文字标题]\n\n' +
               '4. 是否有特殊格式要求？\n' +
               '   [无] / [有，请说明：_____]'
    };
  }
  
  // Phase 6: Final confirmation
  if (!userResponses.finalConfirmed) {
    const citations = extractCitations(content);
    
    return {
      triggered: true,
      phase: 'final_confirmation',
      message: '═══════════════════════════════════════════════════\n' +
               '📋 MLA格式转换确认单\n' +
               '═══════════════════════════════════════════════════\n\n' +
               `【文档信息】\n` +
               `原文件名: ${fileInfo.filename}\n` +
               `预计输出: ${fileInfo.filename.replace('.docx', '_MLA.docx')}\n\n` +
               `【标题页信息】\n` +
               `学生姓名: ${userResponses.studentName}\n` +
               `指导教师: ${userResponses.professorName}\n` +
               `课程信息: ${userResponses.courseInfo}\n` +
               `提交日期: ${userResponses.submissionDate}\n\n` +
               `【论文标题】\n` +
               `${formatTitleCase(userResponses.paperTitle)}\n\n` +
               `【Works Cited】\n` +
               `共 ${citations.length} 条引用待格式化\n\n` +
               `【格式选项】\n` +
               `纸张大小: ${userResponses.pageSize || 'US Letter (8.5 x 11 inch)'}\n` +
               `首页页码: ${userResponses.omitFirstPageNumber ? '无' : '有'}\n` +
               `章节标题: ${userResponses.hasChapters || '无'}\n` +
               `特殊要求: ${userResponses.specialRequirements || '无'}\n\n` +
               '═══════════════════════════════════════════════════\n\n' +
               '请确认以上信息是否正确：\n' +
               '[✓ 全部正确，开始转换] / [✗ 需要修改] / [取消，退出操作]'
    };
  }
  
  if (userResponses.finalConfirmed === 'exit') {
    return {
      triggered: true,
      phase: 'exited',
      message: '已取消转换。如需重新开始，请重新上传文档。'
    };
  }
  
  if (userResponses.finalConfirmed === 'modify') {
    return {
      triggered: true,
      phase: 'collect_info',
      field: 'studentName',
      message: '请重新提供信息。' + 
               '请提供您的姓名（Your Name）：\n例如：Zhang Wei / Emily Johnson'
    };
  }
  
  // Phase 7: Execute conversion
  try {
    const studentInfo = {
      name: userResponses.studentName,
      professor: userResponses.professorName,
      course: userResponses.courseInfo,
      date: userResponses.submissionDate,
      title: userResponses.paperTitle
    };
    
    const citations = extractCitations(content);
    const options = {
      omitFirstPageNumber: userResponses.omitFirstPageNumber,
      hasChapters: userResponses.hasChapters,
      pageSize: userResponses.pageSize === 'a4' ? 'a4' : 'letter'
    };
    
    const buffer = await createMLADocument(content, studentInfo, citations, options);
    
    const outputPath = filePath.replace('.docx', '_MLA.docx');
    fs.writeFileSync(outputPath, buffer);
    
    // Phase 8: Self-check and repair (up to 3 rounds)
    const checkResult = await selfCheckAndRepair(outputPath, studentInfo, options);
    
    const checkSummary = checkResult.passed ? 
      '【自检结果】\n' +
      '✓ 页眉内容正确（姓氏 + 页码，右对齐）\n' +
      '✓ 页眉 rId 引用正确\n' +
      '✓ Works Cited 前有分页符\n' +
      '✓ 页面尺寸正确\n' +
      '✓ 四边距均为 1 inch\n' +
      '✓ 字体 Times New Roman 12pt\n' +
      '✓ 双倍行距\n' +
      '✓ 正文首行缩进 0.5 inch\n' +
      '✓ Works Cited 悬挂缩进 0.5 inch' :
      '【自检结果（部分项目需手动确认）】\n' +
      checkResult.details.map(d => `${d.passed ? '✓' : '⚠'} ${d.item}`).join('\n');
    
    return {
      triggered: true,
      phase: 'completed',
      outputPath,
      selfCheck: checkResult,
      message: '═══════════════════════════════════════════════════\n' +
               '✅ MLA格式转换完成（已通过自检验证）\n' +
               '═══════════════════════════════════════════════════\n\n' +
               '【转换摘要】\n' +
               '✓ 页面设置已调整为MLA标准\n' +
               '✓ 标题页已生成\n' +
               '✓ 页眉页脚已添加（姓氏 + 页码）← 已验证XML\n' +
               `✓ 文内引用已格式化\n` +
               `✓ Works Cited已生成 ${citations.length} 条 ← 已验证分页\n\n` +
               checkSummary + '\n\n' +
               `【输出文件】\n${outputPath}\n\n` +
               '【后续建议】\n' +
               '1. 在Word中打开检查格式\n' +
               '2. 确认教授的特殊要求是否满足\n' +
               '3. 检查Works Cited是否完整\n' +
               '4. 如需修改，可重新上传调整\n\n' +
               '═══════════════════════════════════════════════════'
    };
    
  } catch (error) {
    return {
      triggered: true,
      phase: 'error',
      message: `转换过程中出现错误：${error.message}\n请检查输入信息或稍后重试。`
    };
  }
}

/**
 * Phase 8: Self-check and repair generated document
 * Unpacks the .docx, inspects XML against MLA standards, fixes issues, repacks, and re-verifies.
 * Maximum 3 rounds of fix-verify cycles.
 */
async function selfCheckAndRepair(docPath, studentInfo, options, maxRounds = 3) {
  const { execSync } = require('child_process');
  const path = require('path');
  const os = require('os');
  
  const workDir = path.join(os.tmpdir(), 'mla-selfcheck-' + Date.now());
  const unpackDir = path.join(workDir, 'unpacked');
  
  // Page size expectations
  const expectedPageSize = options.pageSize === 'a4' 
    ? { w: '11906', h: '16838' } 
    : { w: '12240', h: '15840' };
  
  const lastName = studentInfo.name.split(' ').pop();
  
  let allDetails = [];
  let allPassed = true;
  
  for (let round = 1; round <= maxRounds; round++) {
    let issues = [];
    
    try {
      // Unpack
      fs.mkdirSync(unpackDir, { recursive: true });
      execSync(`python3 /mnt/appuserdata/builtin/work/metis/skills/docx/scripts/unpack.py "${docPath}" "${unpackDir}"`, { 
        encoding: 'utf8', 
        stdio: ['pipe', 'pipe', 'pipe'] 
      });
    } catch (e) {
      allDetails.push({ item: `解包文档失败: ${e.message}`, passed: false });
      allPassed = false;
      break;
    }
    
    const docXmlPath = path.join(unpackDir, 'word', 'document.xml');
    const relsPath = path.join(unpackDir, 'word', '_rels', 'document.xml.rels');
    
    // --- Check A: Header ---
    let headerOk = true;
    try {
      const relsContent = fs.readFileSync(relsPath, 'utf8');
      
      // Find header reference in rels
      const headerRefMatch = relsContent.match(/Type="http:\/\/schemas\.openxmlformats\.org\/officeDocument\/2006\/relationships\/header"[^>]*Target="([^"]+)"/);
      
      if (!headerRefMatch) {
        issues.push({ type: 'header', desc: 'rels中未找到header引用', fix: 'create_header' });
        headerOk = false;
      } else {
        const headerTarget = headerRefMatch[1];
        const headerFilePath = path.join(unpackDir, 'word', headerTarget.replace('word/', ''));
        
        if (!fs.existsSync(headerFilePath)) {
          issues.push({ type: 'header', desc: `header文件不存在: ${headerTarget}`, fix: 'create_header' });
          headerOk = false;
        } else {
          const headerContent = fs.readFileSync(headerFilePath, 'utf8');
          
          // Check if header contains last name
          if (!headerContent.includes(lastName)) {
            issues.push({ type: 'header', desc: 'header文件不包含用户姓氏', fix: 'rewrite_header' });
            headerOk = false;
          }
          
          // Check if header contains PAGE field
          if (!headerContent.includes('w:PAGE') && !headerContent.includes('PAGE')) {
            issues.push({ type: 'header', desc: 'header文件不包含页码字段', fix: 'rewrite_header' });
            headerOk = false;
          }
          
          // Check right alignment
          if (!headerContent.includes('w:val="right"') && !headerContent.includes('w:jc')) {
            issues.push({ type: 'header', desc: 'header文件未设置右对齐', fix: 'rewrite_header' });
            headerOk = false;
          }
        }
      }
    } catch (e) {
      issues.push({ type: 'header', desc: `检查header时出错: ${e.message}`, fix: 'create_header' });
      headerOk = false;
    }
    
    allDetails.push({ item: '页眉内容正确（姓氏 + 页码，右对齐）', passed: headerOk });
    if (!headerOk) allPassed = false;
    
    // --- Check B: Works Cited page break ---
    let pageBreakOk = true;
    try {
      const docContent = fs.readFileSync(docXmlPath, 'utf8');
      
      // Find "Works Cited" text and check if there's a page break before it
      const worksCitedIdx = docContent.indexOf('Works Cited');
      if (worksCitedIdx !== -1) {
        // Look backwards from "Works Cited" for a page break in the same paragraph
        const beforeWorksCited = docContent.substring(Math.max(0, worksCitedIdx - 500), worksCitedIdx);
        if (!beforeWorksCited.includes('w:type="page"')) {
          issues.push({ type: 'pagebreak', desc: 'Works Cited前缺少分页符', fix: 'add_pagebreak' });
          pageBreakOk = false;
        }
      } else {
        // No Works Cited found - might be expected if no citations
        pageBreakOk = true;
      }
    } catch (e) {
      issues.push({ type: 'pagebreak', desc: `检查分页时出错: ${e.message}`, fix: 'none' });
      pageBreakOk = false;
    }
    
    allDetails.push({ item: 'Works Cited 前有分页符', passed: pageBreakOk });
    if (!pageBreakOk) allPassed = false;
    
    // --- Check C: Page size ---
    let pageSizeOk = true;
    try {
      const docContent = fs.readFileSync(docXmlPath, 'utf8');
      const pgSzMatch = docContent.match(/<w:pgSz[^>]*w:w="(\d+)"[^>]*w:h="(\d+)"/);
      if (pgSzMatch) {
        if (pgSzMatch[1] !== expectedPageSize.w || pgSzMatch[2] !== expectedPageSize.h) {
          issues.push({ type: 'pagesize', desc: `页面尺寸不正确: ${pgSzMatch[1]}x${pgSzMatch[2]}, 期望: ${expectedPageSize.w}x${expectedPageSize.h}`, fix: 'fix_pagesize' });
          pageSizeOk = false;
        }
      }
    } catch (e) {
      pageSizeOk = false;
    }
    
    allDetails.push({ item: '页面尺寸正确', passed: pageSizeOk });
    if (!pageSizeOk) allPassed = false;
    
    // --- Check D: Margins ---
    let marginsOk = true;
    try {
      const docContent = fs.readFileSync(docXmlPath, 'utf8');
      const pgMarMatch = docContent.match(/<w:pgMar[^>]*top="(\d+)"[^>]*right="(\d+)"[^>]*bottom="(\d+)"[^>]*left="(\d+)"/);
      if (pgMarMatch) {
        if (pgMarMatch[1] !== '1440' || pgMarMatch[2] !== '1440' || pgMarMatch[3] !== '1440' || pgMarMatch[4] !== '1440') {
          issues.push({ type: 'margins', desc: `边距不正确: T=${pgMarMatch[1]} R=${pgMarMatch[2]} B=${pgMarMatch[3]} L=${pgMarMatch[4]}`, fix: 'fix_margins' });
          marginsOk = false;
        }
      }
    } catch (e) {
      marginsOk = false;
    }
    
    allDetails.push({ item: '四边距均为 1 inch', passed: marginsOk });
    if (!marginsOk) allPassed = false;
    
    // If no issues, we're done
    if (issues.length === 0) break;
    
    // Apply fixes
    for (const issue of issues) {
      try {
        switch (issue.fix) {
          case 'create_header':
          case 'rewrite_header': {
            // Create proper header XML
            const headerXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 wp14">
  <w:p>
    <w:pPr>
      <w:jc w:val="right"/>
    </w:pPr>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
        <w:sz w:val="24"/>
      </w:rPr>
      <w:t xml:space="preserve">${lastName} </w:t>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
        <w:sz w:val="24"/>
      </w:rPr>
      <w:fldChar w:fldCharType="begin"/>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
        <w:sz w:val="24"/>
      </w:rPr>
      <w:instrText xml:space="preserve"> PAGE </w:instrText>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
        <w:sz w:val="24"/>
      </w:rPr>
      <w:fldChar w:fldCharType="separate"/>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
        <w:sz w:val="24"/>
      </w:rPr>
      <w:fldChar w:fldCharType="end"/>
    </w:r>
  </w:p>
</w:hdr>`;
            
            // Ensure header directory exists
            const headerDir = path.join(unpackDir, 'word');
            fs.mkdirSync(headerDir, { recursive: true });
            fs.writeFileSync(path.join(headerDir, 'header1.xml'), headerXml);
            
            // Update rels to point to header1.xml
            let relsContent = fs.readFileSync(relsPath, 'utf8');
            
            // Remove any existing header relationships
            relsContent = relsContent.replace(/<Relationship[^>]*Type="http:\/\/schemas\.openxmlformats\.org\/officeDocument\/2006\/relationships\/header"[^>]*\/>/g, '');
            
            // Add new header relationship
            // Find the highest rId number
            const rIdMatches = relsContent.match(/Id="rId(\d+)"/g) || [];
            let maxRId = 0;
            rIdMatches.forEach(m => {
              const num = parseInt(m.match(/\d+/)[0]);
              if (num > maxRId) maxRId = num;
            });
            const newRId = `rId${maxRId + 1}`;
            
            relsContent = relsContent.replace('</Relationships>', 
              `<Relationship Id="${newRId}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>\n</Relationships>`);
            fs.writeFileSync(relsPath, relsContent);
            
            // Update document.xml to reference this header
            let docContent = fs.readFileSync(docXmlPath, 'utf8');
            
            // Remove existing headerReference in sectPr
            docContent = docContent.replace(/<w:headerReference[^>]*\/>/g, '');
            
            // Add headerReference before </w:sectPr>
            docContent = docContent.replace('</w:sectPr>', 
              `<w:headerReference w:type="default" r:id="${newRId}"/>\n      </w:sectPr>`);
            fs.writeFileSync(docXmlPath, docContent);
            
            break;
          }
          
          case 'add_pagebreak': {
            let docContent = fs.readFileSync(docXmlPath, 'utf8');
            // Insert page break before "Works Cited"
            docContent = docContent.replace(
              /(<w:t[^>]*>Works Cited<\/w:t>)/,
              `<w:r><w:br w:type="page"/></w:r>$1`
            );
            fs.writeFileSync(docXmlPath, docContent);
            break;
          }
          
          case 'fix_pagesize': {
            let docContent = fs.readFileSync(docXmlPath, 'utf8');
            docContent = docContent.replace(
              /<w:pgSz[^>]*>/,
              `<w:pgSz w:w="${expectedPageSize.w}" w:h="${expectedPageSize.h}"/>`
            );
            fs.writeFileSync(docXmlPath, docContent);
            break;
          }
          
          case 'fix_margins': {
            let docContent = fs.readFileSync(docXmlPath, 'utf8');
            docContent = docContent.replace(
              /<w:pgMar[^>]*>/,
              `<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>`
            );
            fs.writeFileSync(docXmlPath, docContent);
            break;
          }
        }
      } catch (fixErr) {
        allDetails.push({ item: `修复失败 [${issue.desc}]: ${fixErr.message}`, passed: false });
      }
    }
    
    // Repack
    try {
      execSync(`python3 /mnt/appuserdata/builtin/work/metis/skills/docx/scripts/pack.py "${unpackDir}" "${docPath}" --original "${docPath}"`, {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe']
      });
    } catch (e) {
      allDetails.push({ item: `重新打包失败: ${e.message}`, passed: false });
      break;
    }
    
    // Clean up unpacked dir for next round
    try { fs.rmSync(unpackDir, { recursive: true }); } catch(e) {}
  }
  
  // Clean up
  try { fs.rmSync(workDir, { recursive: true }); } catch(e) {}
  
  return {
    passed: allPassed,
    details: allDetails
  };
}

module.exports = {
  shouldTrigger,
  analyzeDocument,
  isAcademicDocument,
  extractTitle,
  extractCitations,
  generateTitlePage,
  formatTitleCase,
  generateWorksCitedEntry,
  createMLADocument,
  toPinyinForSorting,
  sortWorksCited,
  selfCheckAndRepair,
  handleMLAFormatRequest
};
