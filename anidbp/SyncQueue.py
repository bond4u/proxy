#!/usr/bin/env python3
#
# Synchronized Queue for multithreading
#
import threading
from collections import deque

class SyncQueue():
  '''Synchronized aget/wait queue'''
  def __init__(self):
    '''Creates a condition and queue'''
    self.lock = threading.Condition()
    self.queue = deque()
  def add(self,data):
    '''Acquires a lock and adds data to the end of queue'''
    try:
      self.lock.acquire()
      self.queue.append(data)
      self.lock.notify()
    finally:
      self.lock.release()
  def insertFront(self,data):
    '''Acquires a lock and adds data to the front of queue'''
    try:
      self.lock.acquire()
      self.queue.appendleft(data)
      self.lock.notify()
    finally:
      self.lock.release()
  def size(self):
    '''Returns current queue size'''
    l = None
    try:
      self.lock.acquire()
      l = len(self.queue)
    finally:
      self.lock.release()
    return l
  def get(self):
    '''Acquires a lock, returns 1st item if available'''
    rval = None
    try:
      self.lock.acquire()
      if 0 < len(self.queue):
        rval = self.queue.popleft()
      #else queue is empty, return None
    finally:
      self.lock.release()
    return rval
  #TODO wait()
