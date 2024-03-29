#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Author: Tim Henderson
#Email: tim.tadh@gmail.com
#For licensing see the LICENSE file in the top level directory.

from __future__ import absolute_import

import collections

import zss


class Node():
    """
    A simple node object that can be used to construct trees to be used with
    :py:func:`zss.distance`.

    Example: ::

        Node("f")
            .addkid(Node("a")
                .addkid(Node("h"))
                .addkid(Node("c")
                    .addkid(Node("l"))))
            .addkid(Node("e"))
    """

    def __init__(self, label, children=None):
        self.label = label
        self.children = children or list()

    @staticmethod
    def get_children(node):
        """
        Default value of ``get_children`` argument of :py:func:`zss.distance`.

        :returns: ``self.children``.
        """
        node.children = sorted(node.children,
         key=lambda x: (len(list(x.iter())), len(x.children), x.get_max_value_from_subtree() ,x.label, x.get_value_if_exist()))

        return node.children
    

    def get_max_value_from_subtree(self):
        values = []
        for child in self.iter():
            if child.label == "value":
                value = child.children[0].label
                values.append(value)
        if len(values) == 0:
            return ""
        return max(values, key=len)
    
    def get_value_if_exist(self):
        if len(self.children) == 1:
            return self.children[0].label   
        return ""             

    @staticmethod
    def get_label(node):
        """
        Default value of ``get_label`` argument of :py:func:`zss.distance`.

        :returns: ``self.label``.
        """
        return node.label

    def addkid(self, node, before=False):
        """
        Add the given node as a child of this node.
        """
        if before:  self.children.insert(0, node)
        else:   self.children.append(node)
        return self

    def get(self, label):
        """:returns: Child with the given label."""
        if self.label == label: return self
        for c in self.children:
            if label in c: return c.get(label)

    def iter(self):
        """Iterate over this node and its children in a preorder traversal."""
        queue = collections.deque()
        queue.append(self)
        while len(queue) > 0:
            n = queue.popleft()
            for c in n.children: queue.append(c)
            yield n

    def __contains__(self, b):
        if isinstance(b, str) and self.label == b: return 1
        elif not isinstance(b, str) and self.label == b.label: return 1
        elif (isinstance(b, str) and self.label != b) or self.label != b.label:
            return sum(b in c for c in self.children)
        raise TypeError("Object %s is not of type str or Node" % repr(b))

    def __repr__(self):
        return super(Node, self).__repr__() + " %s>" % self.label

    def __str__(self):
        s = "%d:%s" % (len(self.children), self.label)
        s = '\n'.join([s]+[str(c) for c in self.children])
        return s
    
    def __str__(self, level=0):
        ret = "\t"*level+repr(self.label)+"\n"
        for child in self.children:
            ret += child.__str__(level+1)
        return ret

    def print_tree(self, last=True, header=''):
        elbow = "└──"
        pipe = "│  "
        tee = "├──"
        blank = "   "
        if self.label is None:
            print(header + (elbow if last else tee) + "None")
        else:
            print(header + (elbow if last else tee) + str(self.label))
        children = self.get_children(self)
        for i, c in enumerate(children):
            c.print_tree(header=header + (blank if last else pipe), last=i == len(children) - 1)

    def __sub__(self, other):
        return zss.simple_distance(self, other)