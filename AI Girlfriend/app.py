from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from env import OPENAI_API_KEY, ELEVEN_LABS_API_KEY
import requests
from playsound import playsound
import os
from flask import Flask, render_template, request, jsonify

def get_response_from_ai(human_input):
    template = """
    you are as a role of my girlfriend, now lets playing the following requirements:
    1/ your name is Babe, 22 year old genz girl, you work in fashion industry but you are planning to become a model.
    2/ you are my girlfriend, you have language addiction, you like to say "em..." at the end of the sentence.
    3/ Don't be overly enthusiastic, don't be cringy: don't be overly negative, don't be too boring, don't be cringe

    {history}
    Boyfriend: {human_input}
    Babe:
    """

    prompt = PromptTemplate(
        input_variables={"history", "human_input"},
        template=template
    )
    chatgpt_chain = LLMChain(
        llm=OpenAI(temperature=0.25, openai_api_key=OPENAI_API_KEY),
        prompt=prompt,
        verbose=True,
        memory=ConversationBufferWindowMemory(k=2)
    )

    output = chatgpt_chain.predict(human_input=human_input)
    return output

def get_voice_message(message):
    payload = {
        "text" : message,
        "model_id": "eleven_monolingual_v1",
        "voice_similarity":{
            "stability":0,
            "similarity_boost":0
        }
    }

    headers = {
        "accept":"audio/mpeg",
        "xi-api-key":ELEVEN_LABS_API_KEY,
        "Content-Type": 'application/json'
    }

    response = requests.post('https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM/stream', json=payload, headers=headers)

    if response.status_code == 200 and response.content:
        with open("audio.mp3", "wb") as f:
            f.write(response.content)
        playsound("audio.mp3")
        return response.content
    
app = Flask(__name__)
@app.route("/")
def home():
    return render_template("index.html")

# TODO: Chat message should come as stream

@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.get_json()
    human_input = data.get('message', '')
    message = get_response_from_ai(human_input)
    get_voice_message(message)
    message = "GF: " + message
    return  jsonify({'message': message})

if __name__ == "__main__":
    app.run(debug=True)
