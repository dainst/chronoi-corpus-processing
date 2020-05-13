#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import pandas as pd
import numpy as np

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score


import numpy

class EvalResult():

    def __init__(self, name: str):
        self.precision = 0.0
        self.recall = 0.0
        self.f1 = 0.0
        self.accuracy = 0.0
        self.name = name
        self.report = ""
        self.labels = []


    @classmethod
    def default_eval(cls, name: str, tags_pred: [str], tags_true: [str]):
        result = cls(name=name)

        # the report is generated from the input values directly
        result.report = flat_classification_report(y_pred=tags_pred, y_true=tags_true)

        # flatten the input values
        tags_pred = [s for sublist in tags_pred for s in sublist]
        tags_true = [s for sublist in tags_true for s in sublist]

        assert (len(tags_pred) == len(tags_true)), "Input length mismatch: %d != %d" % (len(tags_pred), len(tags_true))

        all_labels = list(set(tags_pred + tags_true))
        result.labels = [l for l in all_labels if l != "O"]
        labels = result.labels
        if (len(labels) == 1):
            result.precision = precision_score(y_pred=tags_pred, y_true=tags_true, labels=labels, pos_label=labels[0])
            result.recall = recall_score(y_pred=tags_pred, y_true=tags_true, labels=labels, pos_label=labels[0])
        else:
            average = 'micro'
            result.precision = precision_score(y_pred=tags_pred, y_true=tags_true, labels=labels, average=average)
            result.recall = recall_score(y_pred=tags_pred, y_true=tags_true, labels=labels, average=average)

        result.accuracy = accuracy_score(y_pred=tags_pred, y_true=tags_true)
        if (result.precision + result.recall) > 0:
            result.f1 = 2 * (result.precision * result.recall) / (result.precision + result.recall)

        return result



class MemoryTagger(BaseEstimator, TransformerMixin):

    def fit(self, X, y):
        '''
        Expects a list of words as X and a list of tags as y
        '''
        voc = {}
        self.tags = []
        for x, t in zip(X, y):
            if t not in self.tags:
                self.tags.append(t)

            if x in voc:
                if t in voc[x]:
                    voc[x][t] += 1
                else:
                    voc[x][t] = 1
            else:
                voc[x] = {t: 1}

        self.memory = {}
        for k, d in voc.items():
            self.memory[k] = max(d, key=d.get)

    def predict(self, X, y=None):
        '''
        Predict the tag from memory. If word is unknown predict 'O'
        '''
        return [self.memory.get(x, 'O') for x in X]


class FeatureTransformer(BaseEstimator, TransformerMixin):

    def __init__(self):
        self.memory_tagger = MemoryTagger()
        self.tag_encoder = LabelEncoder()
        self.pos_encoder = LabelEncoder()

    def fit(self, X, y):
        words = X["Word"].values.tolist()
        self.pos = X["POS"].values.tolist()
        tags = X["Tag"].values.tolist()
        self.memory_tagger.fit(words, tags)
        self.tag_encoder.fit(tags)
        self.pos_encoder.fit(self.pos)
        return self

    def transform(self, X, y=None):
        def pos_default(p):
            if p in self.pos:
                return self.pos_encoder.transform([p])[0]
            else:
                return -1

        pos = X["POS"].values.tolist()
        words = X["Word"].values.tolist()
        out = []
        for i in range(len(words)):
            # main focus word/pos (actually only used at the bottom)
            w = words[i]
            p = pos[i]

            # encode information about the word following the ith word/pos
            if i < len(words) - 1:
                wp = self.tag_encoder.transform(self.memory_tagger.predict([words[i + 1]]))[0]
                posp = pos_default(pos[i + 1])
            else:
                wp = self.tag_encoder.transform(['O'])[0]
                posp = pos_default(".") # TODO: '$.' for different table?

            # encode information about the word previous to the ith word/pos
            if i > 0:
                # TODO: Check if this should be taken out as we have '.' that are part of timexes
                if words[i - 1] != ".":
                    wm = self.tag_encoder.transform(self.memory_tagger.predict([words[i - 1]]))[0]
                    posm = pos_default(pos[i - 1])
                else:
                    wm = self.tag_encoder.transform(['O'])[0]
                    posm = pos_default(".")
            else:
                posm = pos_default(".")
                wm = self.tag_encoder.transform(['O'])[0]

            # the result are some basic features as well as the memory predictions and pos
            # from the previous and following words
            out.append(np.array([w.istitle(), w.islower(), w.isupper(), len(w), w.isdigit(), w.isalpha(),
                                 self.tag_encoder.transform(self.memory_tagger.predict([w]))[0],
                                 pos_default(p), wp, wm, posp, posm]))
        return out


class SentenceGetter(object):

    def __init__(self, data):
        self.n_sent = 1
        self.data = data
        self.empty = False
        agg_func = lambda s: [(w, p, t) for w, p, t in zip(s["Word"].values.tolist(),
                                                           s["POS"].values.tolist(),
                                                           s["Tag"].values.tolist())]
        self.grouped = self.data.groupby("Sentence #").apply(agg_func)
        self.sentences = [s for s in self.grouped]

    def get_next(self):
        try:
            values = self.get_by_no(self.n_sent)
            self.n_sent += 1
        except KeyError:
            self.empty = True
            return None

        return values

    def get_by_no(self, sent_no: int):
        return self.grouped["Sentence: %d" % sent_no]


