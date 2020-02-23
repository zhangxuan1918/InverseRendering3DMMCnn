import scipy.io as sio
import numpy as np
import tensorflow as tf


def fn_extract_300W_LP_labels(bfm_path, image_size, is_aflw_2000=False):
    # Load BFM
    content = sio.loadmat(bfm_path)
    model = content['model']
    model = model[0, 0]

    shape_ev = model['shapeEV'].astype(np.float32)
    tex_ev = model['texEV'].astype(np.float32)
    image_size = 1.0 * image_size

    def get_labels(img_filename, rescale=1.0):
        # label file has the same name as image
        # mat format
        # roi: shape=(1, 4)
        # Shape_Para: shape=(199, 1)
        # Pose_Para: shape=(1, 7)
        # Exp_Para: shape=(29, 1)
        # Color_Para: shape=(1, 6): remove last value as it's always 1
        # Illum_Para: shape=(1, 9): remove last value as it's always 2
        # pt2d: shape=(2, 68)
        # Tex_Para: shape=(40, 1)
        # Total: 430 params

        mat_filename = '.'.join(img_filename.split('.')[:-1]) + '.mat'
        mat = sio.loadmat(mat_filename)

        # update pose param due to image resizing
        pp = mat['Pose_Para']
        pp[0, 3:6] /= image_size  # translation in 3d
        pp[0, 6] *= 1000  # scaling

        # update landmarks
        if is_aflw_2000:
            lm = mat['pt3d_68'][:2, :] * rescale
        else:
            lm = mat['pt2d'] * rescale

        lm = np.reshape(lm, (-1,))  # to recover lm, np.reshape(lm, (2, -1))

        # update roi
        roi = np.round(mat['roi'] * rescale)

        # rescale shape, exp and tex by their eigenvalue
        shape_para = mat['Shape_Para'] / shape_ev
        exp_para = mat['Exp_Para']
        tex_para = mat['Tex_Para'] / tex_ev

        color_para = mat['Color_Para'][:, :6]
        illum_para = mat['Illum_Para'][:, :9]
        return np.concatenate((roi, lm, pp, shape_para, exp_para, color_para, illum_para, tex_para[:40, :]), axis=None)

    return get_labels


def split_300W_LP_labels(labels):
    # roi: shape=(1, 4)
    # Shape_Para: shape=(199, 1)
    # Pose_Para: shape=(1, 7)
    # Exp_Para: shape=(29, 1)
    # Color_Para: shape=(1, 6): remove last value as it's always 1
    # Illum_Para: shape=(1, 9): remove last value as it's always 2
    # pt2d: shape=(2, 68)
    # Tex_Para: shape=(40, 1)
    # Total: 430 params
    """

    :param labels:
    :return:

    roi: shape=(None, 4)
    Shape_Para: shape=(None, 199)
    Pose_Para: shape=(None, 7)
    Exp_Para: shape=(None, 29)
    Color_Para: shape=(None, 6): remove last value as it's always 1
    Illum_Para: shape=(None, 9): remove last value as it's always 2
    pt2d: shape=(None, 136)
    Tex_Para: shape=(None, 40)
    """
    assert isinstance(labels, tf.Tensor) and labels.shape[1] == 430
    roi, lm, pp, shape_para, exp_para, color_para, illum_para, tex_para = \
        tf.split(labels, num_or_size_splits=[4, 136, 7, 199, 29, 6, 9, 40],  axis=1)
    return roi, lm, pp, shape_para, exp_para, color_para, illum_para, tex_para


def fn_unnormalize_300W_LP_labels(bfm_path, image_size):
    # roi: shape=(None, 1, 4)
    # Shape_Para: shape=(None, 199, 1)
    # Pose_Para: shape=(None, 1, 7)
    # Exp_Para: shape=(None, 29, 1)
    # Color_Para: shape=(None, 1, 6): remove last value as it's always 1
    # Illum_Para: shape=(None, 1, 9): remove last value as it's always 2
    # pt2d: shape=(None, 2, 68)
    # Tex_Para: shape=(None, 40, 1)
    # Total: 430 params

    # Load BFM
    content = sio.loadmat(bfm_path)
    model = content['model']
    model = model[0, 0]

    shape_ev = model['shapeEV'].astype(np.float32)
    tex_ev = model['texEV'].astype(np.float32)
    image_size = 1.0 * image_size

    def unnormalize_labels(roi, landmarks, pose_para, shape_para, exp_para, color_para, illum_para, tex_para):
        batch_size = roi.shape[0]

        # translation and scaling
        pose_para_new = tf.concat([pose_para[:, 0:3], pose_para[:, 3:6] * image_size, pose_para[:, 6:] / 1000.], axis=1)

        landmarks = tf.reshape(landmarks, (batch_size, 2, -1))  # (None, 2, 68)

        # rescale shape, exp and tex by their eigenvalue
        shape_para *= shape_ev
        tex_para *= tex_ev

        # Color_Para: add last value as it's always 1
        # Illum_Para: add last value as it's always 2
        color_para = tf.concat([color_para, tf.constant(1.0, shape=(batch_size, 1))], axis=1)
        illum_para = tf.concat([illum_para, tf.constant(2.0, shape=(batch_size, 1))], axis=1)

        return roi, landmarks, tf.expand_dims(pose_para_new, axis=1), tf.expand_dims(shape_para, axis=2), \
               tf.expand_dims(exp_para, axis=2), tf.expand_dims(color_para, 1), tf.expand_dims(illum_para, axis=1), \
               tf.expand_dims(tex_para, axis=2)

    return unnormalize_labels


def fn_extract_coarse_80k(img_filename):
    # label file has the same name as image
    # txt format
    # txt_filename =
    pass
