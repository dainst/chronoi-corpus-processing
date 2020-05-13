##
# 07_bert
##

import torch
from torch.optim import Adam
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from pytorch_pretrained_bert import BertTokenizer, BertConfig
from pytorch_pretrained_bert import BertForTokenClassification, BertAdam
from tqdm import trange


def do_07_bert(data: pd.DataFrame, cv=5):
    # This has multiple issues, that we couldn't fix at this moment

    # TODO: Try with cased model
    # TODO: Try with data already tokenized by BERT tokenizer
    # TODO: Fix Out uf memory error if possible
    model_name = 'bert-base-uncased'

    getter = SentenceGetter(data)

    # we need actual sentences this time as bert provides a tagger we will re-use
    sentences = [" ".join([s[0] for s in sentence]) for sentence in getter.sentences]
    labels = [[s[2] for s in sent] for sent in getter.sentences]

    tags_vals = list(set(data["Tag"].values))
    tag2idx = {t: i for i, t in enumerate(tags_vals)}

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    n_gpu = torch.cuda.device_count()

    bs = batch_size = 32

    # use berts tokenizer
    tokenizer = BertTokenizer.from_pretrained(model_name, do_lower_case=True)
    tokenized_texts = [tokenizer.tokenize(sent) for sent in sentences]

    MAX_LEN = max(len(s) for s in tokenized_texts)
    print("MAX_LEN: %d" % MAX_LEN)

    # NOTE: The tutorial seems to assume that bert and our input are basically tokenized
    #       to the same units making the labels still applicable to the input
    #       Result of the below for the original texts is:
    #           Mean: 2.68, differing: 0.73
    # for i in [4, 7, 58, 1200]:
    #     print(sentences[i])
    #     print(tokenized_texts[i])
    #     print("---")
    # differences = [len(tokenized_texts[i]) - len(labels[i]) for i in range(len(sentences))]
    # differences = [d * -1  if d < 0 else d for d in differences]
    # mean = sum(differences) / len(differences)
    # print("Mean: %.2f, differing: %.2f" % (mean, len([d for d in differences if d != 0]) / len(sentences)))

    # Pad the inputs
    input_ids = pad_sequences([tokenizer.convert_tokens_to_ids(txt) for txt in tokenized_texts],
                              maxlen=MAX_LEN, dtype="long", truncating="post", padding="post")

    tags = pad_sequences([[tag2idx.get(l) for l in lab] for lab in labels], value=tag2idx["O"],
                         maxlen=MAX_LEN, dtype="long", padding="post", truncating="post")

    # Prepare test and training data
    attention_masks = [[float(i > 0) for i in ii] for ii in input_ids]
    tr_inputs, val_inputs, tr_tags, val_tags = train_test_split(input_ids, tags,
                                                                random_state=2018, test_size=0.1)
    tr_masks, val_masks, _, _ = train_test_split(attention_masks, input_ids,
                                                 random_state=2018, test_size=0.1)
    tr_inputs = torch.tensor(tr_inputs)
    val_inputs = torch.tensor(val_inputs)
    tr_tags = torch.tensor(tr_tags)
    val_tags = torch.tensor(val_tags)
    tr_masks = torch.tensor(tr_masks)
    val_masks = torch.tensor(val_masks)

    # training will be shuffled
    train_data = TensorDataset(tr_inputs, tr_masks, tr_tags)
    train_sampler = RandomSampler(train_data)
    train_dataloader = DataLoader(train_data, sampler=train_sampler, batch_size=bs)

    # test data will be given sequentially
    valid_data = TensorDataset(val_inputs, val_masks, val_tags)
    valid_sampler = SequentialSampler(valid_data)
    valid_dataloader = DataLoader(valid_data, sampler=valid_sampler, batch_size=bs)

    # load the model and send params to gpu if available
    model = BertForTokenClassification.from_pretrained("bert-base-uncased", num_labels=len(tag2idx))
    if device.type == "cuda":
        model.cuda()

    # Paramaters for finetuning
    FULL_FINETUNING = True
    if FULL_FINETUNING:
        # "We also add some weight_decay as regularization to the main weight matrices."
        param_optimizer = list(model.named_parameters())
        no_decay = ['bias', 'gamma', 'beta']
        optimizer_grouped_parameters = [
            {'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)],
             'weight_decay_rate': 0.01},
            {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay)],
             'weight_decay_rate': 0.0}
        ]
    else:
        # "If you have limited resources, you can also try to just train the linear classifier on
        # top of Bert and keep all other weights fixed. This will still give you a good performance."
        param_optimizer = list(model.classifier.named_parameters())
        optimizer_grouped_parameters = [{"params": [p for n, p in param_optimizer]}]
    optimizer = Adam(optimizer_grouped_parameters, lr=3e-5)

    # A function for finetuning
    def flat_accuracy(preds, labels):
        pred_flat = np.argmax(preds, axis=2).flatten()
        labels_flat = labels.flatten()
        return np.sum(pred_flat == labels_flat) / len(labels_flat)

    # RUN FINE-TUNING
    epochs = 5
    max_grad_norm = 1.0

    for _ in trange(epochs, desc="Epoch"):
        # TRAIN loop
        model.train()
        tr_loss = 0
        nb_tr_examples, nb_tr_steps = 0, 0
        for step, batch in enumerate(train_dataloader):
            # add batch to gpu
            print(batch)
            batch = tuple(t.to(device) for t in batch)
            print(batch)
            b_input_ids, b_input_mask, b_labels = batch
            # forward pass
            loss = model(b_input_ids, token_type_ids=None,
                         attention_mask=b_input_mask, labels=b_labels)
            # backward pass
            loss.backward()
            # track train loss
            tr_loss += loss.item()
            nb_tr_examples += b_input_ids.size(0)
            nb_tr_steps += 1
            # gradient clipping
            torch.nn.utils.clip_grad_norm_(parameters=model.parameters(), max_norm=max_grad_norm)
            # update parameters
            optimizer.step()
            model.zero_grad()
        # print train loss per epoch
        print("Train loss: {}".format(tr_loss / nb_tr_steps))
        # VALIDATION on validation set
        model.eval()
        eval_loss, eval_accuracy = 0, 0
        nb_eval_steps, nb_eval_examples = 0, 0
        predictions, true_labels = [], []
        for batch in valid_dataloader:
            batch = tuple(t.to(device) for t in batch)
            b_input_ids, b_input_mask, b_labels = batch

            with torch.no_grad():
                tmp_eval_loss = model(b_input_ids, token_type_ids=None,
                                      attention_mask=b_input_mask, labels=b_labels)
                logits = model(b_input_ids, token_type_ids=None,
                               attention_mask=b_input_mask)
            logits = logits.detach().cpu().numpy()
            label_ids = b_labels.to('cpu').numpy()
            predictions.extend([list(p) for p in np.argmax(logits, axis=2)])
            true_labels.append(label_ids)

            tmp_eval_accuracy = flat_accuracy(logits, label_ids)

            eval_loss += tmp_eval_loss.mean().item()
            eval_accuracy += tmp_eval_accuracy

            nb_eval_examples += b_input_ids.size(0)
            nb_eval_steps += 1
        eval_loss = eval_loss / nb_eval_steps
        print("Validation loss: {}".format(eval_loss))
        print("Validation Accuracy: {}".format(eval_accuracy / nb_eval_steps))
        pred_tags = [tags_vals[p_i] for p in predictions for p_i in p]
        valid_tags = [tags_vals[l_ii] for l in true_labels for l_i in l for l_ii in l_i]
        print("F1-Score: {}".format(f1_score(pred_tags, valid_tags)))

    # EVALUATION
    model.eval()
    predictions = []
    true_labels = []
    eval_loss, eval_accuracy = 0, 0
    nb_eval_steps, nb_eval_examples = 0, 0
    for batch in valid_dataloader:
        batch = tuple(t.to(device) for t in batch)
        b_input_ids, b_input_mask, b_labels = batch

        with torch.no_grad():
            tmp_eval_loss = model(b_input_ids, token_type_ids=None,
                                  attention_mask=b_input_mask, labels=b_labels)
            logits = model(b_input_ids, token_type_ids=None,
                           attention_mask=b_input_mask)

        logits = logits.detach().cpu().numpy()
        predictions.extend([list(p) for p in np.argmax(logits, axis=2)])
        label_ids = b_labels.to('cpu').numpy()
        true_labels.append(label_ids)
        tmp_eval_accuracy = flat_accuracy(logits, label_ids)

        eval_loss += tmp_eval_loss.mean().item()
        eval_accuracy += tmp_eval_accuracy

        nb_eval_examples += b_input_ids.size(0)
        nb_eval_steps += 1

    pred_tags = [[tags_vals[p_i] for p_i in p] for p in predictions]
    valid_tags = [[tags_vals[l_ii] for l_ii in l_i] for l in true_labels for l_i in l]
    print("Validation loss: {}".format(eval_loss / nb_eval_steps))
    print("Validation Accuracy: {}".format(eval_accuracy / nb_eval_steps))
    print("Validation F1-Score: {}".format(f1_score(pred_tags, valid_tags)))

    exit()
