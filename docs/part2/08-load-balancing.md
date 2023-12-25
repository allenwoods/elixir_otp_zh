# 8   Distribution and Load Balancing


This chapter covers:


·      The basics of distributed Elixir


·      Implementing a distributed load tester


·      Building a command line application


·      Tasks, an abstraction for short-lived computations


·      Implementing a distributed and fault-tolerant application


This chapter and the next are going to be the most fun chapters (I say that for *every* chapter). In this chapter, we will explore the distribution capabilities of the Erlang VM. We will learn about the distribution primitives that let us create a cluster of nodes and spawn processes remotely. The next chapter we will explore failover and takeover in a distributed system.


In order to demonstrate all these concepts, we will build *two* applications. The first one is a command line tool to perform load testing on websites. Yes, this could very well be used for evil purposes, but I will leave you to your own exploits.


The other is an application that will demonstrate how a cluster handles failures by having another node automatically stepping up to take the place of a downed node. To take things further, it will also demonstrate how a node yields control when a previously downed node of higher priority rejoins the cluster.


8.1           Why Distributed?


There are at least two good reasons why you would want create a distributed system. When the application you are building has exceeded the physical capabilities of a single machine, then you would have a choice of either upgrading that single machine or adding another machine. There are limits to how much you can upgrade a single machine. There are also physical limits to how much a single machine can handle. Examples include the number of opened file handles and also network connections. Sometimes a machine has to be brought down of scheduled maintenance or upgrades. With a distributed system, you can design the load to be spread across multiple machines. In other words, you are achieving *load balancing*.


Fault-tolerance is the other reason to consider building a distributed system. This is when we have one or more nodes are monitoring the node that is running the application. If that node goes down, the next node next in line will automatically take over that node. Having a setup like this means that you eliminate a single point of failure (unless all your nodes are hosted on a single machine!).


Make no mistake; distributed systems will still be hard given the nature of the problem. It is still up to you to content with the tradeoffs and issues that come up with distributed systems such as net splits. However, what Elixir and the Erlang VM offers are tools that you can weld to make your like *way* easier to build distributed systems.


8.2           Distribution for Load Balancing


In this section, we will learn how to build a distributed load tester. The load tester that we are building basically creates a barrage of GET requests to an endpoint, and measures the response time. Since there is a limit to the number of open network connections a single physical machine can make, this is a perfect use case for a distributed system. In this case, the number of web requests needed is spread evenly across each node in the cluster.


8.2.1        An Overview of Blitzy, the Load Tester


Before we begin learning about distribution and implementing Blitzy, lets briefly see what it can do. Blitzy is a command line program. This is an example of unleashing Blitzy on an unsuspecting victim:

`% ./blitzy -n 100 http://www.bieberfever.com`
`[info]  Pummeling http://www.bieberfever.com with 100 requests`
Here, we are creating 100 workers that will make a HTTP GET request to
`www.bieberfever.com`
and measure the response time and count the number of successful requests. Behind the scenes, Blitzy creates a cluster and splits the workers across the nodes in the cluster. In the above example, 100 workers are split across four nodes. Therefore, there are 25 workers running on each node:


