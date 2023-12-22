xml version='1.0' encoding='utf-8'?



Style A ReadMe





# 6      Fault Tolerance with Supervisors


This chapter covers:


·      How to use the OTP Supervisor behavior


·      Learn how to use ETS, Erlang Term Storage


·      How to use supervisors with normal processes and other OTP behaviors


·      Implementing a very basic worker pool application


In the previous chapter, we built a naïve supervisor made from primitives provided by the language, namely, monitors, links and processes. That should give you a good understanding of how supervisors work under the hood.


After teasing you in the previous chapter, we are finally going to use the real thing: The *OTP Supervisor behavior* (henceforth simply referred to as Supervisor). The sole responsibility of a supervisor is to observe and check if an attached child process goes down and take some action if it happens.


The OTP version offers a few more bells and whistles from our previous implementation. Take *restart strategies* for example, which dictates how a supervisor should restart the children if something goes wrong. It also offers options too for limiting the number of restarts within a specific timeframe. This is especially useful for preventing infinite restarts.


To *really* understand supervisors, it is important to try them out for yourself. Therefore, instead of boring you with every single supervisor option, we are going to build this application (presented in its full glory courtesy of the *Observer* application:


![](../Images/6_1.png)  



Figure 6.1 The completed worker pool application


Figure 6.1 shows the completed worker pool application. #1 is the top-level
`Supervisor`. It supervises #2, another
`Supervisor`
(`PoolsSupervisor`), and a
`GenServer`
(`Pooly.Server`), #3.
`PoolsSupervisor`
in turn supervises three other
`PoolSupervisor`s. One of them is marked as #4. These supervisors have unique names. Each
`PoolSupervisor`
in turn supervises a worker supervisor #5 (represented by its process id) and a GenServer #6. Finally, #7 are the actual workers doing the grunt work. If you are wondering what the
`GenServer`’s are for, they are primarily needed to maintain state for the supervisor “at the same level”. For example, the
`GenServer`
at #6 helps maintain the state for the supervisor at #5.


6.1           Implementing Pooly – a Worker Pool Application


We are going to build a worker pool over the course of two chapters. What is a worker pool, you say? It is something that manages a pool (surprise!) of workers. The reason you want this might be to manage access to a scarce resource. It could be anything from a pool of Redis connections, web socket connections and even a pool of GenServer workers.


For example, if you spawn one million processes, and each process needs a connection to the database. It is impractical to open one million database connections. To get around this, a pool of database connections is created. Each time a process needs a database connection it will issue a request to the pool. Once the process is done with the database connection, it is returned back to the pool. In effect, resource allocation is delegated to the worker pool application.


The worker pool application that we are will build is *not* trivial at all. In fact, if you are familiar with Poolboy, a lot of the design has been adapted for this example. No worries if you have not heard or used Poolboy, it is not a prerequisite.


I believe this is a very rewarding exercise, because it gets you thinking about concepts and issues that would otherwise not come up in simpler examples. You will get hands on with the Supervisor API too.


As such, this example may be slightly more challenging than the previous examples so far. Some of the code/design might not be obvious, but mostly because you didn’t have the benefit of hindsight. But fret not, dear reader, for you will be guided every step of the way. All I ask is work through the code by typing it on your computer, and await enlightenment by the end of the next chapter!


6.1.1        The Plan


We will evolve the design of Pooly through four versions. This chapter covers the fundamentals of Supervisor, and get you building a very basic version (version 1) of Pooly. The following chapter would be completely focused on building the various features of Pooly.


Table 6.1 lists the characteristics of each version of Pooly:




|  |  |
| --- | --- |
| 
Version
 | 
Characteristics
 |
| 1 | Supports a *single* pool
Supports a *fixed* number of workers
No recovery when consumer and/or worker process fail |
| 2 | Same as version 1
Recovery when consumer and/or worker process fail |
| 3 | Supports *multiple* pools
Supports a *variable* number of workers |
| 4 | Same as version 3
Variable sized pool that allows for overflowing of workers
Queuing for consumer processes when all workers are busy |


Table 6. 1 The different changes that Pooly will undergo across four versions


To have an idea of how the design will evolve, version 1 and 2 looks like:


![](../Images/6_2.png)  



Figure 6.2 Version 1 and 2 of Pooly


Rectangles represent
`Supervisor`s, ovals represent
`GenServer`s and circles represent the worker processes. In version 3 and version 4, the design will evolve like so:


![](../Images/6_3.png)  



Figure 6.3 Version 3 and 4 of Pooly


From the diagram, it should be obvious why it’s called a supervision *tree*.


6.1.2        A Sample Run of Pooly


Before we get into the actual coding, it is instructive to see how to use Pooly. This covers the first version of Pooly.


Starting a Pool


In order to start a pool, it must be given a *pool configuration*. It provides the information needed for Pooly to initialize the pool. This is what it looks like:

`pool_config = [`
`mfa: {SampleWorker, :start_link, []},`
`size: 5``]`
This tells the pool to create *five*
`SampleWorker`s. To start the pool:

`Pooly.start_pool(pool_config)`
Checking Out Workers


In Pooly lingo, *checking out* workers means requesting and getting a worker from the pool. The return value is a pid of an available worker.

`worker_pid = Pooly.checkout`
Once a *consumer process* has gotten hold of a
`worker_pid`, it can do whatever it wants with it. What happens if there are no more workers available? For now,
`:noproc`
is returned. We will have more sophisticated ways of handling this in later versions.


Checking in Workers Back to the Pool


Once a consumer process is done with the worker, it must return it to the pool, also known as checking in a worker. Checking in a worker is straightforward:

`Pooly.checkin(worker_pid)`
Getting the status of a pool


It is useful to get some useful information from the pool.

`Pooly.status`
For now, this returns a tuple such as
`{3, 2}`. This means that there are three free workers and two busy ones. That concludes the short tour of the API.


6.1.3        Diving into Pooly, Version 1: Laying the Groundwork


Go to your favorite directory and create a new project with
`mix`:

`% mix new pooly`

A note about the source code



The different versions of this project for this chapter have been split into different branches. For example, to checkout version 3,
`cd`
into the project folder and do a
`git checkout version-3`.



 




mix and the --sup option



You might be aware that
`mix`
includes an option called
`--sup`. This option generates an OTP application skeleton including a supervision tree. If this option is left out, the application is generated *without* a supervisor and application callback. For example, you might be tempted to create Pooly like so:

`% mix new pooly --sup`
However, since we are learning, we shall opt for the flag-less version.



 



The very first version of Pooly will only support a single pool of fixed workers. Furthermore, there will be no recovery handling when either the consumer or worker process fails. By the end of this version, Pooly will look like:


![](../Images/6_4.png)  



Figure 6. 4 Version 1 of Pooly


As you can see, the application consists of a top-level supervisor (`Pooly.Supervisor`) that supervises two other processes, a GenServer process (`Pooly.Server`) and a worker supervisor (`Pooly.WorkerSupervisor`). You might recall from the previous chapter that supervisors can themselves be supervised, since supervisors themselves processes.



How do I even start?



Whenever I am designing Elixir programs with possibly many supervision hierarchies, I will always produce a sketch first. That’s because (as you will find out soon enough) there are quite a few things to keep quite a few things in your head. Probably more so than other languages, you must already have a rough design in your head, which forces you to think slightly ahead.



 



When Pooly first starts, only
`Pooly.Server`
is attached to
`Pooly.Supervisor`.  When the pool is started with pool configuration,
`Pooly.Server`
first verifies that the pool configuration is valid.


After that, it sends a
`:start_worker_supervisor`
to
`Pooly.Supervisor`. This message instructs
`Pooly.Supervisor`
to start
`Pooly.WorkerSupervisor`. Finally,
`Pooly.WorkerSupervisor`
is told to start a number of worker processes based on the
`size`
specified in the pool configuration.


The following diagram illustrates how Pooly version 1 works:


![](../Images/6_2a.png)  



Figure 6. 2 How the various components of Pooly are initialized


6.2           Implementing the Worker Supervisor


We will first create a worker supervisor. This supervisor would be in charge of monitoring all the spawned workers in the pool. Create
`worker_supervisor.ex`
in
`lib/pooly`. Just like a GenServer behavior (or *any* other OTP behavior for that matter), this is how to use the Supervisor behavior:

`defmodule Pooly.WorkerSupervisor do`
`use Supervisor``end`
In Listing 6. 1, we define the good old
`start_link/1`
function that serves as the main entry point when creating a supervisor process. The
`start_link/1`
function that we define is a wrapper function that calls
`Supervisor.start_link/2`, passing in the module name and the arguments.


Just like GenServer, when you define
`Supervisor.start_link/2`, you should then implement the corresponding
`init/1`
callback function next. Whatever arguments passed to
`Supervisor.start_link/2`
would be then passed along to the
`init/1`
callback:


Listing 6.1 lib/pooly/worker\_supervisor.ex – Using pattern matching to validate and destructure arguments

`defmodule Pooly.WorkerSupervisor do`
`use Supervisor`

`#######`
`# API #`
`#######`

`def start_link({_,_,_} = mfa) do             #1`
`Supervisor.start_link(__MODULE__, mfa)`
`end`

`#############`
`# Callbacks #`
`#############`

`def init({m,f,a}) do                         #2`
`# …`
`end``end`
#1 Pattern match the arguments to make sure that the arguments are indeed a tuple containing three elements.


#2 Pattern match the individual elements from the three-element tuple.


In #1, we declare that
`start_link`
takes a three-element tuple, which would be the module, function, and list of arguments of the worker process.


Notice the beauty of pattern matching at work here. Saying
`{_,_,_} = mfa`
essentially does *two* things. First, it asserts that the input argument must be a three-element tuple. Secondly, the input argument is referenced by
`mfa`. We *could* have done written it as
`{m,f,a}`
instead. However, since we are not using the individual elements, we pass along the entire tuple using
`mfa`.


`mfa`
is then passed along to the
`init/1`
callback. This time, we need to use the individual elements of the tuple, and therefore in #2 we assert that the expected input argument is
`{m,f,a}`. The
`init/1`
callback is where the actual initialization occurs.


6.2.1        Initializing the Supervisor


Let’s take a closer look at the
`init/1`
callback, where most of the interesting bits happen in a supervisor:


Listing 6.2  lib/pooly/worker\_supervisor.ex – Initializing the supervisor with a child and supervisor specification

`defmodule Pooly.WorkerSupervisor do`

`#############`
`# Callbacks #`
`#############`

`def init({m,f,a} = x) do`
`worker_opts = [restart:  :permanent,`
`function: f]`

`children = [worker(m, a, worker_opts)]`

`opts     = [strategy: :simple_one_for_one,`
`max_restarts: 5,`
`max_seconds: 5]`

`supervise(children, opts)`
`end`
`end`
Let’s learn how to decipher Listing 6. 2. In order for a supervisor to initialize its children, you must give it a *child specification*. A child specification (we covered this briefly in the previous chapter) is a recipe for the supervisor to spawn its children.


The child specification is created with
`Supervisor.Spec.worker/3`. The
`Supervisor.Spec`
module is imported by the Supervisor behavior by default, so there’s no need to supply the fully qualified version.


The return value of the
`init/1`
callback must be a *supervisor specification*. In order to construct a supervisor specification, we use the
`Supervisor.Spec.supervise/2`
function.


`supervise/2`
takes in two arguments. The first argument is a *list* of children. The second argument is a *keyword list* of options. In the code listing above, this is represented by
`children`
and
`opts`
respectively.


Before we get into defining children, let’s discuss about the *second* argument to
`supervise/2`.


6.2.2        Supervision Options


Our example defines the options to
`supervise/2`
as such:

`opts = [strategy: :simple_one_for_one,`
`max_restarts: 5,``max_seconds: 5]`
There are a few options that can be set here. The most important one is the *restart strategy*, which we will look at next.


6.2.3        Restart Strategies


Restart strategies dictate how a supervisor restarts a child/children when something goes wrong. In order to define a restart strategy, include a
`strategy`
key along with the restart strategy. There are four kinds of restart strategies:


`·`
`:one_for_one`


`·`
`:rest_for_one`


`·`
`:one_for_all`


`·`
`:simple_one_for_one`


Let’s take a quick look at all of them.


:one\_for\_one


If that process dies, only that process is restarted. All the other processes are not affected.


:one\_for\_all


Just like the three musketeers, if *any* process dies, all the processes under the supervision tree die along with it. After that, all of them are restarted again. This strategy is useful if all the processes under the supervise tree depend on each other.


:rest\_for\_one


If one of the processes dies, the rest of the processes that were started *after* that process are terminated. After that, the process that died and the rest of the child processes are restarted. Think of it like dominoes arranged in a circular fashion.


:simple\_one\_for\_one


The previous three strategies are used to build a static supervision tree. This means that the workers are specified upfront via the child specification.


In
`:simple_one_for_one`, you would specify only *one* entry in the child specification. Every child process that is spawned from this supervisor would be the *same* kind of process.


The best way to think about the
`:simple_one_for_one`
strategy is like a factory method (or a constructor in OOP languages), where the workers that are “produced” are alike.
`:simple_one_for_one`
is used when we want to dynamically create workers.


The supervisor initially starts out with empty workers. Workers are then dynamically attached to the supervisor. Next, we look at the other options that allow us to fine-tune the behavior of supervisors.


6.2.4        Max Restarts and Max Seconds


`max_restarts`
and
`max_seconds`
translate to the maximum number of restarts the supervisor can tolerate within a maximum number of seconds before it gives up and terminates.


Why have something like that in the first place? The main reason is that you do not want your supervisor to infinitely restart its children when something is genuinely wrong (programmer error?). Therefore, you might want to specify a threshold for the supervisor to give up. Note that by default,
`max_restarts`
and
`max_seconds`
are set to 3 and 5 respectively.


In the code listing above, we specify that the supervisor should give up if there are more than five restarts within five seconds.


6.2.5        Defining Children


It is now time to learn how to define children. In our code, the children is specified in a list:

`children = [worker(m, a, worker_opts)]`
What does this tell us? It says that this supervisor has one child, or one *kind* of child, in the case of a :`simple_one_for_one`
restart strategy. (It doesn’t make sense to define multiple workers when in general we do not know how many workers we want to spawn when using a
`:simple_one_for_one`
restart strategy.


The
`worker/3`
function creates a child specification for a *worker*, as opposed its sibling
`supervisor/3`. This means that if the child is *not* a supervisor, use
`worker/3`. If you are supervising a supervisor, then use
`supervise/3`. You will use both variants very soon.


Both variants take the module, arguments and options. The first two are exactly what you would expect. The third argument is more interesting.


Child Specification Default Options


By default, when you leave the options out like so

`children = [worker(m, a)]`
Elixir will supply the following options as the default:

`[id: module,`
`function: :start_link,`
`restart: :permanent,`
`shutdown: :infinity,``modules: [module]]`
function: The Start Function of the Worker


`function`
should be obvious – It’s the
`f`
of
`mfa`.  Sometimes the main entry point of a worker is some other function other than
`start_link`.  This is the place to specify the custom function to be called.


restart: Restart Value


The two restart values that we will use throughout the Pooly application are:


·     
`:permanent`
- the child process is always restarted


·     
`:temporary`
- the child process is never restarted.


In
`worker_opts`, we specified
`:permanent`. This means that any crashed worker is always restarted.


Creating a Sample Worker


In order to test this out, we need a sample worker. Create
`sample_worker.ex`
in
`lib/pooly`. Fill it in with this:


Listing 6.3 lib/pooly/sample\_worker.ex – A worker used to test Pooly

`defmodule SampleWorker do`
`use GenServer`

`def start_link(_) do`
`GenServer.start_link(__MODULE__, :ok, [])`
`end`

`def stop(pid) do`
`GenServer.call(pid, :stop)`
`end`

`def handle_call(:stop, _from, state) do`
`{:stop, :normal, :ok, state}`
`end``end`
`SampleWorker`
is a very simple GenServer that pretty much does nothing except having functions that control its lifecycle.

`iex> {:ok, worker_sup} = Pooly.WorkerSupervisor.start_link({SampleWorker, :start_link, []})`
Now, we can create a child:

`iex> Supervisor.start_child(worker_sup, [[]])`
The return value is a two-element tuple that looks like
`{:ok, #PID<0.132.0>}`. Add a few more children to the supervisor. Now, let’s see all the children that the worker supervisor is supervising using
`Supervisor.which_children/1`:

`iex> Supervisor.which_children(worker_sup)`
The result is a list that looks like:

`[{:undefined, #PID<0.98.0>, :worker, [SampleWorker]},`
`{:undefined, #PID<0.101.0>, :worker, [SampleWorker]}]`
We can also count the number of children:

`iex> Supervisor.count_children(worker_sup)`
The return result should be self-explanatory:

`%{active: 2, specs: 1, supervisors: 0, workers: 2}`
Now to see the supervisor in action! Create another child, but this time, save a reference to it:

`iex> {:ok, worker_pid} = Supervisor.start_child(worker_sup, [[]])`
`Supervisor.which_children(worker_sup)`
should look like

`[{:undefined, #PID<0.98.0>, :worker, [SampleWorker]},`
`{:undefined, #PID<0.101.0>, :worker, [SampleWorker]},``{:undefined, #PID<0.103.0>, :worker, [SampleWorker]}]`
Now, let’s stop the worker we just created:

`iex> SampleWorker.stop(worker_pid)`
Let's inspect the state of the worker supervisor's children:

`iex(8)> Supervisor.which_children(worker_sup)`
`[{:undefined, #PID<0.98.0>, :worker, [SampleWorker]},`
`{:undefined, #PID<0.101.0>, :worker, [SampleWorker]},``{:undefined, #PID<0.107.0>, :worker, [SampleWorker]}]`
Woo hoo! The supervisor automatically restarted the stopped worker! I still get a warm fuzzy feeling whenever the supervisor restarts a failed child automatically. Getting something similar in other languages usually require a lot more work. Next, we look at implementing
`Pooly.Server`.


6.3           Implementing the Server: The Brains of the Operation


Now, we will work on the brains of the operation. In general, you want to leave the supervisor with as little logic as possible, since lesser code means lesser chances of things breaking.


Therefore, we introduce a GenServer process that will handle most of the interesting logic of the application. The server process must communicate with both the top-level supervisor and the worker supervisor. One way would be to use *named processes*:


![](../Images/6_3a.png)  



Figure 6. 3 Named processes allow other processes to reference them by their name


In this case, both processes can refer to each other by their respective names. However, a more general solution would be to have the server process contain a reference to the top-level supervisor and the worker supervisor as part of its *state*.


Where will the server get the references to both supervisors? When the top-level supervisor starts the server, the supervisor can pass its own pid to the server. In fact, this is exactly what we will do when we come to the implementation of the top-level supervisor.


![](../Images/6_3b.png)  



Figure 6. 3 A reference to the supervisor is stored in the state of Pooly.Server


Now, since the server has a reference to the top-level supervisor, it can tell it to start a child using the
`Pooly.WorkerSupervisor`
module, pass in the relevant bits of the pool configuration, and
`Pooly.WorkerSupervisor`
will handle the rest.


The server process also maintains the state of the pool. We already know that the server has to store references to the top-level supervisor and the worker supervisor. What else should it store? For starters, it needs to store details about the pool such as what kind of workers to create and how many of them. The pool configuration provides this information.


6.3.1        Pool Configuration


The server accepts a pool configuration that comes in a keyword list. In this version, an example pool configuration would look like this:

`[mfa: {SampleWorker, :start_link, []}, size: 5]`
The key
`mfa`
stands for
`m`odule,
`f`unction, and list of
`a`rguments of the pool of worker(s) to be created. 
`size`
is the number of worker processes to be created.


Enough jibber-jabber[[1]](#up96ptASYY5BuP5vtTDTfHE), let’s see some code! Create a file called
`server.ex`
and place it in
`lib/pooly`.


For now, we will make
`Pooly.Server`
a *named process*, which means that we can reference the server process using the module name (i.e.
`Pooly.Server.status`
instead of
`Pool.Server.status(pid)`). Listing 6. 4 shows how this is done:


Listing 6.4 lib/pooly/server.ex – A reference to the top-level supervisor and pool configuration is passed to initialize the server process

`defmodule Pooly.Server do`
`use GenServer`
`import Supervisor.Spec`

`#######`
`# API #`
`#######`

`def start_link(sup, pool_config) do`
`GenServer.start_link(__MODULE__, [sup, pool_config], name: __MODULE__)`
`end`
`end`
The server process needs both the reference to the top-level supervisor process and the pool configuration, which we pass in as
`[sup, pool_config]`.


Now, we need to implement the
`init/1`
callback. The
`init/1`
callback has two responsibilities. The first one would be to validate the pool configuration. The second one would be to initialize the state, as all good
`init`
callbacks do.


6.3.2        Validating the Pool Configuration


A valid pool configuration looks like:

`[mfa: {SampleWorker, :start_link, []}, size: 5]`
This is a keyword list with two keys,
`mfa`
and
`size`. Any other key will be ignored. As the function goes through the pool configuration keyword list, the state is gradually built up:


Listing 6.5 lib/pooly/server.ex – Setting up the state of the server with multiple init/2 function clauses

`defmodule Pooly.Server do`
`use GenServer`

`defmodule State do                               #1`
`defstruct sup: nil, size: nil, mfa: nil`
`end`

`#############`
`# Callbacks #`
`#############`

`def init([sup, pool_config]) when is_pid(sup) do #2`
`init(pool_config, %State{sup: sup})`
`end`

`def init([{:mfa, mfa}|rest], state) do           #3`
`init(rest,  %{state | mfa: mfa})`
`end`

`def init([{:size, size}|rest], state) do         #4`
`init(rest, %{state | size: size})`
`end`

`def init([_|rest], state) do                     #5`
`init(rest, state)`
`end`

`def init([], state) do                           #6`
`send(self, :start_worker_supervisor)           #7`
`{:ok, state}`
`end`
`end`
Listing 6. 5 sets up the state of the server. #1 declares a
`struct`
that serves as a container for the server’s state.  #2 is the callback when
`GenServer.start_link/3`
is invoked.


The
`init/1`
callback receives the pid of the top level supervisor along with the pool configuration. It then calls
`init/2`, which is given the pool configuration along with a new state that contains the pid of the top-level supervisor.


Each element in a keyword list is represented by a two-element tuple, where the first element is the key and the second element the value.


For now, we are interested in remembering the
`mfa`
and
`size`
values of the pool configuration. #3 and #4 do exactly that. If we wanted to add more fields to the state, we just add more function clauses with the appropriate pattern. #5 ignores any options that we do not care about.


Finally, once we have gone through the entire list as in #6, we expect that that the state has been initialized. Remember that one of the valid return values of
`init/1`
is
`{:ok, state}`. Since
`init/1`
calls
`init/2`, and the empty list case in #6 would be the last function clause invoked, it should therefore return
`{:ok, state}`.


What is the curious looking line on #7? Once we reach #6, we are confident that the state has been built. That is when we can start the worker supervisor that we implemented previously. What is happening is that the server process is sending a message to itself. Because
`send/2`
returns immediately, the
`init/1`
callback is not blocked. You do not want
`init/1`
to time out, do you?


While the number of
`init/1`
functions can look overwhelming, fret not. Individually, each function is as small as it gets. Without pattern matching in the function arguments, we would need to write a large conditional to capture all the possibilities.  


6.3.3        Starting the Worker Supervisor


When the server process sends a message to itself using
`send/2`, the message is handled using
`handle_info/2`:


Listing 6.6 lib/pooly/server.ex – Callback handler for starting the worker supervisor

`defmodule Pooly.Server do`

`defstruct sup: nil, worker_sup: nil, size: nil, workers: nil, mfa: nil`

`#############`
`# Callbacks #`
`#############`

`def handle_info(:start_worker_supervisor, state = %{sup: sup, mfa: mfa, size: size}) do`
`{:ok, worker_sup} = Supervisor.start_child(sup, supervisor_spec(mfa))        #1`
`workers = prepopulate(size, worker_sup)              #2`
`{:noreply, %{state | worker_sup: worker_sup, workers: workers}} #3`
`end`

`#####################`
`# Private Functions #`
`#####################`

`defp supervisor_spec(mfa) do`
`opts = [restart: :temporary]`
`supervisor(Pooly.WorkerSupervisor, [mfa], opts)      #4`
`end`
`end`
There’s quite a bit going on in Listing 6.6. Since the state of the server process contains the top-level supervisor pid (`sup`), we invoke
`Supervisor.start_child/2`
with the supervisor pid and a supervisor specification. After that, we pass the pid of the newly created worker supervisor pid (`worker_sup`) and use it to start
`size`
number of workers. Finally, we update the state with the worker supervisor pid and newly created workers.


#1 returns a tuple with the worker supervisor pid as the second element. In #4, the supervisor specification consists of a worker supervisor as a child. Notice that instead of

`worker(Pooly.WorkerSupervisor, [mfa], opts)`
We use the supervisor variant:

`supervisor(Pooly.WorkerSupervisor, [mfa], opts)`
Here, we pass in
`restart: :temporary`
in #4 as the supervisor specification. This means that the top-level supervisor will not automatically restart the worker supervisor. This seems a bit odd. Why? The reason is that we want to do something more than having the supervisor restart the child. Because we want some custom recovery rules, we “turn off” the supervisor's default behavior of automatically restarting downed workers with
`restart: :temporary`.


Note that this version doesn’t deal with any worker recovery should crashes occur. The later versions will fix this. Let’s deal with pre-populating of the workers next.


6.3.4        Pre-populating the Worker Supervisor with Workers


Given a
`size`
option in the pool configuration, the worker supervisor can pre-populate itself with a pool of workers. The
`prepopulate/2`
function in Listing 6. 7 takes in a size and the worker supervisor pid, and builds a list of
`size`
number of workers, as seen in #1:


Listing 6.7 lib/pooly/server.ex – Prepopulating the worker supervisor with workers

`defmodule Pooly.Server do`

`#####################`
`# Private Functions #`
`#####################`

`defp prepopulate(size, sup) do`
`prepopulate(size, sup, [])`
`end`

`defp prepopulate(size, _sup, workers) when size < 1 do`
`workers`
`end`

`defp prepopulate(size, sup, workers) do`
`prepopulate(size-1, sup, [new_worker(sup) | workers]) #1`
`end`

`defp new_worker(sup) do`
`{:ok, worker} = Supervisor.start_child(sup, [[]]) #2`
`worker`
`end`
`end`
#1 Creates a list of workers that is attached to the worker supervisor.


#2 Dynamically create a worker process and attaching it to the supervisor.


6.3.5        Creating a New Worker Process


The
`new_worker/1`
function in Listing 6. 7 is worth a look. Here, we use the
`Supervisor.start_child/2`
once again to spawn the worker processes. Instead of passing in a child specification, we pass in a *list of arguments*.



The two flavors of Supervisor.start\_child/2



There are two flavors of
`Supervisor.start\_child/2`. The first one takes in a child specification:

`{:ok, sup} = Supervisor.start\_child(sup, supervisor\_spec(mfa))`
The other flavor takes in a list of arguments:

`{:ok, worker} = Supervisor.start\_child(sup, [[]])`
Which flavor should you use?
`Pooly.WorkerSupervisor`
uses a
`:simple\_one\_for\_one`
restart strategy. This means that the child specification has already been pre-defined. Which means that the first flavor is out – the second one is what you want.


The second version lets you pass *additional* arguments to the worker. What happens under the hood is that the arguments defined in the child specification when creating
`Pooly.WorkerSupervisor`
is *concatenated* with the list passed into the
`Supevisor.start\_child/2`
and the result is then passed along to the worker process during initialization.



 



The return result of
`new_worker/2`
is the pid of the newly created worker. We have not yet implemented a way of *getting a worker out* of a pool, and its dual, *putting a worker back* into the pool. There two actions are also known as *checking out* and *checking in* a worker respectively. But before we do that, we need to do a brief detour and talk about ETS in the next section.


6.3.6        Just Enough ETS


In this chapter and the next, we will make use of ETS, also known as Erlang Term Storage. This section will give you just enough background to understand the ETS-related code in this chapter and the next.


What is ETS


It is in essence a very efficient in-memory database built specially to store Erlang/Elixir data. It is able to store large amounts of data without breaking a sweat. Data access is also done in constant time.  It comes for free Erlang, which means we have to use
`:ets`
in order to access it from Elixir.


Creating a New ETS Table


Creating a table is done using
`:ets.new/2`. Let’s create a table to store my Mum’s favorite artists, their date of birth and genre:

`iex> :ets.new(:mum_faves, [])`
`12308`
The most basic form takes it an atom representing the name of the table, and an empty list of options. The return value of
`:ets.new/2`
is a table ID, which is akin to a pid. The process that created the ETS table is deemed the *owner process*. In this case, the
`iex`
process is the owner. The most common options are related to the ETS table’s *type*, *access rights* and whether it is *named*.


ETS Table Types


ETS tables come in four different flavors:


·     
`:set`
– This is the default. Its characteristics are exactly the set data structure you might have learned about in CS101 (unordered, each unique key mapping to an element).


·     
`:ordered_set`
– A sorted version of
`:set`.


·     
`:bag`
– Rows with the same keys *are allowed*, but the rows must be different.


·     
`:duplicate_bag`
– Same as
`:bag`
but without the row-uniqueness restriction.


In this chapter and the next, we are going to use
`:set`, which essentially means we don’t have to specify the table type in the list of options. If we wanted to be specific, we would create the table like so:

`iex> :ets.new(:mum_faves, [:set])`
Access Rights


Access rights control which process can read from and write to the ETS table. There are three options:


·     
`:protected`
– The owner process has full read and write permissions. All other processes can only read from it. This is the default.


·     
`:public`
– No restrictions on reading and writing.


·     
`:private`
– Only the owner process can read from and write to the table.


We will use
`:private`
tables in this chapter, because we will be storing pool-related data that other pools have no business knowing about. So let’s say my Mom is pretty shy about her eclectic music tastes, and wants to make the table private:

`iex> :ets.new(:mum_faves, [:set, :private])`
Named Tables


Notice that when we created the ETS table, we supplied an atom. This is slightly misleading because we *cannot* use
`:mum_faves`
to refer to the table without supplying the
`:named_table`
option. Therefore, to use
`:mum_faves`
instead of a unintelligible reference like
`12308`, you can do:

`iex> :ets.new(:mum_faves, [:set, :private, :named_table])`
`:mum_faves`
Note that if you try run the line above again, you will get:

`iex> :ets.new(:mum_faves, [:set, :private, :named_table])`
`** (ArgumentError) argument error``(stdlib) :ets.new(:mum_faves, [:set, :private, :named_table])`
That’s because names should be a *unique* reference to an ETS table.


Inserting and Deleting Data


Data is inserted using the
`:ets.insert/2`
function. The first argument is the table identifier (the number or the name), the second argument is the data. The data comes in the form of a tuple, where the first element is the key, and the second can be *any*, *arbitrarily nested* term. Here are a few of Mum’s favorites:

`iex> :ets.insert(:mum_faves, {“Michael Bolton”, 1953, “Pop”})`
`true`
`iex> :ets.insert(:mum_faves, {“Engelbert Humperdinck”, 1936, “Easy Listening”})`
`true`
`iex> :ets.insert(:mum_faves, {“Justin Beiber”, 1994, “Teen”})`
`true`
`iex> :ets.insert(:mum_faves, {“Jim Reeves”, 1923, “Country”})`
`true`
`iex> :ets.insert(:mum_faves, {“Cyndi Lauper”, 1953, “Pop”})``true`
We can take a look at what’s in the table using
`:ets.tab2list/1`:

`iex> :ets.tab2list(:mum\_faves)`
`[{“Michael Bolton”, 1953, “Pop”},`
`{“Cyndi Lauper”, 1953, “Pop”},`
`{“Justin Beiber”, 1994, “Teen”},`
`{“Engelbert Humperdinck”, 1936, “Easy Listening”},``{“Jim Reeves”, 1923, “Country”}]`
Note that the return result is a list, and that the elements within the list are unordered. All right, I lied. My Mum isn’t really a Justin Beiber fan[[2]](#uWwoyrKLmBpPBX94Gi5Hau2). Let’s rectify this:

`iex> :ets.delete(:mum_faves, “Justin Beiber”)`
`true`
Looking up Data


A table is of no use if we cannot retrieve data. The simplest way to do that is to use the key. What’s Michael Bolton’s birth year? Let’s find out:

`iex> :ets.lookup(:mum_faves, “Michael Bolton”)`
`[{“Michael Bolton”, 1953, “Pop”}]`
Why is the result a list? Recall that ETS supports other types, such as the
`:duplicate_bag`, which allows for duplicated rows. Therefore, the most general data structure to represent this is the humble list.


What if you wanted to search by the *year* instead? We can use
`:ets.match/2`:

`iex> :ets.match(:mum_faves, {:”$1”, 1953, :”$2”})`
`[[“Michael Bolton”, “Pop”], [“Cyndi Lauper”, “Pop”]]`
We pass in a *pattern*, which looks slightly strange at first sight. Since we are only querying using the year, we use
`:”$N`” as placeholders, where
`N`
is an integer. These numbers correspond to the order in which the elements in each matching result are presented. Let’s swap the placeholders:

`iex(20)> :ets.match(:mum_faves, {:”$2”, 1953, :”$1”})`
`[[“Pop”, “Michael Bolton”], [“Pop”, “Cyndi Lauper”]]`
You can clearly see now that the genre comes before the artiste name. What if you only cared about returning the artiste? We can use an underscore to omit the genre like so:

`iex(25)> :ets.match(:mum_faves, {:”$1”, 1953, :”_”})`
`[[“Michael Bolton”], [“Cyndi Lauper”]]`
There is much more to learn about ETS, but this is all the information you need to understand the ETS bits of the code. Let’s go back to checking out a worker form the pool.


6.3.7        Checking-out a Worker


When a consumer process checks out a worker from the pool, there are a few key logistical issues to handle such as:


·      What is the pid of the consumer process?


·      Which worker pid is the consumer process using?


The consumer process needs to be *monitored* by the server because if it dies, the server process needs to know about it and take recovery action. Once again, we are not implementing the recovery code yet, but laying the groundwork.


We also need to know which worker the consumer process so that when we can pinpoint which consumer process used which worker pid. Here’s the implementation of checking out of workers:


Listing 6.8 lib/pooly/server.ex – Checking out of a worker

`defmodule Pooly.Server do`

`#######`
`# API #`
`#######`

`def checkout do`
`GenServer.call(__MODULE__, :checkout)`
`end`
 
`#############`
`# Callbacks #`
`#############`

`def handle_call(:checkout, {from_pid, _ref}, %{workers: workers, monitors: monitors} = state) do                               #1`
`case workers do                                           #2`
`[worker|rest] ->`
`ref = Process.monitor(from_pid)                       #3`
`true = :ets.insert(monitors, {worker, ref})           #4`
`{:reply, worker, %{state | workers: rest}}`

`[] ->`
`{:reply, :noproc, state}`
`end`
`end`
`end`
We will use an ETS table to store the monitors. The implementation of the callback function is interesting. There are two cases to handle. Either we have workers left for checking out, or we don’t. In the latter case, we return
`{:reply, :noproc, state}`
signifying that no processes are available. In most examples about GenServers, you see that the
`from`
parameter is usually ignored:

`def handle_call(:checkout, _from, state) do`
`# …``end`
In this instance,
`from`
is *very* useful. Note that
`from`
is in fact a two-element tuple consisting of the client pid and a tag (a reference). In #1, we care only about the pid of the client. We use the pid of the client (`from_pid`) and get the server process to monitor it. Then in #4 we use the resulting reference and add it into the ETS table. Finally, the state is updated with one worker less.


We now need to update the
`init/1`
callback because we have introduced a new
`monitors`
field to store the monitors ETS table:


Listing 6.9 lib/pooly/server.ex – Storing a reference to the monitors ETS table into the state of the server

`defmodule Pooly.Server do`

`#############`
`# Callbacks #`
`#############`

`def init([sup, pool_config]) when is_pid(sup) do`
`monitors = :ets.new(:monitors, [:private])                #1`
`init(pool_config, %State{sup: sup, monitors: monitors})   #1`
`end``end`
#1 Update the state to store the monitors table


6.3.8        Checking-in a Worker


The reverse of checking out a worker is (wait for it) checking in. In fact, the implementation shown in Listing 6. 10 is the reverse of Listing 6. 8:


Listing 6.10 lib/pooly/server.ex – Checking in a worker

`defmodule Pooly.Server do`

`#######`
`# API #`
`#######`

`def checkin(worker_pid) do`
`GenServer.cast(__MODULE__, {:checkin, worker_pid})`
`end`

`#############`
`# Callbacks #`
`#############`

`def handle_cast({:checkin, worker}, %{workers: workers, monitors: monitors} = state) do`
`case :ets.lookup(monitors, worker) do`
`[{pid, ref}] ->`
`true = Process.demonitor(ref)`
`true = :ets.delete(monitors, pid)`
`{:no_reply, %{state | workers: [pid|workers]}}`
`[] ->`
`{:no_reply, state}`
`end`
`end`
`end`
Given a worker pid (`worker`), the entry is searched for in the
`monitors`
ETS table. If an entry is not found, nothing is done. If an entry is found, then the consumer process is de-monitored, the entry removed from the ETS table, and the
`workers`
field of the server state is updated with the addition of the pid of the worker.


6.3.9        Getting the Status of the Pool


We would like to have some insight into our pool. That is simple enough to implement:


Listing 6.11 lib/pooly/server.ex – Getting the status of the pool

`defmodule Pooly.Server do`

`#######`
`# API #`
`#######`

`def status do`
`GenServer.call(__MODULE__, :status)`
`end`

`#############`
`# Callbacks #`
`#############`

`def handle_call(:status, _from, %{workers: workers, monitors: monitors} = state) do`
`{:reply, {length(workers), :ets.info(monitors, :size)}, state}`
`end`
`end`
This gives some information about the number of workers available and the number of checked out (busy) workers.


6.4           Implementing the Top Level Supervisor


There’s one last piece before we can claim version 1 as feature complete[[3]](#u6i3m7eccaU4Iqg9jh9Wyh4).  Create
`supervisor.ex`
in
`lib/pooly`. This will be the top-level supervisor. Here’s the full implementation:


Listing 6.12 lib/pooly/supervisor.ex – The top-level supervisor

`defmodule Pooly.Supervisor do`
`use Supervisor`

`def start_link(pool_config) do`
`Supervisor.start_link(__MODULE__, pool_config)`
`end`

`def init(pool_config) do`
`children = [`
`worker(Pooly.Server, [self, pool_config])`
`]`

`opts = [strategy: :one_for_all]`

`supervise(children, opts)`
`end`
`end`
As you can see, the structure of
`Pooly.Supervisor`
is very similar to
`Pooly.WorkerSupervisor`. The
`start_link/1`
function takes a
`pool_config`. The
`init/1`
callback receives the pool configuration.


The
`children`
list consists of the
`Pooly.Server`. Recall that
`Pooly.Server.start_link/2`
takes in two arguments, first the pid of the top-level supervisor process (the one we are working on right now) and the pool configuration.


What about the worker supervisor? Why aren’t we supervising it? Now it should be clear that because it is the *server* that starts the worker supervisor, therefore it is not included here at first.


The restart strategy we use here is
`:one_for_all`. Why not say,
`:one_for_one`? Think about it for a moment.


What happens when the server crashes? It loses all its state. When the server process restarts, the state is essentially a blank slate. Therefore, the state of the server is inconsistent with the actual pool state.


What happens if the worker supervisor crashes? Then the pid of the worker supervisor would be different, along with the worker processes. Once again, the state of the server would be inconsistent with the actual pool state.


There is a *dependency* between the server process and the worker supervisor. If either goes down, it should take the other down with it – hence the
`:one_for_all`
restart strategy.


6.5           Making Pooly an OTP Application


Create a file called
`pooly.ex`
in
`lib`. We will be creating an OTP application, which serves as an entry point to Pooly. It also serves to contain convenience functions such as
`start_pool/1`
so that clients can say
`Pooly.start_pool/2`
instead of
`Pooly.Server.start_pool/2`. First, add this into
`pooly.ex`:


Listing 6. 13 lib/pooly.ex – The Pooly application

`defmodule Pooly do`
`use Application`

`def start(_type, _args) do`
`pool_config = [mfa: {SampleWorker, :start_link, []}, size: 5]`
`start_pool(pool_config)`
`end`

`def start_pool(pool_config) do`
`Pooly.Supervisor.start_link(pool_config)`
`end`

`def checkout do`
`Pooly.Server.checkout`
`end`

`def checkin(worker_pid) do`
`Pooly.Server.checkin(worker_pid)`
`end`

`def status do`
`Pooly.Server.status`
`end`
`end`
`Pooly`
uses an OTP *Application* behavior. What we have done here is to specify
`start/2`, which is called first when
`Pooly`
is initialized. We have predefined a pool configuration and a call to
`start_pool/1`
simply out of convenience.


6.6           Bringing Pooly for a Spin


First, open
`mix.exs`
and modify
`application/0`:

`defmodule Pooly.Mixfile do`
`use Mix.Project`

`def project do`
`[app: :pooly,`
`version: "0.0.1",`
`elixir: "~> 1.0",`
`build_embedded: Mix.env == :prod,`
`start_permanent: Mix.env == :prod,`
`deps: deps]`
`end`

`def application do`
`[applications: [:logger],`
`mod: {Pooly, []}] #1`
`end`

`defp deps do`
`[]`
`end``end`
#1 Start the Pooly application


Next, head to the project directory and launch
`iex`:

`% iex -S mix`
Next, fire up Observer:

`iex> :observer.start`
Select the *Applications* tab and you will see something similar to this:


![](../Images/6_4a.png)  



Figure 6.4 Version 1 of Pooly as seen from Observer


Let’s start by killing a worker. (I hope you are not reading this book aloud). You can do this by right-click on a worker process and selecting *Kill process*:


![](../Images/6_5.png)  



Figure 6.5 Killing a worker from Observer


You would realize that the supervisor spawned a new worker in the killed processes’ place.


More importantly, the crash/exit of a single worker didn’t affect the rest of the supervision tree. In other words, the crash of that single worker was isolated only to *that* worker, and didn’t affect anything else.


![](../Images/6_6.png)  



Figure 6. 6 The supervisor replaced a killed worker with a newly spawned worker


Now, what happens if we kill
`Pooly.Server`? Once again, right click on the
`Pooly.Server`
and select *Kill process* like so:


![](../Images/6_7.png)  



Figure 6. 7 Killing the Server process from Observer


This time, *all* the processes were killed and the top-level restarted *all* its child processes:


![](../Images/6_8.png)  



Figure 6. 8 Killing the Server restarted all the processes under the top-level supervisor


What just happened? Why did the killing of
`Pooly.Server`
cause everything under the top-level supervisor to die? The mere description of the effect should already yield an important clue. What is the restart strategy of the top-level supervisor?


Let’s jolt our memory a little:

`defmodule Pooly.Supervisor do`

`def init(pool_config) do`
`# …`
`opts = [strategy: :one_for_all]`

`supervise(children, opts)`
`end`
`end`
The
`:one_for_all`
restart strategy explains exactly why the killing of
`Pooly.Server`
brought down (and restarted) the rest of the children.


6.7           Exercises


1.  What happens when you kill the
`WorkerSupervisor`
process in Observer? Can you explain what happened?


2.  Shutdown and Restart values. Play around with the various shutdown and restart values. For example, in
`Pooly.WorkerSupervisor`, try changing
`opts`
from

`opts = [strategy: :simple_one_for_one,`
`max_restarts: 5,``max_seconds: 5]`
To something like

`opts = [strategy: :simple_one_for_one,`
`max_restarts: 0,``max_seconds: 5]`
Next, try changing
`worker_opts`
from

`worker_opts = [restart:  :permanent, function: f]`
To

`worker_opts = [restart:  :temporary, function: f]`
Remember to set back
`opts`
to the original value.


6.8           Summary


In this chapter, we learned about:


·      OTP Supervisor behavior


·      Different supervisor restart strategies


·      Using ETS to store state


·      How to construct supervisor hierarchies, both static and dynamic


·      The various supervisor and child specification options


·      Implementing a very basic worker pool application


We have seen how, using different restart strategies, the Supervisor can dictate how its children restart. More importantly, depending again on the restart strategy, the supervisor is able to isolate crashes to only the process affected.


Even though the first version of Pooly is simple, it allowed us to experiment with constructing both static and dynamic supervision hierarchies. In the former case, we declared in the supervision specification of
`Pooly.Supervisor`
that
`Pooly.Server`
is to be supervised. In the latter case,
`Pooly.WorkerSupervisor`
is only added to the supervision tree when
`Pooly.Server`
is initialized.


In the following chapter, we will continue to evolve the design of Pooly while adding more features it. At the same time, we will explore more advanced uses of Supervisor.





[****[1]****](#u7YNvHigi67GoJPRzPXBQf4) This was written with the voice of Mr.T in mind.




[****[2]****](#unZsK4dstzhrpK6CA9DbDs8) She isn’t a Cyndi Lauper fan either, but I was listening to “Girls just want to have fun” while writing this.




[****[3]****](#u5UHZe9erUMjrZtCEGXEoxG) A rare occurrence in the software industry.





