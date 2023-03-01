FROM public.ecr.aws/lambda/python:3.9

COPY app.py requirements.txt ./
COPY embeddings.pkl /opt/ml/embeddings.pkl

RUN python3.9 -m pip install -r requirements.txt -t .

CMD ["app.lambda_handler"]
