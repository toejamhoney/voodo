import sys
import glob
import os
import os.path

class LogTester(object):

    def __init__(self, logdir, sampledir):
        self.logpath = logdir
        self.datapath = sampledir
        self.result_set = set()
        self.sample_set = set()
        self.job_set = set()

    def check_results(self):
        files = glob.glob(self.logpath + '/*.log')
        for f in files:
            filename = f.rpartition('/')[2]
            if filename.startswith('x'):
                md5 = filename.split('.')[2]
                self.result_set.add(md5)
            elif filename.startswith('V'):
                md5 = filename.split('_')[4].rpartition('"')[0]
                self.job_set.add(md5)

    def check_samples(self):
        files = glob.glob(self.datapath + '/*')
        for f in files:
            filename = f.rpartition('/')[2]
            self.sample_set.add(filename)

    def results(self):
        return len(self.result_set)

    def attempts(self):
        return len(self.job_set)

    def samples(self):
        return len(self.sample_set)

    def get_missed(self):
        return self.sample_set.difference(self.job_set)

    def get_failed(self):
        return self.job_set.difference(self.result_set)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Need dirs'
        sys.exit(0)
    test = LogTester(sys.argv[1], sys.argv[2])
    test.check_results()
    test.check_samples()

    num_results = test.results()
    num_trials = test.attempts()
    num_samples = test.samples()
    
    completion = num_results * 1.0 / num_trials
    coverage = num_results * 1.0 / num_samples


    failed = test.get_failed()
    missed = test.get_missed()

    print '----------------------------------------------------------------'
    print 'Samples in failed runs:'
    for sample in failed:
        print sample
    print '----------------------------------------------------------------'
    print 'Samples that did not start:'
    for sample in missed:
        print sample
    print '----------------------------------------------------------------'
    print 'Total catalog given:',num_samples
    print 'Runs started:',num_trials
    print 'Results gathered:',num_results
    print 'Completed runs:',completion
    print 'Sample coverage:',coverage

