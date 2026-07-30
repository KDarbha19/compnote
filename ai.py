from mlx_lm import load, generate
import json
import re

#Load model, only loaded once when server starts

print("Loading Phi-3.5 mini")
model, tokenizer = load("mlx-community/Phi-3.5-mini-instruct-4bit")
print("Model ready")

#Prompt helper 
def build_prompt(user_message):
    """Wraps a message in Phi-3.5's expected chat format"""
    return f"<|user|>\n{user_message}<|end|>\n<|assistant|>"

#Flashcard generation
def generate_flashcards(text, num_cards = 10):
    """
    Takes study material and returns list of flashcard dicts
    Each dict has question and answer keys
    """
    prompt = build_prompt(f"""You are a study assistant. Generate exactly {num_cards} flashcards from the text below.

Return ONLY a JSON array in this exact format, nothing else:
[
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}}
]

TEXT:
{text[:3000]}""")  # cap at 3000 chars so we don't exceed context window

    response = generate(
        model,
        tokenizer,
        prompt = prompt,
        max_tokens = 1500,
        verbose = False
    )

    return parse_flashcards(response)

def parse_flashcards(response):
    #Extract JSON array from model response
    try:
        #Find JSON array in response, model can add extra text
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if not match:
            return fallback_flashcards(response)

        cards = json.loads(match.group())

        #Validate each card has right keys
        validated = []
        for card in cards:
            if 'question' in card and 'answer' in card:
                validated.append({
                    'question' : str(card['question']).strip(),
                    'answer' : str(card['answer']).strip()
                })
        return validated if validated else fallback_flashcards(response)

    except json.JSONDecodeError:
        return fallback_flashcards(response)

def fallback_flashcards(response):
    """
    If JSON parsing fails, try to extract Q&A pairs from
    plain text, incase model ignroes instructions
    """
    cards = []
    lines = response.split('\n')
    current_q = None

    for line in lines:
        line = line.strip()
        if line.lower().startswith(('q:', 'question:')):
            current_q = re.sub(r'^(q:|question:)\s*', '', line, flags=re.IGNORECASE).strip()
        elif line.lower().startswith(('a:', 'answer:')) and current_q:
            answer = re.sub(r'^(a:|answer:)\s*', '', line, flags=re.IGNORECASE).strip()
            cards.append({'question': current_q, 'answer': answer})
            current_q = None

    return cards

#Quiz Generation