def feature_map(word: str):
    """
    Simple feature map
    """
    return np.array([word.istitle(), word.islower(), word.isupper(), len(word),
                     word.isdigit(), word.isalpha()])


def do_01_intro(data: pd.DataFrame, cv=5) -> EvalResult:

    # test the baseline Memory tagger
    # getter = SentenceGetter(data)
    # words, pos, ner = getter.get_by_no(122)
    # tagger = MemoryTagger()
    # tagger.fit(words, ner)
    # print(words)
    # print(ner)
    # print(tagger.predict(words))
    # print(tagger.tags)

    # do an evaluation of the memory tagger
    # words = data["Word"].values.tolist()
    # tags = data["Tag"].values.tolist()
    # pred = cross_val_predict(estimator=MemoryTagger(), X=words, y=tags, cv=5)
    # report = classification_report(y_pred=pred, y_true=tags)

    # do an evaluation of the Random Forest Classifier
    # words = [feature_map(w) for w in data["Word"].values.tolist()]
    # tags = data["Tag"].values.tolist()
    # pred = cross_val_predict(RandomForestClassifier(n_estimators=20), X=words, y=tags, cv=5)
    # report = classification_report(y_pred=pred, y_true=tags)

    # Random Forest with better features
    tags = data["Tag"].values.tolist()
    pipe = Pipeline([
        ("feature_map", FeatureTransformer()),
        ("clf", RandomForestClassifier(n_estimators=20, n_jobs=3))
    ])
    pred = cross_val_predict(pipe, X=data, y=tags, cv=cv)
    pred = pred.tolist()

    # Bring the results in the same form as later experiments for the evaluator
    getter = SentenceGetter(data)
    tags_true = []
    tags_pred = []
    for s in getter.sentences:
        n = len(s)
        tags_true.append(tags[0:n])
        tags_pred.append(pred[0:n])

        tags = tags[n:]
        pred = pred[n:]

    return EvalResult.default_eval("01: Random Forest", tags_pred=tags_pred, tags_true=tags_true)

    # report = classification_report(y_pred=pred, y_true=tags)
    # print(report)

##
# 02_crfs
##

import eli5

from sklearn_crfsuite import CRF
from sklearn_crfsuite.metrics import flat_classification_report

def word2features(sent: [(str, str, str)], i: int):
    word = sent[i][0]
    postag = sent[i][1]

    features = {
        'bias': 1.0,
        'word.lower()': word.lower(),
        'word[-3:]': word[-3:],
        'word[-2:]': word[-2:],
        'word.isupper()': word.isupper(),
        'word.istitle()': word.istitle(),
        'word.isdigit()': word.isdigit(),
        'postag': postag,
        'postag[:2]': postag[:2],
    }
    if i > 0:
        word1 = sent[i - 1][0]
        postag1 = sent[i - 1][1]
        features.update({
            '-1:word.lower()': word1.lower(),
            '-1:word.istitle()': word1.istitle(),
            '-1:word.isupper()': word1.isupper(),
            '-1:postag': postag1,
            '-1:postag[:2]': postag1[:2],
        })
    else:
        features['BOS'] = True

    if i < len(sent) - 1:
        word1 = sent[i + 1][0]
        postag1 = sent[i + 1][1]
        features.update({
            '+1:word.lower()': word1.lower(),
            '+1:word.istitle()': word1.istitle(),
            '+1:word.isupper()': word1.isupper(),
            '+1:postag': postag1,
            '+1:postag[:2]': postag1[:2],
        })
    else:
        features['EOS'] = True

    return features


def sent2features(sent):
    return [word2features(sent, i) for i in range(len(sent))]


def sent2labels(sent):
    return [label for _, _, label in sent]

def sent2words(sent):
    return [word for word, _, _ in sent]


def do_02_crfs(data: pd.DataFrame, cv=5) -> EvalResult:
    getter = SentenceGetter(data)
    sentences = getter.sentences

    X = [sent2features(s) for s in sentences]
    y = [sent2labels(s) for s in sentences]

    crf = CRF(algorithm='lbfgs',
              c1=5.0,
              c2=0.2,
              max_iterations=100,
              all_possible_transitions=False)

    # print some html to show crf top weights in a table
    # crf.fit(X, y)
    # result = eli5.show_weights(crf, top=30)
    # print(result.data)

    pred = cross_val_predict(estimator=crf, X=X, y=y, cv=cv)
    return EvalResult.default_eval("02: CRF", tags_pred=pred, tags_true=y)

    # report = flat_classification_report(y_pred=pred, y_true=y)
    # print(report)


##
# 03_nns
##
from keras.models import Model, Input
from keras.layers import LSTM, Embedding, Dense, TimeDistributed, Dropout, Bidirectional
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical

from sklearn.model_selection import train_test_split

