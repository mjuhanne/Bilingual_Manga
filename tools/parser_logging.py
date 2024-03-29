from jp_parser_helper import *

########### LOGGING FACILITIES ######################

verbose_level = 0
log_file = None

stats_no_refs = dict()

def STATS_NO_REFS(item,cl):
    if (item.txt,cl) not in stats_no_refs:
        stats_no_refs[(item.txt,cl)] = 1
    else:
        stats_no_refs[(item.txt,cl)] += 1

incidences = dict()
def INCIDENCE_COUNTER(incidence, target_word, items):
    if incidence not in incidences:
        incidences[incidence] = []
    incidences[incidence].append((target_word,[item.txt for item in items]))

def LOG_HEADING(level=2):
    if level <= verbose_level:
        print("*************")

def LOG(level, msg, items=None):
    if level <= verbose_level:
        print(msg)
        if log_file is not None:
            print(msg, file=log_file)
            if items is not None:
                print("Phrase:"+''.join([item.txt for item in items]), file=log_file)

def set_verbose_level(level):
    global verbose_level
    verbose_level = level

def get_verbose_level():
    return verbose_level

def open_log_file(file):
    global log_file
    log_file = open(file, "w", encoding="utf-8")

def close_log_file():
    sorted_stats = dict(sorted(stats_no_refs.items(), key=lambda x:x[1], reverse=False))
    print("No refs statistics:", file=log_file)
    for (word,cl),count in sorted_stats.items():
        print("%s %s %s" % ( str(count).ljust(3), unidic_class_to_string(cl).ljust(10),word), file=log_file)
    print("No refs statistics:", file=log_file)
    for (incidence_msg,i_list) in incidences.items():
        print("**** %s ****" % incidence_msg, file=log_file)
        for (target_word, words) in i_list:
            print("%s : %s" %(target_word.ljust(6,'　'),''.join(words)), file=log_file)
        print("-- Total %d incidences" % len(i_list), file=log_file)

    log_file.close()

######### END OF LOGGING FACILITIES #################
