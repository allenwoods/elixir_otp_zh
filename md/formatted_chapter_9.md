xml version='1.0' encoding='utf-8'?



Style A ReadMe





# 1      Introduction


This chapter covers:


·      What Elixir is


·      How Elixir is different from Erlang


·      Why Elixir is a good choice over other languages


·      What Elixir/OTP is good for


·      The road ahead


Just in case you bought this book for medicinal purposes – I’m sorry, wrong book. This book is about Elixir the programming language. No other language (other than Ruby) has made me so excited and happy to work with. Even after spending more than two years of my life writing about Elixir, I still love programming in it.


There is something very special about being involved in a community that is so young and lively. I do not think any language has had at least *four* books written about it, a dedicated screencast series, and a conference – all before v1.0. I think we are really on to something here. Before we get into Elixir, I want to talk about Erlang and its legendary virtual machine, because Elixir is built on top of it.


Erlang is a programming language that excels in building soft real-time, distributed and concurrent systems. Its original use case was to program Ericsson’s telephone switches. Telephone switches basically are machines that connect calls between callers.


These switches had to be concurrent, reliable and scalable. It had to be able to handle multiple calls at the same time. It also had to be extremely reliable. No one expects her calls to be dropped halfway. Additionally, a dropped call (either due to a software/hardware fault) should not affect the rest of the calls on the switch. The switches had to be massively scalable and work with a distributed network of switches.


These *production* requirements shaped Erlang into what it is today. These exact requirements are exactly the situation we have with multi-core and web-scale.


As you will discover in the later chapters, the scheduler of the Erlang Virtual Machine automatically distributes workloads across processors. This means that you get a speedup *almost* for free if you run your program on a machine with more processors. Almost, because you will need to change your thinking in the way you approach writing programs in Erlang and Elixir in order to reap the full benefits.


Writing distributed programs, that is, programs that are running on different computers and are able to communicate with each other, involves very little ceremony.


It’s time to introduce Elixir. Elixir describes itself as *a functional, meta-programming aware language built on top of the Erlang Virtual Machine.* Let’s take this definition apart piece by piece.


Elixir is a *functional* programming language. This means that it has all the usual features you might expect such as immutable state, higher-order functions, lazy evaluation and pattern matching. We will meet all of these features and more in the later chapters.


Elixir is also a very meta-programmable language. Meta-programming can be described as code that generates code (Or, black magic). This is possible because code can be represented in data, and data can be represented as code. These facilities enable the programmer to add new constructs to the language (among other things) that other languages find difficult, or even downright impossible to do.


This book is also about OTP, a framework to build fault tolerant, scalable, and distributed applications. Unlike most frameworks, OTP comes packaged with quite a lot of good stuff. OTP comes with *three* kinds databases, a set of debugging tools, profilers, a test framework and a whole lot more. While we manage only to play with a tiny subset, this book will give you a taste of the pure awesomeness of OTP.


It is important to realize that Elixir essentially gains OTP for free, because OTP comes as part of the Erlang distribution. In case you are wondering what OTP stands for, the short answer is it used to be called **Open Telecom Platform**, which hints of Erlang’s telecom heritage. It also once again demonstrates how naming is a hard problem in computer science. This is because OTP is a general-purpose framework, and has little to do with telecom. Nowadays, OTP is just plain OTP, just like how IBM just means IBM.  


1.1           How is Elixir different from Erlang


Before we talk about how Elixir is different from Erlang, let's talk about their *similarities* first. Both Elixir and Erlang compile down to the same byte-code. This means that both Elixir and Erlang programs, when compiled, emit instructions that run on the same virtual machine.


Another wonderful feature of Elixir is that you can call Erlang code directly from Elixir, and vice versa! If, for example, you find that Elixir lacks a certain functionality that is present in Erlang, you can call the Erlang library function directly from your Elixir code.


Elixir follows most of Erlang's semantics such as message passing. Most Erlang programmers would feel right at home with Elixir.


