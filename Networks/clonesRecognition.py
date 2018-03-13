import numpy as np
import os
import tensorflow as tf
import shutil
import json
import sys
import time
from model import Seq2seq, SiameseNetwork

tf.flags.DEFINE_string('type', 'full', 'Type of evaluation. Could be: \n\ttrain\n\teval\n\tfull')
tf.flags.DEFINE_string('data', os.path.expanduser('~/.rnncodeclones'), 'Directory with data for analysis')
tf.flags.DEFINE_integer('cpus', 1, 'Amount of threads for evaluation')
tf.flags.DEFINE_integer('gpus', 1, 'Amount of GPUs for training')

FLAGS = tf.flags.FLAGS

start = time.time()


def show_time():
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


try:
    tf.reset_default_graph()
    print(tf.__version__)

    directory_seq2seq = FLAGS.data + '/networks/seq2seqModel'
    directory_lstm = FLAGS.data + '/networks/siameseModel'

    if 'eval' != FLAGS.type:
        if os.path.exists(directory_seq2seq):
            shutil.rmtree(directory_seq2seq)
        if os.path.exists(directory_lstm):
            shutil.rmtree(directory_lstm)
        os.mkdir(directory_seq2seq)
        os.mkdir(directory_lstm)


    def train():
        seq2seqtrain()
        siamtrain()


    def seq2seqtrain():
        seq2seq_model.train(length_from, length_to, vocab_lower, vocab_size,
                            batch_size, max_batches, batches_in_epoch, directory_seq2seq)

    def siamtrain():
        origin_seq_file = open(FLAGS.data + '/vectors/indiciesOriginCode', 'r')
        orig_seq = np.array(json.loads(origin_seq_file.read()))

        eval_seq_file = open(FLAGS.data + '/vectors/EvalCode', 'r')
        eval_seq = np.array(json.loads(eval_seq_file.read()))

        mutated_seq_file = open(FLAGS.data + '/vectors/indiciesMutatedCode', 'r')
        mutated_seq = np.array(json.loads(mutated_seq_file.read()))

        eval_mutated_file = open(FLAGS.data + '/vectors/EvalMutatedCode', 'r')
        eval_mutated = np.array(json.loads(eval_mutated_file.read()))

        nonclone_file = open(FLAGS.data + '/vectors/indiciesNonClone', 'r')
        nonclone_seq = np.array(json.loads(nonclone_file.read()))

        eval_nonclone_file = open(FLAGS.data + '/vectors/EvalNonClone', 'r')
        eval_nonclone = np.array(json.loads(eval_nonclone_file.read()))

        seq2seq_eval = Seq2seq(encoder_cell, decoder_cell, vocab_size, input_embedding_size, weights, '/device:CPU:0')
        origin_encoder_states = seq2seq_eval.get_encoder_status(np.append(orig_seq,
                                                                          orig_seq[:nonclone_seq.shape[0]]),
                                                                threads_num=FLAGS.cpus)
        mutated_encoder_states = seq2seq_eval.get_encoder_status(np.append(mutated_seq, nonclone_seq),
                                                                 threads_num=FLAGS.cpus)
        answ = np.append(np.zeros(orig_seq.shape[0]), np.ones(nonclone_seq.shape[0]), axis=0)

        eval_answ = np.append(np.zeros(eval_seq.shape[0]), np.ones(eval_nonclone.shape[0]))

        # LSTM RNN model
        # _________________

        lstm_model.train(origin_encoder_states, mutated_encoder_states, answ, directory_lstm)

        eval_orig_encoder_states = seq2seq_eval.get_encoder_status(np.append(eval_seq,
                                                                             eval_seq[:eval_nonclone.shape[0]]),
                                                                   threads_num=FLAGS.cpus)
        eval_clone_encoder_states = seq2seq_eval.get_encoder_status(np.append(eval_mutated, eval_nonclone), FLAGS.cpus)

        lstm_model_eval = SiameseNetwork(encoder_hidden_units, batch_size, layers, '/device:CPU:0')
        lstm_model_eval.eval(eval_orig_encoder_states, eval_clone_encoder_states, eval_answ, threads_num=FLAGS.cpus)

    def eval():
        if seq2seq_model.restore(directory_seq2seq + '/seq2seq.ckpt') is None:
            seq2seqtrain()
        origin_seq_file = open(FLAGS.data + '/vectors/originCode', 'r')
        orig_seq = np.array(json.loads(origin_seq_file.read()))
        seq2seq_eval = Seq2seq(encoder_cell, decoder_cell, vocab_size, input_embedding_size, weights, '/device:CPU:0')
        encoder_states = seq2seq_eval.get_encoder_status(orig_seq, threads_num=FLAGS.cpus)
        if lstm_model.restore(directory_lstm + '/siam.ckpt') is None:
            siamtrain()

        lstm_model_eval = SiameseNetwork(encoder_hidden_units, batch_size, layers, '/device:CPU:0')
        lstm_model_eval.eval(encoder_states, threads_num=FLAGS.cpus)

    weights_file = open(FLAGS.data + '/networks/word2vec/pretrainedWeights', 'r')
    weights = np.array(json.loads(weights_file.read()))

    vocab_size = weights.shape[0]
    vocab_lower = 2

    length_from = 1
    length_to = 100

    batch_size = 1000
    max_batches = 5000
    batches_in_epoch = 1000

    input_embedding_size = weights.shape[1]

    layers = 10
    encoder_hidden_units = layers
    decoder_hidden_units = encoder_hidden_units

    if tf.FLAGS.gpus != '':
        enc_cells = []
        dec_cells = []
        for i in range(tf.FLAGS.gpus):
            enc_cells.append(tf.contrib.rnn.DeviceWrapper(
                tf.contrib.rnn.LSTMCell(encoder_hidden_units),
                '/device:GPU:%d' % (encoder_hidden_units % tf.FLAGS.gpus)
            ))
            dec_cells.append(tf.contrib.rnn.DeviceWrapper(
                tf.contrib.rnn.LSTMCell(decoder_hidden_units),
                '/device:GPU:%d' % (decoder_hidden_units % tf.FLAGS.gpus)
            ))

        encoder_cell = tf.contrib.rnn.MultRnnCell(enc_cells)
        decoder_cell = tf.contrib.rnn.LSTMCell(dec_cells)
    else:
        encoder_cell = tf.contrib.rnn.LSTMCell(encoder_hidden_units)
        decoder_cell = tf.contrib.rnn.LSTMCell(decoder_hidden_units)

    seq2seq_model = Seq2seq(encoder_cell, decoder_cell, vocab_size, input_embedding_size, weights, '/device:CPU:0')
    lstm_model = SiameseNetwork(encoder_hidden_units, batch_size, layers, '/device:CPU:0')

    if 'train' == FLAGS.type:
        train()
    elif 'eval' == FLAGS.type:
        eval()
    if 'full' == FLAGS.type:
        train()
        eval()

    show_time()
except KeyboardInterrupt:
    print('Keyboard interruption')
    show_time()
    sys.exit(0)
