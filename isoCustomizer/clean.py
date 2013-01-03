# -*- coding: utf-8 -*-

import os


def clean_up(work_path, clean_config, clean_build):
    if clean_config:
        os.system('rm {}'.format(os.path.join(work_path, 'config/config')))
    if clean_build:
        for root,dirs,files in os.walk(os.path.join(work_path, '.build')):
            if os.path.ismount(root):
                os.system('umount -lf {}'.format(root))
        os.system('rm -rf {}'.format(os.path.join(work_path, '.build')))
