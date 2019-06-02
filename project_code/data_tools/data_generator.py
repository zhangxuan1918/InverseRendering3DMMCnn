import pathlib
import random
import tensorflow as tf
from project_code.data_tools.data_util import load_image_labels_3dmm


def get_3dmm_fine_tune_labeled_data(data_root_folder='H:/300W-LP/300W_LP/', suffix='*/*.jpg'):
    data_root = pathlib.Path(data_root_folder)
    all_image_paths = list(data_root.glob(suffix))
    all_image_paths = [str(p) for p in all_image_paths]
    random.shuffle(all_image_paths)

    image_count = len(all_image_paths)
    print('num of images: {0}'.format(image_count))

    all_labels_paths = [p.replace('.jpg', '.mat') for p in all_image_paths]
    print('num of labels: {0}'.format(len(all_labels_paths)))

    image_label_paths_ds = tf.data.Dataset.from_tensor_slices((all_image_paths, all_labels_paths))
    image_label_ds = image_label_paths_ds.map(load_image_labels_3dmm)
    return image_label_ds
