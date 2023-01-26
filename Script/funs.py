"""
    general functions
"""
import os
import shutil
from shutil import copyfile
import para

def SFileToDFile(sourcefile, fileclass, destinationfile):
    if os.path.exists(destinationfile):
        pass
    else:
        os.mkdir(destinationfile)
    # 遍历目录和子目录
    for filenames in os.listdir(sourcefile):
        # 取得文件或文件名的绝对路径
        filepath = os.path.join(sourcefile, filenames)
        # 判断是否为文件夹
        if os.path.isdir(filepath):
            # 如果是文件夹，重新调用该函数
            SFileToDFile(filepath, fileclass, destinationfile)
        # 判断是否为文件
        elif os.path.isfile(filepath):
            # 如果该文件的后缀为用户指定的格式，则把该文件复制到用户指定的目录
            if filepath.endswith(fileclass):
                #dirname = os.path.split(filepath)[-1]
                # 给出提示信息Script
                # print('Copy %s'% filepath +' To ' + destinationfile)
                # 复制该文件到指定目录
                shutil.copy(filepath, destinationfile)


def BackUpScripts(_test_name):
    """
        copy files and back the tested code
        1. copy cpp files
        2. copy input mms data files
    """
    SFileToDFile(sourcefile=para.root_folder+"Script\\", fileclass='.py',
                 destinationfile=para.root_folder+"Tests\\"+_test_name)
    SFileToDFile(sourcefile=para.root_folder+"Script\\", fileclass='.xlsx',
                 destinationfile=para.root_folder+"Tests\\"+_test_name)
