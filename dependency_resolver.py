#!/usr/bin/env python3

import argparse
import collections

import yaml

def to_int_if_whole_number(number):
    return int(number) if isinstance(number, float) and number.is_integer() else number

class Dependency:
    def __init__(self, index, quantity):
        self.index = index
        self.quantity = quantity

class Item:
    def __init__(self, name, dependencies, time):
        self.name = name
        self.dependencies = dependencies
        self.time = time

class Graph:
    def __init__(self):
        self.names = {}
        self.items = []

    def add_item(self, name):
        self.names[name] = len(self.names)
        self.items.append(None)

    def set_item(self, name, dependencies, time):
        if name not in self.names:
            raise RuntimeError(f'Item "{name}" not found')
        dependencies_index = []
        for dependency in dependencies:
            dependency_name = dependency['name']
            if dependency_name not in self.names:
                raise RuntimeError(f'Item "{dependency_name}" not found')
            dependencies_index.append(Dependency(self.names[dependency_name], dependency['quantity']))
        self.items[self.names[name]] = Item(name, dependencies_index, time)

    def get_cycle(self):
        def dfs(cur, visited, path):
            path.append(cur)
            if cur in visited:
                return True
            visited.add(cur)
            for dependency in self.items[cur].dependencies:
                if dfs(dependency.index, visited, path):
                    return True
            visited.remove(cur)
            path.pop()
            return False
        for i in range(len(self.items)):
            visited = set()
            path = []
            if dfs(i, visited, path):
                first = path.index(path[-1])
                path = path[first:]
                path_names = [self.items[i].name for i in path]
                return path_names
        return []

    def resolve_dependency(self, name, quantity):
        cycle = self.get_cycle()
        if len(cycle) > 0:
            raise RuntimeError(f'Circular dependencies detected: {" => ".join(cycle)}')
        if name not in self.names:
            raise RuntimeError(f'Item "{name}" not found')
        que = collections.deque()
        steps = []
        times = []
        que.append(Dependency(self.names[name], quantity))
        while len(que) > 0:
            sum_dependencies = sum(len(self.items[d.index].dependencies) for d in que)
            if len(self.items[que[0].index].dependencies) == 0 and sum_dependencies > 0:
                que.append(que.popleft())
                continue
            steps.append(que.copy())
            if sum_dependencies == 0:
                times.append(sum(self.items[d.index].time * d.quantity for d in que))
                break
            front = que.popleft()
            item = self.items[front.index]
            times.append(item.time * front.quantity)
            for dependency in item.dependencies:
                for i, d in enumerate(que):
                    if d.index == dependency.index:
                        que[i] = Dependency(d.index, d.quantity + dependency.quantity * front.quantity)
                        break
                else:
                    que.append(Dependency(dependency.index, dependency.quantity * front.quantity))
        steps = list(reversed(steps))
        times = list(to_int_if_whole_number(t) for t in reversed(times))
        steps_ret = []
        for que in steps:
            quantities = [0] * len(self.items)
            for dependency in que:
                quantities[dependency.index] += dependency.quantity
            step = [(self.items[i].name, to_int_if_whole_number(quantity)) for i, quantity in enumerate(quantities) if quantity > 0]
            steps_ret.append(step)
        return steps_ret, times

    @staticmethod
    def load(filename):
        with open(filename, 'r') as f:
            data = yaml.safe_load(f)
        graph = Graph()
        for name in data:
            graph.add_item(name)
        for name, item in data.items():
            graph.set_item(name, item['dependencies'], item['time'])
        return graph

def main():
    parser = argparse.ArgumentParser(description='Dependency Resolver')
    parser.add_argument('filename', type=str, help='dependency file')
    parser.add_argument('item', type=str, help='target item to make')
    parser.add_argument('-n', type=float, default=1, help='the number of target items to make')
    args = parser.parse_args()
    graph = Graph.load(args.filename)
    steps, times = graph.resolve_dependency(args.item, args.n)
    for i, step in enumerate(steps):
        step = ', '.join([f'{round(item[1], 2)} {item[0]}' for item in step])
        time = times[i]
        print(f'Make {step} in time {round(time, 2)}')
    print(f'Total time: {round(to_int_if_whole_number(sum(times)), 2)}')

if __name__ == '__main__':
    main()
