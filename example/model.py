"function (and parameter space) definitions for hyperband"
"binary classification with Keras (multilayer perceptron)"

from os.path import join
import subprocess, h5py
from common_defs import *
import numpy as np

# a dict with x_train, y_train, x_test, y_test

from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Flatten, Activation
from keras.layers.normalization import BatchNormalization as BatchNorm
from keras.layers.convolutional import ZeroPadding2D, Conv2D
from keras.layers import GlobalMaxPooling2D
from keras.callbacks import EarlyStopping
from keras.layers.advanced_activations import *
from keras.optimizers import Adadelta,RMSprop

from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler


space = {
	'DROPOUT': hp.choice( 'drop', ( 0.1,0.5,0.75)),
	'DELTA': hp.choice( 'delta', ( 1e-04,1e-06,1e-08)),
	'MOMENT': hp.choice( 'moment', (0.9, 0.99, 0.999 )),
}


def get_params():
	params = sample( space )
	return handle_integers( params )


def print_params( params ):
	pprint({ k: v for k, v in params.items() if not k.startswith( 'layer_' )})
	print


def try_params( n_iterations, params, data=None, datamode='memory'):

    print ("iterations:", n_iterations)
    print_params( params )
    #print(data)
    batchsize = 100
    if datamode == 'memory':
        X_train, Y_train = data['train']
        X_valid, Y_valid = data['valid']

        #print(X_train)
        inputshape = np.asarray(X_train).shape[1:]
    else:
        train_generator = data['train']['gen_func'](batchsize, data['train']['path'])
        valid_generator = data['valid']['gen_func'](batchsize, data['valid']['path'])
        train_epoch_step = data['train']['n_sample'] / batchsize
        valid_epoch_step = data['valid']['n_sample'] / batchsize
        inputshape = data['train']['gen_func'](batchsize, data['train']['path']).next()[0].shape[1:]

    model = Sequential()
    #print(inputshape)
    model.add(Conv2D(128, (1, 24), padding='same', input_shape=inputshape, activation='relu'))
    model.add(GlobalMaxPooling2D())

    model.add(Dense(32,activation='relu'))
    model.add(Dropout(params['DROPOUT']))
    model.add(Dense(2))
    model.add(Activation('softmax'))

    optim = Adadelta
    myoptimizer = optim(epsilon=params['DELTA'], rho=params['MOMENT'])
    mylossfunc = 'categorical_crossentropy'
    model.compile(loss=mylossfunc, optimizer=myoptimizer,metrics=['accuracy'])

    early_stopping = EarlyStopping( monitor = 'val_loss', patience = 3, verbose = 0 )

    if datamode == 'memory':
        model.fit(
                        X_train,
                        Y_train,
                        batch_size=batchsize,
                        epochs=int( round( n_iterations )),
                        validation_data=(X_valid, Y_valid),
                        callbacks = [ early_stopping ])
        score, acc = model.evaluate(X_valid,Y_valid)
    else:
        model.fit_generator(
                        train_generator,
                        steps_per_epoch=train_epoch_step,
                        epochs=int( round( n_iterations )),
                        validation_data=valid_generator,
                        validation_steps=valid_epoch_step,
                        callbacks = [ early_stopping ])
        score, acc = model.evaluate_generator(valid_generator, steps=valid_epoch_step)

    return { 'loss': score, 'model': (model.to_json(), optim, myoptimizer.get_config(), mylossfunc) }

