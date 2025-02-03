import jieba
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score

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

def main() -> None:
    # 训练数据
    train_texts = []
    train_labels = []
    with open('data/messages_type.train', 'r', encoding='utf-8') as file:
        for line in file:
            columns = line.strip().split('\t')
            if len(columns) < 2:
                print("Invalid line:", line)
                continue
            train_texts.append(preprocess_text(columns[0]))
            train_labels.append(columns[1])

    vectorizer = CountVectorizer()
    X_train = vectorizer.fit_transform(train_texts)

    clf = MultinomialNB()
    clf.fit(X_train, train_labels)

    # 测试数据
    test_texts = []
    test_labels = []
    with open('data/messages_type.test', 'r', encoding='utf-8') as file:
        for line in file:
            columns = line.strip().split('\t')
            if len(columns) < 2:
                print("Invalid line:", line)
                continue
            test_texts.append(preprocess_text(columns[0]))
            test_labels.append(columns[1])

    X_test = vectorizer.transform(test_texts)

    # 预测
    predicted_labels = clf.predict(X_test)

    # 输出测试结果
    print("Predicted labels:", predicted_labels)
    print("True labels:", test_labels)
    print("Accuracy:", accuracy_score(test_labels, predicted_labels))

if __name__ == "__main__":
    main()