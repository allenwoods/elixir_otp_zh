# 7   Completing the Worker Pool Application


This chapter covers:


·      Implement the entire worker pool application


·      Build multiple supervision hierarchies


·      Dynamically creating supervisors and workers


In this chapter, we will continue to evolve the design of
`Pooly`, which we started in Chapter 6. By the end of this chapter, we would have a full, working worker pool application. We will get to explore other the Supervisor API more thoroughly, and also explore more advanced (read: fun!) supervisor topics.


In chapter 6, we were left with a very rudimentary worker pool application, if we can even call it that. In the following sections, will add some smarts into
`Pooly`. For example, there is currently no way of handling crashes and restarts gracefully. The current version of
`Pooly`
can only handle a single pool with a fixed number of workers. Version 3 of
`Pooly`
will implement support for multiple pools and support for variable number of worker processes.


Sometimes the pool must deal with unexpected load. What happens when there are too many requests? What happens when all the workers are busy? In version 4, we make pools be variable-sized that allows for the *overflowing* of workers. We also implement queuing for consumer processes when all workers are busy.


7.1           Version 3: Error Handling, Multiple Pools and Workers


How can we tell if a process crashes? We can either monitor or link to it. This leads to the next question, which should we choose? To answer that question, we must think about what should happen when processes crash. There are two cases to consider. There can be crashes between:


·      Server process and Consumer process


·      Server process and Worker process


7.1.1        Case 1: Crashes between the Server and Worker


A crash of the server process shouldn’t affect a consumer process. In fact, the reverse is also true! When a consumer process crashes, it shouldn’t crash the server process. Therefore, *monitors* are the way to go.


We are already monitoring the consumer process each time a checkout of a worker is made. What’s left is to handle the
`:DOWN`
message of a consumer process:


Listing 7.1 lib/pooly/server.ex – Handling :DOWN message from a consumer

`defmodule Pooly.Server do`

`#############`
`# Callbacks #`
`#############`

`def handle_info({:DOWN, ref, _, _, _}, state = %{monitors: monitors, workers: workers}) do`
`case :ets.match(monitors, {:”$1”, ref}) do`
`[[pid]] ->`
`true = :ets.delete(monitors, pid)`
`new_state = %{state | workers: [pid|workers]} #1`
`{:no_reply, new_state}`

`[[]] ->`
`{:no_reply, state}`
`end`
`end`
`end`
#1 Return the worker back to the pool


When a consumer process goes down, we match the reference in the
`monitors`
ETS table, delete the monitor, and add back the worker into the state.


7.1.2        Case 2: Crashes between the Server and Worker


If the server crashes, should it bring down the worker process? It should, because otherwise, the state of the server will be inconsistent with the pool’s actual state. On the other hand, when a worker process crashes, should it bring down the server process? Of course not! What does this mean for us? Well, because of the bi-directional dependency, we should be using *links*. However, since the server should *not* crash when a worker process crashes, the server process should trap exits:


Listing 7.2 lib/pooly/server.ex – Make the server process trap exits to prevent worker processes from crashing itself

`defmodule Pooly.Server do`

`#############`
`# Callbacks #`
`#############`
`def init([sup, pool_config]) when is_pid(sup) do`
`Process.flag(:trap_exit, true)                          #1`
`monitors = :ets.new(:monitors, [:private])`
`init(pool_config, %State{sup: sup, monitors: monitors})`
`end`
`end`
#1 Set the server process to trap exits.


With the server process now trapping exits, we should now handle
`:EXIT`
messages coming from workers:


Listing 7.3 lib/pooly/server.ex – Handling :EXIT messages from workers in the pool server

`defmodule Pooly.Server do`

`#############`
`# Callbacks #`
`#############`

`def handle_info({:EXIT, pid, _reason}, state = %{monitors: monitors, workers: workers, worker_sup: worker_sup}) do`
`case :ets.lookup(monitors, pid) do`
`[{pid, ref}] ->`
`true = Process.demonitor(ref)`
`true = :ets.delete(monitors, pid)`
`new_state = %{state | workers: [new_worker(worker_sup)|workers]}`
`{:noreply, new_state}`

`[[]] ->`
`{:noreply, state}`
`end`
`end`
`end`
When a worker process exits unexpectedly, its entry is looked up in the
`monitors`
ETS table. If an entry doesn’t exist, nothing needs to be done. Otherwise, the consumer process is no longer monitored, and its entry is removed from the
`monitors`
table. Finally, a new worker is created and added back into the workers field of the server state.


7.1.3        Handling Multiple Pools


After version 2, we have a very basic worker pool in place. However, any self-respecting worker pool application should be able to handle multiple pools. Let’s go through a few possible designs before we start coding. The most straight forward way would be to design the supervision tree like so:


![](../../images/7_1.png)  



Figure 7. 1 A possible design to handle multiple pools


Do you see a problem with this? We are essentially sticking more
`WorkerSupervisor`’s into
`Pooly.Supervisor`. This is a bad design. The issue here is the *error kernel*, or the lack thereof.


Allow me to elaborate. Issues with any of the
`WorkerSupervisor`s shouldn’t affect the
`Pooly.Server`. It pays to think about what happens when a process crashes and who gets affected. A potential fix could be to add another supervisor to handle all the worker supervisors, say a
`Pooly.WorkersSupervisor`
(*just* another level of indirection!). Here’s how it could like now:


![](../../images/7_2.png)  



Figure 7. 2 Another possible design. Can you identify the bottleneck?


Do you notice another problem? The poor
`Pooly.Server`
process has to handle *every* request that is meant for any pool. This means that the server process might pose a bottleneck if messages to it come fast and furious, and could potentially flood its mailbox.
`Pooly.Server`
also presents a single point of failure, since it contains the state of every pool. The death of the server process means that *all* of the worker supervisors would have to be brought down. Consider this design then:


![](../../images/7_3.png)  



Figure 7. 3 The final design of Pooly


The top-level supervisor
`Pooly.Supervisor`
supervises a
`Pooly.Server`
and a
`PoolsSupervisor`. The
`PoolsSupevisor`
in turn supervises many
`PoolSupervisor`s. Each
`PoolSupervisor`
supervises its own
`PoolServer`
and
`WorkerSupervisor`.


As you probably have guessed, Pooly is going to undergo a design overhaul. To make things easier to follow, we will implement the changes from top down.


