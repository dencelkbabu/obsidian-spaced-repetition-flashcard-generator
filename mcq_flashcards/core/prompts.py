"""Prompt templates for MCQ generation.

This module contains all the prompt templates, persona definitions,
and instruction sets used by the FlashcardGenerator.
"""

# Persona Definitions
PERSONAS = {
    "ACCT": ("Strict Accounting Professor", "Focus on precise accounting standards (IFRS/GAAP). Distinguish clearly between Bookkeeping and Accounting."),
    "COMM": ("Communication Expert", "Focus on business etiquette, theory, and precise terminology."),
    "MATH": ("Mathematics Professor", "Focus on logic, formulas, and absolute precision."),
    "ECON": ("Economics Professor", "Focus on micro/macro theories and standard economic definitions."),
    "DEFAULT": ("University Professor", "Focus on academic accuracy.")
}

# Bloom's Taxonomy Instructions
BLOOM_INSTRUCTIONS = {
    "remember": "COGNITIVE LEVEL: REMEMBER - Focus on RECALL and RECOGNITION. Ask about facts, terms, basic concepts, and definitions that can be directly retrieved from the text.",
    "understand": "COGNITIVE LEVEL: UNDERSTAND - Focus on COMPREHENSION. Ask students to explain, summarize, interpret, or describe concepts in their own words.",
    "apply": "COGNITIVE LEVEL: APPLY - Focus on APPLICATION. Ask students to use concepts, theories, or procedures in new situations or practical scenarios.",
    "analyze": "COGNITIVE LEVEL: ANALYZE - Focus on ANALYSIS. Ask students to compare, contrast, categorize, or examine relationships between concepts.",
    "evaluate": "COGNITIVE LEVEL: EVALUATE - Focus on EVALUATION. Ask students to judge, critique, assess, or justify decisions based on criteria.",
    "create": "COGNITIVE LEVEL: CREATE - Focus on CREATION. Ask students to design, construct, formulate, or propose new solutions or approaches."
}

# Difficulty Level Instructions
DIFFICULTY_INSTRUCTIONS = {
    "easy": "DIFFICULTY: EASY - Use straightforward scenarios with common cases. Distractors should be clearly wrong to someone who studied. Focus on basic application of concepts.",
    "medium": "DIFFICULTY: MEDIUM - Use realistic scenarios typical of exams. Distractors should be plausible but distinguishable with proper understanding. Standard exam difficulty.",
    "hard": "DIFFICULTY: HARD - Use complex scenarios with edge cases. Distractors should be very plausible, requiring deep understanding to eliminate. Include tricky elements and subtle distinctions."
}

# System Prompt Template
SYSTEM_PROMPT_TEMPLATE = """You are an expert university-level tutor specializing in {persona}.
Your goal is to create high-quality, exam-style multiple-choice questions (MCQs) that test deep understanding, critical thinking, and application of concepts.

{focus}

You must output ONLY valid Markdown.
"""

# Main Generation Prompt Template
GENERATION_PROMPT_TEMPLATE = """
CONTEXT:
{context}

INSTRUCTIONS:
Create {num_questions} multiple-choice questions based on the above context.

{bloom_instruction}
{difficulty_instruction}

STRICT FORMATTING RULES:
1. Output MUST be in valid Markdown.
2. Each question must follow this EXACT format:

 [Your question here]?
1. Option 1
2. Option 2
3. Option 3
4. Option 4
?
**Answer:** 2) Option 2 Text
> **Explanation:** Short explanation of why this is the correct answer.

3. Do NOT include any conversational text (e.g., "Here are the questions").
4. Ensure there is a blank line between questions.
5. The separator '?' must be on its own line before the answer.
6. The answer line must start with "**Answer:**".
7. The explanation line must start with "> **Explanation:**".
"""

# Refine Prompt Template
REFINE_PROMPT_TEMPLATE = """
The previous output did not match the required MCQ format. 
Please REFORMAT the following content to match the exact format required.

CONTENT TO FIX:
{content}

REQUIRED FORMAT:
Question?
1. Opt1
2. Opt2
3. Opt3
4. Opt4
?
**Answer:** 1) Answer
> **Explanation:** Text

Ensure:
1. Exactly 4 options numbered 1-4.
2. Question mark '?' on its own line before the answer.
3. **Answer:** line with the correct option number and text.
4. **Explanation:** blockquote.
"""