import matplotlib.pyplot as plt
plt.style.use("ggplot")

class LSTMClassifier(BaseEstimator):

    def __init__(self, n_words: int, n_tags: int, max_len=50, epochs=5):
        self.n_words = n_words
        self.n_tags = n_tags
        self.max_len = max_len
        self.epochs = epochs

    def fit(self, X, y):
        '''
        Expects a list of lists of encoded words as X and a list of lists of encoded tags as y
        '''
        y = [to_categorical(i, num_classes=self.n_tags) for i in y]
        self.model = self.buildmodel(max_len=self.max_len, n_words=self.n_words, n_tags=self.n_tags)
        self.model.fit(X, np.array(y), batch_size=32, epochs=self.epochs, validation_split=0.1, verbose=1)
        return self

    def predict(self, X) -> [[int]]:
        p = self.model.predict(X)
        return np.argmax(p, axis=-1)

    @classmethod
    def buildmodel(cls, max_len: int, n_words: int, n_tags: int):
        # define the LSTM network to fit an embedding layer
        input = Input(shape=(max_len,))
        model = Embedding(input_dim=n_words, output_dim=50, input_length=max_len)(input)
        model = Dropout(0.1)(model)
        model = Bidirectional(LSTM(units=100, return_sequences=True, recurrent_dropout=0.1))(model)
        out = TimeDistributed(Dense(n_tags, activation="softmax"))(model) # softmax out layer

        # use defitions to compile and train the model
        model = Model(input, out)
        model.compile(optimizer="rmsprop", loss="categorical_crossentropy", metrics=["accuracy"])
        return model


def shorten_lists(padded: [[]], normal: [[]]):
    result = []

    for i, elem in enumerate(padded):
        norm_len = len(normal[i])
        if (norm_len) > 0:
            new_l = elem[0:norm_len]
        else:
            new_l = []
        result.append(new_l)

        assert(len(new_l) == norm_len)
    return result


def do_03_nns_variant(data: pd.DataFrame, cv=5) -> EvalResult:
    # from sklearn.utils.estimator_checks import check_estimator
    # res = check_estimator(LSTMClassifier)
    # print(res)
    # exit()

    getter = SentenceGetter(data)

    words = list(set(data["Word"].values))
    words.append("ENDPAD")
    n_words = len(words)

    tags = list(set(data["Tag"].values))
    n_tags = len(tags)

    # Build integer tables for words and tags...
    word2idx = {w: i for i, w in enumerate(words)}
    tag2idx = {t: i for i, t in enumerate(tags)}

    # The example uses a max length of 50, we have longer sentences and determine this
    max_len = max(len(s) for s in getter.sentences)
    # inputs are padded to max lenght with the highest word "ENDPAD" (see above)
    X = [[word2idx[w[0]] for w in s] for s in getter.sentences]
    X_padded = pad_sequences(maxlen=max_len, sequences=X, padding="post", value=n_words - 1)

    # tags are padded with 'O's and converted to categoricals
    y = [[tag2idx[w[2]] for w in s] for s in getter.sentences]
    y_padded = pad_sequences(maxlen=max_len, sequences=y, padding="post", value=tag2idx['O'])

    # NOTE: set epochs to 0 for a simple test, to 5 for a normal run
    classifier = LSTMClassifier(n_words=n_words, n_tags=n_tags, max_len=max_len, epochs=5)

    # Example usage for a simple sentence
    # classifier.fit(X_padded, y_padded)
    # example_sentence = ["Fin", "d'ora", "buona", "parte", "del", "sito", "di", "Monruz", "(", "66", "m2",
    #                             ",", "450", "tonnellate", "spostate", "nel", "1990", "sulla", "distanza", "di",
    #                             "un", "chilometro", ")", "in", "corso", "di", "sistemazione", "."]
    # example_sentence = [word2idx[w] for w in example_sentence]
    # example_sentence = pad_sequences(maxlen=max_len, sequences=[example_sentence], padding="post", value=n_words -1)
    # pred = classifier.predict(example_sentence)
    # pred = [tags[i] for i in pred[0]]
    # print(pred)
    # exit()

    # make the prediction
    pred_padded = cross_val_predict(estimator=classifier, X=X_padded, y=y_padded, cv=cv)

    # this reverses the effects of labelling and padding and makes sure the result is
    # easily understandable and the report is calculated using the actual length sentences
    pred_a = shorten_lists(pred_padded, y)
    pred_b = [[tags[i] for i in s] for s in pred_a]
    y_true = [[tags[i] for i in s] for s in y]

    return EvalResult.default_eval("03: LSTM", tags_pred=pred_b, tags_true=y_true)

    # report = flat_classification_report(y_pred=pred_b, y_true=y_true)
    # print(report)


