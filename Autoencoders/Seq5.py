import helpers
import numpy as np
import tensorflow as tf
import json
import os
from itertools import cycle
from tensorflow.python.saved_model import builder as model_serialization

tf.reset_default_graph()
sess = tf.InteractiveSession()

print(tf.__version__)

weights_file = open("weights", "r")
weights = np.array(json.loads(weights_file.read()))

PAD = 0
EOS = 1

vocab_size = weights.shape[0]
input_embedding_size = weights.shape[1]

encoder_hidden_units = 20
decoder_hidden_units = encoder_hidden_units

encoder_inputs = tf.placeholder(shape=(None, None), dtype=tf.int32, name='encoder_inputs')
decoder_targets = tf.placeholder(shape=(None, None), dtype=tf.int32, name='decoder_targets')

decoder_inputs = tf.placeholder(shape=(None, None), dtype=tf.int32, name='decoder_inputs')

embeddings = tf.Variable(tf.random_uniform([vocab_size, input_embedding_size], -1.0, 1.0), dtype=tf.float32)

encoder_inputs_embedded = tf.nn.embedding_lookup(embeddings, encoder_inputs)
decoder_inputs_embedded = tf.nn.embedding_lookup(embeddings, decoder_inputs)

encoder_cell = tf.contrib.rnn.LSTMCell(encoder_hidden_units)

encoder_outputs, encoder_final_state = tf.nn.dynamic_rnn(
    encoder_cell, encoder_inputs_embedded,
    dtype=tf.float32, time_major=True,
)

print(encoder_final_state)

decoder_cell = tf.contrib.rnn.LSTMCell(decoder_hidden_units)

decoder_outputs, decoder_final_state = tf.nn.dynamic_rnn(
    decoder_cell, decoder_inputs_embedded,

    initial_state=encoder_final_state,

    dtype=tf.float32, time_major=True, scope="plain_decoder",
)

decoder_logits = tf.contrib.layers.linear(decoder_outputs, vocab_size)
decoder_prediction = tf.argmax(decoder_logits, 2)

print(decoder_logits)

stepwise_cross_entropy = tf.nn.softmax_cross_entropy_with_logits(
    labels=tf.one_hot(decoder_targets, depth=vocab_size, dtype=tf.float32),
    logits=decoder_logits,
)

loss = tf.reduce_mean(stepwise_cross_entropy)
train_op = tf.train.AdamOptimizer().minimize(loss)

sess.run(tf.global_variables_initializer())

sess.run(embeddings.assign(weights))

batch_size = 100
batches = helpers.random_sequences(length_from=1, length_to=8,
                                   vocab_lower=2, vocab_upper=vocab_size,
                                   batch_size=batch_size)

'''file = open("indiciesOriginCode", "r")
batches = np.array(json.loads(file.read()))'''


'''batches = helpers.random_sequences(length_from=3, length_to=8,
                                   vocab_lower=2, vocab_upper=10,
                                   batch_size=batch_size)'''

'''print('head of the batch:')
for seq in next(batches)[:10]:
    print(seq)'''


def next_feed():
    #batch = batches
    batch = next(batches)
    encoder_inputs_, _ = helpers.batch(batch)
    decoder_targets_, _ = helpers.batch(
        [(sequence) + [EOS] for sequence in batch]
    )
    decoder_inputs_, _ = helpers.batch(
        [[EOS] + (sequence) for sequence in batch]
    )
    return {
        encoder_inputs: encoder_inputs_,
        decoder_inputs: decoder_inputs_,
        decoder_targets: decoder_targets_,
    }

saver = tf.train.Saver()
loss_track = []
max_batches = 5001
batches_in_epoch = 1000

try:
    for batch in range(max_batches):
        fd = next_feed()
        _, l = sess.run([train_op, loss], fd)
        loss_track.append(l)
        current_loss = sess.run(loss, fd)
        print('\rBatch ' + str(batch) + '/' + str(max_batches) + ' loss: ' + str(current_loss), end="")

        if batch == 0 or batch % batches_in_epoch == 0:
            print('\nbatch {}'.format(batch))
            print('  minibatch loss: {}'.format(current_loss))#sess.run(loss, fd)))
            predict_ = sess.run(decoder_prediction, fd)
            for i, (inp, pred) in enumerate(zip(fd[encoder_inputs].T, predict_.T)):
                print('  sample {}:'.format(i + 1))
                print('    input     > {}'.format(inp))
                print('    predicted > {}'.format(pred))
                if i >= 2:
                    break
            print()
except KeyboardInterrupt:
    print('training interrupted')

directory = 'trainedModel'
if os.path.exists(directory):
    os.rmdir(directory)

print('Exporting train model to {}'.format(directory))

builder = model_serialization.SavedModelBuilder(directory)
builder.add_meta_graph_and_variables(sess, ['TRAINING'])
builder.save()

import matplotlib.pyplot as plt
plt.plot(loss_track)
plt.savefig('plotfig.png')
print('loss {:.4f} after {} examples (batch_size={})'.format(loss_track[-1], len(loss_track)*batch_size, batch_size))

print('saved_model.loader.load')
tf.saved_model.loader.load(sess, ['TRAINING'], directory)

print('pred')
predict_ = sess.run(decoder_prediction, fd)
for pred in enumerate(zip(predict_.T)):
    print(pred)

