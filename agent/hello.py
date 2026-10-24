from dotenv import load_dotenv
import anthropic

load_dotenv()  # lit la clé dans le fichier .env
client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=300,
    messages=[
        {"role": "user", "content": "Explique en 2 phrases ce qu'est la pharmacovigilance."}
    ],
)

print(message.content[0].text)
print(f"\nTokens utilisés : {message.usage.input_tokens} en entrée, {message.usage.output_tokens} en sortie")