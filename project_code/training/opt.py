import numpy as np
import tensorflow as tf

from project_code.morphable_model import mesh
from project_code.morphable_model.model.morphable_model import MorphableModel
from project_code.training.tf_util import get_shape
bfm_mat_path = 'G:\PycharmProjects\FaceFusion\project_code\data\\3dmm\BFM\BFM.mat'
bfm = MorphableModel(bfm_mat_path)


def split_3dmm_labels(labels):
    """
    split labels into different 3dmm params
    :param labels:
    :return:
    """
    # get different labels
    # Shape_Para: (199,)
    # Pose_Para: (7,)
    # Exp_Para: (29,)
    # Color_Para: (7,)
    # Illum_Para: (10,)
    # pt2d: (136, )
    # Tex_Para: (199,)
    n_size = labels.shape[0]
    shape_labels = labels[:, :199]
    pose_labels = labels[:, 199: 206]
    exp_labels = labels[:, 206: 235]
    color_labels = labels[:, 235: 242]
    illum_labels = labels[:, 242: 252]
    # reshape landmark
    landmark_labels = tf.reshape(labels[:, 252: 388], (-1, 2, 68))
    tex_labels = labels[:, 388:]

    return shape_labels, pose_labels, exp_labels, color_labels, illum_labels, landmark_labels, tex_labels


def compute_landmarks(poses_param, shapes_param, exps_param, output_size=224):
    """
    compute landmarks using pose, shape and expression params
    note, now we compute it in numpy instead of tensor, can be problem for performance

    :param poses_param: batch pose params. (batch_size, 199) = > (batch_size, 199, 1)
    :param shapes_param: batch shapes params. (batch_size, 7) = > (batch_size, 1, 7)
    :param exps_param: batch expression params. (batch_size, 29) = > (batch_size, 29, 1)
    :param bfm: 3dmm model
    :param output_size: 2d landmarks position on image of shape (output_size, output_size)
    :param input_size: the input size of face model, the pose params are computed with image of shape (input_size, input_size)
    :return: tensor: shape [batch_size, 2, 68]
    """

    # convert tensor to numpy array
    poses_param = np.array(poses_param).reshape((-1, 1, 7))
    shapes_param = np.array(shapes_param).reshape((-1, 199, 1))
    exps_param = np.array(exps_param).reshape((-1, 29, 1))

    n_size = poses_param.shape[0]

    # Tri, tri2vt
    landmark_indices = bfm.get_landmark_indices()
    landmarks = []
    for i in range(n_size):
        pose = poses_param[i, :, :]
        shape = shapes_param[i, :, :]
        exp = exps_param[i, :, :]

        vertex3d = bfm.generate_vertices(shape_param=shape, exp_param=exp)
        vertex3d_landmarks = vertex3d[landmark_indices, :]

        # add scaling
        s = pose[0, 6]
        angles = pose[0, 0:3]
        t = pose[0, 3:6]

        projected_vertices = bfm.transform_3ddfa(vertices=vertex3d_landmarks, scale=s, angles=angles, t3d=t)
        vertex2d_landmarks = mesh.transform.to_image(vertices=projected_vertices, h=output_size, w=output_size)
        landmarks.append(vertex2d_landmarks[:, :2].T)

    return np.array(landmarks)