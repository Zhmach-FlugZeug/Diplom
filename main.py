import random
import subprocess
import sys
import time
from widget import *
import psutil as psutil
import os
from multiprocessing import Array, Process, Value, shared_memory

Queue = []

class QueueEntry(object):
    def __init__(self, next_entry=None):
        self.fname = ""                     # File name for the test case
        self.len = int(0)                   # Input length
        self.cal_failed = False               # Calibration failed?
        self.trim_done = False            # Trimmed?
        self.was_fuzzed = False           # Had any fuzzing done yet?
        self.passed_det = False           # Deterministic stages passed?
        self.has_new_cov = False          # Triggers new coverage?
        self.var_behavior = False         # Variable behavior?
        self.favored = False              # Currently favored?
        self.fs_redundant = False         # Marked as redundant in the fs?

        self.bitmap_size = 0           # Number of bits set in bitmap
        self.fuzz_level = 0            # Number of fuzzing iterations
        self.exec_cksum = 0            # Checksum of the execution trace

        self.exec_us = 0               # Execution time (us)
        self.handicap = 0              # Number of queue cycles behind
        self.depth = 0                 # Path depth
        self.n_fuzz = 0                # Number of fuzz, does not overflow

        self.trace_mini = bytes(0)          # Trace bytes, if kept
        self.tc_ref = bytes(0)                 # Trace bytes ref count

        self.next = next_entry     # Next element, if any
        self.next_100 = next_entry  # 100 elements ahead

    def create_queue(self):
        pass

    def destroy(self):
        current = self
        while current:
            # Store a reference to the next entry
            next_entry = current.next
            # Remove references to the current entry
            current.next = None
            current.next_100 = None
            current.fname = None
            current.trace_mini = None
            current.tc_ref = None
            # Move to the next entry
            current = next_entry
            # Reset the head of the list
        self = None


def mutate_data(test_data):
    mode = random.randint(0, 4)
    #print("test data is: ", test_data)
    if mode == 0:
        # flip a random byte
        flipped_data = bytearray(test_data)
        flipped_data[random.randint(0, len(test_data) - 1)] ^= 1
        res = bytes(flipped_data)
        print("data with flipped byte is: ", res)
        return res
    elif mode == 1:
        # Substitute a random byte
        substituted_data = bytearray(test_data)
        substituted_data[random.randint(0, len(test_data) - 1)] = random.randint(0, 255)
        res = bytes(substituted_data)
        print("data with substituted byte is: ", res)
        return res
    elif mode == 2:
        # Insert a random byte
        insert_pos = random.randint(0, len(test_data))
        inserted_data = bytearray(
            test_data[:insert_pos] + bytes([random.randint(0, 255)]) + test_data[insert_pos:])
        res = bytes(inserted_data)
        print("data with inserted byte is: ", res)
        return res
    elif mode == 3:
        # Delete a random byte
        delete_pos = random.randint(0, len(test_data) - 1)
        deleted_data = bytearray(test_data[:delete_pos] + test_data[delete_pos + 1:])
        res = bytes(deleted_data)
        print("data with deleted byte is: ", res)
        return res