def do_03_nns(data: pd.DataFrame):
    getter = SentenceGetter(data)

    # plot an overview of sentence length
    # plt.hist([len(s) for s in getter.sentences], bins=50)
    # plt.show()

    words = list(set(data["Word"].values))
    words.append("ENDPAD")
    n_words = len(words)

    tags = list(set(data["Tag"].values))
    n_tags = len(tags)

    # Build integer tables for words and tags...
    max_len = 200 # NOTE: The example uses 50
    word2idx = {w: i for i, w in enumerate(words)}
    tag2idx = {t: i for i, t in enumerate(tags)}

    # so that the input can be represented by these
    # inputs are padded to max lenght with the highest word "ENDPAD" (see above)
    X = [[word2idx[w[0]] for w in s] for s in getter.sentences]
    X = pad_sequences(maxlen=max_len, sequences=X, padding="post", value=n_words - 1)

    # tags are padded with 'O's and converted to categoricals
    y = [[tag2idx[w[2]] for w in s] for s in getter.sentences]
    y = pad_sequences(maxlen=max_len, sequences=y, padding="post", value=tag2idx['O'])
    y = [to_categorical(i, num_classes=n_tags) for i in y]


    # Using the Keras wrappers didn't work
    # from keras.wrappers.scikit_learn import KerasRegressor
    # from keras.wrappers.scikit_learn import KerasClassifier
    # regressor = KerasClassifier(build_fn=buildmodel, batch_size=32, epochs=5, validation_split=0.1, verbose=1)
    # pred = cross_val_predict(estimator=regressor, X=X, y=y, cv=5)
    # report = flat_classification_report(y_pred=pred, y_true=y)
    # print(report)
    # return


    # split test and training sets
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.1)

    model = LSTMClassifier.buildmodel(max_len=max_len, n_words=n_words, n_tags=n_tags)
    history = model.fit(X_tr, np.array(y_tr), batch_size=32, epochs=5, validation_split=0.1, verbose=1)

    hist = pd.DataFrame(history.history)

    print(hist)
    # show a fancy plot instead of just a table
    # plt.figure(figsize=(12, 12))
    # plt.plot(hist["accuracy"])
    # plt.plot(hist["val_accuracy"])
    # plt.show()

    # Try to print some samples
    i = 122
    input = np.array([X_te[i]])
    p = model.predict(input)
    p = np.argmax(p, axis=-1)
    print("{:15} ({:5}): {}".format("Word", "True", "Pred"))
    for w, pred in zip(X_te[i], p[0]):
        print("{:15}: {}".format(words[w], tags[pred]))


##
# 04_nns_crfs
##

# This needs a github install and a downgrade of keras to work properly:
#   pip3 install git+https://www.github.com/keras-team/keras-contrib.git
#   pip3 install keras==2.2.4
from keras_contrib.layers import CRF as kcCRF

from seqeval.metrics import f1_score, classification_report



class LSTM_CRF_Classifier(BaseEstimator):

    def __init__(self, n_words: int, n_tags: int, max_len=50, epochs=5):
        self.n_words = n_words
        self.n_tags = n_tags
        self.max_len = max_len
        self.epochs = epochs

    def fit(self, X, y):
        '''
        Expects a list of lists of encoded words as X and a list of lists of encoded tags as y
        '''
        y = [to_categorical(i, num_classes=self.n_tags) for i in y]
        self.model = self.buildmodel(max_len=self.max_len, n_words=self.n_words, n_tags=self.n_tags)
        self.model.fit(X, np.array(y), batch_size=32, epochs=self.epochs, validation_split=0.1, verbose=1)
        return self

    def predict(self, X) -> [[int]]:
        p = self.model.predict(X)
        return np.argmax(p, axis=-1) # TODO: Is the axis=-1 needed?

    @classmethod
    def buildmodel(cls, max_len: int, n_words: int, n_tags: int):
        input = Input(shape=(max_len,))
        model = Embedding(input_dim=n_words + 1, output_dim=20,  # TODO: should this be 20 here and 50 in LSTM?
                          input_length=max_len, mask_zero=True)(input)  # 20-dim embedding
        model = Bidirectional(LSTM(units=50, return_sequences=True,
                                   recurrent_dropout=0.1))(model)
        model = TimeDistributed(Dense(50, activation="relu"))(model)
        crf = kcCRF(n_tags)
        out = crf(model)
        model = Model(input, out)

        model.compile(optimizer="rmsprop", loss=crf.loss_function, metrics=[crf.accuracy])

        return model