7.1.4        Adding the Application Behavior to Pooly


The first place to change is
`lib/pooly.ex`, the main entry point of Pooly. Since we are now supporting multiple pools, we want to refer to each pool by its name. This means that the various functions will also accept
`pool_name`
as a parameter:


Listing 7.4 lib/pooly.ex – Adding support for multiple pools

`defmodule Pooly do`
`use Application`

`def start(_type, _args) do`
`pools_config =                                            #2`
`[                                                       #1`
`[name: “Pool1”,                                       #1`
`mfa: {SampleWorker, :start_link, []}, size: 2],     #1`
`[name: “Pool2”,                                       #1`
`mfa: {SampleWorker, :start_link, []}, size: 3],     #1`
`[name: “Pool3”,                                       #1`
`mfa: {SampleWorker, :start_link, []}, size: 4],     #1`
`]                                                       #1`

`start_pools(pools_config)                                 #2`
`end`

`def start_pools(pools_config) do                            #2`
`Pooly.Supervisor.start_link(pools_config)                 #2`
`end`

`def checkout(pool_name) do                                  #3`
`Pooly.Server.checkout(pool_name)                          #3`
`end`

`def checkin(pool_name, worker_pid) do                       #3`
`Pooly.Server.checkin(pool_name, worker_pid)               #3`
`end`

`def status(pool_name) do                                    #3`
`Pooly.Server.status(pool_name)                            #3`
`end`
`end`
#1 Pool configuration now takes in configuration of multiple pools. Pools also have names.


#2 Pluralization change from pool\_config to pools\_config.


#3 The rest of the APIs take in pool\_name as a parameter.


7.1.5        Adding the Top-level Supervisor


Our next stop is the top-level supervisor,
`lib/pooly/supervisor.ex`.  The top-level supervisor is in charged of kick-starting
`Pooly.Server`
and
`Pooly.PoolsSupervisor`. When
`Pooly.PoolsSupervisor`
starts, it starts up individual
`Pooly.PoolSupervisor`s that in turn starts its own
`Pooly.Server`
and
`Pooly.WorkerSupervisor.`


![](../../images/7_4.png)  



Figure 7. 4 Starting from the top-level supervisor


Looking at the diagram
`Pooly.Supervisor`
supervises two processes:
`Pooly.PoolsSupervisor`
(as yet unimplemented) and
`Pooly.Server`. We therefore need to add these two processes to the
`Pooly.Supervisor`’s children list. Let’s do just that:


Listing 7.5 lib/pooly/supervisor.ex – Top-level supervisor supervises the top-level pool server and pools supervisor

`defmodule Pooly.Supervisor do`
`use Supervisor`

`def start_link(pools_config) do                             #1`
`Supervisor.start_link(__MODULE__, pools_config,`
`name: __MODULE__)                   #2`
`end`

`def init(pools_config) do                                   #1`
`children = [`
`supervisor(Pooly.PoolsSupervisor, []),                  #3`
`worker(Pooly.Server, [pools_config])                    #3`
`]`

`opts = [strategy: :one_for_all]`

`supervise(children, opts)`
`end`
`end`
#1 Pluralization change from pool\_config to pools\_config.


#2 Pooly.Supervisor is now a named process.


#3 Pooly.Supervisor now supervises two children. Note that Pooly.Server no longer takes the pid Pooly.Supervisor, since we can refer to it by name.


The major changes to
`Pooly.Supervisor`
are mainly the adding of
`Pooly.PoolsSupervisor`
as a child and giving
`Pooly.Supervisor`
a name. Recall that we are setting the name of
`Pooly.Supervisor`
to
`__MODULE__`
in #1, this means that we can refer to the process as
`Pooly.Supervisor`
instead of pid. Therefore, we do not need to pass in
`self`
(see version 2 of
`Pooly.Supervisor`) into
`Pooly.Server`.


7.1.6        Adding the Supervisor of Pools


Create
`pools_supervisor.ex`
in
`lib/pooly/`. Here’s the implementation:


Listing 7.6 lib/pooly/pools\_supervisor.ex – Full implementation of the pools supervisor

`defmodule Pooly.PoolsSupervisor do`
`use Supervisor`

`def start_link do`
`Supervisor.start_link(__MODULE__, [], name: __MODULE__) #1`
`end`

`def init(_) do`
`opts = [`
`strategy: :one_for_one                                #2`
`]`

`supervise([], opts)`
`end`
`end`
Just like
`Pooly.Supervisor`, we are giving
`Pooly.PoolsSupervisor`
a name. Notice that this supervisor has *no* child specifications. In fact, when it starts up, there are no pools attached to it. The reason for this is because, just as in version 2, we want to validate the pool configuration *before* creating any pools. Therefore, the only information we supply is the restart strategy, as shown in #2. Why
`:one_for_one`? A crash in any of the pools shouldn’t affect every other pool.


7.1.7        Making Pooly.Server Dumber


In version 1 and version 2, we said that
`Pooly.Server`
was the brains of the entire operation. No longer is the case. The
`Pooly.Server`
is going to have some of its job taken over by the dedicated
`Pooly.PoolServer`.


![](../../images/7_6.png)  



Figure 7. 6 Logic from the top-level pool server from previous version will be moved into individual pool servers


Most of the APIs are the same from previous versions, which the addition of the
`pool_name`. Open up
`lib/pooly/server.ex`
and *replace* the previous implementation with this:


Listing 7.7 lib/pooly/server.ex – Full implementation of the top-level pool server

`defmodule Pooly.Server do`
`use GenServer`
`import Supervisor.Spec`

`#######`
`# API #`
`#######`

`def start_link(pools_config) do`
`GenServer.start_link(__MODULE__, pools_config, name: __MODULE__)`
`end`

`def checkout(pool_name) do`
`GenServer.call(:”#{pool_name}Server”, :checkout) #2`
`end`

`def checkin(pool_name, worker_pid) do`
`GenServer.cast(:”#{pool_name}Server”, {:checkin, worker_pid})              #2`
`end`

`def status(pool_name) do`
`GenServer.call(:”#{pool_name}Server”, :status)   #2`
`end`

`#############`
`# Callbacks #`
`#############`

`def init(pools_config) do                         #3`
`pools_config |> Enum.each(fn(pool_config) ->    #3`
`send(self, {:start_pool, pool_config})        #3`
`end)                                            #3`

