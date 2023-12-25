# 9   Distribution and Fault Tolerance


This chapter covers:


·      Implementing a distributed and fault-tolerant application


·      Cookies and Security


·      Connecting to nodes in a Local Area Network (LAN)


In the previous chapter, we looked at the basics of distribution in Elixir. In particular, we now know how to set up a cluster. We also looked at *Tasks*, which are an abstraction over GenServers that make it easy to write short-lived computations.


The next concept that we are going to explore is fault tolerance with respect to distribution. For this, we will be building an application that will demonstrate how a cluster handles failures by having another node automatically stepping up to take the place of a downed node. To take things further, it will also demonstrate how a node yields control when a previously downed node of higher priority rejoins the cluster. In other words, we will build an application that demonstrates the *failover* and *takeover* capabilities of distributed Elixir.


9.1           Distribution for Fault Tolerance


Failover happens when a node running an application goes down, and that application is being restarted on another node automatically, given some time-out period. Takeover happens when a node has a higher priority (defined in a list) than the currently running node, causing the lower priority node to stop and the application be restarted in the higher priority node. Failovers and takeovers are very cool (in programming, at least) when you see them in action.


An Overview of Chucky the Chuck Norris Facts Application


The application we are going to build is going to be deliberately simple, since the main objective is to learn how to wire up your OTP application to be fault-tolerant using failovers and takeovers. We will build *Chucky*, a distributed and fault-tolerant Chuck Norris "facts" application. This is an example run of Chucky:

`iex(1)> Chucky.fact`
`"Chuck Norris’s keyboard doesn’t have a Ctrl key because nothing controls Chuck Norris."`

`iex(2)> Chucky.fact``"All arrays Chuck Norris declares are of infinite size, because Chuck Norris knows no bounds."`
9.2           Building Chucky


Chucky is a simple OTP application. The meat of the application lies in a GenServer. We will first build that, followed by implementing the Application behavior. Finally, we will see for ourselves how to hook everything up to make use of failover and takeover.


9.2.1        Implementing the Server


You know the drill:

`% mix new chucky`
Next, create
`lib/server.ex`:


Listing 9.1 Implementing the main Chucky server (lib/server.ex)

`defmodule Chucky.Server do`
`use GenServer`

`#######`
`# API #`
`#######`

`def start_link do`
`GenServer.start_link(__MODULE__, [], [name: {:global, __MODULE__}]) #1`
`end`

`def fact do`
`GenServer.call({:global, __MODULE__}, :fact)                        #2`
`end`

`#############`
`# Callbacks #`
`#############`

`def init([]) do`
`:random.seed(:os.timestamp)`
`facts = "facts.txt"`
`|> File.read!`
`|> String.split("\n")`

`{:ok, facts}`
`end`

`def handle_call(:fact, _from, facts) do`
`random_fact = facts`
`|> Enum.shuffle`
`|> List.first`

`{:reply, random_fact, facts}`
`end`
`end`
#1 Globally register the GenServer within the cluster


#2 Calls (and casts) to a globally registered GenServer have an extra :global


Most of the code here should not be too hard to understand, although the usage of
`:global`
in
`Chucky.Server.start_link/0`
and
`Chucky.Server.fact/1`
is new. In
`Chucky.Server.start_link/0`, we register the name of the module using
`{:global, __MODULE__}`. This has the effect of registering
`Chucky.Server`
onto the
`global_name_server`
process. This process is started each time a node starts. This means that there isn't single "special" node that keeps track of the name tables. Instead, each node will have a replica of the name tables.


Since we have globally registered this module, calls (and casts) also have to be prefixed with
`:global`. Therefore, instead of writing

`def fact do`
`GenServer.call(__MODULE__, :fact)``end`
We do:


 

`def fact do`
`GenServer.call({:global, __MODULE__}, :fact)``end`
The
`init/1`
callback reads a file called
`facts.txt`, splits it up based on newlines, and initializes the state of
`Chucky.Server`
to be the list of "facts". Store
`facts.txt`
in the project root directory. You can grab a copy of the file from the project's GitHub repository.