def do_04_nns_crfs(data: pd.DataFrame, cv=5) -> EvalResult:
    getter = SentenceGetter(data)

    words = list(set(data["Word"].values))
    words.append("ENDPAD")
    n_words = len(words)

    tags = list(set(data["Tag"].values))

    n_tags = len(tags)

    # Build integer tables for words and tags...
    max_len = max([len(s) for s in getter.sentences]) # determine max_length from sentence langth
    word2idx = {w: i + 1 for i, w in enumerate(words)} # NOTE: i + 1 instead of i in 03_nns
    tag2idx = {t: i for i, t in enumerate(tags)}

    # so that the input can be represented by these
    # inputs are padded to max lenght with the highest word "ENDPAD" (see above)
    X = [[word2idx[w[0]] for w in s] for s in getter.sentences]
    X_padded = pad_sequences(maxlen=max_len, sequences=X, padding="post", value=n_words - 1)

    # tags are padded with 'O's and converted to categoricals
    y = [[tag2idx[w[2]] for w in s] for s in getter.sentences]
    y_padded = pad_sequences(maxlen=max_len, sequences=y, padding="post", value=tag2idx['O'])

    classifier = LSTM_CRF_Classifier(max_len=max_len, n_words=n_words, n_tags=n_tags, epochs=5)

    # make the prediction
    pred_padded = cross_val_predict(estimator=classifier, X=X_padded, y=y_padded, cv=cv)

    # this reverses the effects of labelling and padding
    pred_a = shorten_lists(pred_padded, y)
    # this is not strictly needed but makes sure, that the tags reported are understandable
    pred_b = [[tags[i] for i in s] for s in pred_a]
    y_true = [[tags[i] for i in s] for s in y]

    result = EvalResult.default_eval("04: LSTM CRF", pred_b, y_true)

    return result


    # The official tutorial part:

    # y = [to_categorical(i, num_classes=n_tags) for i in y_padded]
    #
    # X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.1)
    #
    # # build the model
    # model = LSTM_CRF_Classifier.buildmodel(max_len=max_len, n_words=n_words, n_tags=n_tags)
    #
    # # train and print a summary of the training
    # history = model.fit(X_tr, np.array(y_tr), batch_size=32, epochs=5,
    #                     validation_split=0.1, verbose=1)
    # hist = pd.DataFrame(history.history)
    # print("hist:")
    # print(hist)
    #
    # # evaluate a test prediction
    # test_pred = model.predict(X_te, verbose=1)
    # idx2tag = {i: w for w, i in tag2idx.items()}
    # def pred2label(pred):
    #     out = []
    #     for pred_i in pred:
    #         out_i = []
    #         for p in pred_i:
    #             p_i = np.argmax(p)
    #             out_i.append(idx2tag[p_i].replace("PAD", "O"))
    #         out.append(out_i)
    #     return out
    #
    # pred_labels = pred2label(test_pred)
    # test_labels = pred2label(y_te)
    #
    # for i in [12, 17, 32, 78, 123]:
    #     print(len(pred_labels[i]), len(test_labels[i]))
    #
    # print("F1-score: {:.1%}".format(f1_score(test_labels, pred_labels)))
    # print(classification_report(test_labels, pred_labels))


##
# 05_nns_char_embed
##

from keras.layers import Conv1D, concatenate, SpatialDropout1D, GlobalMaxPooling1D



class LSTM_CharEmbedClassifier(BaseEstimator):

    def __init__(self, n_words: int, n_tags: int, max_len: int, max_len_char: int, n_chars: int, epochs=5):
        self.n_words = n_words
        self.n_tags = n_tags
        self.max_len = max_len
        self.max_len_char = max_len_char
        self.n_chars = n_chars
        self.epochs = epochs

    def _prepare_X_input(self, X):
        # reverse the word to char zip, zip(*X) is an idiom for a "unzip"
        X_word, X_char = list(zip(*X))
        X_char_reshaped = np.array(X_char).reshape((len(X_char), self.max_len, self.max_len_char))
        return [np.array(X_word), X_char_reshaped]

    def fit(self, X, y):
        """
        X is a list of pairs: (word_encodings, char_encodings) for each sentence
        y is a list of tag encodings for each sentence
        """
        X_reshaped = self._prepare_X_input(X)
        y_reshaped = np.array(y).reshape(len(y), self.max_len, 1)

        self.model = self.buildmodel(max_len=self.max_len, n_words=self.n_words, n_tags=self.n_tags,
                                     max_len_char=self.max_len_char, n_chars=self.n_chars)

        self.model.fit(X_reshaped, y_reshaped, batch_size=32, epochs=self.epochs, validation_split=0.1, verbose=1)
        return self

    def predict(self, X):
        X_reshaped = self._prepare_X_input(X)
        pred = self.model.predict(X_reshaped)
        return np.argmax(pred, axis=-1)



    @classmethod
    def buildmodel(cls, max_len: int, n_words: int, n_tags: int, max_len_char: int, n_chars: int):
        # input and embedding for words
        word_in = Input(shape=(max_len,))
        emb_word = Embedding(input_dim=n_words + 2, output_dim=20,
                             input_length=max_len, mask_zero=True)(word_in)

        # input and embeddings for characters
        char_in = Input(shape=(max_len, max_len_char,))
        emb_char = TimeDistributed(Embedding(input_dim=n_chars + 2, output_dim=10,
                                             input_length=max_len_char, mask_zero=True))(char_in)
        # character LSTM to get word encodings by characters
        char_enc = TimeDistributed(LSTM(units=20, return_sequences=False,
                                        recurrent_dropout=0.5))(emb_char)

        # main LSTM
        x = concatenate([emb_word, char_enc])
        x = SpatialDropout1D(0.3)(x)
        main_lstm = Bidirectional(LSTM(units=50, return_sequences=True,
                                       recurrent_dropout=0.6))(x)
        out = TimeDistributed(Dense(n_tags + 1, activation="softmax"))(main_lstm)
        model = Model([word_in, char_in], out)
        model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["acc"])
        return model


