# -*- coding: utf-8 -*-

import os
import tempfile

def extract(work_path, filename):
    build_directory = os.path.join(work_path, '.build')
    new_iso = os.path.join(build_directory, 'new_iso')
    new_squashfs = os.path.join(build_directory, 'new_squashfs')
    for directory in [build_directory, new_iso, new_squashfs]:
        if not os.path.exists(directory):
            os.mkdir(directory)
    mountpoint = tempfile.mkdtemp(prefix='tmp')

    os.system('mount -o loop,ro "{}" "{}"'.format(filename, mountpoint))
    os.system('rsync -at --del --exclude=\'casper/filesystem.squashfs\' "{}/" "{}"'.format(mountpoint, new_iso))
    os.system('unsquashfs -f -d "{}" "{}"'.format(new_squashfs, os.path.join(mountpoint, 'casper/filesystem.squashfs')))
    os.system('umount -lf {}'.format(mountpoint))
    os.rmdir(mountpoint)
