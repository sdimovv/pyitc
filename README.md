# pyitc

<img src="https://img.shields.io/github/actions/workflow/status/sdimovv/pyitc/.github%2Fworkflows%2Fbuild-and-run-tests.yml?branch=main&logo=github" alt="Build Status"> <a href="https://codecov.io/gh/sdimovv/pyitc" >
 <img src="https://codecov.io/gh/sdimovv/pyitc/graph/badge.svg"/>
 </a> <a href="https://github.com/sdimovv/pyitc/releases/latest"><img src="https://img.shields.io/github/v/release/sdimovv/pyitc" alt="Latest GitHub Release"></a> <a href="./LICENSE"><img src="https://img.shields.io/github/license/sdimovv/pyitc" alt="License AGPL-3.0"></a>

Python bindings for the [libitc library](https://github.com/sdimovv/libitc).

## What Are Interval Tree Clocks?

Interval Tree Clocks (ITC) are a generalisation of the [Vector Clock](https://en.wikipedia.org/wiki/Vector_clock) and [Version Vector](https://en.wikipedia.org/wiki/Version_vector) mechanisms, allowing for scalable and efficient management of a
highly dynamic number of replicas/processes in a distributed system.


## Features

* Provides easy-to-use Pythonesque bindings for the underlying C library
* Provides `str` methods for easy visualisation of the ITC trees
* Provides bindings the C lib's ["extended api"](https://github.com/sdimovv/libitc?tab=readme-ov-file#features:~:text=%22extended%22%20API%20interface)
* Uses 64-bit event counters

## How to use

Here are some usage examples:

```py
from pyitc import Stamp
from pyitc.extended_api import Id, Event

stamp = Stamp()
stamp.event()

stamp2 = stamp.fork()

print(stamp) # {(0, 1); 1}
print(stamp.peek()) # {0, 1}
print(stamp2) # {(1, 0); 1}

print(stamp.id_component) # (0, 1)
print(stamp.event_component) # 1

stamp.event_component = Event()
stamp.id_component = Id(seed=True)

print(stamp.serialise()) # b'\x00\t\x01\x02\x01\x00'
print(stamp.id_component.serialise()) # b'\x00\x02'
print(stamp.event_component.serialise()) # b'\x00\x00'

remote_stamp = Stamp.deserialise(b'...')
remote_event = Event.deserialise(b'...')
remote_id = Id.deserialise(b'...')
```

## License

Released under AGPL-3.0 license, see [LICENSE](./LICENSE) for details.
