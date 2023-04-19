import boto3
import json
import openai
import pinecone

ssm = boto3.client('ssm')
openai.api_key = ssm.get_parameter(Name='OPENAI_API_KEY', WithDecryption=True)['Parameter']['Value']
pinecone_key = ssm.get_parameter(Name='PINECONE_KEY', WithDecryption=True)['Parameter']['Value']
pinecone_env = ssm.get_parameter(Name='PINECONE_ENV', WithDecryption=True)['Parameter']['Value']

pinecone.init(api_key=pinecone_key, environment=pinecone_env)
index = pinecone.Index('openai')

def create_context(
    question,
):
    """
    Create a context for a question by finding the most similar context from the pinecone index
    """
    max_len=1800
    # Get the embeddings for the question
    q_embeddings = openai.Embedding.create(input=question, engine='text-embedding-ada-002')['data'][0]['embedding']
    
    # Get the distances from the embeddings
    res = index.query([q_embeddings], top_k=5, include_metadata=True)

    returns = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
    for match in res['matches']:
        text = match['metadata']['text']
        n_tokens = match['metadata']['n_tokens']
        # Add the length of the text to the current length
        cur_len += n_tokens + 4
        # If the context is too long, break
        if cur_len > max_len:
            break
        # Else add it to the text that is being returned
        returns.append(text)
    # Return the context
    return "\n\n###\n\n".join(returns)

def answer_question(
    model="gpt-3.5-turbo",
    question="What is AntStack?",
    max_tokens=150,
):
    """
    Answer a question based on the most similar context from pinecone
    """
    context = create_context(
        question,
    )

    try:
        # Create a completions using the question and context
        response = openai.ChatCompletion.create(
            temperature=0,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
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
    body = json.loads(event["body"])
    prompt = body["prompt"]
    response = answer_question(question=prompt)
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Credentials": True
        },
        "body": json.dumps({
            "response": response
        })
    }