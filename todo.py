#!/usr/bin/python2
import sys
import pickle
import os
import time

TODO_LIST = '%s/todo_list.pickled.gz' % os.getenv('HOME')

class Todo:
    def __init__(self, id, text):
        self.m_id   = id
        self.m_created_time = time.time()
        self.m_text = text
        self.m_deps = []
        self.m_done = False
        self.m_done_time = None

    def dependsOn(self, id):
        self.m_deps.append(id)

    def id(self):
        return self.m_id

    def __repr__(self, list=None):
        if self.m_done:
            return "* finished:  [%s] AT %s" % (self.m_text, [time.strftime('%d %b %Y %H:%M:%S',time.localtime(self.m_done_time)),'?'][self.m_done_time is None])
        elif len(self.m_deps) > 0:
            if list:
                deps = []
                for i in self.m_deps:
                    if list.has_key(i) and not list[i].done():
                        deps.append(i)
            else:
                deps = self.m_deps
            if len(deps) > 0:
                return "* requires [%s]:  %s" % (", ".join([str(i) for i in deps]), self.m_text)
            else:
                return '%s [created at %s]'%(self.m_text, [time.strftime('%d %b %Y %H:%M:%S',time.localtime(self.m_created_time)),'?'][self.m_created_time is None])
        else:
            return '%s [created at %s]'%(self.m_text, [time.strftime('%d %b %Y %H:%M:%S',time.localtime(self.m_created_time)),'?'][self.m_created_time is None])

    def finish(self):
        self.m_done_time = time.time()
        self.m_done = True

    def unfinish(self):
        self.m_done = False

    def done(self):
        return self.m_done

    def set_text(self, text):
        self.m_text = text

    def deps(self):
        return self.m_deps

    def checkDeps(self, list):
        for id in self.m_deps:
            if list.has_key(id) and not list[id].done():
                return False
        return True


class TodoList:
    def __init__(self):
        self.m_list = {}
        self.m_id   = 1

    def addTodo(self, text):
        id = self.m_id
        self.m_list[id] = Todo(id, text)
        self.m_id += 1
        return id

    def deleteTodo(self, id):
        if self.m_list.has_key(id):
            del self.m_list[id]
        else:
            print >>sys.stderr, "Invalid id %d" % id

    def list(self):
        return self.m_list

    def listReady(self):
        list = []
        for i in self.m_list:
            if not self.m_list[i].done() and self.m_list[i].checkDeps(self.m_list):
                list.append(self.m_list[i])
        return list

    def get(self, id):
        if self.m_list.has_key(id):
            return self.m_list[id]
        else:
            return Todo('')

    def __repr__(self):
        s = 'Todo Items:\n'
        for i in self.m_list:
            if not self.m_list[i].done():
                s += '  %d.  %s\n' % (i, self.m_list[i].__repr__(self.m_list) )
        return s

    def print_all(self):
        s = 'All Todo Items:\n'
        for i in self.m_list:
            s += '  %d.  %s\n' % (i, self.m_list[i])
        print s

    def print_ready(self):
        list = self.listReady()
        s = 'Ready Todo Items:\n'
        for item in list:
            s += '  %d.  %s\n' % (item.id(), item.__repr__(self.m_list))
        print s

    def print_waiting(self):
        s = 'Waiting Todo Items:\n'
        for i in self.m_list:
            if not self.m_list[i].done() and not self.m_list[i].checkDeps(self.m_list):
                s += '  %d.  %s\n' % (i, self.m_list[i].__repr__(self.m_list))
        print s

    def print_finished(self, time_sorted, week, reverse):
        s = 'Finished Todo Items:\n'
        last_week = time.time()-7*24*60*60
        items = sorted([(self.m_list[x].m_done_time, x, self.m_list[x]) for x in self.m_list
                             if self.m_list[x].done() and
                                (not week or self.m_list[x].m_done_time>last_week)],
                        reverse=reverse)
        print s+'\n'.join('  %d.  %s'%(item[1],item[2].__repr__(self.m_list)) for item in items)

    def print_group(self, group):
        list = self.listReady()
        s = 'Ready Todo Items (for %s):\n' % group
        for item in list:
            name = item.__repr__(self.m_list)
            if name.split(':')[0] == group:
                s += '  %d.  %s\n' % (item.id(), item.__repr__(self.m_list))
        print s

    def print_groups(self):
        list = self.listReady()
        s = 'Ready Todo Items (by Group):\n'
        groups = {}
        for item in list:
            id   = item.id()
            name = item.__repr__(self.m_list)
            group = name.split(':')[0]
            if not groups.has_key( group ):
                groups[group] = []
            groups[group].append((id, name))
        for group in groups:
            s += ' -- %s --\n' % group
            for item in groups[group]:
                s += '  %d.  %s\n' % item
        print s