`{:ok, pools_config}`
`end`

`def handle_info({:start_pool, pool_config}, state) do #4`
`{:ok, _pool_sup} = Supervisor.start_child(Pooly.PoolsSupervisor, supervisor_spec(pool_config))                           #4`
`{:no_reply, state}`
`end`

`#####################`
`# Private Functions #`
`#####################`

`defp supervisor_spec(pool_config) do`
`opts = [id: :”#{pool_config[:name]}Supervisor”]    #5`
`supervisor(Pooly.PoolSupervisor, [pool_config], opts)`
`end`
`end`
In this version,
`Pooly.Server`’s job is to *delegate* all the requests to the respective pools, and to start the pools and attach the pools to
`Pooly.PoolsSupervisor`.


In #2, we are assuming that each individual pool server is named


`:”#{pool_name}Server”`. Notice that the name is an *atom*! Sadly, I have lost hours (and hair) on this because I failed to read the documentation properly.


In #3 the
`pools_config`
is iterated and the
`{:start_pool, pool_config}`
message is sent itself. The handling of the message is performed in #4, where
`Pooly.PoolsSupervisor`
is told to start a child based on the given
`pool_config`.


There is one *tiny* caveat to look out for. Notice in #5 we make sure that each
`Pooly.PoolSupervisor`
is started with a *unique* supervisor specification id. If you forget to do this, you would get a cryptic error message such as:

`12:08:16.336 [error] GenServer Pooly.Server terminating`
`Last message: {:start_pool, [name: “Pool2”, mfa: {SampleWorker, :start_link, []}, size: 2]}`
`State: [[name: “Pool1”, mfa: {SampleWorker, :start_link, []}, size: 2], [name: “Pool2”, mfa: {SampleWorker, :start_link, []}, size: 2]]`
`** (exit) an exception was raised:`
`** (MatchError) no match of right hand side value: {:error, {:already_started, #PID<0.142.0>}}`
`(pooly) lib/pooly/server.ex:38: Pooly.Server.handle_info/2`
`(stdlib) gen_server.erl:593: :gen_server.try_dispatch/4`
`(stdlib) gen_server.erl:659: :gen_server.handle_msg/5``(stdlib) proc_lib.erl:237: :proc_lib.init_p_do_apply/3`
The clue here is
`{:error, {:already_started, #PID<0.142.0>}}`. I spent a couple of hours trying to figure this out before stumbling on this solution. What happens when a
`Pooly.PoolSupervisor`
is starts with a given
`pool_config`?


7.1.8        Adding the Pool Supervisor


![](../../images/7_7.png)  



Figure 7. 7 Implementing the individual pool supervisors


`Pooly.PoolSupervisor`
takes the place of
`Pooly.Supervisor`
of previous versions. As such, there are only a few minor changes. Firstly, each
`Pooly.PoolSupervisor`
is now initialized with a name. Secondly, we need to tell
`Pooly.PoolSupervisor`
to use
`Pooly.PoolServer`
instead. Here are the changes:


Listing 7.8 lib/pooly/pool\_supervisor.ex – Full implementation of individual pool supervisor

`defmodule Pooly.PoolSupervisor do`
`use Supervisor`

`def start_link(pool_config) do`
`Supervisor.start_link(__MODULE__, pool_config, name: :”#{pool_config[:name]}Supervisor”)                     #1`
`end`

`def init(pool_config) do`
`opts = [`
`strategy: :one_for_all`
`]`

`children = [`
`worker(Pooly.PoolServer, [self, pool_config])     #2`
`]`

`supervise(children, opts)`
`end`
`end`
We give individual pool supervisors a name in #1, although this is not strictly necessary. It helps up easily pinpoint the pool supervisors when viewing them in Observer.


Secondly, the child specification in #2 is changed from
`Pooly.Server`
to
`Pooly.PoolServer`. We are passing the same parameters. Even though we are naming
`Pooly.PoolSupervisor`, we will *not* be using the name in
`Pooly.PoolServer`, so that we can reuse much of the implementation from
`Pooly.Server`
from version 2.


7.1.9        Adding the Brains for the Pool


As noted in the previous section, much of the logic remains unchanged, except in places to support multiple pools. In the interest of saving trees and screen real-estate, functions that are exactly the same as
`Pooly.Server`
version 2 has their implementation stubbed out with “`# …`.” In other words, if you are following along, you can copy and paste the implementation of
`Pooly.Server`
version 2 to
`Pooly.PoolyServer`.


Here is implementation of
`Pooly.PoolServer`:


Listing 7.9 lib/pooly/pool\_server.ex – Full implementation of individual pool server

`defmodule Pooly.PoolServer do`
`use GenServer`
`import Supervisor.Spec`

`defmodule State do`
`defstruct pool_sup: nil, worker_sup: nil, monitors: nil, size: nil, workers: nil, name: nil, mfa: nil`
`end`

`def start_link(pool_sup, pool_config) do`
`GenServer.start_link(__MODULE__, [pool_sup, pool_config], name: name(pool_config[:name]))                               #1`
`end`

`def checkout(pool_name) do                                  #2`
`GenServer.call(name(pool_name), :checkout)                #2`
`end`

`def checkin(pool_name, worker_pid) do                       #2`
`GenServer.cast(name(pool_name), {:checkin, worker_pid})   #2`
`end`

`def status(pool_name) do                                    #2`
`GenServer.call(name(pool_name), :status)                  #2`
`end`

`#############`
`# Callbacks #`
`############j`

`def init([pool_sup, pool_config]) when is_pid(pool_sup) do`
`Process.flag(:trap_exit, true)`
`monitors = :ets.new(:monitors, [:private])`
`init(pool_config, %State{pool_sup: pool_sup, monitors:    monitors})         #3`
`end`

`def init([{:name, name}|rest], state) do`
`# …`
`end`

`def init([{:mfa, mfa}|rest], state) do`
`# …`
`end`

`def init([{:size, size}|rest], state) do`
`# …`
`end`

`def init([], state) do`
`send(self, :start_worker_supervisor)                    #4`
`{:ok, state}`
`end`

`def init([_|rest], state) do`
`# …`
`end`

`def handle_call(:checkout, {from_pid, _ref}, %{workers: workers, monitors: monitors} = state) do`
`# …`
`end`

`def handle_call(:status, _from, %{workers: workers, monitors: monitors} = state) do`
`# …`
`end`

