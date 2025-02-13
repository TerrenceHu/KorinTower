from configparser import ConfigParser
from loguru import logger
import joblib
import jieba

class TextProcessor:
    def __init__(self, config: ConfigParser):
        # 加载停用词表
        stopwords_filename = config.get('MODEL', 'stopwords_filename')
        self.stop_words = set(jieba.lcut(open(stopwords_filename, 'r', encoding='utf-8').read()))

        # 加载自定义词表
        userdict_filename = config.get('MODEL', 'userdict_filename')  
        jieba.load_userdict(userdict_filename)

        # 加载消息文本分类模型和向量化器
        try:
            classifier_model_filename = config.get('MODEL', 'classifier_model_filename')
            classifier_vectorizer_filename = config.get('MODEL', 'classifier_vectorizer_filename')
            self.classifier_model = joblib.load(classifier_model_filename)
            self.classifier_vectorizer = joblib.load(classifier_vectorizer_filename)
        except FileNotFoundError:
            logger.error(f"Message classifier model or vectorizer not found: \
                         {classifier_model_filename},{classifier_vectorizer_filename}")
        except Exception as e:
            logger.error(f"Load message classifier model or vectorizer error: {e}")

    def predict(self, message_text: str) -> int:
        message_tokens = list(jieba.cut(message_text))
        filtered_tokens = [word for word in message_tokens if word not in self.stop_words]
        preprocessed_texts = [' '.join(filtered_tokens)]
        transformed_texts = self.classifier_vectorizer.transform(preprocessed_texts)
        message_type = self.classifier_model.predict(transformed_texts)[0]

        return message_type
    
    def segment(self, text: str) -> list:
        return jieba.cut(text)
