#!/usr/bin/env python
 
'''
monitor a directory
print the changed files in the directory
strategy: mtime + checksum
'''
 
import sys
import os
import stat
import cPickle as pickle
 
def print_usage():
    print 'monitor.py init [dir]'
    print 'monitor.py check [dir]'
    print 'monitor.py refresh [dir]'
    print '[dir] defaults to .'
 
def main(argv=None):
    if len(argv) == 1:
        action = argv[0]
        directory = '.'
    elif len(argv) == 2:
        action = argv[0]
        directory = argv[1]
    else:
        print_usage()
        return 1
    
    if action != 'init' and action != 'check' and action != 'refresh':
        print_usage()
        return 1
 
    directory = os.path.abspath(directory)
    monitor = Monitor(directory)
    if action == 'init':
        monitor.init_dir()
        return 0
    elif action == 'check':
        monitor.check_dir()
        return 0
    elif action == 'refresh':
        monitor.refresh_dir()
        return 0
    else:
        print 'Unexpeceted Error!'
        return 1
    
 
class Monitor(object):
    def __init__(self, directory):
        self.directory = directory
 
    def construct_cache(self):
        fileCacheList = []
        # recursively traverse the directory, cache each files's mtime and checksum
        # {filename1:(mtime, checksum), filename2:(mtime, checksum), ....}
        for dirpath, dirnames, filenames in os.walk(self.directory):
            for f in filenames:
                if f == '.cache':
                    continue    # exclude .cache file
                f = os.path.join(dirpath, f)
                print 'dealing with', f
                filecache = FileCache(f)
                fileCacheList.append(filecache)
        # dump fileCacheList to .cache
        cacheFilePath = os.path.abspath(os.path.join(self.directory, '.cache'))
        with open(cacheFilePath, 'wb') as cacheFile:
            pickler = pickle.Pickler(cacheFile)
            for filecache in fileCacheList:
                pickler.dump(filecache)
 
        
    def init_dir(self):
        '''
        init directory
        cache the mtime and checksum of all files in the directory
        dump the cache to .cache in the direcotry
        '''
        print 'init_dir'
        self.construct_cache()
        print 'init', self.directory, 'success'
        return
    
    def check_dir(self):
        '''
        check directory to determine which files have changed
        '''
 #       print 'check_dir'
        # make sure the directory has been initialized
        # i.e. there's a .cache file under this direcotry
        files = os.listdir(self.directory)
        if not '.cache' in files:
            print self.directory, 'has not been initialized yet'
            return
        # reconstruct fileCacheList
        fileCacheList = []
        cacheFilePath = os.path.abspath(os.path.join(self.directory, '.cache'))
        with open(cacheFilePath, 'rb') as cache:
            pickled = pickle.Unpickler(cache)
            while cache:
                try:
                    filecache = pickled.load()
                except:
                    break
                if isinstance(filecache, FileCache):
                    fileCacheList.append(filecache)
        
        # construct a dict from fileCacheList
        dictFiles = {}
        for fc in fileCacheList:
            dictFiles[fc.filepath] = (fc.mtime, fc.checksum)
 
        # traverse the target directory and determine which files have changed
        for dirpath, dirnames, filenames in os.walk(self.directory):
            for f in filenames:
                if f == '.cache':
                    continue    # exclude .cache file
                f = os.path.join(dirpath, f)
#                print 'checking', f
                if f not in dictFiles:
                    print '[ADD]:', f
                else:           # f in dictFiles
                    smtime = dictFiles[f][0]
                    cmtime = os.stat(f)[stat.ST_MTIME]
                    if cmtime == smtime:
                        pass
                    else:
#                        print 'file %s changed mtime, recompute checksum' % f
                        schecksum = dictFiles[f][1]
                        cchecksum = md5_file(f)
                        if schecksum == cchecksum:
                            pass
                        else:
                            print '[CHANGED]:', f
                    # remove entry f from dictFiles
                    dictFiles.pop(f)
 
        # tranverse ended
        if len(dictFiles) != 0:
            for f in dictFiles:
                print '[REMOVE]:', f
        
 
    def refresh_dir(self):
        print 'refresh_dir'
        self.construct_cache()
        print 'refresh %s success' % self.directory
 
 
def md5_file(filename):
    try:
        import hashlib
        m = hashlib.md5()
    except ImportError:
        import md5
        m = md5.new()
        
    for line in open(filename):
        m.update(line)
    return m.hexdigest()
 
class FileCache(object):
    def __init__(self, f):
        self.filepath = os.path.abspath(f)
        self.mtime = os.stat(f)[stat.ST_MTIME]
        self.checksum = md5_file(f)
 
    def __str__(self):
        return self.filepath+str(self.mtime)+str(self.checksum)
 
if __name__ == '__main__':
    main(sys.argv[1:])