![](../images//8_1.png)  



Figure 8.1 The number of requests is split across the available nodes in the cluster


Once all the workers from each individual node have completed, the result will then be sent over the master node.


![](../images//8_2.png)  



Figure 8.2 Once a node has received results from all its workers, the respective node will report back to the worker


The master node will then aggregate and report the results:

`Total workers    : 1000`
`Successful reqs  : 1000`
`Failed res       : 0`
`Average (msecs)  : 3103.478963`
`Longest (msecs)  : 5883.235``Shortest (msecs) : 25.061`
When I am planning to write a distributed application, I always begin with the non-distributed version first, just to keep things slightly simpler. Once you have gotten the non-distributed bits working, you can then move on to layering the distribution layer. Jumping straight into building an application with distribution in mind for a first iteration usually turns out badly.


That is the approach we will take when developing Blitzy in this chapter. In fact, we will begin with baby steps:


1.  Build the non-concurrent version


2.  Build the concurrent version


3.  Build the distributed version, that can run on two virtual machine instances


4.  Build the distributed version, that can run on two separate machines connected to a network


8.2.2        Let the Mayhem Begin!


Give the project a good name:

`% mix new blitzy`
Let's pull in some dependencies that, if we had a crystal ball, we would know to include in
`mix.exs`:


Listing 8.1 Setting up the dependencies for Blitzy (mix.exs)

`defmodule Blitzy.Mixfile do`
`use Mix.Project`

`def project do`
`[app: :blitzy,`
`version: "0.0.1",`
`elixir: "~> 1.1-rc1",`
`deps: deps]`
`end`

`def application do`
`[mod: {Blitzy, []},`
`applications: [:logger, :httpoison, :timex]] #3`
`end`

`defp deps do`
`[`
`{:httpoison, "~> 0.9.0"},   #1`
`{:timex,     "~> 3.0"},      #2`
`{:tzdata, "~> 0.1.8", override: true}`
`]`
`end``end`
#1 HTTPoison is a HTTP client


#2 Timex is a date/time library


#3 Add the prerequisite applications


If you are wondering about
`tzdata`
and the
`override: true`: This needs to be there because newer versions of
`tzdata`
do not play nice with escripts. Escripts will be explained later in the chapter. Finally, do not forget to add the correct entries in
`application/0`.



Always read the README!



I wouldn't know to include the correct entries in
`application/0`
unless I have read the installation instructions given in the respective READMEs of the libraries. Failure to do so will often lead to confusing errors.



 



8.2.3        Implementing the Worker Process


We begin with the worker process. The worker fetches the webpage and computes how long the request took. Create
`lib/blitzy/worker.ex`.


Listing 8.2 Implementing the worker (lib/blitzy/worker.ex)

`defmodule Blitzy.Worker do`
`use Timex`
`require Logger`

`def start(url) do`
`{timestamp, response} = Duration.measure(fn -> HTTPoison.get(url) end)`
`handle_response({Duration.to_milliseconds(timestamp), response})`
`end`

`defp handle_response({msecs, {:ok, %HTTPoison.Response{status_code: code}}})`
`when code >= 200 and code <= 304 do`
`Logger.info "worker [#{node}-#{inspect self}] completed in #{msecs} msecs"`
`{:ok, msecs}`
`end`

`defp handle_response({_msecs, {:error, reason}}) do`
`Logger.info "worker [#{node}-#{inspect self}] error due to #{inspect reason}"`
`{:error, reason}`
`end`

`defp handle_response({_msecs, _}) do`
`Logger.info "worker [#{node}-#{inspect self}] errored out"`
`{:error, :unknown}`
`end`
`end`
The start function takes a
`url`
and an optional
`func`.
`func`
is a function that will be used to make the HTTP request. By specifying an optional function this way, we are free to swap out the implementation with another HTTP client, say *HTTPotion.*


For example, we could have instead chosen to use HTTPotion's
`HTTPotion.get/1`
instead like so:

`Blitzy.Worker.start("http://www.bieberfever.com", &HTTPotion.get/1)`
The HTTP request function is then invoked inside the body of
`Time.measure/1`. Notice that slightly different syntax:
`func.(url)`
instead of
`func(url)`. The dot here is important since we need to tell Elixir that
`func`
is pointing to another function and not that function itself.


`Time.measure/1`
is a handy function from
`Timex`
that measures the time taken for a function to complete. Once that function completes,
`Time.measure/1`
returns a tuple containing the time taken and the return value of that function. Note that all measurements are in milliseconds.


The tuple returned from
`Time.measure/1`
is then passed along to
`handle_response/1`. Here, we are expecting that whatever function we pass into
`start/2`
gives us a return result containing a tuple in either of the following formats:


`·`
`{:ok, %{status_code: code}`


`·`
`{:error, reason}`


In addition to getting a successful response, we also check that the status code falls between a status code of 200 and 304. If we hit into an error response, we return a tuple tagged with
`:error`
along with the reason for the error. Finally, we handle the last case where we handle all other cases.


8.2.4        Running the Worker


Let's try running the worker:

`iex(1)> Blitzy.Worker.start("http://www.bieberfever.com")`
`{:ok, 2458.665}`
Awesome! Hitting Justin Bieber's fan site takes around 2.4 seconds. Notice that this was the amount of time you had to wait to get the result back too. How then can we execute say, a *thousand* concurrent requests? Use
`spawn`/`spawn_link`!


While that *can* work, we also need a way to aggregate the return results of the worker to calculate the average time taken for all successful requests made by the workers, for example. Well, we *could* pass the caller process into the argument of the
`Blitzy.Worker.start`
function, and send a message to the caller process once the result is available. In turn, the caller process must wait for incoming messages of from a thousand workers.


Here's a quick sketch of how we might accomplish this. We introduce a
`Blitzy.Caller`
module:


Listing 8.3 A sketch for aggregating result from the worker processes

`defmodule Blitzy.Caller do`
`def start(n_workers, url) do`
`me = self`

`1..n_workers`
`|> Enum.map(fn _ -> spawn(fn -> Blitzy.Worker.start(url, me) end) end)`
`|> Enum.map(fn _ ->`
`receive do`
`x -> x`
`end`
`end)`
`end``end`
The caller module takes in two arguments. The first is the number of workers to create, followed by the URL to load test against. The above code might not exactly be too intuitive, so let’s go through it bit by bit.


We first save a reference to the calling process in
`me`. Why? That's because if we use
`self`
instead of
`me`
within
`spawn`, then
`self`
would refer to the newly spawned process and *not* the calling process! To convince yourself:

`iex(1)> self`
`#PID<0.159.0>`

`iex(2)> spawn(fn -> IO.inspect self end)``#PID<0.162.0>`
Next, we spawn
`n_workers`
number of workers. The result of

`1..n_workers`
`|> Enum.map(fn _ -> spawn(fn -> Blitzy.Worker.start(url, me) end) end)`
Is a list of worker pids. We expect the pids to be sending the caller process the results (more on that in the next section), therefore we wait for an equal number of the messages:

`worker_pids`
`|> Enum.map(fn _ ->`
`receive do`
`x -> x`
`end``end)`
We only need to make a slight modification to
`Blitzy.Worker.start/1`:


Listing 8.4 Modifying the worker process so that it can send its results to its caller process (lib/worker.ex)

`defmodule Blitzy.Worker do`

`def start(url, caller, func \\ &HTTPoison.get/1) do   #1`
`{timestamp, response} = Duration.measure(fn -> func.(url) end)`
`caller`
`|> send({self,`
`handle_response(`
`{Duration. to_milliseconds (timestamp), response})}) #2`
`end`
`end`
#1: Add a caller argument


#2: Whenever the result is computed, send the result to the caller process


The above modifications allow the
`Blitzy.Worker`
process to send its results to the caller process.


If it sounds messy and starting to make your head hurt a little, then you are in good company. Although honestly it is not *that* hard, spawning a bunch of tasks concurrently and waiting for the result from each of its spawned workers shouldn't be that hard, especially since this is a common use case. Thankfully, this is when *Tasks* come in.


8.3           Introducing Tasks


Tasks are an abstraction in Elixir to execute one particular computation. This computation is usually simple and self-contained, and requires no communication/coordination with other processes. To appreciate how Tasks can make the above scenario easier.


We can create an asynchronous task by invoking
`Task.async/1`:

`iex> task = Task.async(fn -> Blitzy.Worker.start("http://www.bieberfever.com") end)`
What we get back is a
`Task`
struct:

`%Task{pid: #PID<0.154.0>, ref: #Reference<0.0.3.67>}`
At this point, the task is asynchronously executing in the background. In order to get the value out of the task, we need to invoke
`Task.await/1`:


Listing 8.5 Creating ten tasks, each running a Blitzy worker process

`iex> Task.await(task)`
`{:ok, 3362.655}`
What happens if the task is still computing? The caller process will be blocked until the task finishes. Let's try it out:

`iex> worker_fun = fn -> Blitzy.Worker.start("http://www.bieberfever.com") end`
`#Function<20.54118792/0 in :erl_eval.expr/5>`
`iex> tasks = 1..10 |> Enum.map(fn _ -> Task.async(worker_fun) end)`
The return result is a list of ten
`Task`
structs

`[%Task{pid: #PID<0.184.0>, ref: #Reference<0.0.3.1071>},`
`%Task{pid: #PID<0.185.0>, ref: #Reference<0.0.3.1072>},`
`%Task{pid: #PID<0.186.0>, ref: #Reference<0.0.3.1073>},`
`%Task{pid: #PID<0.187.0>, ref: #Reference<0.0.3.1074>},`
`%Task{pid: #PID<0.188.0>, ref: #Reference<0.0.3.1075>},`
`%Task{pid: #PID<0.189.0>, ref: #Reference<0.0.3.1076>},`
`%Task{pid: #PID<0.190.0>, ref: #Reference<0.0.3.1077>},`
`%Task{pid: #PID<0.191.0>, ref: #Reference<0.0.3.1078>},`
`%Task{pid: #PID<0.192.0>, ref: #Reference<0.0.3.1079>},``%Task{pid: #PID<0.193.0>, ref: #Reference<0.0.3.1080>}]`
There are now ten asynchronous workers hitting the site. To grab the results:

`iex> result = tasks |> Enum.map(&Task.await(&1))`
Depending on your network connection, the shell process might be blocked for a while before you get something like:

`[ok: 95.023, ok: 159.591, ok: 190.345, ok: 126.191, ok: 125.554, ok: 109.059, ok: 139.883, ok: 125.009, ok: 101.94, ok: 124.955]`
Isn't this awesome? Not only can we create asynchronous processes to create our workers, but we also have an easy way of collecting results from them.


Hang on to your seats, because this is only going to get better! There is no need to go through the hassle of having to pass in the caller's pid and having to set up any receive blocks. With Tasks, this is all handled nicely for you.


In
`lib/blitzy.ex`, create a
`run/2`
function that creates and waits for the worker tasks:


Listing 8.6 A convenience function to run Blitzy workers in Tasks (lib/blitzy.ex)

`defmodule Blitzy do`

`def run(n_workers, url) when n_workers > 0 do`
`worker_fun = fn -> Blitzy.Worker.start(url) end`

`1..n_workers`
`|> Enum.map(fn _ -> Task.async(worker_fun) end)`
`|> Enum.map(&Task.await(&1))`
`end`
`end`
You can now simply invoke
`Blitzy.run/2`
and get the results in a list:

`iex> Blitzy.run(10, "http://www.bieberfever.com")`

`[ok: 71.408, ok: 69.315, ok: 72.661, ok: 67.062, ok: 74.63, ok: 65.557,``ok: 201.591, ok: 78.879, ok: 115.75, ok: 66.681]`
There's a tiny issue though. Observe what happens when we bump up the number of workers to a *thousand*:

`iex> Blitzy.run(1000, "http://www.bieberfever.com")`
This results in:


Listing 8.7 The error message when a Task timeouts

`(exit) exited in: Task.await(%Task{pid: #PID<0.231.0>, ref: #Reference<0.0.3.1201>}, 5000)`
`** (EXIT) time out`
`(elixir) lib/task.ex:274: Task.await/2`
`(elixir) lib/enum.ex:1043: anonymous fn/3 in Enum.map/2`
`(elixir) lib/enum.ex:1385: Enum."-reduce/3-lists^foldl/2-0-"/3``(elixir) lib/enum.ex:1043: Enum.map/2`
The problem here is that
`Task.await/2`
times out after *five* seconds (the default). We can easily fix this by giving
`:infinity`
to
`Task.await/2`
as the timeout value:


Listing 8.8 Making a Task wait forever (lib/blitzy.ex)

`defmodule Blitzy do`

`def run(n_workers, url) when n_workers > 0 do`
`worker_fun = fn -> Blitzy.Worker.start(url) end`

`1..n_workers`
`|> Enum.map(fn _ -> Task.async(worker_fun) end)`
`|> Enum.map(&Task.await(&1, :infinity))         #1`
`end`
`end`
#1: Letting Task.await/2 wait forever.


Specifying infinity is not a problem in this case because the HTTP client will timeout should the server take too long, therefore we gladly delegate this decision to the HTTP client and not the Task.


Finally, we need to compute the average time taken. In
`lib/blitzy.ex`,
`parse_results/1`
handles computing some simple statistics and formatting the results into a human-friendly format:


Listing 8.9  Computing simple statistics from the workers (lib/blitzy.ex)

`defmodule Blitzy do`

`# ...`

`defp parse_results(results) do`
`{successes, _failures} =`
`Results`
`|> Enum.partition(fn x -> #1`
`case x do`
`{:ok, _} -> true`
`_        -> false`
`end`
`end)`

`total_workers = Enum.count(results)`
`total_success = Enum.count(successes)`
`total_failure = total_workers - total_success`

`data = successes |> Enum.map(fn {:ok, time} -> time end)`
`average_time  = average(data)`
`longest_time  = Enum.max(data)`
`shortest_time = Enum.min(data)`

`IO.puts """`
`Total workers    : #{total_workers}`
`Successful reqs  : #{total_success}`
`Failed res       : #{total_failure}`
`Average (msecs)  : #{average_time}`
`Longest (msecs)  : #{longest_time}`
`Shortest (msecs) : #{shortest_time}`
`"""`
`end`

`defp average(list) do`
`sum = Enum.sum(list)`
`if sum > 0 do`
`sum / Enum.count(list)`
`else`
`0`
`end`
`end`
`end`
#1 Enum.partition/2


The most interesting part is the use of
`Enum.partition/2`. This function takes in a collection and a predicate function, and results in two collections. The first collection contains all the elements where the predicate function returned a truthy value when applied. The second collection contains the rejects. In our case, since a successful request looks like
`{:ok, _}`
and an unsuccessful request looks like
`{:error, _}`, we can pattern match on
`{:ok, _}`.


8.4           Onward to Distribution!


We will revisit Blitzy in a little bit. Let's learn to build a cluster in Elixir! One of the killer features of the Erlang virtual machine is distribution. That is, the ability to have multiple Erlang runtimes talking to each other. Sure, you can probably do it on other languages and platforms, but most will leave you losing faith in computers and humanity in general.


8.4.1        Location Transparency


Processes in an Elixir/Erlang cluster are location transparent. This means that it just as easy to send a message between processes on a single node as it is on a different node, as long as you know the process id of the recipient process.


![](../images//8_3.png)  



Figure 8.3 Location transparency means that is essentially no difference sending a message to a process on the same node and to a process on a remote node


This makes it incredibly easy to have processes communicate across nodes, since there is fundamentally no difference, at least from the developer's point of view.


8.4.2        An Elixir Node


A node is a system running the Erlang virtual machine with a given name. A name is represented as an atom such as
`:justin@bieber.com`, much like an email address. Names come in two flavors, *short* and *long*. Using short names assume that all the nodes will be located within the same IP domain. In general, this is easier to set up and will be what we will be sticking with in this chapter.


8.4.3        Creating a Cluster


The first step in creating a cluster is to start an Erlang system in distributed mode, and to do that, you must give it a name. In a fresh terminal, fire up
`iex`
but this time, give it a short name
`(--sname NAME`):

`$ iex --sname barry`
`iex(barry@imac)>`
Notice that your
`iex`
prompt now has the short name and the hostname of the local machine. To get node name of the local machine, a call to
`Kernel.node/0`
will do the trick:

`iex(barry@imac)> node`
`:barry@imac`
Alternatively,
`Node.self/0`
gives you the same result, but I prefer
`node`
since it's much shorter. Now, in two other separate terminal windows, repeat the process but give each of them different names:


Start the second node:

`$ iex --sname robin`
`iex(robin@imac)>`
Followed by the third one:

`$ iex --sname maurice`
`iex(maurice@imac)>`
At this point, the nodes are still in isolation – They do not know of each other’s existence.



Nodes must have unique names!



If you start a node with a name that has already been registered, the VM will throw a fit. A corollary to this is that you cannot mix long and short names.



 



8.4.4        Connecting Nodes


Go to the
`barry`
node, and connect to
`robin`
using
`Node.connect/1`:

`iex(barry@imac)> Node.connect(:robin@imac)`
`true`
`Node.connect/1`
returns true if the connection is successful. To list all the nodes
`barry`
is connected to, use
`Node.list/0`:

`iex(barry@imac)> Node.list`
`[:robin@imac]`
Note that
`Node.list/1`
doesn't list the current node, only nodes that it is connected to. Now, go to the
`robin`
node, and run
`Node.list/0`
again:

`iex(robin@imac)> Node.list`
`[:barry@imac]`
No surprises here. Connecting
`barry`
to
`robin`
means that a bi-directional connection is set up. Now from
`robin`, let's connect to
`maurice`:

`iex(robin@imac)> Node.connect(:maurice@imac)`
`true`
Now, let's check the nodes that
`robin`
is connected to:

`iex(robin@imac)> Node.list`
`[:barry@imac, :maurice@imac]`
Let's check back to
`barry`. We didn't explicitly run
`Node.connect(:maurice@imac)`
on
`barry`. So what should we see?

`iex(barry@imac)9> Node.list`
`[:robin@imac, :maurice@imac]`
8.4.5        Node Connections Are Transitive


Sweet! Node connections are *transitive*. This means that even though we didn't have to connect
`barry`
to
`maurice`
explicitly, this was done because
`barry`
is connected to
`robin`
and
`robin`
is connected to
`maurice`
so therefore
`barry`
is connected to
`maurice`.


![](../images//8_4.png)  



Figure 8.4 Connecting a node to another node automatically links the new node to all the other nodes in the cluster


Disconnecting a node disconnects it from *all* the members of the cluster. A node might disconnect if
`Node.disconnect/1`
is called or if the node dies due to a network disruption for example.


8.5           Remotely Executing Functions


So now that we know how to connect nodes to a cluster, lets do something useful. First, close all previously opened
`iex`
sessions because we are going to create our cluster again from scratch.


Before that though, head to
`lib/worker.ex`
and make a one line addition to the
`start/3`
function:


Listing 8.10 Adding a line to print the current node (lib/worker.ex)

`defmodule Blitzy.Worker do`

`def start(url, func \\ &HTTPoison.get/1) do`
`IO.puts "Running on #node-#{node}"             #1`
`{timestamp, response} = Duration.measure(fn -> func.(url) end)`
`handle_response({Duration. Duration.to_milliseconds (timestamp), response})`
`end`
`# ... same as before``end`
#1 Print current node


This time, go to the directory of
`blitzy`, and in *three* different terminals. In the first terminal:

`% iex --sname barry -S mix`
And in the second terminal:

`% iex --sname robin -S mix`
Finally, in the third terminal:

`% iex --sname maurice -S mix`
Next, we connect all the nodes together. For example, from the
`maurice`
node:

`iex(maurice@imac)> Node.connect(:barry@imac)`
`true`

`iex(maurice@imac)> Node.connect(:robin@imac)`
`true`

`iex(maurice@imac)> Node.list``[:barry@imac, :robin@imac]`
Now for the fun bit. We are now going run
`Blitzy.Worker.start`
on all three nodes. Let that sink it for a moment, because that is *super* awesome. Note that the rest of the commands will be performed on the
`maurice`
node. While you are free to perform it on any node, some of the output will be different.


First, we store all the references of every single member of the cluster (including the current node) into
`cluster`:

`iex(maurice@imac)>  cluster = [node | Node.list]`
`[:maurice@imac, :barry@imac, :robin@imac]`
Then, we can make use of the
`:rpc.multicall`
function to run
`Blitzy.Worker.start/1`
on all three nodes:

`iex(maurice@imac)> :rpc.multicall(cluster, Blitzy.Worker, :start, ["http://www.bieberfever.com"])`
`"Running on #node-maurice@imac"`
`"Running on #node-robin@imac"``"Running on #node-barry@imac"`
The return result looks like:

`{[ok: 2166.561, ok: 3175.567, ok: 2959.726], []}`
In fact, you do not even need to specify the
`cluster`:

`iex(maurice@imac)> :rpc.multicall(Blitzy.Worker, :start, ["http://www.bieberfever.com"])`
`"Running on #node-maurice@imac"`
`"Running on #node-barry@imac"`
`"Running on #node-robin@imac"``{[ok: 1858.212, ok: 737.108, ok: 1038.707], []}`
Notice that the return value is a tuple of two elements. All successful calls are captured in the first element, and a list of bad (unreachable) nodes is given in the second argument.


So now, how do we execute multiple workers in multiple nodes, while being able to aggregate the results and present them afterwards? We solved that when we implemented
`Blitzy.run/2`
using
`Task.async/1`
and
`Task.await/2`.

`iex(maurice@imac)> :rpc.multicall(Blitzy, :run, [5, "http://www.bieberfever.com"], :infinity)`
The return result is three lists, each with five elements.

`{[[ok: 92.76, ok: 71.179, ok: 138.284, ok: 78.159, ok: 139.742],`
`[ok: 120.909, ok: 75.775, ok: 146.515, ok: 86.986, ok: 129.492],`
`[ok: 147.873, ok: 171.228, ok: 114.596, ok: 120.745, ok: 130.114]],``[]}`
There are many interesting functions in the Erlang documentation for the [RPC module](http://www.erlang.org/doc/man/rpc.html) such as
`:rpc.pmap/3`
and
`parallel_eval/1`, and I encourage you to experiment with them later on. For now, we turn our attention back to Blitzy.


8.6           Making Blitzy Distributed


We will create a simple configuration file that the master node will make use of to connect to the nodes of the cluster. Open
`config/config.exs`
and fill in the following:


Listing 8.11 Configuration file for the entire cluster (config/config.exs)

`use Mix.Config`

`config :blitzy, master_node: :"a@127.0.0.1"`

`config :blitzy, slave_nodes: [:"b@127.0.0.1",`
`:"c@127.0.0.1",``:"d@127.0.0.1"]`
8.6.1        Creating a command line interface


Blitzy is a command-line program. Therefore, let's build a command line interface for it. Create a new file called
`cli.ex`
and place it in
`lib`. This is how we would like to invoke
`Blitzy`:

`./blitzy -n [requests] [url]`
`[requests]`
is an integer which specifies the number of workers to create and
`[url]`
is a string that specifies the endpoint. Also, a help message should be presented if the user fails to supply the right format. In Elixir, it is easy to wire this up.


First, head over to
`mix.exs`
and modify
`project/0`. Create an entry called
`escript`
fill it like so:


Listing 8.12 Adding escript to the project function to determine the main entry point of the command line program (mix.exs)

`defmodule Blitzy.Mixfile do`

`def project do`
`[app: :blitzy,`
`version: "0.0.1",`
`elixir: "~> 1.1",`
`escript: [main_module: Blitzy.CLI], #1`
`deps: deps]`
`end`
`end`
This points
`mix`
to the right module when we call
`mix escript.build`
to generate the
`Blitzy`
command line program. The module pointed to by
`main_module`
is expected to have a
`main/1`
function. Let's provide that, and a few other functions:


8.6.2        Parsing input arguments with OptionParser


Listing 8.13 Handling input arguments using OptionParser (lib/cli.ex)

`use Mix.Config`
`defmodule Blitzy.CLI do`
`require Logger`

`def main(args) do`
`args`
`|> parse_args`
`|> process_options`
`end`

`defp parse_args(args) do`
`OptionParser.parse(args, aliases: [n: :requests],`
`strict: [requests: :integer])`
`end`

`defp process_options(options, nodes) do`
`case options do`
`{[requests: n], [url], []} ->`
`# perform action`

`_ ->`
`do_help`

`end`
`end`
`end`
Most command line programs in Elixir will have the same general structure of taking in the arguments, parsing it, and processing them. Thanks to the pipeline operator, we can express this as such:

`args`
`|> parse_args``|> process_options`
`args`
is a tokenized list of arguments. For example, given

`% ./blitzy -n 100 http://www.bieberfever.com`
Then
`args`
is:

`["-n", "100", "http://www.bieberfever.com"]`
This list is then passed to
`parse_args/1`, which is a thin wrapper for
`OptionParser.parse/2`.
`OptionParser.parse/2`
does most of the heavy lifting.


It accepts a list of arguments and returns the parsed values, the remaining arguments and the invalid options. Let's see how to decipher this:

`OptionParser.parse(args, aliases: [n: :requests],`
`strict: [requests: :integer])`
First, we alias
`--requests`
to
`n`. This is a way to specify shorthand for switches.
`OptionParser`
expects that all switches start with
`--<switch>`, and single character switches
`-<switch>`
should be appropriated aliased. For example,
`OptionParser`
treats this as invalid:

`iex> OptionParser.parse(["-n", "100"])`
`{[], [], [{"-n", "100"}]}`
You can tell it is invalid since it is the third list that is populated. On the other hand, if you added double dashes to the switch (i.e.: the longhand version), then
`OptionParser`
happily accepts it:

`iex(d@127.0.0.1)12> OptionParser.parse(["--n", "100"])`
`{[n: "100"], [], []}`
We can also assert properties on the types of the value of the switch. The value of
`-n`
must be an integer. Hence, we specify this in the
`strict`
option as in the above listing. Note once again that we are using the longhand name of the switch.


Once we are done parsing the arguments, we can hand the results over to
`process_options/1`. In this function, we make use of the fact that
`OptionParser.parse/2`
returns a tuple with three elements, each of them a list.


Listing 8.14 With pattern matching, we can easily declare the format of arguments the program expects (lib/cli.ex)

`defp process_options(options) do`
`case options do`
`{[requests: n], [url], []} -> #1`
`# To be implemented later.`
`_ ->`
`do_help`

`end``end`
#1 Pattern matching the exact format we expect


We also pattern match the *exact* format the program expects. Examine the pattern a little closer:

`{[requests: n], [url], []}`
Can you point out a few properties that we are asserting on the arguments? Here's mine:


1.  
`--requests`
or
`-n`
contains a single value that is also an integer.


2.  There is also a URL.


3.  There are no invalid arguments. This is specified by the empty list in the third element.


If for any reason the arguments are invalid, then we want to invoke the
`do_help`
function to present a friendly message:


Listing 8.15 Adding a simple help function when the user gets the arguments wrong (lib/cli.ex)

`defp do_help do`
`IO.puts """`
`Usage:`
`blitzy -n [requests] [url]`

`Options:`
`-n, [--requests]      # Number of requests`

`Example:`
`./blitzy -n 100 http://www.bieberfever.com`
`"""`
`System.halt(0)``end`
For now, nothing happens when the arguments are valid. Let's fill in the missing pieces now.


8.6.3        Connecting to the Nodes


We created a configuration in
`config/config.exs`
previously, specifying the master and slave nodes. How do we access the configuration from our application? Pretty simple:

`iex(1)> Application.get_env(:blitzy, :master_node)`
`:"a@127.0.0.1"`

`iex(2)>   Application.get_env(:blitzy, :slave_nodes)``[:"b@127.0.0.1", :"c@127.0.0.1", :"d@127.0.0.1"]`
Note that nodes
`b`,
`c`, and
`d`
need to be started in distributed mode with the matching names before the command
`(./blitzy -n 100 http://www.bieberfever.com`) is executed. We need to modify the
`main/1`
function in
`lib/cli.ex`:


Listing 8.16 Modifying main to read from the configuration file (lib/cli.ex)

`defmodule Blitzy.CLI do`

`def main(args) do`
`Application.get_env(:blitzy, :master_node) #1`
`|> Node.start                            #1`

`Application.get_env(:blitzy, :slave_nodes) #2`
`|> Enum.each(&Node.connect(&1))          #2`

`args`
`|> parse_args`
`|> process_options([node|Node.list])     #3`
`end`
`end`
#1 Start the master node in distributed mode


#2 Connect to the slave nodes


We read the configuration from
`config/config.exs`. First, we start the master node in distributed mode, and assign it the name
`a@127.0.0.1`. Next, we connect to the slave nodes. Then, we pass the list of the entire cluster into
`process_options/2`, which now takes in two arguments (previously it took only one). Let's modify that next:


Listing 8.17 This function now takes in the list of nodes in the cluster, and hands it to do\_requests

`defmodule Blitzy.CLI do`
`# ...`

`defp process_options(options, nodes) do`
`case options do`
`{[requests: n], [url], []} ->`
`do_requests(n, url, nodes) #1`

`_ ->`
`do_help`

`end`
`end`
`end`
#1 The list of nodes is passed into do\_requests/3


The list of nodes is passed into the
`do_requests/3`
function, which is the main workhorse function:

`defmodule Blitzy.CLI do`
`# ...`

`defp do_requests(n_requests, url, nodes) do`
`Logger.info "Pummelling #{url} with #{n_requests} requests"`

`total_nodes  = Enum.count(nodes)             #1`
`req_per_node = div(n_requests, total_nodes)  #1`

`nodes`
`|> Enum.flat_map(fn node ->`
`1..req_per_node |> Enum.map(fn _ ->`
`Task.Supervisor.async({Blitzy.TasksSupervisor, node}, Blitzy.Worker, :start, [url])`
`end)`
`end)`
`|> Enum.map(&Task.await(&1, :infinity))`
`|> parse_results`
`end`
`end`
#1 Compute the number of workers to spawn per node


The above code is relatively terse, but fear not! We will return to it shortly. For now, let’s take a short detour and look at Task *supervisors*.


8.6.4        Supervising Tasks with Tasks.Supervisor


We do not want the crashing of a
`Task`
to bring down the entire application. This is especially so when we are spawning possibly *thousands* (or even more than that!)
`Task`
s. By now, you should know that the answer is to place the
`Task`s under supervision.


Happily, Elixir comes equipped with a
`Task`-specific supervisor aptly called
`Task.Supervisor`. This supervisor is a
`:simple_one_for_one`
supervisor where all the supervised
`Tasks`
are temporary (they are not restarted when crashed). In order to use the
`Task.Supervisor`, we need to create
`lib/supervisor.ex`:


![](../images//8_5.png)  



Figure 8.5 The supervision tree of Blitzy


Listing 8. 18 Setting up the top-level supervision tree (lib/supervisor.ex)

`defmodule Blitzy.Supervisor do`
`use Supervisor`

`def start_link(:ok) do`
`Supervisor.start_link(__MODULE__, :ok)`
`end`

`def init(:ok) do`
`children = [`
`supervisor(Task.Supervisor, [[name: Blitzy.TasksSupervisor]])`
`]`

`supervise(children, [strategy: :one_for_one])`
`end`
`end`
We create a top-level supervisor (`Blitzy.Supervisor`) that supervises a
`Task.Supervisor`, that we name
`Blitzy.TasksSupervisor`. Now, we need to start
`Blitzy.Supervisor`
when the application starts. Here is
`lib/blitzy.ex`:

`defmodule Blitzy do`
`use Application`

`def start(_type, _args) do`
`Blitzy.Supervisor.start_link(:ok)`
`end``end`
The start/2 function just starts the top-level supervisor, which will then start the rest of the supervision tree.


8.6.5        Using a Task Supervisor


Let's take a closer look at this piece of code, because it illustrates how we make use of the
`Task.Supervisor`
to spread the workload across all the nodes and how we can use
`Task.await/2`
to retrieve the results:

`nodes`
`|> Enum.flat_map(fn node ->`
`1..req_per_node |> Enum.map(fn _ ->`
`Task.Supervisor.async({Blitzy.TasksSupervisor, node}, Blitzy.Worker, :start, [url])`
`end)`
`end)`
`|> Enum.map(&Task.await(&1, :infinity))``|> parse_results`
This is probably most complicated line:

`Task.Supervisor.async({Blitzy.TasksSupervisor, node}, Blitzy.Worker, :start, [url])`
This is similar to starting a
`Task`:

`Task.async(Blitzy.Worker, :start, ["http://www.bieberfever.com"])`
However, there are a few key differences. Firstly, starting the task from a
`Task.Supervisor`
makes it, well, supervised! Secondly, take a closer look at the first argument. We are passing in a tuple containing the module name *and* the node. In order words, we are remotely telling each node's
`Blitzy.TasksSupervisor`
to spawn workers. That is super awesome!
`Task.Supervisor.async/3`
returns the same thing as
`Task.async/3`, a
`Task`
struct:

`%Task{pid: #PID<0.154.0>, ref: #Reference<0.0.3.67>}`
Therefore, we can call
`Task.await/2`
to wait for the results to be returned from each worker. Now that we have gotten the hard bits out of the way, we can better understand what this code is trying to do. Given a node, we spawn
`req_per_node`
number of workers:

`1..req_per_node |> Enum.map(fn _ ->`
`Task.Supervisor.async({Blitzy.TasksSupervisor, node}, Blitzy.Worker, :start, [url])``end)`
In order to do this on all the nodes, we have to somehow *map* through all the nodes. We *could* use
`Enum.map/2`:

`nodes`
`|> Enum.map(fn node ->`
`1..req_per_node |> Enum.map(fn _ ->`
`Task.Supervisor.async({Blitzy.TasksSupervisor, node}, Blitzy.Worker, :start, [url])`
`end)``end)`
However, this result would be a nested list of
`Task`
structs because the result of the inner
`Enum.map/2`
is list of
`Task`
structs. Instead, what we want is
`Enum.flat_map/2`, which looks like this, which takes a arbitrarily nested list, flattens the list then applies a function to each of the elements on the flattened list. The following diagram illustrates:


![](../images//8_7.png)  



Figure 8.7 Here, we are using flatmap to flatten the list of Task Structs, then mapping each Task Struct to the Blitzy Task Supervisor


Here’s the code:

`nodes`
`|> Enum.flat_map(fn node ->`
`1..req_per_node |> Enum.map(fn _ ->`
`Task.Supervisor.async({Blitzy.TasksSupervisor, node}, Blitzy.Worker, :start, [url])`
`end)``end)`
Since now we have a *flattened* list of
`Task.Struct`s, we can hand it to
`Task.await/2`:

`nodes`
`|> Enum.flat_map(fn node ->`
`# A list of Task structs`
`end) # A list of Task structs (due to flat map)`
`|> Enum.map(&Task.await(&1, :infinity))``|> parse_results`
`Task.await/2`
essentially does the collection of the results from all the nodes from the master node. Once done, we hand over the list the
`parse_results/1`
as before.


8.6.6        Creating the binary with mix escript.build


Almost there! The last step is to generate the binary. In the project directory, run the following
`mix`
command:


Listing 8.19 Building the executable

`% mix escript.build`
`Compiled lib/supervisor.ex`
`Compiled lib/cli.ex`
`Generated blitzy app``Generated escript blitzy with MIX_ENV=dev`
The last line tells you that the
`blitzy`
binary has been created. If you list all the files in your directory, you will find
`blitzy`:


Listing 8.20 The blitzy binary is generated after running mix escript.build

`% ls`
`README.md      blitzy         deps           lib            mix.lock       test``_build         config         erl_crash.dump mix.exs        priv`
8.6.7        Running Blitzy!


Finally! Before we start the binary, we have to start *three* other nodes. Recall that these are the slave nodes. In three separate terminals, start the slave nodes:

`% iex --name b@127.0.0.1 -S mix`

`% iex --name c@127.0.0.1 -S mix`
`% iex --name d@127.0.0.1 -S mix`
Now, we can run
`blitzy`! In another terminal, run the
`blitzy`
command:

`% ./blitzy -n 10000 http://www.bieberfever.com`
You will see all four terminals populated with messages like:

`10:34:17.702 [info]  worker [b@127.0.0.1-#PID<0.2584.0>] completed in 58585.746 msecs`
Here's an example on my machine:


![](../images//8_7a.png)  



Figure 8.7 Running Blitzy on my machine


Finally, when everything is done, the result will be reported on the terminal you launched the
`./blitzy`
command:

`Total workers    : 10000`
`Successful reqs  : 9795`
`Failed res       : 205`
`Average (msecs)  : 31670.991222460456`
`Longest (msecs)  : 58585.746``Shortest (msecs) : 3141.722`
8.7           Summary


In this chapter, we managed to get a broad overview of what distributed Elixir can offer. Here's the quick rundown:


·      The built-in functions that Elixir and the Erlang VM provide to build distributed systems


·      Implement a distributed applications that demonstrates load-balancing


·      Learn how to use Tasks for short-lived computation


·      Implement a command line application


In the next chapter, we continue with our adventures on distribution. We explore how distribution and fault tolerance go hand-in-hand.





