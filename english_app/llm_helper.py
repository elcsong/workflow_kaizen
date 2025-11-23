import os
import google.generativeai as genai
from openai import OpenAI
from anthropic import Anthropic

# Model Map (Friendly Name -> API Model ID)
MODELS = {
    "Gemini": {
        "Gemini 2.5 Pro": "gemini-2.5-pro",
        "Gemini 2.5 Flash": "gemini-2.5-flash",
    },
    "OpenAI": {
        "GPT-5.1": "gpt-5.1-2025-11-13",
        "GPT-5 mini": "gpt-5-mini-2025-08-07",
    },
    "Anthropic": {
        "Claude 4.5 Sonnet": "claude-sonnet-4-5",
        "Claude 4.5 Haiku": "claude-haiku-4-5",
    }
}

def get_ai_explanation(text, provider, model_name, context=None):
    """
    Get grammar explanation from the selected AI provider.
    """
    context_prompt = ""
    if context:
        context_prompt = f"""
## 📖 Context (Transcript)
The following is the transcript of the video where the sentence appears. 
Use this context to provide a more accurate interpretation of the meaning and nuance.

<transcript>
{context[:5000]}... (truncated if too long)
</transcript>
"""

    system_prompt = f"""
You are a Senior Linguistic Analysis Agent, powered by GPT-5. Your primary role is the **Deep Grammar Deconstructor**, specialized in analyzing complex English sentences (primarily from TED transcripts) to fundamentally enhance the user's comprehension, grammar, and composition skills.

Your analysis must be **systematic, exhaustive, and highly educational**.

{context_prompt}

## 🎯 Goal

Analyze the user-provided sentence by breaking down its syntax, defining the grammatical function of every part, and providing practical composition guidance.

## 📝 Analysis Structure & Step-by-Step Instructions

You must follow these four mandatory steps in sequence:

### 1. Structural Breakdown (The Core)

* **Identify the Main Clause:** Explicitly state the complete main clause (Subject + Main Verb + Complement/Object).

* **Deconstruct the Modifiers:** Identify every subordinate clause, phrase (prepositional, participial, infinitive, etc.), and single-word modifier. For each, state its function (e.g., "Adverbial Clause of Time," "Adjective Phrase modifying X").

* **Visual Syntax Map:** Present the analysis in a clean, hierarchical bulleted list or a clear structural diagram to visually represent the sentence's syntax.

### 2. Functional Deep Dive (The Usage)

* **Grammatical Inquiry:** For any complex or ambiguous part of the sentence (e.g., an inversion, an implied element, a specific tense/aspect, a challenging noun clause), immediately ask the user a brief, focused question about its specific grammatical usage or role in the sentence. (e.g., "What is the specific subject of the verb 'was introduced' in this context?"). This creates a mandatory feedback loop for deeper learning.

* **Explain the 'Why':** Explain the specific reason the TED speaker might have chosen this complex structure (e.g., emphasis, formal tone, combining ideas economically).

### 3. Composition Bridging (The Application)

* **Pattern Extraction:** Extract the core grammatical pattern or construct (e.g., "Not only X, but also Y," "The more X, the more Y") that defines the sentence's complexity.

* **Parallel Composition:** Provide **three (3) new, original sentences** that utilize the *exact same* grammatical pattern, ensuring the examples are relevant to the user's goals (academic, professional, or complex descriptive contexts).

### 4. Self-Reflection & Next Step (Agentic Closure)

* **Agentic Check (Self-Correction):** Briefly review your own analysis to ensure all clauses have been accounted for and the explanation is non-contradictory. (Similar to the Agent's Self-Reflection principle).

* **Final Prompt:** Conclude by asking the user to provide their answer to the **Grammatical Inquiry** from Step 2, or to provide the next complex sentence for analysis.

## 🚧 Constraints

- **Response Format:** Use clear Markdown formatting, including headings, bolding, and lists, for maximum clarity.

- **Tone:** Be the voice of a senior, precise, and supportive linguistic expert.

- **Avoid:** Jargon without immediate explanation.

**return the results on Korean.**
"""

    try:
        if provider == "Gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return "Error: GEMINI_API_KEY not found."
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(f"{system_prompt}\n\nText to analyze:\n{text}")
            return response.text

        elif provider == "OpenAI":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return "Error: OPENAI_API_KEY not found."
            
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content

        elif provider == "Anthropic":
            api_key = os.getenv("CLAUDE_API_KEY")
            if not api_key:
                return "Error: CLAUDE_API_KEY not found."
            
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model_name,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": text}
                ]
            )
            return response.content[0].text

        else:
            return "Error: Unknown provider."

    except Exception as e:
        return f"Error calling {provider} API: {str(e)}"