def do_05_nns_char_embed(data: pd.DataFrame, cv=5):
    getter = SentenceGetter(data)

    words = list(set(data["Word"].values))
    words.append("ENDPAD")
    n_words = len(words)

    tags = list(set(data["Tag"].values))
    n_tags = len(tags)

    # Determine max dimensions for the sentence and words inputs
    max_len = max([len(s) for s in getter.sentences])
    max_len_char = max(len(w) for w in words)

    # Build indices for words and tags
    word2idx = {w: i + 2 for i, w in enumerate(words)}
    word2idx["UNK"] = 1
    word2idx["PAD"] = 0
    idx2word = {i: w for w, i in word2idx.items()}
    tag2idx = {t: i + 1 for i, t in enumerate(tags)}
    tag2idx["PAD"] = 0
    idx2tag = {i: w for w, i in tag2idx.items()}

    # Build an index for the characters as well
    chars = set([w_i for w in words for w_i in w])
    n_chars = len(chars)
    char2idx = {c: i + 2 for i, c in enumerate(chars)}
    char2idx["UNK"] = 1
    char2idx["PAD"] = 0

    # build a char representation for every sentence
    X_char = []
    for sentence in getter.sentences:
        sent_seq = []
        for i in range(max_len):
            word_seq = []
            for j in range(max_len_char):
                try:
                    word_seq.append(char2idx.get(sentence[i][0][j]))
                except:
                    word_seq.append(char2idx.get("PAD"))
            sent_seq.append(word_seq)
        X_char.append(np.array(sent_seq))


    # pad the input
    X_word = [[word2idx[w[0]] for w in s] for s in getter.sentences]
    X_word_padded = pad_sequences(maxlen=max_len, sequences=X_word, value=word2idx["PAD"], padding='post', truncating='post')
    y = [[tag2idx[w[2]] for w in s] for s in getter.sentences]
    y_padded = pad_sequences(maxlen=max_len, sequences=y, value=tag2idx["PAD"], padding='post', truncating='post')

    # we deviate from the tutorial: zip the input to provide a single
    # input to the crossprediction step
    X_input = list(zip(X_word_padded, X_char))
    classifier = LSTM_CharEmbedClassifier(max_len=max_len, n_words=n_words, n_tags=n_tags,
                                                max_len_char=max_len_char, n_chars=n_chars, epochs=10)

    # this would train the classifier and print a result sentence with predicted labels:
    # classifier.fit(X_input, y_padded)
    # i = 23
    # p = classifier.predict([X_input[i]])[0]
    # for w, t, pred in zip(X_word[i], y[i], p):
    #     if w != 0:
    #         print("{:15}: {:5} {}".format(idx2word[w], idx2tag[t], idx2tag[pred]))

    # make the prediction
    pred_padded = cross_val_predict(estimator=classifier, X=X_input, y=y_padded, cv=cv)

    # this reverses the effects of labelling and padding
    pred_a = shorten_lists(pred_padded, y)
    # this is not strictly needed but makes sure, that the tags reported are understandable
    pred_b = [[idx2tag[i] for i in s] for s in pred_a]
    y_true = [[idx2tag[i] for i in s] for s in y]

    result = EvalResult.default_eval("05: LSTM chars embed", pred_b, y_true)
    return result

    # tutorial part:
    # X_word_tr, X_word_te, y_tr, y_te = train_test_split(X_word_padded, y_padded, test_size=0.1, random_state=2018)
    # X_char_tr, X_char_te, _, _ = train_test_split(X_char, y_padded, test_size=0.1, random_state=2018)
    # model = LSTM_CharEmbedClassifier.buildmodel(max_len=max_len, n_words=n_words, n_tags=n_tags,
    #                                             max_len_char=max_len_char, n_chars=n_chars)
    #
    # X_char_reshaped = np.array(X_char_tr).reshape((len(X_char_tr), max_len, max_len_char))
    # y_reshaped = np.array(y_tr).reshape(len(y_tr), max_len, 1)
    #
    # print(type(X_word_tr), type(X_word_tr[0]))
    # print(type(X_char_reshaped), type(X_char_reshaped[0]))
    # print(type(y_reshaped), type(y_reshaped[0]))
    #
    # model.fit([X_word_tr, X_char_reshaped], y_reshaped,
    #           batch_size=32, epochs=10, validation_split=0.1, verbose=1)
    #
    # print(model.summary())
    #
    # y_pred = model.predict([X_word_te,
    #                         np.array(X_char_te).reshape((len(X_char_te),
    #                                                      max_len, max_len_char))])
    # i = 23
    # p = np.argmax(y_pred[i], axis=-1)
    # print("{:15}||{:5}||{}".format("Word", "True", "Pred"))
    # print(30 * "=")
    # for w, t, pred in zip(X_word_te[i], y_te[i], p):
    #     if w != 0:
    #         print("{:15}: {:5} {}".format(idx2word[w], idx2tag[t], idx2tag[pred]))




##
# 05_elmo
##

import tensorflow as tf
import tensorflow_hub as hub
from keras import backend as K
from keras.layers.merge import add
from keras.layers import Lambda


