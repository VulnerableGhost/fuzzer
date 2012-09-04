from sys import exit, argv
from sys import stdout
from Mutator import Mutator
from Executor import executor
from time import ctime, time
from multiprocessing import Pool
from optparse import OptionParser
import logging

# todo
#
# - make the to_run string (and the way the user defines where the mutated file goes in the command line) more generic
#   - fill in with a regex or something
#
# - allow a max time for a process to run
#
# - support multiple processes
#
# - add "example" to usage()

def check_usage(check_args):
    ''' Parse command line options '''

    parser = OptionParser()
    parser.add_option('-p', action="store", dest="program_cmd_line", help='Program to launch, the full command line that will be executed', metavar="program")
    parser.add_option('-f', action="store", dest="original_file", help='File to be mutated', metavar="file")
    parser.add_option('-d', action="store", dest="temp_directory", help='Directory for temporary files to be created', metavar="temp_directory")
    parser.add_option('-t', action="store", dest="mutation_type", help='Type of mutation ("byte", "word", "dword")', metavar="mutation_type")
    parser.add_option('-l', action="store", dest="log_file", help='Log file', metavar="log")
    parser.add_option('-s', action="store", dest="save_directory", help='Save-directory, for files to be saved that cause crashes', metavar="save_directory")
    parser.add_option('-m', action="store", dest="max_processes", help='Max Processes (not implemented currently)', metavar="max_processes")
    parser.epilog = "Example:\n\n"
    parser.epilog += './fuzzer.py -p "C:\Program Files\Blah\prog.exe" -f original_file.mp3 -d temp -t dword -l log.txt -s save'
    options, args = parser.parse_args(check_args)

    # pull them out
    program_cmd_line = options.program_cmd_line
    original_file    = options.original_file
    temp_directory   = options.temp_directory
    mutation_type    = options.mutation_type
    log_file         = options.log_file
    save_directory   = options.save_directory
    max_processes    = 1 # options.max_processes

    # make sure enough args are passed
    if not all((program_cmd_line, original_file, temp_directory, mutation_type, log_file, save_directory)):
        parser.error("Incorrect number of arguments")

    return (program_cmd_line, original_file, temp_directory, mutation_type, log_file, save_directory, max_processes)


if __name__ == "__main__":

    # check command line args
    (cmd_line, original_file, temp_directory, mutation_type, logfile_name, save_directory, max_processes) = check_usage(argv[1:])

    # typecast, create the worker pool
    max_processes   = int(max_processes)
    pool            = Pool(max_processes, maxtasksperchild=50)
    
    # log basic starting information
    logging.basicConfig(filename=logfile_name, level=logging.INFO)
    logging.info("Starting Fuzzer")
    logging.info("%s" % ctime())
    logging.info('cmd_line        = %s' % cmd_line)
    logging.info('original_file   = %s' % original_file)
    logging.info('temp_director   = %s' % temp_directory)
    logging.info('mutation_type   = %s' % mutation_type)
    logging.info('max_processes   = %d' % max_processes)
    logging.info('logfile_name    = %s' % logfile_name)
    logging.info('save_directory  = %s' % save_directory)

    # create the mutator, and log the possible values it will produce
    mutator = Mutator(original_file, temp_directory, mutation_type)    
    logging.info('total mutations = %d' % mutator.total_mutations)
    logging.info('possible mutation list :')
    for offset, mutation in enumerate(mutator.getValues()):
        logging.info('[%02d] : %s'% (offset, repr(mutation)) )

    # figure out some relative percentages
    ten_percent = mutator.total_mutations / 10
    percent = 0

    # the main loop - yield each mutation, execute and log it
    start_time = time()
    for counter, (offset, value_index, value_type, new_file) in enumerate(mutator.createNext()):

        # just for sanity
        if counter % ten_percent == 0:
            print '%02d%% - %s' % (percent, ctime())
            percent += 10

        torun = '%s %s' % (cmd_line, new_file)
        logger=logging.getLogger('Executor-%d'%counter)
        # awesome, but creates the files up front :( - pool.apply_async(executor, (torun,offset,value_index,new_file,counter,save_directory,0), callback=output_logging_callback)#logger))
        res = pool.apply(executor, (torun,offset,value_index,new_file,counter,save_directory))
        logging.info(res)

    # clean up and wait
    pool.close()
    pool.join()
    logging.info("test finished")
    end_time = time() - start_time
    print 'total time =', end_time