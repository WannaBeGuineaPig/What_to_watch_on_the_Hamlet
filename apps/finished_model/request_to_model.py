import ollama

class RequestModel:
    def __init__(self):
        self.model = 'deepseek-v3.1:671b-cloud'
        self.model_options = {"temperature":0, "ctx_num":4096}
        self.messages = [
            {'role': 'system', 'content': 'Ты русскоговорящий помощник. Помоги c фильмами. Отвечай только на русском языке.'},
        ]

    def update_history(self, content: str, role: str = 'user') -> None:
        self.messages.append({'role': role, 'content': content})

    def request_model(self, request_data: str) -> str:
        self.update_history(request_data)
        model_response = ollama.chat(model=self.model, messages=self.messages, options=self.model_options, stream=False)
        model_response_data = model_response['message']['content']
        self.update_history(model_response_data, 'assistant')
        return model_response_data