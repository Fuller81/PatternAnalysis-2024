from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from torchvision import transforms
import os
import shutil
from random import sample

ROOT = "../../../AD_NC"
NEW_ROOT = "../../../PatientSplit"
TESTPATH = "/test"
TRAINPATH = "/train"
VALPATH = "/val"
IMG_SIZE = 224

TRAIN_TRANSFORM = transforms.Compose([
    transforms.RandomResizedCrop((IMG_SIZE, IMG_SIZE)),
    transforms.RandAugment(num_ops = 3),
    transforms.Grayscale(),
    transforms.ToTensor(),
    transforms.Normalize(mean = 0.1156, std = 0.2198)
])
TEST_TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.Grayscale(),
    transforms.ToTensor(),
    transforms.Normalize(mean = 0.1156, std = 0.2198)
])
CALC_TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor()
])

def getTrainLoader(path: str = NEW_ROOT + TRAINPATH, batchSize: int = 128, shuffle: bool = True, gpu = False, workers = 1):
    '''
    Get Pytorch DataLoader with ADNI training DATA

    Input:
        path: str - relative path to training data
        batchSize: int - batch size of the DataLoader
        suffle: bool - DataLoader shuffle option
    Returns:
        Pytorch DataLoader with ADNI training data loaded
    '''
    trainData = ImageFolder(
        root = path,
        transform = TRAIN_TRANSFORM
    )
    trainLoader = DataLoader(trainData, batch_size = batchSize, shuffle = shuffle, num_workers=workers, pin_memory = gpu)
    return trainLoader

def getValLoader(path = NEW_ROOT + VALPATH, batchSize = 128, shuffle = True, gpu = False):
    '''
    Get Pytorch DataLoader with ADNI test DATA

    Input:
        path: str - relative path to training data
        batchSize: int - batch size of the DataLoader
        suffle: bool - DataLoader shuffle option
    Returns:
        Pytorch DataLoader with ADNI test data loaded
    '''
    valData = ImageFolder(
        root = path,
        transform = TEST_TRANSFORM
    )
    valLoader = DataLoader(valData, batch_size = batchSize, shuffle = shuffle, num_workers=0, pin_memory = gpu)
    return valLoader

def getTestLoader(path = NEW_ROOT + TESTPATH, batchSize = 128, shuffle = True):
    '''
    Get Pytorch DataLoader with ADNI test DATA

    Input:
        path: str - relative path to training data
        batchSize: int - batch size of the DataLoader
        suffle: bool - DataLoader shuffle option
    Returns:
        Pytorch DataLoader with ADNI test data loaded
    '''
    testData = ImageFolder(
        root = path,
        transform = TEST_TRANSFORM
    )
    testLoader = DataLoader(testData, batch_size = batchSize, shuffle = shuffle)
    return testLoader

def formatByPatient(path = ROOT, newPath = NEW_ROOT):
    if os.path.exists(newPath):
        print("Patient split has already been completed. Aborting:")
        return 1
    os.mkdir(newPath)
    print("Patient split has not been completed. Starting now:")
    q = []
    q.append((path, newPath))
    testroot = None
    while q:
        info = q.pop(0)
        p = info[0]
        newP = info[1]
        files = False
        for item in (os.listdir(p)):
            if (os.path.isfile(os.path.join(p, item))):
                files = True
                break
        if (files == True):
            for item in (os.listdir(p)):
                patient = item.split("_")[0]
                if not os.path.exists(os.path.join(newP, patient)):
                    os.mkdir(os.path.join(newP, patient))
                shutil.copy(os.path.join(p, item), os.path.join(newP, patient))
        else:
            for item in (os.listdir(p)):
                if item == "test":
                    testroot = (os.path.join(newP, item), os.path.join(newP, "val"))
                os.mkdir(os.path.join(newP, item))
                q.append((os.path.join(p, item), os.path.join(newP, item)))

    valq = []
    valq.append(testroot)
    os.mkdir(testroot[1])
    while valq:
        info = valq.pop(0)
        p = info[0]
        newP = info[1]
        files = False
        for item in (os.listdir(p)):
            item2 = os.listdir(os.path.join(p, item))[0]
            if (os.path.isfile(os.path.join(p, item, item2))):
                files = True
                break
        if files:
            samples = sample(os.listdir(p), (len(os.listdir(p))) // 2)
            for folder in samples:
                shutil.copytree(os.path.join(p, folder), os.path.join(newP, folder))
                shutil.rmtree(os.path.join(p, folder))
        else:
            for item in (os.listdir(p)):
                os.mkdir(os.path.join(newP, item))
                valq.append((os.path.join(p, item), os.path.join(newP, item)))

import torch

def meanStdCalc(path = NEW_ROOT + TRAINPATH, device = "cpu"):
    trainData = ImageFolder(
            root = path,
            transform = CALC_TRANSFORM
        )

    trainLoader = DataLoader(trainData, batch_size = 128)

    mean = 0.0
    std = 0.0
    nb_samples = 0.0
    
    for data in trainLoader:
        data = data[0]
        batch_samples = data.size(0)
        data = data.view(batch_samples, data.size(1), -1)
        mean += data.mean(2).sum(0)
        std += data.std(2).sum(0)
        nb_samples += batch_samples

    mean /= nb_samples
    std /= nb_samples

    return (mean, std)