`def handle_cast({:checkin, worker}, %{workers: workers, monitors: monitors} = state) do`
`# …`
`end`

`def handle_info(:start_worker_supervisor, state = %{pool_sup: pool_sup, name: name, mfa: mfa, size: size}) do`
`{:ok, worker_sup} = Supervisor.start_child(pool_sup, supervisor_spec(name, mfa))#5`
`workers = prepopulate(size, worker_sup)                 #6`
`{:no_reply, %{state | worker_sup: worker_sup, workers: workers}}`
`end`

`def handle_info({:DOWN, ref, _, _, _}, state = %{monitors: monitors, workers: workers}) do`
`# …`
`end`

`def handle_info({:EXIT, pid, _reason}, state = %{monitors: monitors, workers: workers, pool_sup: pool_sup}) do`
`case :ets.lookup(monitors, pid) do`
`[{pid, ref}] ->`
`true = Process.demonitor(ref)`
`true = :ets.delete(monitors, pid)`
`new_state = %{state | workers: [new_worker(pool_sup)|workers]}`
`{:no_reply, new_state}`

`_ ->`
`{:no_reply, state}`
`end`
`end`

`def terminate(_reason, _state) do`
`:ok`
`end`

`#####################`
`# Private Functions #`
`#####################`

`defp name(pool_name) do                                   #7`
`:”#{pool_name}Server”`
`end`

`defp prepopulate(size, sup) do`
`# …`
`end`

`defp prepopulate(size, _sup, workers) when size < 1 do`
`# …`
`end`

`defp prepopulate(size, sup, workers) do`
`# …`
`end`

`defp new_worker(sup) do`
`# …`
`end`

`defp supervisor_spec(name, mfa) do                         #8`
`opts = [id: name <> “WorkerSupervisor”, restart: :temporary]`
`supervisor(Pooly.WorkerSupervisor, [self, mfa], opts)    #9`
`end`
`end`
There are a few notable changes. The server’s
`start_link/2`
function takes in the *pool supervisor* as the first argument. In #3, the pid of the pool supervisor is saved in the state of the server process. Also, note that the state of the server has been extended to store the pid of the pool supervisor and worker supervisor:

`defmodule State do`
`defstruct pool_sup: nil, worker_sup: nil, monitors: nil, size: nil,`
`workers: nil, name: nil, mfa: nil``end`
Once the server is done processing the pool configuration, it will eventually send itself the
`:start_worker_supervisor`
message to itself, as seen in #4. This message is handled by the
`handle_info/2`
callback. In #5, the pool supervisor is told to start a worker supervisor as a child, using the child specification defined in #8. In addition to
`mfa`, we also pass in the pid of the server process. Once the pid of the worker supervisor is returned, it is used in #6 to pre-populate itself with workers. #2 makes use of
`name/1`
to reference the appropriate pool server to call the appropriate functions.


7.1.10     Adding the Worker Supervisor for the Pool


The last piece is the worker supervisor. It is tasked with managing the individual workers. It manages any crashing workers. There is a subtle detail. During initialization, the worker supervisor creates a *link* its corresponding pool server. Why bother? If either the pool server or worker supervisor goes down, there is no point in one or the other to continue to exist.


![](../../images/7_8.png)  



Figure 7. 8 Implementing the individual pools' worker supervisor


Let’s look at the full implementation for more details:


Listing 7.10 lib/pooly/worker\_supervisor.ex – Full implementation of the pool's worker supervisor

`defmodule Pooly.WorkerSupervisor do`
`use Supervisor`

`def start_link(pool_server, {_,_,_} = mfa) do           #1`
`Supervisor.start_link(__MODULE__, [pool_server, mfa]) #1`
`end`

`def init([pool_server, {m,f,a}]) do`
`Process.link(pool_server)                             #2`
`worker_opts = [restart:  :temporary,`
`shutdown: 5000,`
`function: f]`

`children = [worker(m, a, worker_opts)]`
`opts     = [strategy:     :simple_one_for_one,`
`max_restarts: 5,`
`max_seconds:  5]`

`supervise(children, opts)`
`end`
`end`
The only changes are the additional
`pool_server`
argument, and linking of
`pool_server`
to the worker supervisor process. Why? As previously mentioned, there is a dependency between both processes, and the pool server needs to be notified when the worker supervisor goes down. Similarly, should the worker supervisor crash, it should also take down the pool server.


In order for the pool server to handle the message, you need to add another
`handle_info/2`
callback in
`lib/pooly/pool_server.ex`:ð


Listing 7.11 lib/pooly/pool\_server.ex – Let the pool server detect if the worker supervisor goes down

`defmodule Pooly.PoolServer do`

`#############`
`# Callbacks #`
`#############`

`def handle_info({:EXIT, worker_sup, reason}, state = %{worker_sup: worker_sup}) do`
`{:stop, reason, state}`
`end`
`end`
Here, whenever the worker supervisor exits, it will terminate the pool server too, with the reason being the same reason that terminated the worker supervisor.


7.1.11     Taking it for a spin


Let’s make sure we wired everything up correctly. First, open up
`lib/pooly.ex`
to configure the pool. Make sure the
`start/2`
function looks like this:


Listing 7.12 lib/pooly.ex – Configuring Pooly to start three pools of various sizes

`defmodule Pooly do`
`use Application`

`def start(_type, _args) do`
`pools_config =`
`[`
`[name: “Pool1”, mfa: {SampleWorker, :start_link, []}, size: 2],`
`[name: “Pool2”, mfa: {SampleWorker, :start_link, []}, size: 3],`
`[name: “Pool3”, mfa: {SampleWorker, :start_link, []}, size: 4]`
`]`

`start_pools(pools_config)`
`end`

`# …``end`
Here, we are telling Pooly to create three pools, each with a given size and type of worker. For simplicity (laziness, really), we are using
`SampleWorker`
in all three pools. In a fresh terminal session, launch
`iex`
and start Observer:

`% iex -S mix`
`iex> :observer.start`
Bear witness to the glorious supervision tree you have created:


![](../../images/7_9.png)  



Figure 7. 9 The Pooly supervision tree as seen from Observer


Now, starting from the leaves (the lowest/rightmost) of the supervision tree, try right-clicking the process and killing it. You will again notice that a new process will take over.


