import os
import os.path as osp
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import cv2
from tqdm import tqdm
from glob import glob
import time

pbar = None
crop_sz = 192
step = crop_sz // 2
thres_sz = crop_sz // 4
    
def main():
    global pbar
    
    """A multi-thread tool to crop sub imags."""
    input_folder = '/content/data/LOK EP01/R'
    save_folder = '/content/data/LRTiles'
    # input_folder = 'D:\\tmp\\BasicSR\\data_samples\\samples'
    # save_folder = 'D:\\tmp\\BasicSR\\data_samples\\test_sample'
    
    compression_level = 3  # 3 is the default value in cv2
    # CV_IMWRITE_PNG_COMPRESSION from 0 to 9. A higher value means a smaller size and longer
    # compression time. If read raw images during training, use 0 for faster IO speed.

    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        print('mkdir [{:s}] ...'.format(save_folder))
    
    img_list = glob(input_folder + '/*')

    pbar = tqdm(total=len(img_list))

    start = time.time()
    
    # with ThreadPoolExecutor() as executor:
    #     future_worker = {executor.submit(worker, path, save_folder, compression_level): path for path in img_list}
        
    #     for future in as_completed(future_worker):
    #         try:
    #             future.result()
    #         except Exception as exc:
    #             print(exc)
            
    for path in img_list:
        print(path)
        worker(path, save_folder, compression_level)
    
    print('result time {}'.format(time.time() - start))
    # print('All subprocesses done.')


def worker(path, save_folder, compression_level):
    img_name = os.path.basename(path)
    names = img_name.split('.')
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)

    n_channels = len(img.shape)
    if n_channels == 2:
        h, w = img.shape
    elif n_channels == 3:
        h, w, c = img.shape
    else:
        raise ValueError('Wrong image shape - {}'.format(n_channels))

    h_space = np.arange(0, h - crop_sz + 1, step)
    if h - (h_space[-1] + crop_sz) > thres_sz:
        h_space = np.append(h_space, h - crop_sz)
    w_space = np.arange(0, w - crop_sz + 1, step)

    if w - (w_space[-1] + crop_sz) > thres_sz:
        w_space = np.append(w_space, w - crop_sz)

    xy_arr = []
    
    for x in h_space:
        for y in w_space:
            xy_arr.append((x, y))
    
    def sub_f(img, x, y, idx):
        if n_channels == 2:
                crop_img = img[x:x + crop_sz, y:y + crop_sz]
        else:
            crop_img = img[x:x + crop_sz, y:y + crop_sz, :]
        crop_img = np.ascontiguousarray(crop_img)
        
        cv2.imwrite(
            os.path.join(save_folder, '{}-{}.{}'.format(names[0], idx, names[1])),
            crop_img, [cv2.IMWRITE_PNG_COMPRESSION, compression_level])
        
        
    with ThreadPoolExecutor() as executor:
        future_worker = {executor.submit(sub_f, img, xy[0], xy[1], idx): (idx, xy) for idx, xy in enumerate(xy_arr)}
        
        for future in as_completed(future_worker):
            try:
                future.result()
            except Exception as exc:
                print(exc)
        
    pbar.update(1)


if __name__ == '__main__':
    main()
