from glob import glob
from os import path
import subprocess
from collections import OrderedDict
from junit_xml import TestSuite, TestCase

file_list = glob('build/x86-linux-native/test/*-test-*')

test_suites = []
print file_list
for fn in file_list:
    if path.isfile(fn):
        result = subprocess.check_output([fn])
        print result
        bits = result.split(">>>")

        bits.pop(0) # empty

        summary = bits.pop(-1)

        testcase_output = bits[::2]
        testcase_summary = bits[1::2]

        test_cases = []
        assert(len(testcase_output) == len(testcase_summary))
        for i, op in enumerate(testcase_output):
            ops = op.strip().split('...')
            metadata = ops[0].split(' ')

            test_id = int(metadata[2][1:-1])
            test_name = metadata[-1].strip('\'')
            test_stdout = ops[1]

            ts = testcase_summary[i].strip()
            success = int(ts.split(' ')[-4])
            fail = int(ts.split(' ')[-2])

            tc = TestCase(test_id, test_name, stdout=test_stdout)
            if not success and fail:
                tc.add_failure_info('', 'failed')
            test_cases.append(tc)

        ts = TestSuite(path.basename(fn), test_cases)
        test_suites.append(ts)

module_name = path.basename(file_list[0]).split('-test-')[0]
with open(module_name+'_test_result_junit.xml', "w") as fd:
    TestSuite.to_file(fd, test_suites)
