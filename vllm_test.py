# import argparse
import pprint
import requests


def post_http_request(prompt: dict, api_url: str) -> requests.Response:
    headers = {"User-Agent": "Test Client"}
    response = requests.post(api_url, headers=headers, json=prompt)
    return response


def main(host, port, model):
    api_url = f"http://{host}:{port}/score"
    model_name = model

    # text_1 = "부산광역시 2025년도 친환경 정책은?"
    # text_2 = "부산광역시 친환경 정책은 아래와 같다."
    # prompt = {"model": model_name, "text_1": text_1, "text_2": text_2}
    # score_response = post_http_request(prompt=prompt, api_url=api_url)
    # print("\nPrompt when text_1 and text_2 are both strings:")
    # pprint.pprint(prompt)
    # print("\nScore Response:")
    # pprint.pprint(score_response.json())

    text_1 = "부산광역시 2025년도 친환경 정책은?"
    text_2 = ["부산광역시 친환경 정책은 아래와 같다.", "부산광역시는 대한민국의 광역시이다."]
    prompt = {"model": model_name, "text_1": text_1, "text_2": text_2}
    score_response = post_http_request(prompt=prompt, api_url=api_url)
    print("\nPrompt when text_1 is string and text_2 is a list:")
    pprint.pprint(prompt)
    print("\nScore Response:")
    pprint.pprint(score_response.json())

    # text_1 = ["What is the capital of Brazil?", "What is the capital of France?"]
    # text_2 = ["The capital of Brazil is Brasilia.", "The capital of France is Paris."]
    # prompt = {"model": model_name, "text_1": text_1, "text_2": text_2}
    # score_response = post_http_request(prompt=prompt, api_url=api_url)
    # print("\nPrompt when text_1 and text_2 are both lists:")
    # pprint.pprint(prompt)
    # print("\nScore Response:")
    # pprint.pprint(score_response.json())

if __name__ == '__main__':
    host = "localhost"
    port = 8000
    model = "dragonkue/bge-reranker-v2-m3-ko"
    main(host, port, model)