class ELMoClassifier(BaseEstimator):

    def __init__(self, n_tags: int, max_len: int, batch_size: int, epochs=5):
        self.n_tags = n_tags
        self.max_len = max_len
        self.batch_size = batch_size
        self.epochs = epochs

    def fit(self, X, y):
        # adjust data sizes to multiples of the batch size (rounds down, sacrifices max two batches
        # in the the middle which are neither used for training nor for validation)
        batch_size = self.batch_size
        n_train = int((len(X) * (9/10)) / batch_size) * batch_size
        n_val =   int((len(X) * (1/10)) / batch_size) * batch_size
        # useful for program tests with very few input sentences
        if n_val < batch_size:
            n_val = batch_size

        print("train/val: ", n_train, n_val)
        X, X_val = X[:n_train], X[:n_val]
        y, y_val = y[:n_train], y[:n_val]

        # Not sure what this is good for
        y = y.reshape(y.shape[0], y.shape[1], 1)
        y_val = y_val.reshape(y_val.shape[0], y_val.shape[1], 1)

        # actually fit the model
        self.model = self.buildmodel(n_tags=self.n_tags, max_len=self.max_len, batch_size=batch_size)
        self.model.fit(np.array(X), y, validation_data=(np.array(X_val), y_val),
                  batch_size=batch_size, epochs=self.epochs, verbose=1)
        return self

    def predict(self, X):
        if (len(X) % self.batch_size != 0):
            print("WARN: prediction input not divisible by batch size:", len(X), "/", self.batch_size)
        pred = self.model.predict(X)
        return np.argmax(pred, axis=-1)


    @classmethod
    def buildmodel(cls, n_tags: int, max_len: int, batch_size: int):
        # the elmo embeddings are downloaded (if necessary) and initialized here
        sess = tf.Session()
        K.set_session(sess)
        elmo_model = hub.Module("https://tfhub.dev/google/elmo/2", trainable=True)
        sess.run(tf.global_variables_initializer())
        sess.run(tf.tables_initializer())

        def ElmoEmbedding(x):
            return elmo_model(inputs={
                "tokens": tf.squeeze(tf.cast(x, tf.string)),
                "sequence_len": tf.constant(batch_size * [max_len])
            },
                signature="tokens",
                as_dict=True)["elmo"]

        # build the actual model
        input_text = Input(shape=(max_len,), dtype=tf.string)
        embedding = Lambda(ElmoEmbedding, output_shape=(None, max_len, 1024))(input_text)
        x = Bidirectional(LSTM(units=512, return_sequences=True,
                               recurrent_dropout=0.2, dropout=0.2))(embedding)
        x_rnn = Bidirectional(LSTM(units=512, return_sequences=True,
                                   recurrent_dropout=0.2, dropout=0.2))(x)
        x = add([x, x_rnn])  # residual connection to the first biLSTM
        out = TimeDistributed(Dense(n_tags, activation="softmax"))(x)
        model = Model(input_text, out)
        model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
        return model


def do_06_elmo(data: pd.DataFrame, cv=5):

    # needed for elmo embedding initialization and later for adjusting the training data
    batch_size = 32
    sentences = SentenceGetter(data).sentences

    # for this example the data size must be a multiple of the batch size always, so we reduce
    # it early on to a multiple of that and the cv amount
    len_before = len(sentences)
    while (len(sentences) % (cv * batch_size) != 0):
        sentences.pop()
    print("Using input sentences: %d, threw away: %d" % (len(sentences), len_before - len(sentences)))

    # length of the longest sentence in the data
    max_len = max(len(s) for s in sentences)

    # sets of all different words/tags
    words = list(set(data["Word"].values))
    # words.append("__PAD__")
    n_words = len(words)
    tags = list(set(data["Tag"].values))
    n_tags = len(tags)

    # we need actual words this time, manually pad them to max_len
    X = [[w[0] for w in s] for s in sentences]
    X_padded = [ws + ["__PAD__"] * (max_len - len(ws)) for ws in X]

    # tags are still represented by numbers
    tag2idx = {t: i for i, t in enumerate(tags)}
    idx2tag = {i: w for w, i in tag2idx.items()}
    y = [[tag2idx[w[2]] for w in s] for s in sentences]
    y_padded = pad_sequences(maxlen=max_len, sequences=y, padding="post", value=tag2idx["O"])

    # define the classifier and make a cross predicttion of the whole input
    classifier = ELMoClassifier(n_tags=n_tags, max_len=max_len, batch_size=batch_size, epochs=5)
    pred_padded = cross_val_predict(estimator=classifier, X=X_padded, y=y_padded, cv=cv)

    # this reverses the effects of labeling and padding
    pred_a = shorten_lists(pred_padded, y)
    # this is not strictly needed but makes sure, that the tags reported are understandable
    pred_b = [[idx2tag[i] for i in s] for s in pred_a]
    y_true = [[idx2tag[i] for i in s] for s in y]

    result = EvalResult.default_eval("06: ELMo", pred_b, y_true)
    return result

    # Below is the tutorial content:
    # divide train and test sets
    # X_tr, X_te, y_tr, y_te = train_test_split(X_padded, y_padded, test_size=0.1, random_state=2018)
    #
    # model = ELMoClassifier.buildmodel(max_len=max_len, n_tags=n_tags, batch_size=batch_size)
    #
    # # adjust data sizes to multiples of the batch size (rounds down, sacrifices max two batches
    # # in the the middle which are neither used for training nor for validation)
    # n_train = int((len(X_tr) * (9/10)) / batch_size) * batch_size
    # n_val =   int((len(X_tr) * (1/10)) / batch_size) * batch_size
    # # useful for program tests with very few input sentences
    # if n_val < batch_size:
    #     n_val = batch_size
    #
    # print("train/val: ", n_train, n_val)
    # X_tr, X_val = X_tr[:n_train], X_tr[:n_val]
    # y_tr, y_val = y_tr[:n_train], y_tr[:n_val]
    #
    # # Not sure what this is good for
    # y_tr = y_tr.reshape(y_tr.shape[0], y_tr.shape[1], 1)
    # y_val = y_val.reshape(y_val.shape[0], y_val.shape[1], 1)
    #
    # # actually fit the model
    # history = model.fit(np.array(X_tr), y_tr, validation_data=(np.array(X_val), y_val),
    #                     batch_size=batch_size, epochs=5, verbose=1)
    # hist = pd.DataFrame(history.history)
    # print(hist)
    #
    # # only useful for program tests with very few input sequences
    # while (len(X_te) < batch_size):
    #     X_te += X_te
    #
    # # print some predictions
    # i = 0
    # p = model.predict(np.array(X_te[i:i + batch_size]))[0]
    # print(p)
    # p = np.argmax(p, axis=-1)
    # print(p)
    # print("{:15} {:5}: ({})".format("Word", "Pred", "True"))
    # print("=" * 30)
    # for w, true, pred in zip(X_te[i], y_te[i], p):
    #     if w != "__PAD__":
    #         print("{:15}:{:5} ({})".format(w, tags[pred], tags[true]))