The
`handle_call/3`
callback simply picks a random entry from its state (the list of "facts”), and returns it.


9.2.2        Implementing the Application Behavior


Next, we will implement the Application behavior that will serve as the entry point to the application. In addition, instead of creating an explicit supervisor, we can create one from within
`Chucky.start/2`. This is done by importing
`Supervisor.Spec`
that exposes the
`worker/2`
function (which creates the child specification) that we can pass into the
`Supervisor.start_link`
function at the end of
`start/2`. Create
`lib/chucky.ex`:


Listing 9.2 Implementing the Application behavior (lib/chucky.ex)

`defmodule Chucky do`
`use Application`
`require Logger`

`def start(type, _args) do`
`import Supervisor.Spec`
`children = [`
`worker(Chucky.Server, [])`
`]`

`case type do`
`:normal ->`
`Logger.info("Application is started on #{node}")`

`{:takeover, old_node} ->`
`Logger.info("#{node} is taking over #{old_node}")`

`{:failover, old_node} ->`
`Logger.info("#{old_node} is failing over to #{node}")`
`end`

`opts = [strategy: :one_for_one, name: {:global, Chucky.Supervisor}]`
`Supervisor.start_link(children, opts)`
`end`

`def fact do`
`Chucky.Server.fact`
`end`
`end`
This is a simple supervisor that supervises
`Chucky.Server`. Just like
`Chucky.Server`,
`Chucky.Supervisor`
is also globally registered, and therefore is registered with
`:global`.


9.2.3        Application type arguments


Notice that we are using the
`type`
argument of
`start/2`, which we usually ignore. For non-distributed applications, the value of
`type`
is usually
`:normal`. It is when we start playing with takeover and failover when things start to get a little interesting.


If you look up the Erlang documentation on the data types that
`type`
expects, you will see this:


![](../images//9_0.png)  



This are exactly the three cases that we pattern match for in the above code listing. The pattern match succeeds for the
`{:takeover, node}`
and
`{:failover, node}`
if the application is started in distribution-mode.


Without going into too much detail (that happens in the next section), when a node gets started because it is taking over another node (because it has higher priority), then
`node`
in
`{:takeover, node}`
is the node being taken over.


In a similar vein, when a node gets started because another node dies, then
`node`
`{:failover, node}`
is the node that died. Up till now, we haven't done any failover or takeover specific code yet. We tackle that next.


9.3           An Overview of Failover and Takeover in Chucky


Before we go into the specifics, let's talk about the *behavior* of the cluster. In this example, we will configure a cluster of three nodes. For ease of reference, and mostly due to a lack of imagination on the author's part, we will name the nodes
`a@<host>`,
`b@<host>`
and
`c@< host>`, where
`<host>`
 is your hostname. I will refer to all the nodes by
`a`,
`b`
and
`c`
for the remaining of this section.


Node
`a`
will be the master node, while
`b`
and
`c`
will be the slave nodes. In the figures that follow, the node with a green ring is the master node. The remaining ones are the slave nodes.


The *order* in which the nodes are started matters. In this case,
`a`
starts first, followed by
`b`
and
`c`. The cluster is fully initialized when all the nodes have started. In other words, only
`a`,
`b`
and
`c`
are initialized, the cluster will then be usable.


All three nodes have Chucky *compiled* (this is an important detail). However, when the cluster starts, only *one* application is started, and it is started on the master node (surprise!). This means that while the requests can be made from any node in the cluster, only the master node serves back that request:


![](../images//9_1.png)  



Figure 9.1 All requests are handled by a@host, no matter which node receives the request


Now let's make things interesting. When
`a`
fails, the remaining nodes will, after some time detect that
`a`
has failed. It will then spin up the application on one of the slave nodes. In this case,
`b`:


![](../images//9_2.png)  



Figure 9.2 Assuming a@host fails. Within 5 seconds, a failover node will take over (See next figure)


![](../images//9_3.png)  



Figure 9.3 b@host takes over automatically once it has been detected that a@host has failed


What if
`b`
fails? Then
`c`
is next in line to spin up the application. So far, what we have covered are failover situations.


Now, consider something more interesting. What happens when
`a`
restarts? Since
`a`
is the master node, it has the *highest priority* amongst the rest of the nodes. Therefore, it will initiate a *takeover*:


![](../images//9_4.png)  



Figure 9. 4 Once a@host is back, it will initiate a takeover


Whichever slave node is running the application will exit, and yield control to the master node. How awesome is that? Now, we can see how we can implement failover and takeover strategies in Chucky.


9.3.1        Configuring Failover and Takeover


In this section, we will see the steps needed to configure your distributed application for failover and takeover.


Step 1: Determine the hostname(s) of the machine(s)


The first step is to find out the hostname of the machine(s) that you are going to be on. For example, on my Mac OSX:

`% hostname –s`
`manticore`
Step 2: Create configuration files for each of the nodes


The second step would be to create configuration files for each of your nodes. To keep it simple, create these three files in the
`config`
directory:


`·`
`a.config`


`·`
`b.config`


`·`
`c.config`


Notice that they are named
`<name-of-node>.config`. While you are free to give it any file name you like, I suggest you stick to this convention since each file will contain node-specific configuration details.


Step 3: Filling up the configuration files for each of the nodes


The configuration file for each node looks slightly complicated in structure, but we will examine it a little more closely in a moment. For now, enter this in
`config/a.config`:


Listing 9. 3 The configuration for a@host (config/a.config)

`[{kernel,`
`[{distributed, [{chucky, 5000, [a@manticore, {b@manticore, c@manticore}]}]},`
`{sync_nodes_mandatory, [b@manticore, c@manticore]},`
`{sync_nodes_timeout, 30000}``]}].`
This represents the configuration needed to configure failover/takeover for a single node. Let's break it down. We start with the most complicated part, the
`distributed`
configuration parameter:

`[{distributed, [{chucky, 5000, [a@manticore, {b@manticore, c@manticore}]}]}]`
`chucky`
is of course the application name.
`5000`
represents the timeout in milliseconds before the node is considered down the application is restarted in the next highest priority node.


`[a@manticore, {b@manticore, c@manticore}]`
lists the nodes in priority. In this case,
`a`
is first in line, followed by *either*
`b`
or
`c`. Nodes defined in a tuple do not have a priority amongst themselves. For example, consider the following entry:

`[a@manticore, {b@manticore, c@manticore}, d@manticore]`
In this case, the highest priority is
`a`, then
`b/c`, followed by
`d`.


·     
`sync_nodes_mandatory`: The list of nodes that *must* be started within the time specified by
`sync_nodes_timeout`


·     
`sync_nodes_optional`: The list of nodes that *can* be started within the time specified by
`sync_nodes_timeout`. (Note that we are not using this option for this application)


·     
`sync_nodes_timeout`: How long to wait for the other nodes to start (in milliseconds)


What's the difference of
`sync_nodes_mandatory`
and
`sync_nodes_optional`? As its name suggests, the node being started will wait for all the nodes in
`sync_nodes_mandatory`
to start up, within the timeout limit set by
`sync_nodes_timeout`. If even one fails to start, the node terminates itself. The case is not so strict for
`sync_nodes_optional`. The node will just wait till the timeout elapses, and will *not* terminate itself if any node is not up.


Configuring the Slave Nodes


For the remaining nodes, the configuration is *almost* the same, except for the
`sync_nodes_mandatory`
entry. In fact, it is *very* important that the rest of the configuration is unchanged. For example, having an inconsistent
`sync_nodes_timeout`
value would lead to undetermined behavior of the cluster.


Here's the configuration for
`b`:


Listing 9.4 The configuration for b@host (config/b.config)

`[{kernel,`
`[{distributed,`
`[{chucky,`
`5000,`
`[a@manticore, {b@manticore, c@manticore}]}]},`
`{sync_nodes_mandatory, [a@manticore, c@manticore]},`
`{sync_nodes_timeout, 30000}``]}].`
And here's the configuration for
`c`:


Listing 9.5 The configuration for c@host (config/c.config)

`[{kernel,`
`[{distributed,`
`[{chucky,`
`5000,`
`[a@manticore, {b@manticore, c@manticore}]}]},`
`{sync\_nodes\_mandatory, [a@manticore, b@manticore]},`
`{sync\_nodes\_timeout, 30000}``]}].`
Step 4: Compile Chucky on all the Nodes


The application should be compiled on machine it is on. Compiling
`Chucky`
is easy enough:

`% mix compile`
Once again, remember to do this on *every machine* of the cluster.


Step 5: Start the Distributed Application


Open three different terminals. On each of them, run these commands:


For
`a`:

`% iex --sname a -pa _build/dev/lib/chucky/ebin --app chucky --erl "-config config/a.config"`
Next, for
`b`:

`% iex --sname b -pa _build/dev/lib/chucky/ebin --app chucky --erl "-config config/b.config"`
Finally, for
`c`:

`% iex --sname c -pa _build/dev/lib/chucky/ebin --app chucky --erl "-config config/c.config"`
The above incantation is slightly cryptic, but still decipherable:


·     
`--sname <name>`: Starts a distributed node, and assigns a *short name* to it.


·     
`-pa <path>`: *Prepends* the given path to the Erlang code path. This path points to the BEAM files generated from Chucky after running
`mix compile`. (The *appends* version is
`-pz`.)


·     
`--app <application>`: Starts the application along with its dependencies.


·     
`--erl <switches>`: Switches passed down to Erlang. In our example,
`-config config/c.config`
is used to configure OTP applications.


9.4           Failover and Takeover in Action


After all that hard work, let's see some action! You will notice that when you started
`a`
(and even
`b`), nothing happens until
`c`
is started. In each terminal, run
`Chucky.fact`:


Listing 9.6 Chucky can be accessed from any node in the cluster

`23:10:54.465 [info]  Application is started on a@manticore`
`iex(a@manticore)1> Chucky.fact`
`"Chuck Norris doesn't read, he just stares the book down untill it tells him what he wants."`

`iex(b@manticore)1> Chucky.fact`
`"Chuck Norris can use his fist as his SSH key. His foot is his GPG key."`

`iex(c@manticore)1> Chucky.fact``"Chuck Norris never wet his bed as a child. The bed wet itself out of fear."`
While it *seems* that the application is running on each individual node, we can easily convince ourselves that this is not the case. Notice that in the first terminal, the message
`Application is started on a@manticore`
is printed out on
`a`, but not the others.


There is another way to tell what applications are running on the current node. With
`Application.started_applications/1`, we can clearly see that
`Chucky`
is running on
`a`:


Listing 9.7 Application.started\_applications/0 shows Chucky on a@host

`iex(a@manticore)1> Application.started_applications`
`[{:chucky, 'chucky', '0.0.1'}, {:logger, 'logger', '1.1.1'},`
`{:iex, 'iex', '1.1.1'}, {:elixir, 'elixir', '1.1.1'},`
`{:compiler, 'ERTS  CXC 138 10', '6.0.1'}, {:stdlib, 'ERTS  CXC 138 10', '2.6'},``{:kernel, 'ERTS  CXC 138 10', '4.1'}]`
However, it
`Chucky`
is *not* running on
`b`
and
`c`. Only the output of
`b`
is shown here, since the output on both nodes is identical:


Listing 9.8 Chucky is not running on b@host and c@host (not shown)

`iex(b@manticore)1> Application.started_applications`
`[{:logger, 'logger', '1.1.1'}, {:iex, 'iex', '1.1.1'},`
`{:elixir, 'elixir', '1.1.1'}, {:compiler, 'ERTS  CXC 138 10', '6.0.1'},``{:stdlib, 'ERTS  CXC 138 10', '2.6'}, {:kernel, 'ERTS  CXC 138 10', '4.1'}]`
Now, let's terminate
`a`
by exiting
`iex`
(entering Ctrl + C twice). In about 5 seconds, you will notice that
`Chucky`
has now automatically started in
`b`:


Listing 9.9 When a@host goes down, b@host takes over

`iex(b@manticore)1>`
`23:16:42.161 [info]  Application is started on b@manticore`
How awesome is that? The remaining nodes in the cluster determined that
`a`
was unreachable and presumed dead. Therefore,
`b`
assumed the responsibility of running
`Chucky`. If you now run
`Application.started_applications/1`
on
`b`, you would see something like:


Listing 9.10 Re-running Application.started\_applications/0 now shows Chucky on b@host

`iex(b@manticore)2> Application.started_applications`
`[{:chucky, 'chucky', '0.0.1'}, {:logger, 'logger', '1.1.1'},`
`{:iex, 'iex', '1.1.1'}, {:elixir, 'elixir', '1.1.1'},`
`{:compiler, 'ERTS  CXC 138 10', '6.0.1'}, {:stdlib, 'ERTS  CXC 138 10', '2.6'},``{:kernel, 'ERTS  CXC 138 10', '4.1'}]`
On
`c`, you can convince yourself that
`Chucky`
is still running:


Listing 9.11 As usual, Chucky can still be accessed from c@host

`iex(c@manticore)1> Chucky.fact`
`"The Bermuda Triangle used to be the Bermuda Square, until Chuck Norris Roundhouse kicked one of the corners off."`
Now, let's see some takeover in action. What happens when
`a`
rejoins the cluster? Since
`a`
is the highest priority node in the cluster,
`b`
will yield control to
`a`. In other words,
`a`
will takeover
`b`. Start
`a`
again:

`% iex --sname a -pa _build/dev/lib/chucky/ebin --app chucky --erl "-config config/a.config"`
In
`a`, you will see something like:

`23:23:36.695 [info]  a@manticore is taking over b@manticore`
`iex(a@manticore)1>`
In
`b`, you will notice that the application has stopped:


Listing 9.12 When a@host restarts and rejoins the cluster, b@host yields control

`iex(b@manticore)3>`
`23:23:36.707 [info]  Application chucky exited: :stopped`
Of course,
`b`
can still dish out some Chuck Norris facts:

`iex(b@manticore)4> Chucky.fact`
`"It takes Chuck Norris 20 minutes to watch 60 Minutes."`
There you have it! We have seen one complete cycle of failover and takeover. In the next section, we will look at connecting nodes that are in the same local area network.


9.5           Connecting Nodes in a LAN, Cookies and Security


Security wasn’t a huge thing on the minds of Erlang designers when they were thinking about distribution. The reason for that was that the nodes were going to be used in their own internal/trusted networks. As such, things were kept pretty simple.


In order for two nodes to communicate, all they need to do is share a *cookie*. This cookie is a plain text file stored usually in your home directory:

`% cat ~/.erlang.cookie`
`XLVCOLWHHRIXHRRJXVCN`
When you start nodes on the same machine, you didn’t have to worry about cookies because all the nodes shared the same cookie in your home directory. However, once you start connecting to other machines, you will have to ensure that these cookies are all the same. There is an alternative though. You can also explicitly call
`Node.set_cookie/2`. In this section, we will see how we can connect to nodes that are not on the same machine, but on the same local network.


9.5.1        Find out the IP Addresses of both machines


First, we need to find out the IP addresses of both machines. On Linux/Unix systems, that's usually
`ifconfig`. Also, do make sure that they both are connected to the same LAN. This could mean either plugging the machines into the same router/switch or having the machines connected to the same wireless endpoint. Here is a sample output on one of my machines:


Listing 9.13 The output of ifconfig on my machine

`% ifconfig`
`lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 16384`
`options=3<RXCSUM,TXCSUM>`
`inet6 ::1 prefixlen 128`
`inet 127.0.0.1 netmask 0xff000000`
`inet6 fe80::1%lo0 prefixlen 64 scopeid 0x1`
`nd6 options=1<PERFORMNUD>`
`gif0: flags=8010<POINTOPOINT,MULTICAST> mtu 1280`
`stf0: flags=0<> mtu 1280`
`en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500`
`ether 10:93:e9:05:19:da`
`inet6 fe80::1293:e9ff:fe05:19da%en0 prefixlen 64 scopeid 0x4`
`inet 192.168.0.100 netmask 0xffffff00 broadcast 192.168.0.255`
`nd6 options=1<PERFORMNUD>`
`media: autoselect``status: active`
The numbers you should be looking out for is
`192.168.0.100`. When I performed the same steps on the other machine, the IP address is
`192.168.0.103`. Do note that we are using IPv4 addresses here. If you were using IPv6 addresses you would have to use the IPv6 addresses for the following examples.


9.5.2        Connecting both Nodes together


Let's give this a go. On the first machine, start
`iex`
but this time with the long name (`--name`) flag. Also, append
`@<ip-address>`
after the name.

`% iex --name one@192.168.0.100`
`Erlang/OTP 18 [erts-7.1] [source] [64-bit] [smp:4:4] [async-threads:10] [hipe] [kernel-poll:false] [dtrace]`

`Interactive Elixir (0.13.1-dev) - press Ctrl+C to exit (type h() ENTER for help)``iex(one@192.168.0.100)1>`
Perform the same steps on the second node:

`% iex --name two@192.168.0.103`
`Erlang/OTP 18 [erts-7.1] [source] [64-bit] [smp:4:4] [async-threads:10] [hipe] [kernel-poll:false] [dtrace]`

`Interactive Elixir (1.1.1) - press Ctrl+C to exit (type h() ENTER for help)``iex(two@192.168.0.103)1>`
Now, let's try to connect
`one@192.168.0.100`
and [`two@192.168.0.103`](mailto:two@192.168.0.103) together:

`iex(one@192.168.0.100)1> Node.connect :'two@192.168.0.103'`
`false`
Wait what? On
`two@192.168.0.103`, you would be able to see a similar error report:

`=ERROR REPORT==== 25-May-2014::22:32:25 ===`
`** Connection attempt from disallowed node 'one@192.168.0.100' **`
What happened? Turns out, we are missing a key ingredient – The *cookie*.


9.5.3        Remember the Cookie!


When you connect nodes on the same machine *and* you do not set any cookie with the
`--cookie`
flag, the Erlang VM simply uses the generated one that sits in your home directory:

`% cat ~/.erlang.cookie`
`XBYWEVWSNBAROAXWPTZX%`
This means that if you connect nodes *without* the cookie flag on the *same* local machine, you usually will not hit into any problems.


On different machines however, this *is* a problem. That's because the cookies are most likely different across the various machines. With this in mind, let's restart the entire process. This time however, we supply the same cookie value for every node. Alternatively, you can either copy the same
`.~/.erlang-cookie`
across all the nodes. In this section, we use the former technique. On the first machine:

`% iex --name one@192.168.0.100 --cookie monster`
`Erlang/OTP 18 [erts-7.1] [source] [64-bit] [smp:4:4] [async-threads:10] [hipe] [kernel-poll:false] [dtrace]`

`Interactive Elixir (1.1.1) - press Ctrl+C to exit (type h() ENTER for help)``iex(one@192.168.0.100)1>`
On the second machine, we make sure we use the *same* cookie value:

`% iex --name two@192.168.0.103 --cookie monster`
`Erlang/OTP 18 [erts-7.1] [source] [64-bit] [smp:4:4] [async-threads:10] [hipe] [kernel-poll:false] [dtrace]`

`Interactive Elixir (1.1.1) - press Ctrl+C to exit (type h() ENTER for help)``iex(two@192.168.0.103)1>`
Let's connect
`one@192.168.0.100`
to
`two@192.168.0.103`
again:

`iex(one@192.168.0.100)1> Node.connect :'two@192.168.0.103'`
`true`
Great success! We have successfully set up an Elixir cluster over a LAN. As a sanity check, we can also do a
`Node.list/0.`
Recall that this function only lists its neighbors and therefore doesn’t include the current node:

`iex(one@192.168.0.100)2> Node.list`
`[:"two@192.168.0.103"]`
9.6           Summary


Having proper failover and takeover implemented in an application that is expected to survive crashes is absolutely essential. Unlike a lot of languages and platforms, failover and takeover are baked into OTP. In this chapter, we continued our explorations in distribution. In particular, we covered:


·      Implement a distributed application that demonstrates failover and takeover


·      Configure for failover and takeover


·      Connect nodes to a local area network (LAN)


·      Make use of cookies


·      A few Chuck Norris jokes


In the next chapter and the chapter after that, we look at testing in Elixir. Instead of covering unit testing, we explore property-based testing and also learn how to test concurrent programs.





