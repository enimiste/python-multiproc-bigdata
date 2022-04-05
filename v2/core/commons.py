from abc import ABC
from functools import reduce
import logging
from logging import ERROR, Logger
import multiprocessing
import threading
import traceback
from typing import Any, Callable, Generator

class WithLogging(ABC):
    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    @staticmethod
    def log_msg_sync(logger: Logger, msg: str, exception: Exception = None, level: int = logging.DEBUG):
        if not logger is None:
            if not exception is None and level==ERROR:
                logger.log(level, "{}, Trace : {}".format(msg, str(traceback.format_exception(exception))))
            else:
                logger.log(level, msg)
        else:
            print(msg)
        
    def log_msg(self, msg: str, exception: Exception = None, level: int = logging.DEBUG):
        WithLogging.log_msg_sync(self.logger, msg, exception, level)
        # threading.Thread(target=WithLogging.log_msg_sync, args=(self.logger, msg, exception, level)).start()
    

class LoggerWrapper(WithLogging):
    def __init__(self, logger: Logger) -> None:
        super().__init__(logger)
        

def rotary_iter(items: list):
    n = len(items)
    i = n-1
    while True:
        i = (i+1)%n
        yield items[i]

def dict_deep_get(dictionary: dict, keys: list[str]):
    return reduce(lambda d, key: d.get(key) if (type(d) is dict and key in d) else None, keys, dictionary)

def dict_deep_set(dictionary: dict, keys: list[str], value):
    if len(keys)==0:
        return
    container = reduce(lambda d, key: d.get(key) if (type(d) is dict and key in d) else {}, keys[:-1], dictionary)
    container[keys[-1]] = value

def dict_deep_remove(dictionary: dict, keys: list[str]):
    if keys is not None:
        if len(keys)==0:
            return
        container = dict_deep_get(dictionary, keys[:-1])
        if container is not None and keys[-1] in container:
            del container[keys[-1]]

def flatMapApply(item:Any, mappers: list[Callable[[Any], Generator[Any, None, None]]], **kwargs) -> Generator[Any, None, None]:
        if len(mappers)==0:
            yield item
        else:
            mapper = mappers[0]
            g = mapper(item, **kwargs)
            for x in g:
                if x is not None:
                    for a in  flatMapApply(x, mappers[1:], **kwargs):
                        if a is not None:
                            yield a

def get_thread_process_id(th):
    if type(th) is threading.Thread:
        return th.ident
    elif type(th) is multiprocessing.Process:
        return th.pid
    raise RuntimeError('Invalid thread/process object <>'.format(str(type(th))))

def get_thread_process_is_joined(th) -> bool:
    if type(th) is threading.Thread:
        return not t.is_alive()
    elif type(th) is multiprocessing.Process:
        return th.exitcode is not None
    raise RuntimeError('Invalid thread/process object <>'.format(str(type(th))))

def kill_threads_processes(threads: list[Any], ignore_exception:bool=True):
    for th in threads:
        kill_thread_process(th, ignore_exception)
        
def kill_thread_process(th, ignore_exception:bool=True):
    try:
        if type(th) is threading.Thread:
            th._stop()
            return
        elif type(th) is multiprocessing.Process:
            th.kill()
            return
    except Exception as ex:
        if not ignore_exception:
            raise ex
    raise RuntimeError('Invalid thread/process object <>'.format(str(type(th))))

def block_join_threads_or_processes(threads: list[Any], interrupt_on: Callable[[], bool], join_timeout: int = 0.01, ignore_exception:bool=True) -> bool:
    nbr_threads = len(threads)
    joined_ids = set()
    while len(joined_ids) < nbr_threads:
        for t in threads:
            try:
                t_id = get_thread_process_id(t)
                if t_id not in joined_ids:
                    if interrupt_on():
                        joined_ids.add(t_id) # should be before terminate()
                        kill_thread_process(t)
                    else:
                        t.join(timeout=join_timeout)
                        is_joined = get_thread_process_is_joined(t)
                        if is_joined:
                            joined_ids.add(t_id)
                            t.terminate()
            except Exception as ex:
                if not ignore_exception:
                    raise ex
    return True