import jieba
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report
import joblib

# 加载停用词列表
stop_words = set(jieba.lcut(open('data/stopwords.txt', 'r', encoding='utf-8').read()))
# 加载自定义词表
jieba.load_userdict('data/userdict.txt')

def preprocess_text(text):
    tokens = list(jieba.cut(text))
    filtered_tokens = [word for word in tokens if word not in stop_words]
    '''
    print(text)
    print('|' . join(tokens))
    print('|' . join(filtered_tokens))
    print()
    '''
    return ' ' . join(filtered_tokens)

def load_data(file_path):
    texts, labels = [], []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            columns = line.strip().split('\t')
            if len(columns) < 2:
                print(f"Invalid line: {line}")
                continue
            texts.append(preprocess_text(columns[0]))
            labels.append(columns[1])
    return texts, labels

def main() -> None:
    #vectorizer = CountVectorizer()
    vectorizer = TfidfVectorizer()

    # 训练数据
    train_texts, train_labels = load_data('data/messages_type.train')
    X_train = vectorizer.fit_transform(train_texts)

    clf = MultinomialNB()
    clf.fit(X_train, train_labels)

    # 测试数据
    test_texts, test_labels = load_data('data/messages_type.test')
    X_test = vectorizer.transform(test_texts)

    # 预测
    predicted_labels = clf.predict(X_test)

    # 输出测试结果
    print("Predicted labels:", predicted_labels)
    print("True labels:", test_labels)
    print("Accuracy:", accuracy_score(test_labels, predicted_labels))
    print("\nClassification Report:\n" + classification_report(test_labels, predicted_labels))

    # 导出模型和向量化器
    model_filename = 'models/message_type_classifier_model.joblib'
    vectorizer_filename = 'models/tfidf_vectorizer.joblib'
    
    joblib.dump(clf, model_filename)
    joblib.dump(vectorizer, vectorizer_filename)

if __name__ == "__main__":
    main()