import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
from rich.console import Console
from rich.markdown import Markdown as RichMarkdown

load_dotenv(override=True)

# IPython's display(Markdown(...)) only renders in Jupyter; Rich renders Markdown in terminals.
_console = Console()


def show_markdown(text: str) -> None:
    _console.print(RichMarkdown(text))


RESPONSES_FILE = Path(__file__).resolve().parent / "multimodel_orchestration_responses2.txt"


def print_model_then_answer(model_name: str, answer: str) -> None:
    _console.print(f"\n[bold cyan]── {model_name} ──[/bold cyan]\n")
    show_markdown(answer)


def write_responses_file(models: list[str], responses: list[str], path: Path) -> None:
    lines: list[str] = []
    for name, text in zip(models, responses):
        lines.append(f"Model: {name}")
        lines.append("")
        lines.append(text)
        lines.append("")
        lines.append("=" * 72)
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"\nSaved model responses to {path}")


openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY')
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
groq_api_key = os.getenv('GROQ_API_KEY')

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
    
if anthropic_api_key:
    print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
else:
    print("Anthropic API Key not set (and this is optional)")

if gemini_api_key:
    print(f"Gemini API Key exists and begins {gemini_api_key[:2]}")
else:
    print("Gemini API Key not set (and this is optional)")

if deepseek_api_key:
    print(f"DeepSeek API Key exists and begins {deepseek_api_key[:3]}")
else:
    print("DeepSeek API Key not set (and this is optional)")

if groq_api_key:
    print(f"Groq API Key exists and begins {groq_api_key[:4]}")
else:
    print("Groq API Key not set (and this is optional)")


#request = "Please come up with a challenging, nuanced question that I can ask a number of LLMs to evaluate their intelligence. "
request = "Who is Lord Krishna, Shiva and Guru Raghavendra in Hinduism? Write a short answer about each of them."
request += "Answer only with the question, no explanation."
messages = [{"role": "user", "content": request}]

openai = OpenAI(api_key=openai_api_key)
response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages
)
question = response.choices[0].message.content.strip()  
print(question)

competitors = []
answers = []
messages = [{"role": "user", "content": question}]

model_name = "gpt-5-nano"

response = openai.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

print_model_then_answer(model_name, answer)
competitors.append(model_name)
answers.append(answer)
# Anthropic has a slightly different API, and Max Tokens is required

model_name = "claude-sonnet-4-5"

claude = Anthropic()
response = claude.messages.create(model=model_name, messages=messages, max_tokens=1000)
answer = response.content[0].text

print_model_then_answer(model_name, answer)
competitors.append(model_name)
answers.append(answer)


gemini = OpenAI(api_key=gemini_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model_name = "gemini-2.5-flash"

response = gemini.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

print_model_then_answer(model_name, answer)
competitors.append(model_name)
answers.append(answer)


# deepseek = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")
# model_name = "deepseek-chat"

# response = deepseek.chat.completions.create(model=model_name, messages=messages)
# answer = response.choices[0].message.content

# print_model_then_answer(model_name, answer)
# competitors.append(model_name)
# answers.append(answer)
# Updated with the latest Open Source model from OpenAI

groq = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
model_name = "openai/gpt-oss-120b"

response = groq.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

print_model_then_answer(model_name, answer)
competitors.append(model_name)
answers.append(answer)

ollama = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
model_name = "llama3.2"

response = ollama.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

print_model_then_answer(model_name, answer)
competitors.append(model_name)
answers.append(answer)


write_responses_file(competitors, answers, RESPONSES_FILE)

print(competitors)
print(answers)
# It's nice to know how to use "zip"
for competitor, answer in zip(competitors, answers):
    print(f"Competitor: {competitor}\n\n{answer}")
# Let's bring this together - note the use of "enumerate"

together = ""
for index, answer in enumerate(answers):
    together += f"# Response from competitor {index+1}\n\n"
    together += answer + "\n\n"
print(together)
judge = f"""You are judging a competition between {len(competitors)} competitors.
Each model has been given this question:

{question}

Your job is to evaluate each response for clarity and strength of argument, and rank them in order of best to worst.
Respond with JSON, and only JSON, with the following format:
{{"results": ["best competitor number", "second best competitor number", "third best competitor number", ...]}}

Here are the responses from each competitor:

{together}

Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks."""
print(judge)
judge_messages = [{"role": "user", "content": judge}]
# Judgement time!

openai = OpenAI()
response = openai.chat.completions.create(
    model="gpt-5-mini",
    messages=judge_messages,
)
results = response.choices[0].message.content
print(results)
# OK let's turn this into results!

results_dict = json.loads(results)
ranks = results_dict["results"]
for index, result in enumerate(ranks):
    competitor = competitors[int(result)-1]
    print(f"Rank {index+1}: {competitor}")
