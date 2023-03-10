import os
import boto3
import json
import base64
import openai
from openai.embeddings_utils import distances_from_embeddings, cosine_similarity
import pandas as pd
import numpy as np
# from dotenv import load_dotenv
# load_dotenv()

ssm = boto3.client('ssm')
# OPENAI_API_KEY = ssm.get_parameter(Name='OPENAI_API_KEY', WithDecryption=True)['Parameter']['Value']
openai.api_key = ssm.get_parameter(Name='OPENAI_API_KEY', WithDecryption=True)['Parameter']['Value']

df = pd.read_pickle('/opt/ml/embeddings.pkl')

def create_context(
    question, df, max_len=1800, size="ada"
):
    """
    Create a context for a question by finding the most similar context from the dataframe
    """

    # Get the embeddings for the question
    q_embeddings = openai.Embedding.create(input=question, engine='text-embedding-ada-002')['data'][0]['embedding']

    # Get the distances from the embeddings
    df['distances'] = distances_from_embeddings(q_embeddings, df['embeddings'].values, distance_metric='cosine')


    returns = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
    for i, row in df.sort_values('distances', ascending=True).iterrows():
        
        # Add the length of the text to the current length
        cur_len += row['n_tokens'] + 4
        
        # If the context is too long, break
        if cur_len > max_len:
            break
        
        # Else add it to the text that is being returned
        returns.append(row["text"])

    # Return the context
    return "\n\n###\n\n".join(returns)

def answer_question(
    df,
    model="gpt-3.5-turbo",
    question="What is AntStack?",
    max_len=1800,
    size="ada",
    debug=False,
    max_tokens=150,
    stop_sequence=None
):
    """
    Answer a question based on the most similar context from the dataframe texts
    """
    context = create_context(
        question,
        df,
        max_len=max_len,
        size=size,
    )
    # If debug, print the raw model response
    if debug:
        print("Context:\n" + context)
        print("\n\n")

    try:
        # Create a completions using the question and context
        response = openai.ChatCompletion.create(
            temperature=0,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence,
            model=model,
            messages = [
                {"role": "system", "content": f"You are a chatbot for a Serverless company AntStack and strictly answer the question based on the context below, and if the question can't be answered based on the context, say \"I'm sorry I cannot answer the question, contact connect@antstack.com\"\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:"},
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print(e)
        return ""
        
def lambda_handler(event, context):
    body = (event["body"])
    if isinstance(body, str):
        body = json.loads(base64.b64decode(body))
    prompt = body["prompt"]
    response = answer_question(df, question=prompt, debug=False)
    
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        },
        "body": json.dumps({
            "response": response
        })
    }