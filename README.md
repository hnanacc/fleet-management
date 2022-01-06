# fleet-management
DS Project


# middlewares
communication.
p2p - http
client-server - http


# Notes on Implementation

`Node`

* For the `initConnection` method we need some kind of waiting mechanism.
* Also, while waiting we don't want the `performRole` method to wait.
* The best option which covers both cases is executing both on different threads.

`Networks`

* This is an absraction for all the network related activities.
* We pass an instance of `Network` class while instantiating `Node`.

```py
    newNode = Node(eventInstance, networkInstance)
```






