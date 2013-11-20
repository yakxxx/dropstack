#!/usr/bin/python
import re
import os
import sys
import subprocess as sp
import time
import logging
logging.basicConfig(level=logging.ERROR)
LOG = logging.getLogger()


HERE = os.path.dirname(os.path.realpath(__file__))
RUNDIR = os.getcwd()
DROPBOX_UPLOADER = '/usr/bin/dropbox_uploader'
REMOTE_PATH = 'dropstack'
TMP_TAR_PATH = '_dropstack_tmp.tar.gz'

to_clean = []

def push(local_filename):
    if os.path.isdir(os.path.join(RUNDIR, local_filename)):
        remote_filename = 'd_{0}_{1}.tar.gz'.format(next_num(), local_filename)
        ret = pack_dir(local_filename)
        local_filename = '{0}'.format(TMP_TAR_PATH)
        to_clean.append(local_filename)
        if ret != 0:
            LOG.error('Failed to compress dir')
            clean()
            sys.exit(1)
    else:
        remote_filename = 'f_{0}_{1}'.format(next_num(), local_filename)

    print 'UPLOADING....'
    ret, out, err = run_dropbox_uploader(
        'upload',
        os.path.join(RUNDIR, local_filename),
        REMOTE_PATH + '/' + remote_filename
    )
    if ret == 0:
        print "OK"
    else:
        LOG.ERROR(out)
        LOG.ERROR(err)
        print "FAILED!"
    clean()


def pop(num=None):
    stack = list_stack()
    if len(stack) == 0:
        LOG.error("Nothing to pop")
        sys.exit(1)

    remote_filename = stack[-1][1]
    local_filename = stack[-1][2]
    f_type = stack[-1][3]
    print "DOWNLOADING"
    ret, out, err = run_dropbox_uploader('download', REMOTE_PATH+'/'+remote_filename, local_filename)
    if ret == 0:
        print 'OK!'
    else:
        LOG.error(out)
        LOG.error(ret)
        print 'FAILED!'
        clean()
        sys.exit(1)
    
    if f_type == 'd':
        print 'UNPACKING'
        ret = unpack_dir(local_filename)
        to_clean.append(local_filename)
        if ret == 0:
            print 'OK!'
        else:
            LOG.error(out)
            LOG.error(err)
            print 'FAILED!'

    clean()

def pack_dir(dirname):
    ret, out, err = run_system(
        'tar', 'cvzf', TMP_TAR_PATH, dirname
    )
    return ret
    
def unpack_dir(tar_gz_name):
    ret, out, err = run_system(
        'tar', 'xvzf', tar_gz_name
    )
    return ret

def check_dropbox():
    ret, out, err = run_dropbox_uploader('list')
    if not re.search(r'\[D\] {0}'.format(REMOTE_PATH), out):
        LOG.debug('main dir for dropstack ({0}) not present'.format(REMOTE_PATH))
        mkdir(REMOTE_PATH)
        
def mkdir(name):
    ret, _, _ = run_dropbox_uploader('mkdir', name)
    LOG.debug('creating dir {0} finished with code {1}'.format(name, ret))
    return ret

def next_num():
    stack = list_stack()
    if len(stack) == 0:
        return 0

    return stack[-1][0] + 1

def list_stack():
    ret, out, _ = run_dropbox_uploader('list', REMOTE_PATH)
    entries = []
    for line in out.split('\n'):
        s = re.search(r'\[F\] (([df])_([0-9]+)_(.+))', line)
        if s:
            local_filename = s.group(4)
            remote_filename = s.group(1)
            f_type = s.group(2)
            f_num = int(s.group(3))
            entries.append((f_num, remote_filename, local_filename, f_type))
    return sorted(entries)

def run_system(*args, **kwargs):
    p = sp.Popen(args, stdout=sp.PIPE, stderr=sp.PIPE, cwd=RUNDIR)
    out, err = p.communicate()
    ret = p.returncode
    return ret, out, err

def run_dropbox_uploader(*args):
    LOG.debug('run dropbox_uploader with {0}'.format(str(args)))
    p = sp.Popen((DROPBOX_UPLOADER, ) + args, stdout=sp.PIPE, stderr=sp.PIPE, cwd=RUNDIR)
    out, err = p.communicate()
    ret = p.returncode
    LOG.debug(
        'dropbox_uploader returned {0} with output: {1} {2}'.format(ret, out, err)
    )
    return ret, out, err

def clean():
    for f in to_clean:
        path = os.path.join(RUNDIR, f)
        if os.path.isfile(path):
            os.remove(path)

def test_check():
    LOG.debug('***TEST CHECK***')
    check_dropbox()

def test_list_stack():
    LOG.debug('***TEST LIST STACK***')
    print list_stack(), 'stack'

def test_last_num():
    LOG.debug('***TEST LAST NUM***')
    print 'next num', next_num()

def test_push():
    LOG.debug('***TEST PUSH***')
    push('xxx')
    time.sleep(3)
    push('asas')

def test_pop():
    LOG.debug('***TEST POP***')
    pop()

if __name__ == '__main__':
    if len(sys.argv) == 0:
        LOG.error('Give some parameters')
        sys.exit(1)
    
    if sys.argv[1] == 'push':
        push(sys.argv[2])
    elif sys.argv[1] == 'pop':
        pop()

    if sys.argv[1] == 'test':
        test_check()
        test_list_stack()
        test_last_num()
        test_push()
        time.sleep(2)
        test_pop()


