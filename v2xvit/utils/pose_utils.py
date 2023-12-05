import numpy as np
import torch
import torch.distributions as dist

def add_noise_data_dict(data_dict, noise_setting):
    """ Update the base data dict. 
        We retrieve lidar_pose and add_noise to it.
        And set a clean pose.
    """
    # path = 'pose_noise.txt'
    # file = open(path,'w+')
    if noise_setting['add_noise']:
        for cav_id, cav_content in data_dict.items():
            cav_content['params']['lidar_pose_clean'] = cav_content['params']['lidar_pose'] # 6 dof pose
            if cav_content['ego']:
                continue
            pose_noise = generate_noise(
                                                        noise_setting['args']['pos_std'],
                                                        noise_setting['args']['rot_std'],
                                                        noise_setting['args']['pos_mean'],
                                                        noise_setting['args']['rot_mean']
                                                    )
            cav_content['params']['lidar_pose'] = cav_content['params']['lidar_pose'] + pose_noise
            # print(pose_noise)
            # file.write(str(pose_noise[0])+'  ')
    else:
        for cav_id, cav_content in data_dict.items():
            cav_content['params']['lidar_pose_clean'] = cav_content['params']['lidar_pose'] # 6 dof pose

    # file.write('\n')
    # file.close()    
    return data_dict

def generate_noise(pos_std, rot_std, pos_mean=0, rot_mean=0):
    """ Add localization error to the 6dof pose
        Noise includes position (x,y) and rotation (yaw).
        We use gaussian distribution to generate noise.
    
    Args:

        pos_std : float 
            std of gaussian dist, in meter

        rot_std : float
            std of gaussian dist, in degree

        pos_mean : float
            mean of gaussian dist, in meter

        rot_mean : float
            mean of gaussian dist, in degree
    
    Returns:
        pose_noise: np.ndarray, [6,]
            [x, y, z, roll, yaw, pitch]
    """

    xy = np.random.normal(pos_mean, pos_std, size=(2))
    yaw = np.random.normal(rot_mean, rot_std, size=(1))

    pose_noise = np.array([xy[0], xy[1], 0, 0, yaw[0], 0])
    # pose_noise = np.array([xy[0], xy[1], 0, 0, 0, yaw[0]])
    # print(pose_noise)
    return pose_noise



def generate_noise_torch(pose, pos_std, rot_std, pos_mean=0, rot_mean=0):
    """ only used for v2vnet robust.
        rotation noise is sampled from von_mises distribution
    
    Args:
        pose : Tensor, [N. 6]
            including [x, y, z, roll, yaw, pitch]

        pos_std : float 
            std of gaussian dist, in meter

        rot_std : float
            std of gaussian dist, in degree

        pos_mean : float
            mean of gaussian dist, in meter

        rot_mean : float
            mean of gaussian dist, in degree
    
    Returns:
        pose_noisy: Tensor, [N, 6]
            noisy pose
    """

    N = pose.shape[0]
    noise = torch.zeros_like(pose, device=pose.device)
    concentration = (180 / (np.pi * rot_std)) ** 2

    noise[:, :2] = torch.normal(pos_mean, pos_std, size=(N, 2), device=pose.device)
    noise[:, 4] = dist.von_mises.VonMises(loc=rot_mean, concentration=concentration).sample((N,)).to(noise.device)


    return noise


def remove_z_axis(T):
    """ remove rotation/translation related to z-axis
    Args:
        T: np.ndarray
            [4, 4]
    Returns:
        T: np.ndarray
            [4, 4]
    """
    T[2,3] = 0 # z-trans
    T[0,2] = 0
    T[1,2] = 0
    T[2,0] = 0
    T[2,1] = 0
    T[2,2] = 1
    
    return T