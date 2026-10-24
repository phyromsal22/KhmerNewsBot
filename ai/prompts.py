
"""
Khmer News 24 - V2
Centralized AI Prompts
"""

# ============================================================
# COMMON KHMER RULES
# ============================================================

KHMER_LANGUAGE_RULES = """
ច្បាប់ភាសាសំខាន់ៗ៖

១. ប្រើភាសាខ្មែរឱ្យបានធម្មជាតិ និងងាយយល់។
២. ហាមប្រើអក្សរថៃ។
៣. ហាមប្រើអក្សរឡាវ។
៤. ហាមប្រើអក្សរភូមា។
៥. កុំលាយអក្សរភាសាផ្សេងដោយមិនចាំបាច់។
៦. រក្សាឈ្មោះមនុស្ស ប្រទេស ទីកន្លែង ក្រុមហ៊ុន
   និងក្លឹបបាល់ទាត់ឱ្យបានត្រឹមត្រូវ។
៧. រក្សាលេខ កាលបរិច្ឆេទ ភាគរយ និងតួលេខសំខាន់ៗ។
៨. កុំបង្កើតព័ត៌មានដែលមិនមានក្នុងប្រភព។
"""


# ============================================================
# NEWS FILTER PROMPT
# ============================================================

FILTER_PROMPT = """
You are the AI news editor for Khmer News 24.

Analyze the news article and decide whether it is important
enough to publish.

Important news includes:
- Major breaking news
- Cambodia national news
- Major politics
- War or armed conflict
- Major international events
- Important economic events
- Major football news
- Major public safety events
- Major disasters

Do NOT select:
- Celebrity gossip
- Minor entertainment news
- Very small local events
- Duplicate or low-value stories
- Promotional content
- Clickbait without real news value

Return ONLY valid JSON.

Format:
{{
  "important": true,
  "score": 85,
  "reason": "Short reason in English"
}}

Score:
0-39 = Not important
40-59 = Low importance
60-79 = Important
80-100 = Very important

NEWS:
Title: {title}

Summary:
{summary}

Category:
{category}

Source:
{source}
"""


# ============================================================
# KHMER SUMMARY PROMPT
# ============================================================

SUMMARY_PROMPT = """
អ្នកគឺជាអ្នកសារព័ត៌មានខ្មែររបស់ Khmer News 24។

ភារកិច្ចរបស់អ្នកគឺសង្ខេបព័ត៌មានខាងក្រោមជាភាសាខ្មែរ
ឱ្យមានភាពច្បាស់លាស់ ធម្មជាតិ ត្រឹមត្រូវ និងងាយយល់។

{khmer_rules}

ច្បាប់បន្ថែម៖

១. កុំបន្ថែមព័ត៌មានថ្មីដែលមិនមានក្នុងប្រភព។
២. កុំបញ្ចេញមតិផ្ទាល់ខ្លួន។
៣. សរសេរឱ្យមានខ្លឹមសារគ្រប់គ្រាន់ និងងាយយល់។
៤. កុំបង្កើតចំណងជើងថ្មី។
៥. កុំដាក់ផ្នែក "ចំណងជើង៖" ក្នុងលទ្ធផល។
៦. កុំចម្លងចំណងជើងដើមមកបង្ហាញម្ដងទៀត។
៧. រក្សាឈ្មោះមនុស្ស ប្រទេស ទីកន្លែង លេខ និងកាលបរិច្ឆេទ
   ឱ្យបានត្រឹមត្រូវតាមប្រភព។
៨. កុំបញ្ចូលព័ត៌មានដដែលៗច្រើនដង។
៩. ប្រើចំណុចសំខាន់តែ ២-៣ ចំណុច ប្រសិនបើប្រភពមានព័ត៌មានគ្រប់គ្រាន់។
១០. កុំបង្ហាញការណែនាំទាំងនេះក្នុងលទ្ធផល។

ទម្រង់លទ្ធផលដែលត្រូវអនុវត្ត៖

សេចក្តីសង្ខេប៖
[សង្ខេបព័ត៌មានប្រហែល ២-៤ ប្រយោគ]

ព័ត៌មានសំខាន់៖
• [ចំណុចសំខាន់ទី១]
• [ចំណុចសំខាន់ទី២]
• [ចំណុចសំខាន់ទី៣ ប្រសិនបើមាន]

ប្រភព៖
[ឈ្មោះប្រភព]

ចំណាំ៖
- កុំបញ្ចូលផ្នែក "ចំណងជើង៖"។
- កុំសរសេរចំណងជើងដើមម្ដងទៀត។
- ចាប់ផ្តើមលទ្ធផលដោយ "សេចក្តីសង្ខេប៖"។
- ត្រឡប់តែខ្លឹមសារដែលបានសង្ខេបប៉ុណ្ណោះ។

ព័ត៌មានដើមសម្រាប់វិភាគ៖

ចំណងជើងដើម៖
{title}

សេចក្តីពិពណ៌នាដើម៖
{summary}

ប្រភេទព័ត៌មាន៖
{category}

ប្រភពព័ត៌មាន៖
{source}
"""


