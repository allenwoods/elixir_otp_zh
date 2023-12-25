# 5   Concurrent Error Handling and Fault Tolerance with Links, Monitors, and Processes


This chapter covers:


·      Handling Errors, à la Elixir style


·      Links, Monitors and Trapping Exits


·      Implementing a Supervisor


Ever watched *The Terminator* played by Arnold Schwarzenegger about the assassin cyborg from the future? Whenever the terminator receives multiple shots, it just keeps coming back unfazed, over and over again. Once you are acquainted with the fault tolerance features by the end of this chapter, you can build programs that are able to handle errors gracefully and take corrective actions to fix the problem. You would not be able to build Skynet though, at least not yet.


In sequential programs, there is usually only one main process doing all the hard work. What happens if this process crashes? Usually, this means that the entire program has crashed. The usual approach would be to program *defensively*. This usually means lacing the program with
`try’`s,
`catch’`s and
`if err != nil`s.


The story is different when it comes to building concurrent programs. Since there is more than one process running, it is possible for *another* process to *detect the crash* and subsequently *handle the error*. Let that sink it for a while, because that is a very liberating notion.


You might have heard or read about the unofficial Erlang motto – “Let it crash” – that Erlang programmers are so fond of saying. That’s because that’s the way of doing things in the Erlang VM. As it turns out, there are several good reasons too, as we will soon learn. This unique way of handling errors can cause programmers who are used to defensive programming to twitch involuntarily.


In this section, we will first learn about *links*, *monitors*, *trapping* *exits* and *processes*, and how they come together to be the fundamental building blocks in building fault-tolerant systems. We then embark on building a simplistic version of a supervisor, whose only job is to manager worker processes. This will be a perfect segue to the next chapter, where we can then fully appreciate the convenience and additional features that the OTP Supervisor behavior provide.


5.1           Links – Till Death Do Us Part


When a process links to another, it creates a bi-directional relationship. A linked process has a *link set*, which contains a set of all the processes it is linked to. If either process terminates for whatever reason, an *exit signal* is propagated to all the processes it is linked to. Furthermore, if any of these processes is linked to a different set of processes, then the *same* exit signal is propagated along too.


![](../images//5_1.png)  



Figure 5.1    When a process dies, all other processes linked to it will die too (assuming they are not trapping exits).


If you are scratching your head now and wonder why is this a good thing, consider the following example where a bunch of processes working on a map-reduce job. If any of these processes crashes and dies, it does not make sense for the rest of the processes to keep on working. In fact, having the processes linked would ease the clean up of the remaining processes, since a failure in one of the processes automatically brings down the rest of the linked processes.


5.1.1        Linking Processes Together


To make sense of this, an example is in order. A link is created using
`Process.link/1`, the sole argument being the process id of the process to *link to*. This means that
`Process.link/1`
must be called from within an existing process.


Process.link/1 and Process.monitor/1 are called from within the context of a process


Note that
`Process.link/1`
must be called from an existing process, since there is no such thing as
`Process.link(link\_from, link\_to)`. The same applies for
`Process.monitor/1.`


Open up an
`iex`
session. We are going to create a process that is linked to the
`iex`
shell process. Since we are in the context of the shell process, whenever we invoke
`Process.link/1`, we are linking the shell process to whatever process we point it.


The process that we are going to create will crash when we send it a
`:crash`
message. Observe what happens when it does. First, let’s make a note of the pid of the current shell process:

`iex> self`
`#PID<0.119.0>`
We can inspect the current link set of the shell process:

`iex> Process.info(self, :links)`
`{:links, []}`
`Process.info/1`
contains a bunch of other useful information about a process. We are using
`Process.info(self, :links)`
since we are only interested in the link set for now. Other interesting information includes total number of messages in the mailbox, heap size and the arguments that the process was spawned with.


As expected, it is empty since we have not linked any processes yet. Next, let’s make a process that only responds to a
`:crash`
message:

`iex> pid = spawn(fn -> receive do :crash -> 1/0 end end)`
`#PID<0.133.0>`
Now, we shall link the shell process to the process we have just created:

`iex> Process.link(pid)`
`<0.133.0>`
is now in
`self`'s link set:

`iex> Process.info(self, :links)`
`{:links, [#PID<0.133.0>]}`
Conversely,
`self`
`(<0.119.0>`) is also in
`<0.133.0>`'s link set:

`iex> Process.info(pid, :links)`
`{:links, [#PID<0.119.0>]}`
It should now be clear that calling
`Process.link/1`
from within the shell process creates a bi-directional link between the shell process and process we just spawned.


Now, the moment we have all been waiting for – Let's crash the process and see what happens:

`iex> send(pid, :crash)`

`11:39:40.961 [error] Error in process <0.133.0> with exit value: {badarith,[{erlang,'/',[1,0],[]}]}`
 
`** (EXIT from #PID<0.119.0>) an exception was raised:`
`** (ArithmeticError) bad argument in arithmetic expression``:erlang./(1, 0)`
The error is telling us that we perform some shoddy math calculation in
`<0.133.0>`
that caused the
`ArithmeticError`. In addition, notice that *same* error has also brought down the shell process,
`<0.119.0>`. To convince ourselves that the previous shell process is really gone:

`iex> self`
`#PID<0.145.0>`
The pid of
`self`
is no longer
`<0.119.0>`.


5.1.2        Chain Reaction of Exit Signals


