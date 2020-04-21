'''Train a simple deep CNN on the CIFAR10 small images dataset.
It gets to 75% validation accuracy in 25 epochs, and 79% after 50 epochs.
(it's still underfitting at that point, though).
'''
import os

# os.environ["KERAS_BACKEND"] = "plaidml.keras.backend"
# os.environ["RUNFILES_DIR"] = "/usr/local/share/plaidml"
# os.environ["PLAIDML_NATIVE_PATH"] = "/usr/local/lib/libplaidml.dylib"

import keras
from keras.datasets import cifar10
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D, Activation

import deepkit

import sys
print(os.getcwd())
print(__file__)
print(sys.path)
print(os.listdir("/"))

experiment = deepkit.experiment()
experiment.add_file(__file__)

batch_size = experiment.intconfig('batch_size', 16)
num_classes = 10
epochs = experiment.intconfig('epochs', 15)
data_augmentation = experiment.boolconfig('data_augmentation', False)
num_predictions = 20

save_dir = os.path.join(os.getcwd(), 'saved_models')
model_name = 'keras_cifar10_trained_model.h5'

# The data, split between train and test sets:
(x_train, y_train), (x_test, y_test) = cifar10.load_data()

labels = ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']

x_train = x_train[0:experiment.intconfig('train_samples', 10000)]
y_train = y_train[0:experiment.intconfig('train_samples', 10000)]

x_test = x_test[0:experiment.intconfig('test_samples', 10000)]
y_test = y_test[0:experiment.intconfig('test_samples', 10000)]

experiment.log_insight(*x_train[0:50], name='samples/train/sample')

for i, x in enumerate(x_test[0:20]):
    experiment.log_insight(x, name='samples/test/sample_' + str(i), meta=labels[y_test[i][0]])

experiment.log_insight({'my-data': 123, 'more': True}, name='json-like/sample1')
experiment.log_insight({'my-data': 234, 'more': False}, name='json-like/sample2')
experiment.log_insight(12312312.333, name='json-like/sample3')
experiment.log_insight("This is just text\nYay.", name='json-like/sample4')
experiment.log_insight(
    "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's "
    "standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make "
    "a type specimen book. It has survived not only five centuries.",
    name='json-like/sample5')
experiment.log_insight(x_test[0], name='numpy-shizzle/sample1', image_convertion=False)
experiment.log_insight(x_test[1], name='numpy-shizzle/sample2', image_convertion=False)
experiment.log_insight(x_test[2], name='numpy-shizzle/sample3', image_convertion=False)
experiment.log_insight(x_test[3], name='numpy-shizzle/sample4', image_convertion=False)
experiment.log_insight(y_test[0:50], name='numpy-shizzle/y_test', image_convertion=False)

print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')
print(x_test.shape[0], 'test samples')

# Convert class vectors to binary class matrices.
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

model = Sequential()
model.add(Conv2D(12, kernel_size=(3, 3), input_shape=x_train.shape[1:]))
model.add(Activation('relu'))
model.add(Conv2D(64, (3, 3)))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Conv2D(64, (3, 3), padding='same'))
model.add(Activation('relu'))
model.add(Conv2D(64, (3, 3)))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(512))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes))
model.add(Activation('softmax'))

opt = keras.optimizers.Adadelta(lr=experiment.floatconfig('lr', 0.1))

deepkit_callback = experiment.create_keras_callback(model)

callbacks = [deepkit_callback]

# Let's train the model using RMSprop
model.compile(loss='categorical_crossentropy',
              optimizer=opt,
              metrics=['accuracy'])

model.summary()

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255

if not data_augmentation:
    print('Not using data augmentation.')
    model.fit(x_train, y_train,
              batch_size=batch_size,
              epochs=epochs,
              callbacks=callbacks,
              validation_data=(x_test, y_test),
              shuffle=True)
else:
    print('Using real-time data augmentation.')
    # This will do preprocessing and realtime data augmentation:
    datagen = ImageDataGenerator(
        featurewise_center=False,  # set input mean to 0 over the dataset
        samplewise_center=False,  # set each sample mean to 0
        featurewise_std_normalization=False,  # divide inputs by std of the dataset
        samplewise_std_normalization=False,  # divide each input by its std
        zca_whitening=False,  # apply ZCA whitening
        zca_epsilon=1e-06,  # epsilon for ZCA whitening
        rotation_range=0,  # randomly rotate images in the range (degrees, 0 to 180)
        # randomly shift images horizontally (fraction of total width)
        width_shift_range=0.1,
        # randomly shift images vertically (fraction of total height)
        height_shift_range=0.1,
        shear_range=0.,  # set range for random shear
        zoom_range=0.,  # set range for random zoom
        channel_shift_range=0.,  # set range for random channel shifts
        # set mode for filling points outside the input boundaries
        fill_mode='nearest',
        cval=0.,  # value used for fill_mode = "constant"
        horizontal_flip=True,  # randomly flip images
        vertical_flip=False,  # randomly flip images
        # set rescaling factor (applied before any other transformation)
        rescale=None,
        # set function that will be applied on each input
        preprocessing_function=None,
        # image data format, either "channels_first" or "channels_last"
        data_format=None,
        # fraction of images reserved for validation (strictly between 0 and 1)
        validation_split=0.0)

    # Compute quantities required for feature-wise normalization
    # (std, mean, and principal components if ZCA whitening is applied).
    datagen.fit(x_train)

    # Fit the model on the batches generated by datagen.flow().
    model.fit_generator(datagen.flow(x_train, y_train,
                                     batch_size=batch_size),
                        epochs=epochs,
                        steps_per_epoch=len(x_train)/batch_size,
                        verbose=0,
                        callbacks=callbacks,
                        validation_data=(x_test, y_test),
                        workers=4)

# Save model and weights
if not os.path.isdir(save_dir):
    os.makedirs(save_dir)
model_path = os.path.join(save_dir, model_name)
model.save(model_path)
print('Saved trained model at %s ' % model_path)

# Score trained model.
scores = model.evaluate(x_test, y_test, verbose=1)
print('Test loss:', scores[0])
print('Test accuracy:', scores[1])