import zlib
import shutil
def loadTodoList(file=TODO_LIST):
    if os.path.exists( file ):
        fp = open(file, 'rb')
        todo = pickle.loads( zlib.decompress(fp.read()) )
        fp.close()
        return todo
    else:
        return TodoList()

def saveTodoList(todo, file=TODO_LIST):
    fp = open(TODO_LIST+'.tmp', 'w')
    fp.write( zlib.compress( pickle.dumps(todo) ) )
    fp.close()
    shutil.move(TODO_LIST+'.tmp', TODO_LIST)

from optparse import OptionParser

def main():
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    parser.add_option("-l", "--list", dest="list",
                      action="store_true", help="list all todo items not finished")
    parser.add_option("-L", "--list-all", dest="list_all",
                      action="store_true", help="list all todo items")
    parser.add_option("-r", "--list-ready", dest="list_ready",
                      action="store_true", help="list all ready todo items")
    parser.add_option("-w", "--list-waiting", dest="list_waiting",
                      action="store_true", help="list all waiting todo items")
    parser.add_option("-F", "--list-finished", dest="list_finished",
                      action="store_true", help="list all finished todo items")
    parser.add_option("-T", "--time-sorted", dest="time_sorted",
                      action="store_true", help="sort the output by time")
    parser.add_option("-W", "--week", dest="week",
                      action="store_true", help="limit to one week")
    parser.add_option("-R", "--reverse", dest="reverse", default=False,
                      action="store_true", help="reverse the output order")
    parser.add_option("-G", "--list-groups", dest="list_groups",
                      action="store_true", help="list all ready todo items by group")
    parser.add_option("-a", "--add", dest="add",
                      action="store_true", help="add a new todo item")
    parser.add_option("-i", "--id", dest="id",
                       help="set changing todo id as specified")
    parser.add_option("-f", "--finish", dest="finish",
                       help="finish the supplied todo id")
    parser.add_option("-x", "--erase", dest="delete",
                       help="remove the supplied todo id")
    parser.add_option("-u", "--unfinish", dest="unfinish",
                       help="unfinish the supplied todo id")
    parser.add_option("-e", "--edit", dest="edit",
                       help="edit text of supplied todo id")
    parser.add_option("-g", "--group", dest="group",
                       help="limit to todo items starting with specified group")
    parser.add_option("-d", "--depends-on", dest="depends",
                       help="add this todo item as a dependent to ID")

    (options, args) = parser.parse_args()

    todolist = loadTodoList()
    changed = False
#    for id in todolist.m_list:
#        todolist.m_list[id].m_created_time = time.time()
#        changed=True

    if options.list:
        print todolist

    elif options.list_groups:
        todolist.print_groups()

    elif options.list_all:
        todolist.print_all()

    elif options.list_waiting:
        todolist.print_waiting()

    elif options.list_finished:
        todolist.print_finished(options.time_sorted, options.week, options.reverse)

    elif options.group:
        todolist.print_group(options.group)

    elif options.add:
        if len(args) <= 0:
            print >>sys.stderr, "todo.py: error: You must supply quoted text to add to the todo list"
        else:
            for arg in args:
                id = todolist.addTodo(arg)
                print >>sys.stderr, "Added Todo Item '%s' as id %d" % (arg, id)
        changed = True

    elif options.finish:
        print 'finishing %s -- %s' % (options.finish, todolist.get(int(options.finish)))
        todolist.get(int(options.finish)).finish()
        changed = True

    elif options.unfinish:
        print 'unfinishing %s -- %s' % (options.unfinish, todolist.get(int(options.unfinish)))
        todolist.get(int(options.unfinish)).unfinish()
        changed = True

    elif options.delete:
        print 'deleting %s -- %s' % (options.delete, todolist.get(int(options.delete)))
        todolist.deleteTodo( int(options.delete) )
        changed = True

    elif options.edit:
        if len(args) != 1:
            print >>sys.stderr, "todo.py: error: You must supply quoted text to set the todo item to"
        else:
            print 'relabeling %s from "%s" to "%s"' % (options.edit, todolist.get(int(options.edit)), args[0])
            todolist.get(int(options.edit)).set_text(args[0])
        changed = True

    elif options.depends and options.id:
        print '%s depends on %s' % (options.id, options.depends)
        todolist.get(int(options.id)).dependsOn(int(options.depends))
        changed = True

    elif len(args) >= 1:
        for arg in args:
            id = todolist.addTodo(arg)
            print >>sys.stderr, "Added Todo Item '%s' as id %d" % (arg, id)
        changed = True

    elif options.list_ready:
        todolist.print_ready()

    else:
        todolist.print_groups()

    if changed:
        saveTodoList(todolist)

if __name__ == '__main__':
    main()