In the previous example, we set up a link between two processes.  In this example, we will create a ring of linked processes so that you can see for yourself the error being propagated and re-propagated to all the links. In a terminal, create a new project:

`% mix new ring`
Open up
`lib/ring.ex`, and add the following:


Listing 5.1    ring.ex – Create a ring of processes that are linked together

`defmodule Ring do`

`def create_processes(n) do`
`1..n |> Enum.map(fn _ -> spawn(fn -> loop end) end)`
`end`

`def loop do`
`receive do`
`{:link, link_to} when is_pid(link_to) ->`
`Process.link(link_to)`
`loop`

`:crash ->`
`1/0`
`end`
`end`
`end`
The above should be pretty straightforward.
`Ring.create_processes/1`
creates
`n`
processes that each run the
`loop`
function defined before. The return value of
`Ring.create_processes/1`
is a list of spawned pids.


The loop function defines two types of messages that the process can receive. These are:


·     
`{:link, link_to}`
– to link to a process specified by
`link_to`.


·     
`:crash`
– to purposely crash the process


5.1.3        Setting up the Ring


Setting up a ring of links is more interesting. In particular, pay attention to how we make use of pattern matching and recursion to set up the ring:


Listing 5.2    ring.ex – Setting up the ring of links using recursion

`defmodule Ring do`

`# ...`

`def link_processes(procs) do`
`link_processes(procs, [])`
`end`

`def link_processes([proc_1, proc_2|rest], linked_processes) do`
`send(proc_1, {:link, proc_2})`
`link_processes([proc_2|rest], [proc_1|linked_processes])`
`end`

`def link_processes([proc|[]], linked_processes) do`
`first_process = linked_processes |> List.last`
`send(proc, {:link, first_process})`
`:ok`
`end`

`# ...`
`end`
The first function clause,
`link_processes/1`, is the entry point to
`link_processes/2`. The
`link_processes/2`
function initializes the second argument to the empty list. The first argument of
`link_processes/2`
is a list of processes (initially unlinked):


Listing 5.3    ring.ex – Linking the first two processes using pattern matching

`def link_processes([proc_1, proc_2|rest], linked_processes) do`
`send(proc_1, {:link, proc_2})`
`link_processes([proc_2|rest], [proc_1|linked_processes])``end`
We can use pattern matching to get the first two processes in the list. We then tell the first process to link to the second process by sending it a
`{:link, link_to}`
message.


Next,
`link_processes/2`
is recursively called. This time, the input processes *do not* include the first process. Instead, it is add to the second argument, signifying that this process has been sent the
`{:link, link_to}`
message.


Soon enough, there will only be one process left in the input process list. It shouldn’t be hard to see why. That's because each time we recursively call
`link_processes/2`, the size of the input list decreases by one. We can detect this condition by pattern matching
`[proc|[]]`:


Listing 5.4    ring.ex – The terminating condition when there is only one process left

`def link_processes([proc|[]], linked_processes) do`
`first_process = linked_processes |> List.last`
`send(proc, {:link, first_process})`
`:ok``end`
Finally, in order to complete the ring, we need to link
`proc`
to the first process. Because processes are added to the
`linked_processes`
list in a LIFO (last in, first out) order, this means that the first process is the last element. Once we have created the link from the last process to the first, we have completed the ring. Let’s take this for a spin, shall we:

`% iex -S mix`
Let’s create five processes:

`iex(1)> pids = Ring.create_processes(5)`
`[#PID<0.84.0>, #PID<0.85.0>, #PID<0.86.0>, #PID<0.87.0>, #PID<0.88.0>]`
Next, we link all of them up:

`iex(2)> Ring.link_processes(pids)`
`:ok`
What is the link set of each of these processes? Let’s find out:

`iex> pids |> Enum.map(fn pid -> “#{inspect pid}: #{inspect Process.info(pid, :links)}” end)`
This gives us:

