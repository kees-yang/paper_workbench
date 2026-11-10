# Rule reference · 规则一览

The rules of the `default` pack, generated with `python -m paper_workbench rules markdown`. *Default* shows whether a rule is on out of the box.
Stages S1–S6 are the stages of the rule tree (read top-down). **Scope** is the unit the rule reads; **Method** says who decides:
`auto` the checker decides, `partial` the checker flags and the author decides, `manual` a person checks (the rule appears on the report's checklist).

`default` 规则包的全部规则，由 `python -m paper_workbench rules markdown` 生成。*Default* 表示开箱是否启用。S1–S6 是规则树的层（自上而下读）。
**Scope** 是规则读取的单位；**Method** 说明由谁判断：`auto` 由检查器判定，`partial` 检查器标出、作者判断，`manual` 由人检查（出现在报告的核对清单里）。

| ID | Stage | Scope | Method | Default | Rule | 规则 |
|---|---|---|---|---|---|---|
| B1 | S1 | document | auto | on | Every cited key exists in the bibliography. | 每个被引用的键都在参考文献库中。 |
| B8 | S1 | document | auto | on | Every bibliography entry is cited. | 参考文献库中的每个条目都被引用。 |
| B9 | S1 | document | auto | on | No duplicate keys in the bibliography. | 参考文献库中没有重复的键。 |
| B7 | S1 | document | auto | on | Bibliography entries are complete: required fields present, full author lists; optional: given names as initials. | 参考文献条目完整：必备字段齐全、作者列表完整；可选：名用首字母。 |
| B4 | S1 | document | auto | off | Bibliography entries carry no DOI or URL (venue style). | 参考文献条目不含DOI与URL（视期刊格式）。 |
| A3 | S1 | sentence | auto | on | The text uses the glossary term, not the old name or alias (glossary field avoid_en). | 全文使用术语表中的主术语，不用旧名与别名（术语表字段avoid_en）。 |
| W1 | S2 | document | manual | on | The abstract states, in order: the state of the field, the gap, the motivation, the method, the results. | 摘要按顺序写：研究现状、不足、动机、方法、结果。 |
| E6 | S2 | document | auto | off | The abstract carries at most a few numbers (document.json: E6.max_numbers). | 摘要只写少数几个数字（document.json：E6.max_numbers）。 |
| E7 | S2 | document | manual | off | Each number in the abstract has a role: one shows the overall ability of the method and one shows a specific ability, each stated as a lead over the runner-up. | 摘要中的每个数字都有角色：一个说明方法的整体能力，一个说明某项具体能力，均写成相对第二名的领先幅度。 |
| W20 | S2 | document | auto | off | The abstract states what the paper does in one sentence (“We propose …”), lists the mechanisms as First/Second/Third, and states what the method provides in one sentence (document.json: W20). | 摘要用一句说明本文做什么（“We propose …”），机制按First/Second/Third分层列出，再用一句说明方法的作用（document.json：W20）。 |
| W4 | S2 | document | manual | on | The conclusion echoes the abstract and adds no new claim. | 结论回扣摘要，不引入新的主张。 |
| W6 | S2 | sentence | partial | on | A comparative or superiority claim is traced to a table, a figure or a citation (the checker flags; the author decides). | 比较性或优势性表述须有依据：表、图或引用（自动标出，作者判断）。 |
| W2 | S3 | document | manual | on | In the introduction the problem and the motivation each have their own paragraph, both before the method. | 引言中“问题”与“动机”各成一段，均在“方法”段之前。 |
| F2 | S3 | sentence | auto | on | No sentence is printed twice. | 同一句话不出现两次。 |
| W21 | S3 | paragraph | partial | off | Old before new: a sentence links to the one before it by a shared word, a word that points back (this, these, such, it), a connective or a continued subject (the checker flags a sentence with none of them; the author decides). | 旧信息在前：每句通过共有的词、回指词（this、these、such、it）、连接词或延续的主语与上一句相连（检查器标出四者皆无的句子，作者判断）。 |
| O2 | S3 | document | manual | on | The discussion answers the research question and does not list limitations item by item. | 讨论回答研究问题，不逐条罗列局限。 |
| O3 | S3 | sentence | partial | off | The body stands alone: no body sentence points to the supplement or the appendix (the checker flags; the author decides). | 正文自成一体：正文句子不指向补充材料或附录（自动标出，作者判断）。 |
| W14 | S4 | sentence | partial | on | One main action per sentence: at most two finite clauses (a main clause plus one complete supporting clause), no clause nested in a subordinate clause, no “which” that refers to a whole clause. Flagged sentences are rewritten or kept with a written reason. | 一句一个主要动作：至多两个限定小句（主句加一个完整从句），不嵌套从句，不用指代整句的which；标出的句子改写，或写明理由后保留。 |
| W15 | S4 | sentence | auto | on | Complete clauses: no participle phrase set off by a comma (“…, thereby joining …”) and no verbless adjective clause (“…, possible because …”). | 完整从句：不用逗号后的分词短语（“…, thereby joining …”）或无动词的形容词从句（“…, possible because …”）。 |
| W16 | S4 | sentence | auto | on | Qualifiers first: no prepositional qualifier appended after the last comma of a sentence. | 限定成分在前：不在句末逗号后追加介词短语。 |
| W11 | S4 | sentence | auto | on | A real condition or time clause (if, unless, only when, when, before, after, until, once) comes before the action. | 真实的条件与时间从句（if、unless、only when、when、before、after、until、once）放在动作之前。 |
| W23 | S4 | sentence | auto | off | A sentence has at most a set number of words (tone.json: W23.max_words; captions excepted). | 每句不超过设定的词数（tone.json：W23.max_words；图注、表题除外）。 |
| W10 | S4 | sentence | auto | on | Active voice: body sentences have no passive (captions excepted); an adjectival use is an exception with a written reason. | 主动语态：正文句不用被动（图注除外）；形容词用法逐句写明理由后作为例外。 |
| W12 | S4 | sentence | auto | on | “We” only where the authors are the actor (proposing the method, stating contributions); otherwise the item is the subject. | 少用“we”：作者是施事时（提出方法、贡献）才用，其余以事物作主语。 |
| W7 | S4 | sentence | partial | on | No filler: no sentence without information (signposts, restatements, display or processing disclaimers). Restatement needs a reading. | 不写空话：无信息的路标句、重述句、显示或处理说明（重述靠通读）。 |
| W8 | S4 | sentence | auto | on | No self-criticism outside the discussion or limitation sections (project setting limitation_sections). | 讨论与局限章节以外不写自我限定或自我批评（项目设置limitation_sections）。 |
| W9 | S4 | sentence | auto | on | No sentence implies that an experiment that could have been run is missing. | 不写暗示缺少本可做的实验的句子。 |
| W22 | S4 | sentence | partial | off | Affirmative wording: no pre-emptive concession that answers an imagined objection (“we do not claim”, “admittedly”, “merely”, “serves only as”). State the fact, or state the convention with its source (the checker flags; the author decides). | 肯定式表述：不写预先让步、回应假想质疑的句子（“we do not claim”“admittedly”“merely”“serves only as”）。直接陈述事实，或陈述惯例并给出出处（自动标出，作者判断）。 |
| W13 | S4 | paragraph | partial | on | Consequence connectives (therefore, thus, so, thereby) mark only a real consequence: at most one per sentence, no repeat in a paragraph, not in two consecutive sentences, not before “we propose”. The premise is checked by hand. | 结果连接词（therefore、thus、so、thereby）只标真实的结果：每句至多一个、同段不重复、不连续两句、不用于“we propose”之前；前提逐句人工核对。 |
| A6 | S4 | sentence | auto | off | The head noun of every subject and object comes from the glossary or from the closed noun lists; otherwise use a pronoun. | 主语、宾语的中心名词取自术语表或闭合名词清单，否则用代词。 |
| A7 | S4 | sentence | auto | on | One thing keeps one head noun: concept rules list phrases that name a glossary concept with another noun. | 同一事物同一中心名词：概念规则列出用别的名词指称术语表概念的短语。 |
| M1 | S4 | sentence | manual | on | Plain words and direct verbs; no decoration with elevated words; necessary terms stay. | 用常见词和直接动词，不用高级词装饰；必要术语保留。 |
| M2 | S4 | sentence | manual | on | While, whereas, instead, unlike mark a real parallel, contrast or replacement, never a cause. | while、whereas、instead、unlike只用于真实的并行、对照或替代关系，不代替因果。 |
| J1 | S5 | document | auto | off | The abstract length is within the venue limit (document.json: J1.min, J1.max). | 摘要字数在期刊限制内（document.json：J1.min、J1.max）。 |
| J2 | S5 | document | auto | on | The abstract contains no citation. | 摘要不含引用。 |
| J3 | S5 | document | auto | off | The number of keywords is within the venue limit (document.json: J3). | 关键词数量在期刊限制内（document.json：J3）。 |
| T5 | S5 | sentence | auto | off | Running text refers to figures as “Fig. N” (not “Figure N” inside a sentence). | 正文用“Fig. N”引用图（句中不写“Figure N”）。 |
| T1 | S5 | document | auto | on | Figures, tables and algorithms are numbered in the order of their first citation (checked on the source). | 图、表与算法各自按首次引用的顺序编号（按源文件核查）。 |
| T2 | S5 | document | auto | on | A text citation comes before the figure or table it cites, and every figure and table is cited. A float placed above its citation on purpose is accepted in exceptions.json by its label. | 正文引用先于对应的图表出现，且每个图表都被引用。有意排在引用之上的图表在exceptions.json中按标签登记为例外。 |
| T10 | S5 | document | auto | off | The proposed method is not the first row of a table; comparison tables list it last (document.json: T10.method). | 本文方法不放在表格第一行；对比表把它列在最后（document.json：T10.method）。 |
| B2 | S5 | document | auto | on | Every \ref, \eqref, \autoref and \cref points to an existing \label. | 每个\ref、\eqref、\autoref、\cref都指向存在的\label。 |
| T9 | S5 | document | manual | on | Captions are short: only what is needed to read the figure; the mechanism belongs in the text. | 图注、表题简短：只写看图所需，机制放正文。 |
| T11 | S5 | document | auto | off | Every caption has a set number of words (document.json: T11.min, T11.max). | 每条图注、表题的词数在设定范围内（document.json：T11.min、T11.max）。 |
| T12 | S5 | document | auto | off | In the compiled PDF, a figure, table or algorithm sits on the page of its first text citation or at most T12.pages_after pages later, never before it (document.json; needs the PDF and PyMuPDF). | 在编译出的PDF中，图、表、算法位于正文首次引用所在页或其后至多T12.pages_after页，不早于引用（document.json；需要PDF与PyMuPDF）。 |
| T13 | S5 | document | manual | off | A figure of chosen cases says in a few words how the cases were chosen, and it shows a phenomenon; it does not present a named method as worse. | 展示所选案例的图用几个词说明案例如何选出，并只展示现象，不把某个具名方法呈现为更差。 |
| M5 | S5 | document | manual | on | Text inside raster images and screenshots is readable at the final column width (G3 measures vector text only). | 位图与截图中的文字在最终栏宽下可读（G3只测量矢量文字）。 |
| G1 | S5 | figure | auto | on | Figure files are print-ready: every file exists, PDF figures embed their fonts and use no Type 3 fonts, raster images have at least 300 dpi at the printed width (document.json: figures.min_dpi). | 图件文件可直接印刷：文件都存在，PDF图件嵌入字体、不含Type 3字体，位图在印刷宽度下至少300 dpi（document.json：figures.min_dpi）。 |
| G2 | S5 | figure | auto | on | Figure text uses the body font family; math may use math fonts (document.json: figures.body_font). | 图内文字用正文字族；数学符号可用数学字体（document.json：figures.body_font）。 |
| G3 | S5 | figure | auto | on | Figure text is readable at the printed size: the main text prints within figures.main_pt (default 8–10 pt) and nothing prints below figures.min_pt (default 6 pt, subscripts included). | 图内文字在印刷尺寸下可读：主字号印刷后在figures.main_pt之内（默认8–10 pt），任何文字不小于figures.min_pt（默认6 pt，含下标）。 |
| G4 | S5 | figure | partial | on | Lines survive printing: no stroke prints thinner than figures.min_line_pt (default 0.4 pt); connectors about 1 pt, frames one step heavier, only grid lines thinner. | 线条印刷后仍清楚：线宽不低于figures.min_line_pt（默认0.4 pt）；连接线约1 pt，模块与面板框重一级，只有网格线更细。 |
| G5 | S5 | figure | manual | on | All figures share one visual language: the same font family and label style, the same line weights, and fixed colour roles (each modality, state or signal keeps one colour in every figure); the proposed method keeps one highlight colour everywhere, named in the captions. | 全部图件用同一种视觉语言：同一字族与标签样式、同样的线宽、固定的颜色角色（每个模态、状态或信号在各图中颜色不变）；本文方法在所有图中用同一强调色，并在图注中写明颜色。 |
| G6 | S5 | figure | manual | on | Lines carry meaning: data flow as solid arrows, parameters as dashed lines, zoom or expansion links as thin dashed lines without arrowheads; arrowheads are visible, scale with the line and land on box edges; no line crosses a label or panel title. | 线条有含义：数据流用实线箭头，参数用虚线，放大或展开的关联用无箭头的细虚线；箭头清楚、与线宽成比例并落在框的边缘；线条不穿过标签与面板标题。 |
| G7 | S5 | figure | manual | on | Framework figures show modules, symbols and data labels only: no explanatory small grey text and no formulas inside the figure; explanations go to the caption, exact operations to the equations in the text, and icons stand for actions. | 框架图只放模块、符号与数据标签：图内不写灰色解释小字、不写公式；解释写进图注，精确运算写在正文公式里，用图标表示动作。 |
| G8 | S5 | figure | manual | on | Boxes are sized to their content and every label sits inside its box without overlap; repeated modules use the same shape and icon, and an expanded view uses the same name and icon as its compact form. | 方框按内容定尺寸，每个标签都在框内且互不重叠；重复的模块用同一形状与图标，展开图与其缩略形式用同一名称与图标。 |
| G9 | S5 | figure | manual | on | Images within one panel group are all real or all schematic; real images come from registered result files (never generated pixels shown as results); plots are drawn from frozen data files, and marker areas encode the plotted values. | 同一面板组内的图像要么全是真实图像、要么全是示意；真实图像取自登记的结果文件（不得把生成的像素当作结果）；数据图由冻结的数据文件绘制，标记面积按所绘数值编码。 |
| R0 | S6 | document | auto | on | Every rule is in the register exactly once and sits in the rule tree. | 每条规则都在规则登记中且只出现一次，并位于规则树中。 |
| R1 | S6 | document | auto | on | Every testable rule flags its “flag” sentences and passes its “pass” sentences. | 每条可测试的规则都标出它的“flag”测试句、放过它的“pass”测试句。 |
