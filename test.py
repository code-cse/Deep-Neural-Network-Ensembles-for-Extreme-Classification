from __future__ import print_function

import os
import random
import cv2
import inspect
from datetime import *
from cdimage import CDiscountDataset
from torch.utils.data.sampler import RandomSampler
from logging import Logger
from torch.autograd import Variable
from torch import optim
import torch.nn.functional as F
from timeit import default_timer as timer
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
import time

from common import *
# from net.rate import *
# from net.loss import *
# from utility.file import *

# from dataset.cdimage import *
# from dataset.sampler import *
from transform import *
from Log import *
from StepLR import *
from Utils import *
from AverageMeter import *
# --------------------------------------------------------

from net.inception_v3 import Inception3 as Net

use_cuda = True
IDENTIFIER = "inception"
SEED = 123456
PROJECT_PATH = './project'
CDISCOUNT_HEIGHT = 180
CDISCOUNT_WIDTH = 180
CDISCOUNT_NUM_CLASSES = 5270

csv_dir = './data/'
root_dir = '../output/train/'
train_data_filename = 'train.csv'
validation_data_filename = 'validation.csv'

####################################################################################################
## common functions ##

def image_to_tensor_transform(image):
    tensor = pytorch_image_to_tensor_transform(image)
    tensor[ 0] = tensor[ 0] * (0.229 / 0.5) + (0.485 - 0.5) / 0.5
    tensor[ 1] = tensor[ 1] * (0.224 / 0.5) + (0.456 - 0.5) / 0.5
    tensor[ 2] = tensor[ 2] * (0.225 / 0.5) + (0.406 - 0.5) / 0.5
    return tensor

def valid_augment(image):

    image  = fix_center_crop(image, size=(160,160))
    tensor = image_to_tensor_transform(image)
    return tensor

def evaluate(net, test_loader):
    cnt = 0

    all_image_ids = []
    all_probs = []

    # for iter, (images, labels, indices) in enumerate(test_loader, 0):
    for iter, (images, images_id) in enumerate(test_loader, 0):#remove indices for testing
        images = Variable(images.type(torch.FloatTensor)).cuda() if use_cuda else Variable(images.type(torch.FloatTensor))
        images_id = images_id.cpu().data if use_cuda else images_id.data

        logits = net(images)
        probs  = F.softmax(logits)

        all_image_ids += images_id
        all_probs += probs

        cnt = cnt + 1

    product_to_prediction_map = product_predict(all_image_ids, all_probs)

    return product_to_prediction_map

def write_test_result(path, product_to_prediction_map):
    with open(path, "a") as file:
        file.write("_id,category_id\n")
        for product_id, prediction in product_to_prediction_map.iteritems():
            file.write(product_id + "," + prediction + "\n")



# main #################################################################
if __name__ == '__main__':
    print( '%s: calling main function ... ' % os.path.basename(__file__))

    initial_checkpoint = "../checkpoint/"+ IDENTIFIER + "/best_val_model.pth"
    res_path = "../test_res/" + IDENTIFIER + "_test.res"

    net = Net(in_shape = (3, CDISCOUNT_HEIGHT, CDISCOUNT_WIDTH), num_classes=CDISCOUNT_NUM_CLASSES)
    if use_cuda: net.cuda()

    if os.path.isfile(initial_checkpoint):
        print("=> loading checkpoint '{}'".format(initial_checkpoint))
        checkpoint = torch.load(initial_checkpoint)
        net.load_state_dict(checkpoint['state_dict'])  # load model weights from the checkpoint
        print("=> loaded checkpoint '{}'".format(initial_checkpoint))
    else:
        print("=> no checkpoint found at '{}'".format(initial_checkpoint))
        exit(0)

    transform_valid = transforms.Compose([transforms.Lambda(lambda x: valid_augment(x))])
    test_loader = CDiscountDataset(csv_dir + train_data_filename, root_dir, transform=transform_valid)
    product_to_prediction_map = evaluate(net, test_loader)

    write_test_result(res_path, product_to_prediction_map)

    print('\nsucess!')