This interoperability also means that the wealth of Erlang third-party libraries are at the disposal of the Elixir developer (that's you!). So why would you want to use Elixir instead of Erlang? There are at least two reasons – The tooling and ecosystem.


1.1.1        Tooling


Out of the box, Elixir comes with a few handy tools built in:


Interactive Elixir


The Interactive Elixir shell, or
`iex`
for short, is a REPL (read-eval-print-loop) that is similar to Ruby's
`irb`. It comes with some pretty nifty features, such as syntax highlighting and a beautiful documentation system, as shown in Figure 1.1.


![](../Images/1_1.png)  



Figure 1.1 Interactive Elixir has documentation built-in


There is more to
`iex!`
This tool allows you to connect to *nodes*, which you can think of as separate Erlang runtimes that can talk to each other. Each of this runtimes can live on the same computer, same LAN or the same network.


`iex`
has another superpower inspired by the Ruby library Pry. If you have used Pry before, you will know that it is a debugger that allows you to pry into the state of your program.
`iex`
comes with a similarly named function called the same function called
`IEx.pry`. We won’t be using this feature in the book, but this is an invaluable tool to be familiar with. Here’s a brief overview on how to use it. Let’s assume I have code like this:

`require IEx`

`defmodule Greeter do`
`def ohai(who, adjective) do`
`greeting = "Ohai!, #{adjective} #{who}"`
`**IEx.pry**`
`end``end`
The line where
`IEx.pry`
will cause the interpreter to pause, allowing me to inspect the variables that have been passed in. First, I’ll run the function:

`iex(1)> Greeter.ohai "leader", "glorious"`
`Request to pry #PID<0.62.0> at ohai.ex:6`

`def ohai(who, adjective) do`
`greeting = "Ohai!, #{adjective} #{who}"`
`IEx.pry`
`end`
`end`

`Allow? [Yn] Y`

`Once I answered yes, I get brought into
`iex`
where I can start inspecting the variables that were passed in:`

`Interactive Elixir (1.2.4) - press Ctrl+C to exit (type h() ENTER for help)`
`pry(1)> who`
`"leader"`
`pry(2)> adjective``"glorious"`
There other nice features like *autocomplete* that you will find out in the course of using
`iex.`
Almost every release of Elixir brings some nice improvements and additional helper functions to
`iex,`
so it’s worth it to keep up with the changelog!  


Testing with ExUnit


Testing aficionados will be pleased to know that there is a test framework built in called ExUnit. ExUnit has some very nice features such as being able to run *asynchronously* and also producing beautiful failure messages, as show in figure 1.2. ExUnit is able to perform nifty tricks with error reporting mainly due to *macros*, which we will not cover in this book. Nonetheless, it is a fascinating topic to explore.


![](../Images/1_2.png)  



Figure 1.2 ExUnit comes with excellent error messages


Mix


Mix is a build tool used for creating, compiling, testing Elixir projects. It is also used for managing dependencies, among other things. Think of it like
`rake`
in Ruby, and
`lein`
in Clojure. In fact, some of the first contributors to
`mix`
also wrote
`lein`. Projects such as the Phoenix web framework have used Mix to great effect, such as building generators that reduce writing needless boilerplate.


Standard Library


Elixir comes shipped with an excellent standard library. Data structures such as ranges, strict and lazy enumeration APIs and a sane way to manipulate strings are just some of the nice things that come packaged.


While Elixir might not be the best language to write scripts, there are familiar sounding libraries such as
`Path`
and
`File`. The documentation is also a joy to use. Explanations are clear and concise, with examples on how to use the various libraries and its functions.


Elixir has modules that are *not* in the standard Erlang library. My favorite of these is
`Stream`. Streams are basically composable, lazy enumerables. They are often used to model potentially infinite streams of value.


Elixir has also added functionality to the OTP framework. For example, it has added quite a number of abstractions such as
`Agent`
to handle state,
`Task`
to handle one-off asynchronous computation. Both of these are built upon
`GenServer`
(this stands for generic server) that comes with OTP by default.


Metaprogramming


Elixir has LISP-like macros built into it, minus the parentheses. Macros are used to extend the Elixir language by giving it new constructs expressed in existing ones. The language implementation employs the use of macros throughout the language. Library authors also use it extensively to cut down on boilerplate code.


1.1.2        Ecosystem


Elixir being a relatively new programming language built on top of a solid and proven language definitely has its advantages.


Thank You, Erlang!


I think the biggest gain for Elixir is the years of experience and tooling available from the Erlang community. Almost any Erlang library can be used in Elixir with little effort. Elixir developers do not have to reinvent the wheel in order to build rock-solid applications. Instead, they can happily rely on OTP. Instead, they can focus on building additional abstractions based on existing libraries.


Learning Resources


The excitement of Elixir has led to a wellspring of learning resources (not to beat my own drum here). There are already multiple sources for screencasts, books and conferences. In fact, once you have learned to translate from Elixir to Erlang, you will also stand to benefit from the numerous well-written Erlang books such as Learn You Some Erlang for Great Good! and Designing for Scalability with Erlang/OTP.


Phoenix


Phoenix is a web framework written in Elixir that has gotten a lot of developers very excited, and for good reason. For starters, response times in Phoenix can reach *microseconds*. Phoenix proves that you can have *both* a high performance and simple framework coupled with built-in support for WebSockets and backed the awesome power of OTP.


It Is Still Evolving


Elixir is still constantly evolving and exploring new ideas. One of the most interesting things I've seen come up are the concurrency abstractions that are being worked on. Even better, the Elixir core team is constantly on the hunt for great ideas from other languages. There is already (at least!) Ruby, Clojure and F# DNA in Elixir if you know where to look.


1.2           Why Elixir and not X?


On many occasions when I give a talk about Elixir, or write about it, the same question inevitably pops up: Should I learn Elixir over *X*? X is usually Clojure, Scala, or Golang. This question usually stems from two other questions. First, whether Elixir is gaining traction. Second is the availability of Elixir jobs. Here is my response to these questions:


Elixir is a very young language (around 5 years old at this point of writing), so it will take time. You could use this to your advantage. Firstly, functional programming is on the rise. There are certain principles that remain more or less the same in most functional programming languages. This means that whether it's Scala, Clojure or Erlang, *these skills are portable*.


Erlang seems to be gaining popularity again. There is also a surge in interest in distributed systems and the Internet of Things (IoT), domains that are right up Elixir's alley.


I have a gut feeling Elixir will take off very soon. It's like Java in its early days. Not many bothered with it when it first came out. But then, the early adopters were hugely rewarded. Same story goes for Ruby. There is definitely an advantage to being ahead of the curve.


It would be too selfish of me to keep everyone else from learning and experiencing this wonderful language. Cast your doubts aside, have a little faith, and enjoy the ride!


1.3           What is Elixir/OTP good for?


Everything Erlang is great for would also apply to Elixir. Elixir and OTP combined both provide facilities to build concurrent, scalable, fault-tolerant and distributed programs. These include, but obviously not limited to:


·      Chat servers (WhatsApp, Ejabberd)


·      Game servers (Wooga)


·      Web frameworks (Phoenix)


·      Distributed databases (Riak and CouchDB)


·      Real-time bidding servers


·      Video streaming services


·      Long running services/daemons


·      Command line applications


From the list, you can probably gather that Elixir is great at building server side software – And you'll be right! These software share similar characteristics. They have to:


·      Serve multiple users and clients, often numbering in the thousands to millions, and yet manage to maintain a decent level of responsiveness


·      Stay up even in the event of failure, or have graceful failover mechanisms


·      Scale gracefully, either by adding more CPU cores or additional machines


Elixir is no wonder drug (pun intended). You probably will not want to do any image processing, computationally intensive tasks, or build GUI applications on Elixir. You would not use Elixir to build hard real-time systems. For example, you should not use Elixir to write software for a F-22 fighter jet.


But hey, don't let me tell you what you can or cannot do with Elixir. Let your creativity flow. That's why programming is so awesome.


1.4           The Road Ahead


Now that we've covered some background on Elixir, Erlang and the OTP framework, the following appetite-whetting sections give a high level overview of what's the come.


1.4.1        A Sneak Preview of OTP Behaviours


Say you want to build a weather application. You decide to get some VC funding and before you know it, you are funded.


After some thinking, you realize that what you are building essentially is a simple client-server application. Of course, you don’t tell your investors this. Basically clients (this could come from via HTTP for example) would make request and your application has to perform some computation and return the results to each client in a timely manner.


So you go on implementing your weather application and it goes to production. Your weather application goes viral and suddenly your users are encountering all sorts of issues like slow load times and even worse, service disruptions. You attempt to do some performance-profiling, tweak settings here and there, maybe even try to add more concurrency.


Everything seems OK for a while, but that’s just the calm before the storm. Eventually, your users are experiencing the same issues again, except that this time you are getting errors of deadlocks and other weird error messages. In the end, you give up and write a long blog post on why your startup failed why you should have built your startup in Node.js or Golang. The post goes #1 on Hacker News for a month.


While this book will *not* show you how to get VC funding, it will show you how to build a weather service using OTP, among other fun things. The OTP framework is what gives BEAM languages (Erlang, Elixir, etc.) its superpowers and comes bundled together when you install Elixir.


We have mentioned that OTP is used to build concurrent, scalable, fault-tolerant and distributed programs. One of the most important concepts in OTP is the notion of *behaviours*. Behaviours can be thought of as a contract between you and OTP.


When you use a behaviour, OTP expects you to fill in certain functions. In exchange for that, OTP takes care of a whole slew of issues like message handling (implementing synchronous or asynchronous), concurrency errors (deadlocks and race conditions), fault-tolerance and failure handling. These issues are general – almost every respectable client/server program will have to handle them somehow, and OTP steps in and handles all these for you. Furthermore, these generic bits have been used in production has been battle-tested for years.


In this book, we will work with two of the most used *behaviours*, the GenServer and the Supervisor. There are of course other behaviours. Once you are comfortable with learning how to use the aforementioned behaviours, using other behaviours would be pretty straightforward.


While you could very well roll your own Supervisor behaviour for example, there is simply no good reason for 99.999999999% of the time. The implementers have thought long and hard about the features that needed to be included in most client-server programs, and have also accounted for concurrency errors and all sorts of edge cases. How do you use an OTP behaviour? Here's a minimal implementation of a weather service that uses a GenServer behaviour:


Listing 1.1 An example of a GenServer.

`defmodule WeatherService do`
`use GenServer # <- This brings in GenServer behaviour`

`# this is a synchronous request`
`def handle_call({:temperature, city}, _from, state) do`
`# ...`
`end`

`# this is an asynchronous request`
`def handle_cast({:email_weather_report, email}, state) do`
`# ...`
`end`
`end`
While above implementation is obviously incomplete, the important thing to realize (and you will see this as you work through the book) is what are the things you do *not* need to do. For example, you do not have to implement *how* to handle a synchronous or an asynchronous request. I will leave you in suspense for now (anyway, it's a sneak preview), but we will build the same application *without* OTP and then *with* OTP.


While OTP might look extremely complicated and scary at first sight, you will see that this is not the case as you work through the examples in the book.


*The best way to learn how something works is to implement it yourself*. In that spirit, you will learn how to implement the Supervisor behaviour from scratch. The point of this is to demonstrate that there is really not much magic involved, just that the language provides the necessary tools to build out these useful abstractions.


We will also implement a worker pool application from scratch and evolve it in stages. This builds upon the previous GenServer and Supervisor chapters.


1.4.2        Distribution for Load-Balancing and Fault-Tolerance


Elixir and OTP is an excellent candidate to build distributed systems. In this book, we will build *two* distributed applications, highlighting two different uses of distribution.


One reason you might want to create a distributed application is to spread the load across multiple computers. You will create a load tester and see how you can exploit distribution to scale up the capabilities of your application.


You will see how given the message passing oriented nature of Elixir and the distribution primitives available make building distributed applications a much more pleasant experience compared to other languages and platforms.


Another reason why you might require distribution is for fault-tolerance. If one node fails, you would want another node to stand in its place. You will see how to create an application that does this too.


1.4.3        Dialyzer and Type-Specifications


Since Elixir is a dynamic language, we need to be wary of introducing type errors in our programs. Therefore, one aspect of reliability is to make sure that is type-safe.


Dialyzer is a tool in OTP that aims to detect some of these problems. You will learn how to use Dialyzer in a series of examples. You will also learn about the limitations of Dialyzer.


Finally, you will see how to help Dialyzer overcome some of these limitations with the use of type specifications. You will also learn how type specifications, besides helping Dialyzer out, also serve as documentation. For example, this is taken from the List module:


Listing 1.2 An example of a function that has been annotated with type specifications.

`@spec foldl([elem], acc, (elem, acc -> acc)) :: acc when elem: var, acc: var`
`def foldl(list, acc, function) when is_list(list) and is_function(function) do`
`:lists.foldl(function, acc, list)``end`
After learning about Dialyzer and type specifications, you will come to appreciate type specifications and how they can help make your programs clearer and safer.


1.4.4        Property and Concurrency Testing


The last two chapters are dedicated to property-based and concurrency testing. In particular, we will learn how to use QuickCheck and Concuerror respectively. Both of these tools do not come with Elixir or OTP by default. However, both tools are extremely useful in revealing bugs that traditional unit-testing tools do not.


We will learn about QuickCheck for property-based testing, and learn how property-based testing turns traditional unit testing on its head. Instead of thinking about specific examples as in unit-testing, property-based testing forces you to come up with general properties in which your tested code should hold. Once you have created a property, you can test it against hundred and even thousands of *generated* test input. Here’s an example saying that reversing a list twice gives you back the same list:


Listing 1.3 An example a property test.

`@tag numtests: 100`
`property "reverse is idempotent" do`
`forall l <- list(char) do`
`ensure l |> Enum.reverse |> Enum.reverse == l`
`end``end`
This will generate a hundred lists and asserts that the above property holds for each generated list.


The other tool that we will explore is Concuerror. Concuerror is a tool borne out of academia yet has seen real-world uses. We will learn how Concuerror reveals hard to detect concurrency bugs such as deadlocks and race conditions. Through a series of intentionally buggy examples, you will use Concuerror to reveal the bugs.


1.5           Summary


In this chapter, we’ve looked at the motivations behind the creation of Erlang, and how it perfectly fits into the multi-core and web-scale phenomenon we have today. We then learned about the motivations of Elixir, and presented a few reasons of why Elixir is better than Erlang, such as Elixir’s standard library and tool chain. We also looked at a few examples that are a perfect use case for Elixir and OTP.


The other half of this chapter gave an overview of what’s to come. We began with a brief introduction of OTP, and a sneak peek at implementing a weather service using OTP. We then talked about distribution for load balancing and distribution. As you will soon seen, the distribution primitives that Elixir and the OTP provide make it way easier to write distributed programs compared to other languages that you may have used. Finally, we explored some of the tools that help make your code more reliable, namely Dialyzer, QuickCheck and Concuerror.


In the next chapter, we hit the ground running with a whirlwind tour of the language features of Elixir. You will learn about the core data types, pattern matching, recursion, writing functions and more!