Next, work your way higher. What happens when say,
`Pool3Server`
is killed? You will notice that the corresponding
`WorkerSupervisor`
and the workers underneath it will all be killed and the re-spawned. It is important to note that
`Pool3Server`
is a brand new process.


Go even higher now. What happens when you kill a
`PoolSupervisor`? As expected, everything underneath it gets killed, and another
`PoolSupervisor`
is re-spawned and everything underneath it re-spawns too. Notice what *doesn’t* happen. The rest of the application remains unaffected. Isn’t that wonderful? When crashes happen, as the inevitably will, having a nicely layered supervision hierarchy allows the error to be handled in a very isolated way, thereby not affecting the rest of the application.


7.2           Version 4: Implementing Overflowing and Queuing


In the final version of Pooly, we are going to extend it a little to support a variable number of workers by specifying a *maximum overflow*.


We also want to introduce the notion of *queuing* up workers. That is, when the maximum overflow limit has been reached, Pooly has the ability to queue up workers for consumers that are willing to *block and wait* for a next available worker.


7.2.1        Implementing Maximum Overflow


As usual, in order to specify the maximum overflow, we add a new field to the pool configuration. In
`lib/pooly.ex`, modify
`pools_config`
in
`start/2`
to look like:


Listing 7.13 lib/pooly.ex – Implementing maximum overflow

`defmodule Pooly do`

`def start(_type, _args) do`
`pools_config =`
`[`
`[name: “Pool1”,`
`mfa: {SampleWorker, :start_link, []},`
`size: 2,`
`max_overflow: 3                       #1`
`],`
`[name: “Pool2”,`
`mfa: {SampleWorker, :start_link, []},`
`size: 3,`
`max_overflow: 0                       #1`
`],`
`[name: “Pool3”,`
`mfa: {SampleWorker, :start_link, []},`
`size: 4,`
`max_overflow: 0                       #1`
`]`

`]`

`start_pools(pools_config)`
`end`
`end`
#1 Specifying the maximum overflow in the pools configuration.


Now that we have a new option for the pool configuration, we must now head over to
`lib/pooly/pool_server.ex`
to add support for
`max_overflow`. This includes:


·      Adding an entry called
`max_overflow`
in
`State`


·      Adding an entry called
`overflow`
in
`State`
to keep track of the current overflow count


·      Adding a function clause in
`init/2`
to handle
`max_overflow`


Here are the additions:


Listing 7.14 lib/pooly/pool\_server.ex – Adding a maximum overflow option in the pool server

`defmodule Pooly.PoolServer do`

`defmodule State do`
`defstruct pool_sup: nil, worker_sup: nil, monitors: nil, size: nil, workers: nil, name: nil, mfa: nil, overflow: nil, max_overflow: nil`
`end`

`#############`
`# Callbacks #`
`#############`

`def init([{:name, name}|rest], state) do`
`# …`
`end`

`# … more init/1 definitions`

`def init([{:max_overflow, max_overflow}|rest], state) do`
`init(rest, %{state | max_overflow: max_overflow})`
`end`

`def init([], state) do`
`#…`
`end`

`def init([_|rest], state) do`
`# …`
`end`
`end`
Next, we must consider the case of an actual overflow. An overflow is said to happen if the total number of busy workers exceeds
`size`
*and* is within the limits of
`max_overflow`. When can overflows happen? When a worker is checked *out*. Therefore, the only place to look for is
`handle_call({:checkout, block}, from, state)`.


Handling this case is quite simple. #1 checks if we are within the limits of overflowing. If so, a new worker is created and the necessary bookkeeping information is added into the
`monitors`
ETS table. A reply containing the worker pid is given to the consumer process along with an increment of the
`overflow`
count:


Listing 7.15 lib/pooly/pool\_server.ex – Handling overflows during checking out in the pool server

`defmodule Pooly.PoolServer do`

`#############`
`# Callbacks #`
`#############`

`def handle_call({:checkout, block}, {from_pid, _ref} = from, state) do`
`%{worker_sup:   worker_sup,`
`workers:      workers,`
`monitors:     monitors,`
`overflow:     overflow,`
`max_overflow: max_overflow} = state`

`case workers do`
`[worker|rest] ->`
`# …`
`{:reply, worker, %{state | workers: rest}}`

`[] when max_overflow > 0 and overflow < max_overflow -> #1`
`{worker, ref} = new_worker(worker_sup, from_pid)`
`true = :ets.insert(monitors, {worker, ref})`
`{:reply, worker, %{state | overflow: overflow+1}}`

`[] ->`
`{:reply, :full, state};`
`end`
`end`
`end`
7.2.2        Handling Worker Check-ins


Now that we can handle overflow, how then do we handle worker check-ins? How then do we handle *check-ins*? Previously in version 2, all we did was add the worker pid back into the
`workers`
field of the
`PoolServer`
state:

`{:no_reply, %{state | workers: [pid|workers]}}`
However, when handling a check-in of an *overflowed* worker, we do not want to add it back into the
`workers`
field. It is sufficient to just *dismiss* the worker. We will implement a helper function to handle check-ins:


Listing 7. 16 lib/pooly/pool\_server.ex – Handling worker overflows in the pool server

`defmodule Pooly.PoolServer do`

`#####################`
`# Private Functions #`
`#####################`

`def handle_checkin(pid, state) do`
`%{worker_sup:   worker_sup,`
`workers:      workers,`
`monitors:     monitors,`
`overflow:     overflow} = state`

`if overflow > 0 do`
`:ok = dismiss_worker(worker_sup, pid)`
`%{state | waiting: empty, overflow: overflow-1}`
`else`
`%{state | waiting: empty, workers: [pid|workers], overflow: 0}`
`end`
`end`

`defp dismiss_worker(sup, pid) do`
`true = Process.unlink(pid)`
`Supervisor.terminate_child(sup, pid)`
`end`
`end`
What
`handle_checkin/2`
does is check that the pool is indeed overflowed when a worker is being checked back in. If so, it delegates to
`dismiss_worker/2`
to terminate the worker, and decrement
`overflow`. Otherwise, the worker should be added back into
`workers`
as before.


The function for dismissing workers should not be too hard to understand. All we need to do is unlink the worker from the pool server, and tell the worker supervisor to terminate the child. Now, we can update
`handle_cast({:checkin, worker}, state)`:


Listing 7.17 lib/pooly/pool\_server.ex – Updating the check-in callback to use handle\_checkin/2

