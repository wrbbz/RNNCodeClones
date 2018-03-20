import numpy as np
import tensorflow as tf
import json
import sys
import os
from model import Seq2seq, SiameseNetwork

tf.flags.DEFINE_string('type', 'full', 'Type of evaluation. Could be: \n\ttrain\n\teval\n\tfull')
tf.flags.DEFINE_string('data', os.path.expanduser('~/.rnncodeclones'), 'Directory with data for analysis')
tf.flags.DEFINE_integer('cpus', 1, 'Amount of threads for evaluation')
tf.flags.DEFINE_integer('gpus', None, 'Amount of GPUs for training')

FLAGS = tf.flags.FLAGS

if len(sys.argv) < 2:
    print('Invalid usage of Seq2seq script')
    print('Please set directory with data')
    sys.exit(0)

if sys.argv[1] == '-h' or sys.argv[1] == '--help':
    print('Help message')
    sys.exit(0)

print('Arguments: {}'.format(sys.argv[1]))

tf.reset_default_graph()
print(tf.__version__)

weights_file = open(sys.argv[1] + '/networks/pretrainedWeights', 'r')
weights = np.array(json.loads(weights_file.read()))

directory_seq2seq = sys.argv[1] + '/networks/trainedModel'
directory_lstm = sys.argv[1] + '/networks/lstmTrainedModel'

vocab_size = weights.shape[0]
vocab_lower = 2
vocab_upper = vocab_size

length_from = 1
length_to = 1000

batch_size = 100
max_batches = 20000
batches_in_epoch = 1000

input_embedding_size = weights.shape[1]

layers = 5
encoder_hidden_units = layers
decoder_hidden_units = encoder_hidden_units

encoder_cell = tf.contrib.rnn.LSTMCell(encoder_hidden_units)
decoder_cell = tf.contrib.rnn.LSTMCell(decoder_hidden_units)

model = Seq2seq(encoder_cell, decoder_cell, vocab_size, input_embedding_size, weights)
model.train(length_from, length_to, vocab_lower, vocab_size,
     batch_size, max_batches, batches_in_epoch, directory_seq2seq)

origin_seq_file = open(sys.argv[1] + '/indiciesOriginCode', 'r')
orig_seq = np.array(json.loads(origin_seq_file.read()))

eval_seq_file = open(sys.argv[1] + '/EvalCode', 'r')
eval_seq = np.array(json.loads(eval_seq_file.read()))

mutated_seq_file = open(sys.argv[1] + '/indiciesMutatedCode', 'r')
mutated_seq = np.array(json.loads(mutated_seq_file.read()))

eval_mutated_file = open(sys.argv[1] + '/EvalMutatedCode', 'r')
eval_mutated = np.array(json.loads(eval_mutated_file.read()))

nonclone_file = open(sys.argv[1] + '/indiciesNonClone', 'r')
nonclone_seq = np.array(json.loads(nonclone_file.read()))

eval_nonclone_file = open(sys.argv[1] + '/EvalNonClone', 'r')
eval_nonclone = np.array(json.loads(eval_nonclone_file.read()))

origin_encoder_states = model.get_encoder_status(np.append(orig_seq, orig_seq[:nonclone_seq.shape[0]]))
mutated_encoder_states = model.get_encoder_status(np.append(mutated_seq, nonclone_seq))
answ = np.append(np.zeros(orig_seq.shape[0]), np.ones(nonclone_seq.shape[0]), axis=0)

# origin_encoder_states = model.get_encoder_status(orig_seq[:30000])
# mutated_encoder_states = model.get_encoder_status(np.append(mutated_seq[:20000], nonclone_seq[:10000]))
# answ = np.append(np.zeros(20000), np.ones(10000), axis=0)

eval_orig_encoder_states = model.get_encoder_status(np.append(eval_seq, eval_seq[:eval_nonclone.shape[0]]))
eval_clone_encoder_states = model.get_encoder_status(np.append(eval_mutated, eval_nonclone))
eval_answ = np.append(np.zeros(eval_seq.shape[0]), np.ones(eval_nonclone.shape[0]))

# print(len(origin_encoder_states))
# print(len(mutated_encoder_states))
# print(len(answ))

# LSTM RNN model
# _________________

lstm_model = SiameseNetwork(origin_encoder_states[0].shape[1], batch_size, layers)
lstm_model.train(origin_encoder_states, mutated_encoder_states, answ, directory_lstm)
lstm_model.eval(eval_orig_encoder_states, eval_clone_encoder_states, eval_answ)def show_time(start):


def train(model, length, vocab, batch, seq2seq_dir, siam_dir, vectors_dir):
    seq2seq_train(model, length, vocab, batch, seq2seq_dir)
    siam_train(vectors_dir, model, siam_dir)


def seq2seq_train(model, length, vocab, batch, directory):
    model.train(length['from'], length['to'], vocab['lower'], vocab['size'],
                batch['size'], batch['max'], batch['epoch'], directory)


def siam_train(vectors, seq2seq_model, directory):
    orig_file = open(vectors + '/indiciesOriginCode', 'r') # correct indices
    mutated_file = open(vectors + '/indiciesMutatedCode', 'r')
    nonclone_file = open(vectors + '/indiciesNonClone', 'r')

    orig_seq = np.array(json.loads(orig_file.read()))
    mutated_seq = np.array(json.loads(mutated_file.read()))
    nonclone_seq = np.array(json.loads(nonclone_file.read()))

    orig_encst = seq2seq_model.get_encoder_status(np.append(orig_seq, orig_seq[:nonclone_seq.shape[0]]))
    mut_encst = seq2seq_model.get_encoder_status(np.append(mutated_seq, nonclone_seq))
    answ = np.append(np.zeros(orig_seq.shape[0]), np.ones(nonclone_seq.shape[0]), axis=0)

    lstm_model = SiameseNetwork(orig_encst[0].shape[1], batch_size, layers)
    lstm_model.train(orig_encst, mut_encst, answ, directory)


    end = time.time()
    secs = round(end - start, 3)
    mins = 0
    hour = 0

    if secs > 59:
        mins = (int)(secs / 60)
        secs -= mins * 60
        if mins > 59:
            hour = (int)(mins / 60)
            mins -= hour * 60

    if mins < 10:
        mins = '0' + str(mins)
    print('\nElapsed time: {}:{}:{}'.format(hour, mins, round(secs, 3)))