`[“#PID<0.84.0>: {:links, [#PID<0.85.0>, #PID<0.88.0>]}”,`
`“#PID<0.85.0>: {:links, [#PID<0.84.0>, #PID<0.86.0>]}”,`
`“#PID<0.86.0>: {:links, [#PID<0.85.0>, #PID<0.87.0>]}”,`
`“#PID<0.87.0>: {:links, [#PID<0.86.0>, #PID<0.88.0>]}”,``“#PID<0.88.0>: {:links, [#PID<0.87.0>, #PID<0.84.0>]}”]`
![](../images//5_2.png)  



Figure 5.2    A ring of linked processes. Notice that each process has two other processes in its link set.


Let’s crash a random process! We pick a random pid from the list of
`pids`
and send it the
`:crash`
message:

`iex(6)> pids |> Enum.shuffle |> List.first |> send(:crash)`
`:crash`
We can now check that none of the processes survived:

`iex(8)> pids |> Enum.map(fn pid -> Process.alive?(pid) end)`
`[false, false, false, false, false]`
5.1.4        Trapping Exits


So far, all we have done is see the links bring down all the linked processes. What if we didn’t want the process to die when it received an error signal? We need to make the process *trap exit signals*. To make a process trap exit signals, it needs to call
`Process.flag(:trap_exit, true)`. Calling this turns the process from a normal process to a system process.


What’s the difference between a normal process and a system process? When a system process receives an error signal, instead of crashing like normal processes, it can turn the signal into a regular message that looks like
`{:EXIT, pid, reason}`, where
`pid`
is the process that was terminated and
`reason`
is the reason for the termination.


This way, the system process can take corrective action on the terminated process. Let’s see how this works with two processes, similar to the first example in this section.


We first note the current shell process:

`iex> self`
`#PID<0.58.0>`
Next, turn the shell process into a system process by making it trap exits:

`iex> Process.flag(:trap_exit, true)`
`false`
Note that just like
`Process.link/1`, this must be called from within the calling process. Once again, we create a process that we are going to crash:

`iex> pid = spawn(fn -> receive do :crash -> 1/0 end end)`
`#PID<0.62.0>`
Then link the newly created process to the shell process:

`iex> Process.link(pid)`
`true`
Now, what happens if we try to crash the newly created process?

`iex> send(pid, :crash)`
`:crash``14:37:10.995 [error] Error in process <0.62.0> with exit value: {badarith,[{erlang,’/‘,[1,0],[]}]}`
First, let’s check if the shell process survived:

`iex> self`
`#PID<0.58.0>`
Yup! It’s the same process as before. Now, let’s see what message the shell process receive:

`iex> flush`
`{:EXIT, #PID<0.62.0>, {:badarith, [{:erlang, :/, [1, 0], []}]}}`
As expected, because the shell process receives a message in the form of
`{:EXIT, pid, reason}`. We will exploit this later when we learn how to create our own supervisor process.


5.1.5        Linking a terminated/non-existent process


Let’s try to link a dead process see what happens. First, let’s create a process that exits quickly:

`iex> pid = spawn(fn -> IO.puts “Bye, cruel world.” end)`
`Bye, cruel world.`
`#PID<0.80.0>`
We make sure that the process is really dead:

`iex> Process.alive? pid`
`false`
Then we’ll attempt to link a dead process:

`iex> Process.link(pid)`
`** (ErlangError) erlang error: :noproc``:erlang.link(#PID<0.62.0>)`
`Process.link/1`
makes sure that you are linking to a non-terminated process, and errors out if you try to link to a terminated or non-existent process.


5.1.6        spawn\_link/3: spawn and link in One Atomic Step


Most of the time when spawning a process, you would want to use
`spawn_link/3`. Is
`spawn_link/3`
like a glorified wrapper for
`spawn/3`
and
`link/1`? In order words, is
`spawn_link(Worker, :loop, [])`
the same as doing

`pid = spawn(Worker, :loop, [])`
`Process.link(pid)`
Turns out, the story is slightly more complicated than that.
`spawn_link/3`
does the spawning and linking in *one atomic operation*. Why is this important? This is because when
`link/1`
is given a process that has terminated or does not exist, it throws an error. Since
`spawn/3`
and
`link/1`
are two separate steps,
`spawn/3`
could very well fail, causing the subsequent call to
`link/1`
to raise an exception.


5.1.7        Exit Messages


There are three flavors of :`EXIT`
messages. You have seen the first one where the reason for termination is returned describes the exception.


Normal Termination


Processes send :`EXIT`
messages when the process terminates normally. This means that the process doesn’t have any more code to run. For example, given this process whose only job is to receive an
`:ok`
message then exit:

`iex> pid = spawn(fn -> receive do :ok -> :ok end end)`
`#PID<0.73.0>`
Remember to link the process:

`iex> Process.link(pid)`
`true`
We then send the process the
`:ok`
message, causing it to exit normally:

`iex> send(pid, :ok)`
`:ok`
Now, let’s reveal the message that the shell process received:

`iex> flush`
`{:EXIT, #PID<0.73.0>, :normal}`
Note that for *normal* process that is linked to a process that has just exited normally (i.e. with a
`:normal`
as the reason), then the former process is *not* terminated.


Forcefully Killing a Process


There is one more way a process can die, and that is using
`Process.exit(pid, :kill)`. This sends an *un-trappable* exit signal is sent to the targeted process. This means that even though the process might be trapping exits, this is one signal that it cannot trap.  Let’s set up the shell process to trap exits:

`iex> self`
`#PID<0.91.0>`

`iex> Process.flag(:trap_exit, true)``false`
When we try to kill it using
`Process.exit/2`
with a reason other than
`:kill`:

`iex> Process.exit(self, :whoops)`
`true`

`iex> self`
`#PID<0.91.0>`

`iex> flush`
`{:EXIT, #PID<0.91.0>, :whoops}`

`iex> self``#PID<0.91.0>`
Here, we have shown that the shell process has successfully trapped the signal since it receives the
`{:EXIT, pid, reason}`
message in its mailbox. Now, lets try
`Process.exit(self, :kill)`:

`iex> Process.exit(self, :kill)`
`** (EXIT from #PID<0.91.0>) killed`

`iex> self``#PID<0.103.0>`
This time, notice that the shell process restarts and the process id is no longer the one we had before.


5.1.8        Ring, revisited


Consider the ring again. Only two processes are trapping exits. This is what we want to create:


![](../images//5_3.png)  



Figure 5.3 What happens when process 2 is killed?


Open up
`lib/ring.ex`
again, and add messages let the process trap exit and handle
`{:EXIT, pid, reason}`:


Listing 5.5    ring.ex – Let the process handle :EXIT and :DOWN messages

`defmodule Ring do`
`# …`

`def loop do`
`receive do`
`{:link, link_to} when is_pid(link_to) ->`
`Process.link(link_to)`
`loop`

`:trap_exit ->`
`Process.flag(:trap_exit, true)                #1`
`loop`

`:crash ->`
`1/0`

`{:EXIT, pid, reason} ->                         #2`
`IO.puts “#{inspect self} received {:EXIT, #{inspect pid}, #{reason}}”`
`loop`

`end`
`end`
`end`
#1 Handle a message to trap exits  


#2 Handle a message to detect :DOWN messages


Process 1 and Process 2 are trapping exits. All Processes are linked to each other. Now, what happens when 2 is killed? We can create three processes to find out:

`iex> [p1, p2, p3]  = Ring.create_processes(3)`
`[#PID<0.97.0>, #PID<0.98.0>, #PID<0.99.0>]`
And link all of them together:

`iex> [p1, p2, p3] |> Ring.link_processes`
We set the first two processes to trap exits.

`iex> send(p1, :trap_exit)`
`iex> send(p2, :trap_exit)`
Observer what happens when we kill
`p2`:

`iex> Process.exit(p2, :kill)`
`#PID<0.97.0> received {:EXIT, #PID<0.98.0>, killed}``#PID<0.97.0> received {:EXIT, #PID<0.99.0>, killed}`
As a final check, only
`p1`
survives:

`iex> [p1, p2, p3] |> Enum.map(fn p -> Process.alive?(p) end)`
`[true, false, false]`
Here’s the lesson:


If a process is trapping exits, and it is targeted to be killed using
`Process.exit(pid, :kill)`, it is going to get killed anyway. When it dies, it propagates a
`{:EXIT, #PID<0.98.0>, :killed}`
message to the processes in its link set, which *can* be trapped.


Here’s a table to summarize all the different scenarios:


Table 5. 1    The different scenarios that can happen when a process in a link set exits




|  |  |  |
| --- | --- | --- |
| 
When a process in its link set …
 | 
Trapping exits?
 | 
What happens then?
 |
| Exits normally | Yes | Receives
`{:EXIT, pid, :normal}`
|
|   | No | Nothing |
| Killed using
`Process.exit(pid, :kill)`
| Yes | Receives
`{:EXIT, pid, :normal}`
|
|   | No | Terminates with
``:killed``
|
| Killed using
`Process.exit(pid, other)`
| Yes | Receives
`{:EXIT, pid, other }`
|
|   | No | Terminates with
`other`
|


5.2           Monitors


Sometimes, you don’t need a bidirectional link. You just want the process to know if some other process has gone down, and not affect anything about the monitoring process. For example, in a client-server architecture, if the client goes down for whatever reason, the server shouldn’t go down.


That’s what *monitors* are for. They set up a uni-directional link between the monitoring process and the process to be monitored. Let’s do some monitoring! We create our favorite crash-able process:

`iex> pid = spawn(fn -> receive do :crash -> 1/0 end end)`
`#PID<0.60.0>`
Then, we tell the shell to monitor this process:

`iex> Process.monitor(pid)`
`#Reference<0.0.0.80>`
Notice that the return value is a *reference* to the monitor.


A reference is unique, and can be used to identify where the message comes from, although that’s a topic for a chapter later on.


Now, crash the process and see what happens:

`iex> send(pid, :crash)`
`:crash`

`iex>`
`18:55:20.381 [error] Error in process <0.60.0> with exit value: {badarith,[{erlang,’/‘,[1,0],[]}]}``nil`
Let’s inspect the shell processes’ mailbox:

`iex> flush`
`{:DOWN, #Reference<0.0.0.80>, :process, #PID<0.60.0>,``{:badarith, [{:erlang, :/, [1, 0], []}]}}`
Notice that the reference matches the reference returned from
`Process.monitor/1`.


5.2.1        Monitoring a Terminated/Non-Existent Process


What happens when you try to monitor a terminated/non-existent process? Continue from our previous example, we first convince ourselves that
`pid`
is indeed dead:

`iex> Process.alive?(pid)`
`false`
Then let’s try monitoring again:

`iex(11)> Process.monitor(pid)`
`#Reference<0.0.0.114>`
`Process.monitor/1`
processes without incident, unlike
`Process.link/1`, which throws an
`:noproc`
error. What message does the shell process get?

`iex(12)> flush`
`{:DOWN, #Reference<0.0.0.114>, :process, #PID<0.60.0>, :noproc}`
We get a similar looking
`:noproc`
message, except that it is not an error but a plain old message lying in the mailbox. Therefore, this message can be pattern matched from the mailbox.


5.3           Implementing a Supervisor


A supervisor is a process whose only job is to monitor one or more processes. These processes can be worker processes or even other supervisors.


![](../images//5_4.png)  



Figure 5.4    A supervision tree can be layered with other supervision trees. Both supervisors and workers can be supervised.


Supervisors and workers are arranged in a supervision tree. If any of the workers die, the supervisor can restart the dead worker, and potentially other workers in the supervision tree, based on certain *restart strategies*. What are worker processes? They are usually processes that have implemented the GenServer, GenFSM or GenEvent behaviors.


So far, you have all the building blocks needed to build your own Supervisor. Once you are done with this section, Supervisors will not seem magical anymore, although that does not make them any less awesome.


5.3.1        Supervisor API


The follow table lists the API of the supervisor along with a brief description:


Table 5.2    A summary of APIs that we will implement




|  |  |
| --- | --- |
| 
API
 | 
Description
 |
|
`start_link(child_spec_list)`
| Given a list of child specifications (possibly empty), start the supervisor process and corresponding children |
|
`start_child(supervisor, child_spec)`
| Given a supervisor pid and a child specification, start the child process and link it to the supervisor. |
|
`terminate_child(supervisor, pid)`
| Given a supervisor pid and a child pid, terminate the child. |
|
`restart_child(supervisor, pid, child_spec)`
| Given a supervisor pid, child pid, and a child specification, restart the child process and initialize the child process with the child specification. |
|
`count_children(supervisor)`
| Given the supervisor pid, return the number of child processes. |
|
`which_children(supervisor)`
| Given the supervisor pid, return the state of the supervisor. |


Implementing the above API will give us a pretty good grasp of how the actual OTP Supervisor works under the hood.


5.3.2        Building Our Own Supervisor


As usual, we start with a new
`mix`
project. Since calling it
`Supervisor`
is unoriginal, and
`MySupervisor`
is boring, let’s give it some Old English flair and call it
`ThySupervisor`
instead:

`% mix new thy_supervisor`
As a form of revision, we are going to build our supervisor using the GenServer behavior. You might be surprised to know that the supervisor behavior does, in fact, implement the GenServer behavior.

`defmodule ThySupervisor do`
`use GenServer`
`end`
5.3.3        start\_link(child\_spec\_list)


The first thing is to implement
`start_link/1`.

`defmodule ThySupervisor do`
`use GenServer`

`def start_link(child_spec_list) do`
`GenServer.start_link(__MODULE__, [child_spec_list])`
`end`
`end`
This is the main entry point to creating a supervisor process. Here, we call
`GenServer.start_link/2`
with the name of the module and passing in a list with a single element of
`child_spec_list`.
`child_spec_list`
specifies a list of (potentially empty) *child specifications*.


This is a fancy way of telling the supervisor what *kinds* of processes it should manage. A child specification for two (similar) workers could look like
`[{ThyWorker, :start_link, []}, {ThyWorker, :start_link, []}]`.


Recall that
`GenServer.start_link/2`
expects the
`ThySupervisor.init/1`
callback to be implemented. It passes the second argument (the list) into
`:init/1`. Let’s do that:


Listing 5.6    thy\_supervisor.ex – start\_link/1 and init callback/1. Notice that exits are being trapped in the init/1 callback.

`defmodule ThySupervisor do`
`use GenServer`

`#######`
`# API #`
`#######`

`def start_link(child_spec_list) do`
`GenServer.start_link(__MODULE__, [child_spec_list])`
`end`

`######################`
`# Callback Functions #`
`######################`

`def init([child_spec_list]) do`
`Process.flag(:trap_exit, true)                      #1`
`state = child_spec_list`
`|> start_children`
`|> Enum.into(HashDict.new)`

`{:ok, state}`
`end`
`end`
#1 Make the supervisor process trap exits


The first thing we do here is to let the supervisor process trap exits. This is so that it can receive exit signals from its children as normal messages.


There is quite a bit going on in the lines that follow. The
`child_spec_list`
is fed into
`start_children/1`. This function, as you will soon see, spawns the child processes and returns a list of tuples. Each tuple is a pair that contains the pid of the newly spawned child and the child specification. For example:

`[{<0.82.0>, {ThyWorker, :init, []}}, {<0.84.0>, {ThyWorker, :init, []}}]`
This list is then fed into
`Enum.into/2`. By passing in
`HashDict.new`
as the second argument, we are effectively transforming the list of tuples into a
`HashDict`, with the pids of the child processes as the keys and the child specifications as the values.


transforming an enumerable to a collectable with enum.into


`Enum.into/2`
(and
`Enum.into/3`
that takes an additional transformation function) takes an enumerable (like a
`List`) and inserts it into a
`Collectable`
(like a
`HashDict`. This is very helpful because HashDict knows that if it gets a tuple, the first element becomes the key, and the second element becomes the value:

`iex> h = [{:pid1, {:mod1, :fun1, :arg1}}, {:pid2, {:mod2, :fun2, :arg2}}] |> Enum.into(HashDict.new)`
This returns a HashDict:

`#HashDict<[pid2: {:mod2, :fun2, :arg2}, pid1: {:mod1, :fun1, :arg1}]>`
The key can be retrieved like so:

`iex> HashDict.fetch(h, :pid2)`
`{:ok, {:mod2, :fun2, :arg2}}`
The resulting
`HashDict`
of pid and child specification mappings forms the *state* of the supervisor process, which we return in a
`{:ok, state}`
tuple, which is expected of
`init/1`.


start\_child(supervisor, child\_spec)


I have not described what goes on in the private function
`start_children/1`
that is used in
`init/1`. Let’s skip ahead a little and look at
`start_child/2`
first. This function takes in the supervisor pid and child specification and attaches the child to the supervisor:


Listing 5.7    thy\_supervisor.ex – Starting a single child process

`defmodule ThySupervisor do`
`use GenServer`

`#######`
`# API #`
`#######`

`def start_child(supervisor, child_spec) do`
`GenServer.call(supervisor, {:start_child, child_spec})`
`end`
  
`######################`
`# Callback Functions #`
`######################`

`def handle_call({:start_child, child_spec}, _from, state) do`
`case start_child(child_spec) do`
`{:ok, pid} ->`
`new_state = state |> HashDict.put(pid, child_spec)`
`{:reply, {:ok, pid}, new_state}`
`:error ->`
`{:reply, {:error, “error starting child”}, state}`
`end`
`end`

`#####################`
`# Private Functions #`
`#####################`

`defp start_child({mod, fun, args}) do`
`case apply(mod, fun, args) do`
`pid when is_pid(pid) ->`
`Process.link(pid)`
`{:ok, pid}`
`_ ->`
`:error`
`end`
`end`
`end`
The
`start_child/2`
API call makes a synchronous call request to the supervisor. The request contains a tuple containing the
`:start_child`
atom and child specification. The request is handled by the
`handle_call({:start_child, child_spec}, _, _)`
callback. It attempts to start a new child process using the
`start_child/1`
private function.


Upon success, the caller process receives
`{:ok, pid}`
and the state of the supervisor is updated to
`new_state`. Otherwise, the caller process receives as tuple tagged with
`:error`
and is provided a reason.


Supervisor and Spawning Child Processes with spawn\_link


Here is an important point, and we are making a large assumption here. The assumption is that we assume that the created process links to the supervisor process. What does this mean? This means that we assume that the process is spawned using
`spawn\_link`. In fact, in the OTP Supervisor behavior assumes that processes are created using
`spawn\_link`.


Starting child processes


Now, we can look at the
`start_children/1`
function, which is used in
`init/1`. Here it is:


Listing 5.8  thy\_supervisor .ex – Starting children processes

`defmodule ThySupervisor do`
`# …`

`#####################`
`# Private Functions #`
`#####################`

`defp start_children([child_spec|rest]) do`
`case start_child(child_spec) do`
`{:ok, pid} ->`
`[{pid, child_spec}|start_children(rest)]`
`:error ->`
`:error`
`end`
`end`

`defp start_children([]), do: []``end`
The
`start_children/1`
function takes a list of child specifications and hands
`start_child/1`
a child specification, all the while accumulating a list of tuples. As previously seen, each tuple is a pair that contains the
`pid`
and the child specification.


How does
`start_child/1`
do its work? Turns out, there isn’t a lot of sophisticated machinery involved. Whenever we see a
`pid`, we will link it to the supervisor process:

`defp start_child({mod, fun, args}) do`
`case apply(mod, fun, args) do`
`pid when is_pid(pid) ->`
`Process.link(pid)`
`{:ok, pid}`
`_ ->`
`:error`
`end``end`
terminate\_child(supervisor, pid)


The supervisor needs a way to terminate its children. Here’s the API, callback and private function implementation:


Listing 5.9    thy\_supervisor.ex – Terminating a single child process

`defmodule ThySupervisor do`
`use GenServer`

`#######`
`# API #`
`#######`

`def terminate_child(supervisor, pid) when is_pid(pid) do`
`GenServer.call(supervisor, {:terminate_child, pid})`
`end`

`######################`
`# Callback Functions #`
`######################`

`def handle_call({:terminate_child, pid}, _from, state) do`
`case terminate_child(pid) do`
`:ok ->`
`new_state = state |> HashDict.delete(pid)`
`{:reply, :ok, new_state}`
`:error ->`
`{:reply, {:error, “error terminating child”}, state}`
`end`
`end`

`#####################`
`# Private Functions #`
`#####################`

`defp terminate_child(pid) do`
`Process.exit(pid, :kill)`
`:ok`
`end`
`end`
We use
`Process.exit(pid, :kill)`
to terminate the child process. Remember how we set the supervisor to trap exits? When a child is forcibly killed using
`Process.exit(pid, :kill)`, the supervisor will receive a message in the form of
`{:EXIT, pid, :killed}`. In order to handle this message, the
`handle_info/3`
callback is used:


Listing 5.10  thy\_supervisor.ex – :EXIT messages are handled via the handle\_info/3 callback

`def handle_info({:EXIT, from, :killed}, state) do`
`new_state = state |> HashDict.delete(from)`
`{:no_reply, new_state}``end`
All we need to do is to update the supervisor state by remove its entry in the
`HashDict`, and return the appropriate tuple in the callback.


restart\_child(pid, child\_spec)


Sometimes it is helpful to manually restart a child process. When we want to restart a child process, we need to supply the process id and the child specification. Why do we need the child specifications passed in along with the process id?  The reason is that you might want to add in more arguments, and that has to go into the child specification.


The
`restart_child/2`
private function is a combination of
`terminate_child/1`
and
`start_child/1`.


Listing 5.11  thy\_supervisor.ex – Restarting a child process

`defmodule ThySupervisor do`
`use GenServer`

`#######`
`# API #`
`#######`

`def restart_child(supervisor, pid, child_spec) when is_pid(pid) do`
`GenServer.call(supervisor, {:restart_child, pid, child_spec})`
`end`

`######################`
`# Callback Functions #`
`######################`

`def handle_call({:restart_child, old_pid}, _from, state) do`
`case HashDict.fetch(state, old_pid) do`
`{:ok, child_spec} ->`
`case restart_child(old_pid, child_spec) do`
`{:ok, {pid, child_spec}} ->`
`new_state = state`
`|> HashDict.delete(old_pid)`
`|> HashDict.put(pid, child_spec)`
`{:reply, {:ok, pid}, new_state}`
`:error ->`
`{:reply, {:error, “error restarting child”}, state}`
`end`
`_ ->`
`{:reply, :ok, state}`
`end`
`end`

`#####################`
`# Private Functions #`
`#####################`

`defp restart_child(pid, child_spec) when is_pid(pid) do`
`case terminate_child(pid) do`
`:ok ->`
`case start_child(child_spec) do`
`{:ok, new_pid} ->`
`{:ok, {new_pid, child_spec}}`
`:error ->`
`:error`
`end`
`:error ->`
`:error`
`end`
`end`
`end`
count\_children(supervisor)


This function returns the number of children that is linked to the supervisor. The implementation is straightforward:


Listing 5.12    thy\_supervisor.ex – Counting the number of child processes

`defmodule ThySupervisor do`
`use GenServer`

`#######`
`# API #`
`#######`

`def count_children(supervisor) do`
`GenServer.call(supervisor, :count_children)`
`end`

`######################`
`# Callback Functions #`
`######################`

`def handle_call(:count_children, _from, state) do`
`{:reply, HashDict.size(state), state}`
`end`
`end`
which\_children(supervisor)


This is similar to
`count_children/1`’s implementation. Because our implementation is simple, it is fine to return the entire state:


Listing 5.13    thy\_supervisor.ex –  A simplistic implementation of which\_childre/1 that returns the entire state of the supervisor

`defmodule ThySupervisor do`
`use GenServer`

`#######`
`# API #`
`#######`

`def which_children(supervisor) do`
`GenServer.call(supervisor, :which_children)`
`end`

`######################`
`# Callback Functions #`
`######################`

`def handle_call(:which_children, _from, state) do`
`{:reply, state, state}`
`end`
`end`
terminate(reason, state)


This callback is called to shutdown the supervisor process. Before we terminate the supervisor process, we need to terminate all the children it is linked to, which is handled by the
`terminate_children/1`
private function:


Listing 5.14    thy\_supervisor.ex – Terminating the supervisor involves terminating the child processes first

`defmodule ThySupervisor do`
`use GenServer`

`######################`
`# Callback Functions #`
`######################`

`def terminate(_reason, state) do`
`terminate_children(state)`
`:ok`
`end`

`#####################`
`# Private Functions #`
`#####################`

`defp terminate_children([]) do`
`:ok`
`end`

`defp terminate_children(child_specs) do`
`child_specs |> Enum.each(fn {pid, _} -> terminate_child(pid) end)`
`end`

`defp terminate_child(pid) do`
`Process.exit(pid, :kill)`
`:ok`
`end`
`end`
5.3.4        Handling Crashes


I’ve saved the best for last. What happens when one of the child processes crashes? If you were paying attention, the supervisor would receive a message that looks like
`{:EXIT, pid, reason}`. Once again, we use the
`handle_info/3`
callback to handle the exit messages.


There are two cases to consider (other than
`:killed`, which we handled in
`terminate_child/1`).


The first case is when the process exited normally. The supervisor doesn’t have to do anything in this case, except update its state:


Listing 5.15    thy\_supervisor.ex – Do nothing when a child process exits normally

`def handle_info({:EXIT, from, :normal}, state) do`
`new_state = state |> HashDict.delete(from)`
`{:no_reply, new_state}``end`
The second case is when the process has exited abnormally and hasn’t been forcibly killed. In that case, the supervisor should automatically restart the failed process:


Listing 5.16    thy\_supervisor.ex – Restart a child process automatically if it exits for an abnormal reason

`def handle_info({:EXIT, old_pid, _reason}, state) do`
`case HashDict.fetch(state, old_pid) do`
`{:ok, child_spec} ->`
`case restart_child(old_pid, child_spec) do`
`{:ok, {pid, child_spec}} ->`
`new_state = state`
`|> HashDict.delete(old_pid)`
`|> HashDict.put(pid, child_spec)`
`{:no_reply, new_state}`
`:error ->`
`{:no_reply, state}`
`end`
`_ ->`
`{:no_reply, state}`
`end``end`
This above function is nothing new. It is almost the same implementation as
`restart_child/2`, except that the child specification is *reused*.


5.3.5        Full Completed Source


Here is the full source of our hand-rolled supervisor in all its glory:


Listing 5.17    The full implementation of thy\_supervisor.ex

`defmodule ThySupervisor do`
`use GenServer`

`#######`
`# API #`
`#######`

`def start_link(child_spec_list) do`
`GenServer.start_link(__MODULE__, [child_spec_list])`
`end`

`def start_child(supervisor, child_spec) do`
`GenServer.call(supervisor, {:start_child, child_spec})`
`end`

`def terminate_child(supervisor, pid) when is_pid(pid) do`
`GenServer.call(supervisor, {:terminate_child, pid})`
`end`

`def restart_child(supervisor, pid, child_spec) when is_pid(pid) do`
`GenServer.call(supervisor, {:restart_child, pid, child_spec})`
`end`

`def count_children(supervisor) do`
`GenServer.call(supervisor, :count_children)`
`end`

`def which_children(supervisor) do`
`GenServer.call(supervisor, :which_children)`
`end`

`######################`
`# Callback Functions #`
`######################`

`def init([child_spec_list]) do`
`Process.flag(:trap_exit, true)`
`state = child_spec_list`
`|> start_children`
`|> Enum.into(HashDict.new)`

`{:ok, state}`
`end`

`def handle_call({:start_child, child_spec}, _from, state) do`
`case start_child(child_spec) do`
`{:ok, pid} ->`
`new_state = state |> HashDict.put(pid, child_spec)`
`{:reply, {:ok, pid}, new_state}`
`:error ->`
`{:reply, {:error, “error starting child”}, state}`
`end`
`end`

`def handle_call({:terminate_child, pid}, _from, state) do`
`case terminate_child(pid) do`
`:ok ->`
`new_state = state |> HashDict.delete(pid)`
`{:reply, :ok, new_state}`
`:error ->`
`{:reply, {:error, “error terminating child”}, state}`
`end`
`end`

`def handle_call({:restart_child, old_pid}, _from, state) do`
`case HashDict.fetch(state, old_pid) do`
`{:ok, child_spec} ->`
`case restart_child(old_pid, child_spec) do`
`{:ok, {pid, child_spec}} ->`
`new_state = state`
`|> HashDict.delete(old_pid)`
`|> HashDict.put(pid, child_spec)`
`{:reply, {:ok, pid}, new_state}`
`:error ->`
`{:reply, {:error, “error restarting child”}, state}`
`end`
`_ ->`
`{:reply, :ok, state}`
`end`
`end`

`def handle_call(:count_children, _from, state) do`
`{:reply, HashDict.size(state), state}`
`end`

`def handle_call(:which_children, _from, state) do`
`{:reply, state, state}`
`end`

`def handle_info({:EXIT, from, :normal}, state) do`
`new_state = state |> HashDict.delete(from)`
`{:no_reply, new_state}`
`end`

`def handle_info({:EXIT, from, :killed}, state) do`
`new_state = state |> HashDict.delete(from)`
`{:no_reply, new_state}`
`end`

`def handle_info({:EXIT, old_pid, _reason}, state) do`
`case HashDict.fetch(state, old_pid) do`
`{:ok, child_spec} ->`
`case restart_child(old_pid, child_spec) do`
`{:ok, {pid, child_spec}} ->`
`new_state = state`
`|> HashDict.delete(old_pid)`
`|> HashDict.put(pid, child_spec)`
`{:no_reply, new_state}`
`:error ->`
`{:no_reply, state}`
`end`
`_ ->`
`{:no_reply, state}`
`end`
`end`

`def terminate(_reason, state) do`
`terminate_children(state)`
`:ok`
`end`

`#####################`
`# Private Functions #`
`#####################`

`defp start_children([child_spec|rest]) do`
`case start_child(child_spec) do`
`{:ok, pid} ->`
`[{pid, child_spec}|start_children(rest)]`
`:error ->`
`:error`
`end`
`end`

`defp start_children([]), do: []`

`defp start_child({mod, fun, args}) do`
`case apply(mod, fun, args) do`
`pid when is_pid(pid) ->`
`Process.link(pid)`
`{:ok, pid}`
`_ ->`
`:error`
`end`
`end`

`defp terminate_children([]) do`
`:ok`
`end`

`defp terminate_children(child_specs) do`
`child_specs |> Enum.each(fn {pid, _} -> terminate_child(pid) end)`
`end`

`defp terminate_child(pid) do`
`Process.exit(pid, :kill)`
`:ok`
`end`

`defp restart_child(pid, child_spec) when is_pid(pid) do`
`case terminate_child(pid) do`
`:ok ->`
`case start_child(child_spec) do`
`{:ok, new_pid} ->`
`{:ok, {new_pid, child_spec}}`
`:error ->`
`:error`
`end`
`:error ->`
`:error`
`end`
`end``end`
5.4           A Sample Run (Or: Does It Really Work?)


Before we put our supervisor through its paces, create a new file
`lib/thy_worker.ex`:


Listing 5.18    lib/thy\_worker.ex – An example worker to be used with ThySupervisor

`defmodule ThyWorker do`
`def start_link do`
`spawn(fn -> loop end)`
`end`

`def loop do`
`receive do`
`:stop -> :ok`

`msg ->`
`IO.inspect msg`
`loop`
`end`
`end``end`
We begin by creating a worker:

`iex> {:ok, sup_pid} = ThySupervisor.start_link([])`
`{:ok, #PID<0.86.0>}`
Let’s create a process and add it to the supervisor. We save the pid of the newly spawned child process.

`iex> {:ok, child_pid} = ThySupervisor.start_child(sup_pid, {ThyWorker, :start_link, []})`
Let’s see what links are present in the supervisor:

`iex(3)> Process.info(sup_pid, :links)`
`{:links, [#PID<0.82.0>, #PID<0.86.0>]}`
Interesting – there are two processes linked to the supervisor process. The first one is obviously the child process we just spawned. What about the other one?

`iex> self`
`#PID<0.82.0>`
A little thought should reveal that since the supervisor process is spawned and linked by the shell process, it would have the shell’s pid in its link set.


Let’s kill the child process:

`iex> Process.exit(child_pid, :crash)`
What happens when we inspect the link set of the supervisor again?

`iex> Process.info(sup_pid, :links)`
`{:links, [#PID<0.82.0>, #PID<0.90.0>]}`
Sweet! The supervisor automatically took care of spawning and linking the new child process. To convince ourselves, we can peek at the supervisors state:

`iex> ThySupervisor.which_children(sup_pid)`
`#HashDict<[{#PID<0.90.0>, {ThyWorker, :start_link, []}}]>`
5.5           Summary


In this chapter, we worked through several examples that highlight how:


·      The “Let it Crash” philosophy means delegating error detection and handling to another process and not coding too defensively


·      Links set up bi-directional relationships between processes that serve to propagate exit signals when a crash happens in one of the processes


·      Monitors set up a unidirectional relationship between processes so that the monitoring process is simply notified when a monitored process dies


·      Exit signals can be trapped by so-called system processes that convert exit signals into normal messages


·      Implement a simplistic supervisor process using processes and links


In the next chapter, we are ready to dive into the OTP Supervisor behavior. We will learn about the most important Supervisor features, and get to experiment with them by building a worker pooler. Fun times!