`defmodule Pooly.PoolServer do`

`#############`
`# Callbacks #`
`#############`

`def handle_cast({:checkin, worker}, %{monitors: monitors} = state) do`
`case :ets.lookup(monitors, worker) do`
`[{pid, ref}] ->`
`# …`
`new_state = handle_checkin(pid, state) #1`
`{:no_reply, new_state}`

`[] ->`
`{:no_reply, state}`
`end`
`end``end`
#1 Update this line to use handle\_checkin/2


7.2.3        Handling Worker Exits


What happens when an overflowed worker exits? Let’s turn to the callback function
`handle_info({:EXIT, pid, _reason}, state)`. Similar to the case when handling worker check-ins, we delegate the task of handling worker exits to a helper function:


Listing 7.18 lib/pooly/pool\_server.ex – A helper function to compute the state for worker exits

`defmodule Pooly.PoolServer do`

`#####################`
`# Private Functions #`
`#####################`

`defp handle_worker_exit(pid, state) do`
`%{worker_sup:   worker_sup,`
`workers:      workers,`
`monitors:     monitors,`
`overflow:     overflow} = state`

`if overflow > 0 do`
`%{state | overflow: overflow-1}`
`else`
`%{state | workers: [new_worker(worker_sup)|workers]}`
`end`
`end``end`
The logic is the reverse of
`handle_checkin/2`. We check if the pool is overflowed, and if so, decrement the counter. Since the pool is overflowed, we do not bother to add the worker back into the pool. On the other hand, if the pool is not overflowed, then we need to add a worker back into the worker list.


Listing 7.19 lib/pooly/pool\_server.ex – Updating the handle\_info callback to handle worker exits

`defmodule Pooly.PoolServer do`

`#############`
`# Callbacks #`
`#############`

`def handle_info({:EXIT, pid, _reason}, state = %{monitors: monitors, workers: workers, worker_sup: worker_sup}) do`
`case :ets.lookup(monitors, pid) do`
`[{pid, ref}] ->`
`# …`
`new_state = handle_worker_exit(pid, state) #1`
`{:no_reply, new_state}`

`_ ->`
`{:no_reply, state}`
`end`
`end`
`end`
#1 Update this line to use handle\_worker\_exit/2


7.2.4        Updating Status with Overflow Information


Let’s give
`Pooly`
the ability to report whether it is overflowed or not. The pool will have three states:
`:overflow`,
`:full`
and
`:ready`. Here’s the updated implementation of
`handle_call(:status, from, state)`:


Listing 7.20 lib/pooly/pool\_server.ex – Adding overflow information into the status

`defmodule Pooly.PoolServer do`

`#############`
`# Callbacks #`
`#############`

`def handle_call(:status, _from, %{workers: workers, monitors: monitors} = state) do`
`{:reply, {state_name(state), length(workers), :ets.info(monitors, :size)}, state}`
`end`

`#####################`
`# Private Functions #`
`#####################`

`defp state_name(%State{overflow: overflow, max_overflow: max_overflow, workers: workers}) when overflow < 1 do`
`case length(workers) == 0 do`
`true ->`
`if max_overflow < 1 do`
`:full`
`else`
`:overflow`
`end`
`false ->`
`:ready`
`end`
`end`

`defp state_name(%State{overflow: max_overflow, max_overflow: max_overflow}) do`
`:full`
`end`

`defp state_name(_state) do`
`:overflow`
`end`
`end`
7.2.5        Queuing Worker Processes


For the last bit of
`Pooly`, we are going to handle the case where consumers are willing to wait for a worker to be available. In other words, the consumer process is willing to block until the worker pool frees up a worker.


For this to work, we need to queue up worker processes, and match a newly freed worker process with a waiting consumer process.


A Blocking Consumer


A consumer must tell
`Pooly`
if it is willing to block. We can do this by simply extending the API for
`checkout`
in
`lib/pooly.ex`:

`defmodule Pooly do`
`@timeout 5000`

`#######`
`# API #`
`#######`

`def checkout(pool_name, block \\ true, timeout \\ @timeout) do`
`Pooly.Server.checkout(pool_name, block, timeout)`
`end`
`end`
In this new version of
`checkout`, we add two extra parameters,
`block`
and
`timeout`. Head over now to
`lib/pooly/server.ex`, where we will update the
`checkout`
function accordingly:

`defmodule Pooly.Server do`

`#######`
`# API #`
`#######`

`def checkout(pool_name, block, timeout) do`
`Pooly.PoolServer.checkout(pool_name, block, timeout)`
`end`
`end`
Now, to the real meat of the implementation,
`lib/pooly/pooly_server.ex`:


Listing 7.21 lib/pooly/pool\_server.ex – Setting up Pool Server to use queue for waiting consumers

`defmodule Pooly.PoolServer do`

`defmodule State do`
`defstruct pool_sup: nil, …, waiting: nil, …, max_overflow: nil #1`
`end`

`#############`
`# Callbacks #`
`############j`

`def init([pool_sup, pool_config]) when is_pid(pool_sup) do`
`Process.flag(:trap_exit, true)`
`monitors = :ets.new(:monitors, [:private])`
`waiting  = :queue.new                              #1`
`state    = %State{pool_sup: pool_sup, monitors: monitors, waiting: waiting, overflow: 0}                                  #1`

`init(pool_config, state)`
`end`

`#######`
`# API #`
`#######`

`def checkout(pool_name, block, timeout) do`
`GenServer.call(name(pool_name), {:checkout, block}, timeout) #2`
`end`
`end`
#1 Update the state to store the queue of waiting consumers


#2 Add block and timeout callback for checkout.