def replace_words_with_occurences_less_than(data: pd.DataFrame, n=10, replacement="__RARE_WORD__"):

    words = [w for w in data["Word"]]
    words2counts = {w: 0 for w in set(words)}
    for w in words:
        words2counts[w] += 1

    below = len([w for w, c in words2counts.items() if c < n])
    print("Replacing words occuring less than %d times: %d (%.2f from %d)" %\
          (n, below, (below / len(words)), len(words)))

    words2replacement = {w: w for w in words}
    for w, c in words2counts.items():
        if c < n:
            words2replacement[w] = replacement
    data["Word"].replace(to_replace=words2replacement, inplace=True)




if __name__ == '__main__':

    import time

    # NOTE: This follows and slightly builds upon this tutorial series
    #       https://www.depends-on-the-definition.com/sequence-tagging-lstm-crf/

    description = "Test some NER. Needs a table as input that can be created with" + \
                    "postprocessing/docs_to_sentences_table.py"

    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument("datapath", type=str, help="Path to a csv containing sentence#, word, POS-, and NER-tags.")
    argparser.add_argument("--test", action='store_true', help="If set, only use a very small portion of the data.")
    argparser.add_argument("--cv", type=int, default=5, help="The number of crossevaluation-predictions to perform.")
    argparser.add_argument("--quota", type=float, default=1.0, help="Use only the given fraction of the data.")
    argparser.add_argument("--words-replace", type=int, default=0, help="Mask words that are used less than n times by simple replacement.")

    args = argparser.parse_args()
    try:
        data = pd.read_csv(args.datapath, encoding="utf-8")
    except UnicodeDecodeError:
        data = pd.read_csv(args.datapath, encoding="latin1")
    data = data.fillna(method='ffill')

    if args.test:
        data = data.tail(8000)

    if args.quota < 1.0 and args.quota > 0.0:
        new_len = int(len(data) * args.quota)
        print("Using %.2f * %d = %d data rows." % (args.quota, len(data), new_len))
        data = data.head(new_len)
    else:
        print("Using n rows of data:", len(data))

    if args.words_replace > 0:
        replace_words_with_occurences_less_than(data, args.words_replace)

    methods = [
        do_01_intro,
        do_02_crfs,
        # do_03_nns_variant,
        # do_04_nns_crfs,
        # do_05_nns_char_embed,
        # do_06_elmo,
        # do_07_bert
    ]
    results = []
    for method in methods:
        print("~~~~~> start:", method.__name__)
        start = time.time()
        results.append(method(data, cv=args.cv))
        end = time.time()
        print("~~~~~> end:", method.__name__, "took: ", (end - start), "s")

    header =   "                     | PREC  | REC   | F1    | ACC   | labels"
    template =                 "%20s | %5.2f | %5.2f | %5.2f | %5.2f | %s    "
    print(header)
    for r in results:
        print(template % (r.name, r.precision, r.recall, r.f1, r.accuracy, ",".join(r.labels)))

    for r in results:
        print("~~~~", r.name, "~~~~")
        print(r.report)

