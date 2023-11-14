import openai
import json, os
import requests
from pyairtable import Table
from env import *
openai.api_key = OPENAI_API_KEY

headers = {
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": "ms-finance.p.rapidapi.com"
}


table = Table(AIR_TABLE_API_KEY, "appspj4peYS5zcMqE", "tbljJy20gmAggDjJy")

def get_stock_news(performance_id):

    url = "https://ms-finance.p.rapidapi.com/news/list"

    querystring = {"performanceId":performance_id}
    response = requests.get(url, headers=headers, params=querystring)

    print(response.json())
    return response.json()

def get_stock_movers():

    url = "https://ms-finance.p.rapidapi.com/market/v2/get-movers"
    response = requests.get(url, headers=headers)

    print(response.json())
    return response.json()

def function_call(ai_response):
    fn_call = ai_response["choices"][0]["message"]["function_call"]
    fn_name = fn_call["name"]
    arguments = fn_call["arguments"]
    if fn_name == "get_stock_news":
        performance_id = eval(arguments).get("performance_id")
        return get_stock_news()
    elif fn_name == "get_stock_movers":
        return get_stock_movers()
    elif fn_name == "add_stock_news_airtable":
        stock = eval(arguments).get("stock")
        news_summary = eval(arguments).get("news_summary")
        move = eval(arguments).get("move")
        return add_stock_news_airtable(stock, move, news_summary)
    else:
        return


def add_stock_news_airtable(stock, move, news_summary):
    table.create({"stock":stock, "move%": move, "news_summary":news_summary})

function_descriptions = [
    {
        "name": "get_stock_movers",
        "description": "Get the stocks that has biggest price/volume moves, e.g. actives, gainers, losers, etc.",
        "parameters": {
            "type": "object",
            "properties": {
            },
        }
    },
    {
        "name": "get_stock_news",
        "description": "Get the latest news for a stock",
        "parameters": {
            "type": "object",
            "properties": {
                "performanceId": {
                    "type": "string",
                    "description": "id of the stock, which is referred as performanceID in the API"
                },
            },
            "required": ["performanceId"]
        }
    },
    {
        "name": "add_stock_news_airtable",
        "description": "Add the stock, news summary & price move to Airtable",
        "parameters": {
            "type": "object",
            "properties": {
                "stock": {
                    "type": "string",
                    "description": "stock ticker"
                },
                "move": {
                    "type": "string",
                    "description": "price move in %"
                },
                "news_summary": {
                    "type": "string",
                    "description": "news summary of the stock"
                },
            }
        }
    }
]

def ask_function_calling(query):
    messages = [{"role": "user", "content": query}]

    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=messages,
        functions = function_descriptions,
        function_call="auto"
    )

    print(response)

    while response["choices"][0]["finish_reason"] == "function_call":
        function_response = function_call(response)
        messages.append({
            "role": "function",
            "name": response["choices"][0]["message"]["function_call"]["name"],
            "content": json.dumps(function_response)
        })

        print("messages: ", messages) 

        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=messages,
            functions = function_descriptions,
            function_call="auto"
        )   

        print("response: ", response) 
    else:
        print(response)


user_query = """What is the stock that has the biggest price movement today and what are the latest
news about this stock that might cause the price movement? Please add a record to Aairtable with the stock ticker price move and news summary."""

ask_function_calling(user_query)