First, update the state with a
`waiting`
field. That will store the *queue* of consumers. While Elixir doesn’t come with a queue data structure, it doesn’t need to! Erlang comes with queue implementation. There’s a bigger lesson to this. Whenever you find something that may be missing in Elixir, instead of reaching for a third-party library[[1]](#uwSRyDKLGjMmgjcGYhoZfmG), try finding out if Erlang has the functionality you need. This highlights the wonderful interoperability between Erlang and Elixir.


7.2.6        Slight Detour: Queues in Erlang


The queue implementation that Erlang provides is very interesting. I will let the examples do the talking. We only look at the basics of using a queue, namely creating a queue, adding and removing items from a queue. In a fresh
`iex`
session, create a queue:

`iex(1)> q = :queue.new`
`{[], []}`
Notice that the return value is a tuple of two elements. Lists, to be more precise. Why two? To answer that question, add a couple of items into the queue:

`iex(2)> q = :queue.in(“uno”, q)`
`{[“uno”], []}`

`iex(3)> q = :queue.in(“dos”, q)`
`{[“dos”], [“uno”]}`

`iex(4)> q = :queue.in(“tres”, q)``{[“tres”, “dos”], [“uno”]}`
The first element (i.e. the head of the queue) is the *second* element of the tuple, while the remaining of the queue is represented by the *first* element. Now, try removing an element from the queue:

`iex(5)> :queue.out(q)`
`{{:value, “uno”}, {[“tres”], [“dos”]}}`
This is an interesting looking tuple. Let’s break it down a little.

`{{:value, “uno”}, …}`
This tagged tuple (with
`:value`) contains the value of the first element of the queue. Now for the other part:

`{…, {[“tres”], [“dos”]}}`
This tuple is the new queue, after the first element has been removed. The representation of the new queue is the same as the one we saw earlier, with the first element being the second element of the tuple, while the remaining part of the queue in the first element.


Yes, I know it’s slightly confusing, but hang in there. Arranging the result this way makes sense because remember, data structures are immutable in Elixir/Erlang land. Also, this is a perfect case for pattern matching:

`iex(6)> {{:value, head}, q} = :queue.out(q)`
`{{:value, “uno”}, {[“tres”], [“dos”]}}`

`iex(7)> {{:value, head}, q} = :queue.out(q)`
`{{:value, “dos”}, {[], [“tres”]}}`

`iex(8)> {{:value, head}, q} = :queue.out(q)``{{:value, “tres”}, {[], []}}`
What happens when we try to get something out of an empty queue?

`iex(9)> {{:value, head}, q} = :queue.out(q)`
`** (MatchError) no match of right hand side value: {:empty, {[], []}}`
Whoops! For an empty queue, the return value is a tuple that contains
`:empty`
as the first element. This concludes the brief detour on using the queue, and all that you need to understand the examples that follow.


7.2.7        Back to Queuing Worker Processes


Next, we add
`block`
and
`timeout`
to the invocation of the callback function. However, what’s that
`make_ref`
doing there in #2? In order to answer that question, we need to look at the updated implementation of the callback:


Listing 7.22 lib/pooly/pool\_server.ex – Handling waiting consumers

`defmodule Pooly.PoolServer do`

`#############`
`# Callbacks #`
`#############`

`def handle_call({:checkout, block}, {from_pid, _ref} = from, state) do`
`%{worker_sup:   worker_sup,`
`workers:      workers,`
`monitors:     monitors,`
`waiting:      waiting,`
`overflow:     overflow,`
`max_overflow: max_overflow} = state # 1`

`case workers do`
`[worker|rest] ->`
`# …`

`[] when max_overflow > 0 and overflow < max_overflow ->`
`# …`

`[] when block == true ->                                #2`
`ref = Process.monitor(from_pid)`
`waiting = :queue.in({from, ref}, waiting)             #2`
`{:noreply, %{state | waiting: waiting}, :infinity}`

`[] ->`
`{:reply, :full, state};`
`end`
`end`
`end`
#1 Update state with waiting


#2 Add waiting consumer into the queue.


There are two things we’ve added:


·     
`waiting`
to the state


·      Handling the case when consumer is willing to block


Let’s deal with the case when we are overflowed, and there is a request for a worker where the consumer is willing to wait. This case is covered in #3.


Handling a Consumer that is Willing to Block


When a consumer is willing to block, we will first monitor it. That’s because if it crashes for some reason, we must know about it, and remove it from the queue.


Next, we add to the
`waiting`
queue a tuple of the form
`{from, ref}`.
`from`
is the same
`from`
of the callback. Note that
`from`
is in fact a *tuple*, containing a tuple of the consumer pid and a tag, itself a reference.


Finally, note that the reply is in fact a
`:noreply`, with
`:infinity`
as the timeout. Returning
`:noreply`
means that
`GenServer.reply(from_pid, message)`
must be called from *somewhere* else. Since we do not know how long we must wait, we pass in
`:infinity`.


*Where* do we need to call
`GenServer.reply/2`? In other words, when we need to reply the consumer process? During a check-in of a worker! Time to update
`handle_checkin/2`. This time, we will use the
`waiting`
queue and pattern matching:


Listing 7.23 lib/pooly/pool\_server.ex – Handling a consumer check in that is willing to block

`defmodule Pooly.PoolServer do`

`#####################`
`# Private Functions #`
`#####################`

`def handle_checkin(pid, state) do`
`%{worker_sup:   worker_sup,`
`workers:      workers,`
`monitors:     monitors,`
`waiting:      waiting,`
`overflow:     overflow} = state`

`case :queue.out(waiting) do`
`{{:value, {from, ref}}, left} ->`
`true = :ets.insert(monitors, {pid, ref})`
`GenServer.reply(from, pid)                   #1`
`%{state | waiting: left}`

`{:empty, empty} when overflow > 0 ->`
`:ok = dismiss_worker(worker_sup, pid)`
`%{state | waiting: empty, overflow: overflow-1}`

`{:empty, empty} ->`
`%{state | waiting: empty, workers: [pid|workers], overflow: 0}`
`end`
`end``end`
#1 Replying to the consumer process when a worker is available


Depending on the output of the queue, we have three cases that we have to handle. The first case is when the queue is not empty. This means that we have at least one consumer process waiting for a worker. We insert a three-element tuple into the
`monitors`
ETS table. Now, we can finally tell the consumer process that we have an available worker by doing
`GenServer.reply/2`.


The second case is when there are no consumers currently waiting, and yet we are in an overflow state. This means that we just have to decrement the
`overflow`
count by 1.


The last case to handle is when there are no consumers currently waiting, and we are *not* in an overflow state. For this, we can just add back the worker back into the
`workers`
field.


Getting a Worker from Worker Exits


There is another way that a waiting consumer can get a worker, and that is if some other worker process exits. The modification is simple. Head to
`handle_worker_exit/2`
and modify
`handle_worker_exit/2`:


Listing 7.24 lib/pooly/pool\_server.ex – Handling worker exits

`defmodule Pooly.PoolServer do`

`#####################`
`# Private Functions #`
`#####################`

`defp handle_worker_exit(pid, state) do`
`%{worker_sup:   worker_sup,`
`workers:      workers,`
`monitors:     monitors,`
`waiting:      waiting,`
`overflow:     overflow} = state`

`case :queue.out(waiting) do`
`{{:value, {from, ref}}, left} ->`
`new_worker = new_worker(worker_sup)`
`true = :ets.insert(monitors, {new_worker, ref})`
`GenServer.reply(from, new_worker)`
`%{state | waiting: left}`

`{:empty, empty} when overflow > 0 ->`
`%{state | overflow: overflow-1, waiting: empty}`

`{:empty, empty} ->`
`workers = [new_worker(worker_sup) | workers]`
`%{state | workers: workers, waiting: empty}`
`end`
`end``end`
Similar to
`handle_checkin/2`, we use pattern matching from the result of
`:queue.out/1`. The first case is when we have a waiting consumer process. Since a worker has crashed or exited, we simply create a new one, and hand it to the consumer process. The rest of the cases are pretty self-explanatory.


7.2.8        Taking it for a spin


Now to see reap the fruits of our labor. Configure the pool like so:

`defmodule Pooly do`

`def start(_type, _args) do`
`pools_config =`
`[`
`[name: “Pool1”,`
`mfa: {SampleWorker, :start_link, []},`
`size: 2,`
`max_overflow: 1`
`],`
`[name: “Pool2”,`
`mfa: {SampleWorker, :start_link, []},`
`size: 3,`
`max_overflow: 0`
`],`
`[name: “Pool3”,`
`mfa: {SampleWorker, :start_link, []},`
`size: 4,`
`max_overflow: 0`
`]`
`]`

`start_pools(pools_config)`
`end``end`
Here, only Pool 1 has overflow configured. Open a new
`iex`
session:

`% iex –S mix`
`iex(1)> w1 = Pooly.checkout(“Pool1”)`
`#PID<0.97.0>`

`iex(2)> w2 = Pooly.checkout(“Pool1”)`
`#PID<0.96.0>`

`iex(3)> w3 = Pooly.checkout(“Pool1”)``#PID<0.111.0>`
With max overflow set to 1, the pool can handle one extra worker. What happens when you try to check out another worker? The client will be blocked indefinitely or timeout, depending on how you try to check out the worker. For example, doing this will block indefinitely:

`iex(4)> Pooly.checkout(“Pool1”, true, :infinity)`
On the other hand, doing this will time out after five seconds:

`iex(4)> Pooly.checkout(“Pool1”, true, 5000)`
If you are following along the example, you will realize that the session is blocked. Before we continue, open up
`lib/pooly/sample_worker.ex`. Add the
`work_for/2`
function and its corresponding callback:


Listing 7.25 lib/pooly/sample\_worker.ex – Enable SampleWorker to simulate processing for a given period of time

`defmodule SampleWorker do`
`use GenServer`

`# …`

`def work_for(pid, duration) do`
`GenServer.cast(pid, {:work_for, duration})`
`end`

`def handle_cast({:work_for, duration}, state) do`
`:timer.sleep(duration)`
`{:stop, :normal, state}`
`end`
`end`
This function tells the worker to sleep for some time then exits normally. This is to simulate a short-lived worker. Restart the session as per the above steps. In other words, check out three workers:

`iex(1)> w1 = Pooly.checkout(“Pool1”)`
`#PID<0.97.0>`

`iex(2)> w2 = Pooly.checkout(“Pool1”)`
`#PID<0.96.0>`

`iex(3)> w3 = Pooly.checkout(“Pool1”)``#PID<0.111.0>`
This time, we tell the first worker to work for ten seconds.

`iex(4)> SampleWorker.work_for(w1, 10_000)`
`:ok`
Now try to checkout a worker. Since we have exceeded the maximum overflow, the pool will cause the client to block.

`iex(5)> Pooly.checkout(“Pool1”, true, :infinity)`
Ten seconds later, the console prints out a pid:

`#PID<0.114.0>`
Success! Even though we were in an overflowed state, once the first worker has completed it job, another slot became available and was handled over to the waiting client.


7.3           Exercises


1.   *Restart Strategies.* Play around with the different restart strategies. For example, pick one supervisor and its restart strategy to something different. Launch
`:observer.start`
and see what happens. Did the supervisor restart the child/children processes as you expected?


2.   *Transactions*. There’s a limitation with this implementation. It is assumed that all consumers behave like good citizens of the pool and check back in the workers when they are done with it. In general, the pool shouldn’t make assumptions like this, since it is way too easy to cause a starvation of workers. In order to get around this, Poolboy has *transactions*. Here’s the skeleton:

`defmodule Pooly.Server do`

`def transaction(pool_name, fun, timeout) do`
`worker = <FILL ME IN>`
`try do`
`<FILL ME IN>`
`after`
`<FILL ME IN>`
`end`
`end`
`end`
3.   Currently, it is possible to check-in the same worker *multiple* times. Fix this!


7.4           Summary


Believe it or not, we are done with
`Pooly`! If you have made it this far, you deserve a nice meal. Not only that, you have re-implemented 96.777% of Poolboy, but in Elixir. This is probably the most complicated and largest example in this chapter. But I’m pretty sure after working through this example you would have gained a deeper appreciation of not only supervisors, but also how they interact with other processes and how supervisors can be structured in a layered way to provide fault tolerance.


If you struggled with Chapter 6 and 7, don’t worry[[2]](#uDaQkkzKLpF45pTTXpKN5X8), there’s nothing wrong with you. I struggled with grasping this too. There were a lot of moving parts in
`Pooly`. However if you step back and look at the code again, it’s pretty amazing how everything fits so well together. In this chapter, we:


·      Understand how to use the OTP Supervisor behavior


·      Build multiple supervision hierarchies


·      Dynamically create supervisors and workers using the OTP Supervisor API


·      Took a grand tour of building a non-trivial application using a mixture of Supervisors and GenServers.


In the next chapter, we look at an equally exciting topic, distribution!





[****[1]****](#uTtuo3MaRXcuCm9c6Xiu2jC) Or even worse, building one yourself (unless it’s for educational purposes)!




[****[2]****](#uZv3OqK4r8HhoLncUO8eZeD) If you didn’t, I don’t want to hear about it.





