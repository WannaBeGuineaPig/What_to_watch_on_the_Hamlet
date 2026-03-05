from googletrans import Translator
from transformers import AutoTokenizer
from gliclass import GLiClassModel, ZeroShotClassificationPipeline

class ClassificationMessage:
    def __init__(self):
        model = GLiClassModel.from_pretrained("knowledgator/gliclass-instruct-large-v1.0")
        tokenizer = AutoTokenizer.from_pretrained("knowledgator/gliclass-instruct-large-v1.0")
        self.pipeline = ZeroShotClassificationPipeline(model, tokenizer)
        self.labels = ["positive", "negative"]
        self.prompt = 'Determine the emotional coloring of this message'
        self.labels_english_to_russian = {
            "positive" : 'Положительный',
            "negative" : 'Негативный'
        }
    
    async def get_predict(self, text: str) -> str:
        english_text = await self.translate_text(text)
        results = self.pipeline(english_text, self.labels, prompt=self.prompt, threshold=0.5)[0]
        accuracy_type, type_text = self.find_classification_predict(results)
        return {
            'english_type_message' : type_text,
            'russian_type_message' : self.labels_english_to_russian[type_text],
            'accuracy' : accuracy_type
        }

    def find_classification_predict(self, results: list) -> str:
        type_message = ''
        max_score = 0

        for item in results:
            if max_score < item['score']:
                max_score = item['score']
                type_message = item['label']
        
        return max_score, type_message

    async def translate_text(self, text_to_translate: str) -> str:
        async with Translator() as translator:
            result = await translator.translate(text_to_translate)
            return result.text