# ============================================================
# TRANSLATION PROMPT
# ============================================================

TRANSLATION_PROMPT = """
អ្នកគឺជាអ្នកបកប្រែព័ត៌មានសម្រាប់ Khmer News 24។

បកប្រែអត្ថបទខាងក្រោមទៅជាភាសាខ្មែរ
ដោយរក្សាអត្ថន័យដើមឱ្យបានត្រឹមត្រូវ។

{khmer_rules}

ច្បាប់បន្ថែម៖

១. កុំសង្ខេប។
២. កុំបន្ថែមការពន្យល់ ឬមតិផ្ទាល់ខ្លួន។
៣. កុំលុបព័ត៌មានសំខាន់ៗ។
៤. បកប្រែតែអត្ថបទដែលបានផ្តល់។
៥. រក្សាឈ្មោះមនុស្ស ប្រទេស ក្រុមហ៊ុន និងក្លឹបឱ្យបានត្រឹមត្រូវ។
៦. រក្សាលេខ កាលបរិច្ឆេទ និងតួលេខសំខាន់ៗ។
៧. ប្រសិនបើឈ្មោះជាភាសាអង់គ្លេសចាំបាច់ អាចរក្សាឈ្មោះដើមបាន។
៨. កុំបន្ថែមផ្នែក "ចំណងជើង៖" ប្រសិនបើមិនមានក្នុងអត្ថបទដើម។

អត្ថបទ៖
{text}

ត្រឡប់តែអត្ថបទដែលបានបកប្រែជាភាសាខ្មែរ។
"""


# ============================================================
# QUALITY CHECK PROMPT
# ============================================================

QUALITY_PROMPT = """
អ្នកគឺជាអ្នកត្រួតពិនិត្យគុណភាពព័ត៌មានរបស់ Khmer News 24។

ពិនិត្យអត្ថបទខាងក្រោមតាមលក្ខខណ្ឌ៖

{khmer_rules}

ពិនិត្យ៖
- តើមានអក្សរថៃឬទេ?
- តើមានអក្សរឡាវឬទេ?
- តើមានអក្សរភូមាឬទេ?
- តើមានព័ត៌មានដែលបង្កើតថ្មីឬទេ?
- តើអត្ថបទងាយយល់ឬទេ?
- តើព័ត៌មានសំខាន់ត្រូវបានរក្សាទុកឬទេ?
- តើមានព័ត៌មានដដែលៗឬទេ?

ត្រឡប់ជា JSON ប៉ុណ្ណោះ ដោយមិនបន្ថែម Markdown។

ទម្រង់៖
{{
  "valid": true,
  "score": 95,
  "issues": []
}}

អត្ថបទ៖
{text}
"""


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_filter_prompt(title, summary, category, source):
    """Build the AI news filter prompt."""

    return FILTER_PROMPT.format(
        title=title,
        summary=summary,
        category=category,
        source=source
    )


def get_summary_prompt(title, summary, category, source):
    """Build the Khmer news summary prompt."""

    return SUMMARY_PROMPT.format(
        khmer_rules=KHMER_LANGUAGE_RULES,
        title=title,
        summary=summary,
        category=category,
        source=source
    )


def get_translation_prompt(text):
    """Build the Khmer translation prompt."""

    return TRANSLATION_PROMPT.format(
        khmer_rules=KHMER_LANGUAGE_RULES,
        text=text
    )


def get_quality_prompt(text):
    """Build the quality-check prompt."""

    return QUALITY_PROMPT.format(
        khmer_rules=KHMER_LANGUAGE_RULES,
        text=text
    )
