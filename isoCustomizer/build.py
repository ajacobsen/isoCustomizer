# -*- coding: utf-8 -*-

import os
import logging
import subprocess

from error import SystemError


def build(work_path, filename, config):
    logger = logging.getLogger('isoCustomizer.build')
    logger.info('Started building {}'.format(filename))

    squash_fs = os.path.join(work_path, '.build/new_squashfs')
    iso_dir = os.path.join(work_path, '.build/new_iso')

    for e in [squash_fs, iso_dir]:
        if not os.path.exists(e):
            raise OSError('Run extract first')

    logger.info('Preparing chroot environment ...')

    set_up_chroot(squash_fs)

    command = 'LANG=C chroot "{}" /bin/bash -c "apt-get update" 2>&1 |tee -a build.log'.format(squash_fs)
    subprocess.check_call(command, shell=True)

    package_list = ' '.join(config['packages'])
    command = 'LANG=C chroot "{}" /bin/bash -c "apt-get --yes install {}" 2>&1 |tee -a build.log'.format(squash_fs, package_list)
    subprocess.check_call(command, shell=True)

    if True:
        logger.info('Opening chroot shell ...')
        command = 'LANG=C chroot "{}" /bin/bash'.format(squash_fs)
        subprocess.check_call(command, shell=True)

    logger.info('Cleaning up chroot environment ...')
    on_exit_chroot(squash_fs)

    logger.info('Syncing chroot includes whith root filesystem ...')
    command = 'rsync --numeric-ids --progress -DrlHpvt "{}/" "{}" 2>&1 |tee -a build.log'.format(config['chroot_includes'], squash_fs)
    subprocess.check_call(command, shell=True)
    logger.info('Syncing binary includes with iso filesystem ...')
    command = 'rsync --numeric-ids --progress -DrlHpvt "{}/" "{}" 2>&1 |tee -a build.log'.format(config['binary_includes'], iso_dir)
    subprocess.check_call(command, shell=True)

    logger.info('Creating filesystem.manifest ...')
    manifest = os.path.join(iso_dir, 'casper/filesystem.manifest')
    command = "chroot {} dpkg-query -W --showformat='${{Package}} ${{Version}}\n' > {}".format(squash_fs, manifest)
    subprocess.check_call(command, shell=True)
    logger.info('Creating filesystem.manifest-desktop ...')
    command = 'cp -f {0} {0}-desktop'.format(manifest)
    subprocess.check_call(command, shell=True)
    command = "sed -i '/ubiquity\|casper\|gparted\|libdebian-installer4\|user-setup/d' {}-desktop".format(manifest)
    subprocess.check_call(command, shell=True)

    logger.info('Creating filesystem.squashfs ...')
    if os.path.exists(os.path.join(iso_dir, 'casper/filesystem.squashfs')):
        command = 'rm -f {}'.format(os.path.join(iso_dir, 'casper/filesystem.squashfs'))
        subprocess.check_call(command, shell=True)

    command = 'mksquashfs \
                    \"{0}\" \
                    \"{1}\" \
                    -comp xz \
                    -no-progress'.format(
                                        squash_fs, 
                                        os.path.join(iso_dir, 'casper/filesystem.squashfs'))
    subprocess.check_call(command, shell=True)

    logger.info('Creating md5sum.txt ...')
    command = 'find {0} -not -name md5sum.txt -and -not -name boot.cat -and -not -name isolinux.bin -type f -print0 | xargs -0 md5sum > {0}/md5sum.txt'.format(iso_dir)
    subprocess.check_call(command, shell=True)

    # Just a hack I use for debuging.
    # So I don't have to run the whole function just to test a few changes.
    # logger.warning('Warning, exception ahead!')
    # raise SystemError("I've warned you!")

    logger.info('Creating iso image ...')
    if os.path.isfile('/usr/bin/genisoimage'):
        isotool = 'genisoimage'
    else:
        isotool = 'mkisofs'
    command = '{} \
            -o \"{}\" \
            -b \"isolinux/isolinux.bin\" \
            -c \"isolinux/boot.cat\" \
            -no-emul-boot \
            -boot-load-size 4 \
            -boot-info-table -V \"{}\" \
            -cache-inodes \
            -r \
            -J \
            -l \
            \"{}\"'.format(
                isotool,
                filename,
                config['volid'],
                iso_dir)
    subprocess.check_call(command)

def set_up_chroot(root_path):
    print root_path
    if os.path.exists(os.path.join(root_path, 'etc/resolv.conf')):
        chroot_resolvconf = os.path.join(root_path, 'etc/resolv.conf')
        command = 'mv -v "{}" "{}" 2>&1 |tee -a build.log'.format(chroot_resolvconf, '{}.bak'.format(chroot_resolvconf, '.bak'))
        subprocess.check_call(command, shell=True)

    if os.path.exists('/etc/resolv.conf'):
        command = 'cp -v /etc/resolv.conf "{}" 2>&1 |tee -a build.log'.format(os.path.join(root_path, 'etc/'))
        subprocess.check_call(command, shell=True)

    mntlst = ['proc', 'sys', 'dev', 'dev/pts', 'var/run/dbus']
    for entry in mntlst:
        mountpoint = os.path.join(root_path, entry)
        command = 'mount -vo bind {} {} 2>&1 |tee -a build.log'.format(os.path.join('/', entry), mountpoint)
        subprocess.check_call(command, shell=True)
    
    if os.path.ismount('/var/run/dbus'):
        mountpoint = os.path.join(root_path, 'var/lib/dbus/')
        command = 'mount -vo bind {} {} 2>&1 |tee -a build.log'.format('/var/run/dbus', mountpoint)
        subprocess.check_call(command, shell=True)

def on_exit_chroot(root_path):
    command = 'rm -fv {} 2>&1 |tee -a build.log'.format(os.path.join(root_path, 'etc/resolv.conf'))
    subprocess.check_call(command, shell=True)

    if os.path.exists(os.path.join(root_path, 'etc/resolv.conf.bak')):
        command = 'mv -v {} {} 2>&1 |tee -a build.log'.format(os.path.join(root_path, 'etc/resolv.conf.bak'), os.path.join(root_path, 'etc/resolv.conf'))
        subprocess.check_call(command, shell=True)

    command = 'LANG=C chroot {} /bin/bash -c "apt-get clean" 2>&1 |tee -a build.log'.format(root_path)
    subprocess.check_call(command, shell=True)
    command = 'LANG=C chroot {} /bin/bash -c "rm -rfv /tmp/*" 2>&1 |tee -a build.log'.format(root_path)
    subprocess.check_call(command, shell=True)
    command = 'LANG=C chroot {} /bin/bash -c "rm  -v /root/.bash_history" 2>&1 |tee -a build.log'.format(root_path)
    subprocess.check_call(command, shell=True)
    for root,dirs,files in os.walk(root_path):
        if os.path.ismount(root):
            command = 'umount -lfv {}'.format(root)
            subprocess.check_call(command, shell=True)