class Fuzzer(object):
    def __init__(self):
        self.in_dir = str()
        self.out_dir = str()
        self.out_file = str()
        self.extras_dir = str()
        self.timeout_given = int()
        self.dynamorio_dir = str()
        self.target_path = str()
        self.shm_name = str()
        self.shm = None
        self.fuzzer_id = int()
        self.sync_dir = str()
        self.sync_id = 0
        #self.queue = QueueEntry()
        self.head = None
        self.tail = None

    def setup_shm(self):
        name_seed = random.randint(0, 2 ** 32 - 1)
        self.fuzzer_id = hex(name_seed)
        self.shm_name = 'shm_' + self.fuzzer_id
        self.shm = shared_memory.SharedMemory(create=True, size=2 ** 32 - 1, name=self.shm_name)
        pass

    def remove_shm(self):
        self.shm.close()
        self.shm.unlink()
        pass

    def setup_dirs_fds(self):
        if self.sync_dir != "" and not os.path.exists(self.sync_dir):
            print(self.sync_dir)
            os.mkdir(self.sync_dir)
        else:
            pass
        #print("Недопустимый путь для директории синхронизации")

        if not os.path.exists(self.out_dir):
            os.mkdir(self.out_dir)
        else:
            pass

        # Create queue directory
        queue_dir = os.path.join(self.out_dir, "queue")
        if not os.path.exists(queue_dir):
            os.mkdir(queue_dir)

        # Create state directory
        state_dir = os.path.join(queue_dir, ".state")
        if not os.path.exists(state_dir):
            os.mkdir(state_dir)

        # Create deterministic_done directory
        deterministic_done_dir = os.path.join(state_dir, "deterministic_done")
        if not os.path.exists(deterministic_done_dir):
            os.mkdir(deterministic_done_dir)

        # Create auto_extras directory
        auto_extras_dir = os.path.join(state_dir, "auto_extras")
        if not os.path.exists(auto_extras_dir):
            os.mkdir(auto_extras_dir)

        # The set of paths currently deemed redundant.
        redundant_edges_dir = os.path.join(state_dir, "redundant_edges")
        if not os.path.exists(redundant_edges_dir):
            os.mkdir(redundant_edges_dir)

        # The set of paths showing variable behavior.
        variable_behavior_dir = os.path.join(state_dir, "variable_behavior")
        if not os.path.exists(variable_behavior_dir):
            os.mkdir(variable_behavior_dir)

        # Sync directory for keeping track of cooperating fuzzers.
        if self.sync_id != 0:
            synced_dir = os.path.join(self.out_dir, ".synced")
            try:
                os.mkdir(synced_dir)
            except OSError as e:
                raise Exception("Unable to create '%s'" % synced_dir)

        # All recorded crashes.
        tmp = os.path.join(self.out_dir, "crashes\\")
        if not os.path.exists(tmp):
            try:
                os.mkdir(tmp)
            except OSError:
                raise Exception("Unable to create '%s'" % tmp)

        # All recorded hangs.
        tmp = os.path.join(self.out_dir, "hangs")
        if not os.path.exists(tmp):
            try:
                os.mkdir(tmp)
            except OSError:
                raise Exception("Unable to create '%s'" % tmp)

        tmp = os.path.join(self.out_dir, "drcache")
        if not os.path.exists(tmp):
            try:
                os.mkdir(tmp)
            except OSError:
                raise Exception("Unable to create '%s'" % tmp)

    def read_test_cases(self):
        for fname in os.listdir(self.in_dir):
            # Create a new QueueEntry object for the test case
            entry = QueueEntry()
            entry.fname = fname
            entry.len = os.path.getsize(os.path.join(self.in_dir, fname))

            Queue.append(entry)

    def perform_dry_run(self):

        for q in Queue:
            fn = os.path.join(self.in_dir, q.fname)
            #print("q.fname is: ", fn)
            try:
                fd = open(fn, 'rb')
                test_case = fd.read(q.len)
                fd.close()
                self.write_to_testcase(test_case)
                # Launch the program under test
                start_time = time.time()
                current_dir = os.getcwd()
                res = subprocess.run([self.target_path, self.out_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout = res.stdout
                stderr = res.stderr
                end_time = time.time()
                elapsed_time = end_time - start_time
                if elapsed_time > self.timeout_given:
                    print("Program exceeded timeout of", self.timeout_given, "seconds")
                    return 'timeout'
                print("stdout is: ", stdout)
                print("return code is: ", res.returncode)
                if res.returncode != 0:
                    full_path = os.path.join(os.getcwd(), 'crush' + '_' + str(1) + '.txt')

                    f = open(full_path, 'wb')
                    fd = open(self.out_file, 'rb')

                    file_data = fd.read()

                    f.write(file_data)

                    f.close()
                    fd.close()
                    '''print("    Oops, the program crashed with one of the test cases provided. There are\n" +
                          "    several possible explanations:\n\n" +

                          "    - The test case causes known crashes under normal working conditions. If\n" +
                          "      so, please remove it. The fuzzer should be seeded with interesting\n" +
                          "      inputs - but not ones that cause an outright crash.\n\n")'''
                #return 'crash'
                    pass

            except FileNotFoundError:
                print("Unable to reed testcase")
                #sys.exit(1)
        return 'success'

    def write_to_testcase(self, data):
        fn = os.path.join(os.getcwd(), 'test.txt')
        #print("out_file is: ", fn)
        try:
            fd = open(fn, 'wb')
            fd.write(data)
            fd.close()
        except:
            pass


    def run(self):
        for q in Queue:
            #print("q.fname is: ", q.fname)
            fn = os.path.join(self.in_dir, q.fname)
            with open(fn, 'rb') as fd:
                test_data = fd.read()
                print("test_data is: ", test_data)

                mutated_data = mutate_data(test_data)

                print("mutated data is: ", mutated_data)
                self.write_to_testcase(mutated_data)

                # Run the test program with the mutated data
                start_time = time.time()
                process = subprocess.Popen([self.target_path, self.out_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()

                # Check the return code
                return_code = process.wait()
                if return_code != 0:
                    print("return code is: ", return_code)
                    print("Program returned non-zero exit code:", return_code)
                    return 'crash'

                # Check the timeout
                end_time = time.time()
                elapsed_time = end_time - start_time
                if elapsed_time > self.timeout_given:
                    print("Program exceeded timeout of", self.timeout_given, "seconds")
                    return 'timeout'
        return 'success'


def get_core_count():
    cpu_core_count = psutil.cpu_count()
    if cpu_core_count:
        cur_utilization = psutil.cpu_percent()
        print(f"You have {cpu_core_count} CPU cores with average utilization of {cur_utilization}%.")
        if cpu_core_count > 1:
            if cur_utilization >= 90:
                print("System under apparent load, performance may be spotty.")
            else:
                print(f"Try parallel jobs.")
    else:
        print("Unable to figure out the number of CPU cores.")


def destroy_queue():
    while Queue:
        Queue.pop()




def init(fuzzer):
    # Get information about quantity of logical processors and average utilization
    get_core_count()
    # Setup shared memory
    fuzzer.setup_shm()
    # Read testcases and save them into queue
    fuzzer.read_test_cases()
    # Setup output dirs for fuzzer
    fuzzer.setup_dirs_fds()
    # Check the given testcases
    fuzzer.perform_dry_run()
    # Fuzzing
    fuzzer.run()

    fuzzer.remove_shm()

    destroy_queue()
    pass


def push():
    fuzzer = Fuzzer()
    fuzzer.target_path = widget.ui.trg_module.text()
    print("Target path is: " + fuzzer.target_path)
    fuzzer.in_dir = widget.ui.input_dir.text()
    # print(in_dir)
    fuzzer.out_dir = widget.ui.output_dir.text()
    # print(out_dir)
    fuzzer.out_file = widget.ui.out_file.text()
    fuzzer.timeout_given = int(widget.ui.time_limit.text())
    fuzzer.extras_dir = widget.ui.dict_dir.text()
    if widget.ui.drio_dir == "":
        fuzzer.drioless = True
    else:
        fuzzer.drioless = False
        fuzzer.dynamorio_dir = widget.ui.drio_dir.text()
        print(fuzzer.dynamorio_dir)

    if widget.ui.distrib_mode.isEnabled():
        fuzzer.force_deterministic = True
        fuzzer.fuzzer_id = widget.ui.fuzz_id.text()
    init(fuzzer)
    pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    widget.ui.in_button.clicked.connect(widget.on_in_button_clicked)
    widget.ui.out_button.clicked.connect(widget.on_out_button_clicked)
    widget.ui.drio_button.clicked.connect(widget.on_drio_button_clicked)
    widget.ui.dict_button.clicked.connect(widget.on_dict_button_clicked)
    widget.ui.trg_button.clicked.connect(widget.on_trg_button_clicked)
    widget.ui.distrib_mode.clicked.connect(widget.on_distrib_mode_clicked)
    widget.ui.dbg_checkbox.clicked.connect(widget.on_dbg_mode_clicked)
    widget.ui.dumb.clicked.connect(widget.on_dumb_clicked)
    widget.ui.start_button.clicked.connect(push)
    widget.ui.outf_button.clicked.connect(widget.on_outf_button_clicked)
    sys.exit(app.exec())
